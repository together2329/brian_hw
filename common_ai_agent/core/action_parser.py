"""
Action parsing utilities for ReAct-style LLM output.

Extracted from src/main.py. Consolidates duplicated parsing logic that also
existed in core/agent_runner.py.

Public API:
  sanitize_action_text(text)
  parse_all_actions(text, debug=False)
  parse_implicit_actions(text, debug=False)
  parse_tool_arguments(args_str)
  parse_value(text)
  _strip_native_tool_tokens(text)
  _convert_all_glm_tool_calls(text, xml_params_to_action_fn)
  _extract_annotation_ranges(text)
  KNOWN_TOOLS  (frozenset)
"""
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.text_utils import strip_thinking_tags as _strip_thinking_tags


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

KNOWN_TOOLS: frozenset = frozenset({
    'read_file', 'write_file', 'run_command', 'list_dir', 'grep_file',
    'read_lines', 'find_files', 'replace_in_file', 'replace_lines',
    'git_diff', 'git_status', 'todo_write', 'todo_update',
    'background_task', 'background_output', 'background_cancel', 'background_list',
    'read_image',
    'analyze_verilog_module', 'find_signal_usage', 'find_module_definition',
    'extract_module_hierarchy', 'generate_module_testbench', 'find_potential_issues',
    'analyze_timing_paths', 'generate_module_docs', 'suggest_optimizations',
})

# ---------------------------------------------------------------------------
# Markdown code-fence stripping — prevents LLM "thought demo" tool calls
# inside ``` fences from being executed as real tool calls.
# ---------------------------------------------------------------------------

def _strip_markdown_fences(text: str) -> str:
    """Replace markdown code fences that contain tool-call examples.

    LLMs sometimes embed tool-call examples inside ``` fences for illustration.
    Without this filter, the parser would extract and execute those fake calls.

    Unlike the old blanket-strip approach, this only replaces code blocks that
    actually contain tool-call patterns (Action:, <tool_call>, <invoke>, etc.).
    Legitimate code blocks (directory trees, code snippets, etc.) are preserved.

    Strategy: replace only tool-call-containing fence blocks with a placeholder
    that cannot match any tool-call regex.
    """
    # Patterns that indicate a code fence contains tool-call examples
    _TOOL_CALL_INDICATORS = re.compile(
        r'(?:Action|tool_call)\s*:\s*\w+\s*\(|'           # Action: tool(
        r'<\s*/?\s*(?:tool_call|invoke|tool_use|tool|parameter|tool_calls)[>\s]|'  # XML/DSML tags
        r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"',  # bare JSON tool call
        re.IGNORECASE,
    )

    # Match ``` or ~~~ fences: opening, optional lang, content, closing
    _FENCE_RE = re.compile(
        r'(```|~~~)\s*(\w*)\s*\n(.*?)\n\1',
        re.DOTALL,
    )

    def _replace(m: re.Match) -> str:
        content = m.group(3)
        if _TOOL_CALL_INDICATORS.search(content):
            _lang = m.group(2) or ''
            _content_len = len(content)
            return f'{m.group(1)}{_lang}\n[CODE_FENCE({_content_len} chars)]\n{m.group(1)}'
        # No tool-call patterns — leave the code block intact
        return m.group(0)

    return _FENCE_RE.sub(_replace, text)


# ---------------------------------------------------------------------------
# Tag extraction with nesting depth tracking
# ---------------------------------------------------------------------------

def _extract_tag(text: str, tag_name: str, with_positions: bool = False):
    """Extract content from the first non-nested occurrence of an XML tag.

    Unlike naive <tag>(.*?)</tag> regex, this counts nesting depth so
    <tool_call>...<tool_call>inner</tool_call>...</tool_call> correctly
    extracts the outer content without false matches on inner tags.

    Inspired by leaked Claude Code's extractTag() — see
    leaked-claude-code/utils/messages.ts.

    Args:
        text: String containing XML.
        tag_name: Tag name to extract (e.g. 'tool_use', 'tool_call').
        with_positions: If True, return (content, tag_start, tag_end) tuple.
            If False, return content string only.

    Returns:
        Content between tags, tag_start, tag_end (if with_positions=True).
        Content string or None (if with_positions=False).
    """
    if not text.strip() or not tag_name.strip():
        return (None, -1, -1) if with_positions else None

    esc_tag = re.escape(tag_name)
    open_re = re.compile(r'<' + esc_tag + r'(?:\s+[^>]*)?>', re.IGNORECASE)
    close_re = re.compile(r'</' + esc_tag + r'>', re.IGNORECASE)

    # Find first opening tag
    open_m = open_re.search(text)
    if not open_m:
        return (None, -1, -1) if with_positions else None

    tag_start = open_m.start()
    depth = 1
    pos = open_m.end()
    while pos < len(text) and depth > 0:
        # Check for nested opening tag first
        nested_open = open_re.match(text, pos)
        if nested_open:
            depth += 1
            pos = nested_open.end()
            continue

        # Check for closing tag
        close_m = close_re.match(text, pos)
        if close_m:
            depth -= 1
            if depth == 0:
                tag_end = close_m.end()
                if with_positions:
                    return (text[open_m.end():close_m.start()], tag_start, tag_end)
                return text[open_m.end():close_m.start()]
            pos = close_m.end()
            continue

        pos += 1

    return (None, -1, -1) if with_positions else None


# ---------------------------------------------------------------------------
# sanitize_action_text
# ---------------------------------------------------------------------------

def sanitize_action_text(text: str) -> str:
    """Sanitize common LLM output errors in Action calls.

    Fixes patterns like:
      **Action:** spawn_plan(...)  ->  Action: spawn_plan(...)
      end_line=26")                ->  end_line=26)
    """
    # Remove markdown bold around "Action:"
    text = re.sub(r'\*\*(?:Action|tool_call):\*\*', 'Action:', text)
    text = re.sub(r'\*\*(?:Action|tool_call)\*\*:', 'Action:', text)
    text = re.sub(r'tool_call:', 'Action:', text)
    # Normalize lowercase "action:" to "Action:" (GLM-4.7 sometimes generates lowercase)
    text = re.sub(r'(?m)^action:', 'Action:', text)
    # Korean/Japanese fallbacks: LLM sometimes outputs localized tool-call prefixes
    text = re.sub(r'(?m)^작업\s*:', 'Action:', text)       # Korean "작업:"
    text = re.sub(r'(?m)^동작\s*:', 'Action:', text)       # Korean "동작:"
    text = re.sub(r'(?m)^実行\s*[:：]', 'Action:', text)    # Japanese "実行:"
    text = re.sub(r'(?m)^アクション\s*[:：]', 'Action:', text)  # Japanese "アクション:"
    # Pattern: number followed by quote then closing paren/comma
    text = re.sub(r'=(\d+)"([,\)])', r'=\1\2', text)
    text = re.sub(r"=(\d+)'([,\)])", r'=\1\2', text)
    return text


# ---------------------------------------------------------------------------
# _convert_all_glm_tool_calls
# ---------------------------------------------------------------------------

def _convert_all_glm_tool_calls(text: str, xml_params_to_action_fn: Callable) -> str:
    """Convert GLM 4.7 style XML tool calls to Action: format.

    Handles tag name variations and typos:
      <tool>list_dir</tool><parameter><path>.</path></parameter>
      <action><execute>read_file</execute><paramater><path>f.py</path></paramater>
      <tool>grep_file</tool><paratemeter><pattern>x</pattern></paratemeter>
    """
    result = text
    tool_tag_re = re.compile(
        r'<(tool|action|execute|func\w*)\s*>'
        r'\s*(?:<(execute|tool)\s*>\s*)?'
        r'(\w+)'
        r'\s*(?:</\w+>\s*)?'
        r'</\w+>'
    )

    matches = list(tool_tag_re.finditer(result))
    if not matches:
        return text

    for m in reversed(matches):
        tool_name = m.group(3)
        after_tool = result[m.end():]

        param_re = re.match(
            r'\s*<(p(?:ar|ra)\w*)\s*>'
            r'(.*)'
            r'</(p(?:ar|ra)\w*)\s*>',
            after_tool,
            re.DOTALL
        )

        if param_re:
            params_block = param_re.group(2)
            total_end = m.end() + param_re.end()
            action_str = xml_params_to_action_fn(tool_name, params_block)
            result = result[:m.start()] + action_str + result[total_end:]
        else:
            action_str = f"\nAction: {tool_name}()\n"
            result = result[:m.start()] + action_str + result[m.end():]

    return result


# ---------------------------------------------------------------------------
# _strip_native_tool_tokens
# ---------------------------------------------------------------------------

# Aliases from LLM-invented tool names to actual registered tool names
_TOOL_NAME_ALIASES: Dict[str, str] = {
    "execute_command":   "run_command",
    "run_shell_command":  "run_command",
    "shell_command":      "run_command",
    "bash":             "run_command",
    "bash_command":     "run_command",
    "run_shell":        "run_command",
    "execute_bash":     "run_command",
    "read":             "read_file",
    "open_file":        "read_file",
    "list_directory":   "list_dir",
    "ls":               "list_dir",
    "search":           "grep_file",
    "grep":             "grep_file",
    "find":             "find_files",
    "write":            "write_file",
    "create_file":      "write_file",
    "edit_file":        "replace_in_file",
    "patch_file":       "replace_in_file",
}


def _resolve_tool_name(name: str) -> str:
    """Map LLM-invented or aliased tool names to registered ones."""
    return _TOOL_NAME_ALIASES.get(name, name)


def _convert_tool_use_xml(text: str, xml_params_to_action_fn: Callable) -> str:
    """Convert Anthropic-style <tool_use> XML to Action: format.

    Handles:
      <tool_use>
        <server_name>...</server_name>
        <tool_name>list_dir</tool_name>
        <arguments>
          <path>.</path>
        </arguments>
      </tool_use>
      <tool_use id="toolu_xxx">...</tool_use>  (also nested, with attributes)

    Uses depth-counting _extract_tag to handle nested same-name tags correctly.
    Tag positions from _extract_tag ensure we always replace the exact match.
    """
    result = text
    while True:
        block, tag_start, tag_end = _extract_tag(result, 'tool_use', with_positions=True)
        if block is None:
            break

        # Extract tool_name from the block
        name_m = re.search(r'<tool_name>\s*(\w+)\s*</tool_name>', block)
        if not name_m:
            # No tool name found — strip the tag wrapper but keep content
            result = result[:tag_start] + block.strip() + result[tag_end:]
            continue

        tool_name = _resolve_tool_name(name_m.group(1))
        # Extract <arguments>...</arguments> block
        args_block = _extract_tag(block, 'arguments')
        if args_block:
            replacement = xml_params_to_action_fn(tool_name, args_block)
        else:
            replacement = f"\nAction: {tool_name}()\n"

        result = result[:tag_start] + replacement + result[tag_end:]

    return result


def _normalize_dsml_brackets(text: str) -> str:
    """Convert DSML corner brackets 〈〉 to standard angle brackets <>.

    Some LLMs (DeepSeek) emit tool call XML using U+300C LEFT CORNER BRACKET
    and U+300D RIGHT CORNER BRACKET to avoid triggering native tool-call
    parsers.  We normalize them early so all downstream patterns work.
    """
    # ── Corner brackets: U+300C 〈  U+300D 〉 ──
    text = text.replace('\u300c', '<').replace('\u300d', '>')
    # ── Fullwidth brackets: U+FF1C ＜  U+FF1E ＞ ──
    text = text.replace('\uff1c', '<').replace('\uff1e', '>')
    return text


def _convert_dsml_invoke(text: str) -> str:
    """Convert DSML <invoke> blocks to Action: format.

    DSML (DeepSeek Markup Language) format:
      <tool_calls>
        <invoke name="tool_name">
          <parameter name="key" string="true">value</parameter>
          <parameter name="num" string="false">42</parameter>
        </invoke>
      </tool_calls>

    This is the non-native tool-call format emitted by DeepSeek models
    when native tool calling is disabled.  Each <invoke> block contains
    one tool call; <parameter> tags carry name/string attributes.
    """
    result = text

    # Strip the outer <tool_calls> wrapper (with optional attributes)
    result = re.sub(r'<\s*tool_calls[^>]*>\s*', '', result)
    result = re.sub(r'\s*<\s*/\s*tool_calls\s*>', '', result)

    # Process each <invoke name="X">...</invoke> block
    # Use a tag-with-attributes regex that captures name="X"
    invoke_open_re = re.compile(
        r'<\s*invoke\s+[^>]*\bname\s*=\s*"([^"]+)"[^>]*>',
        re.IGNORECASE,
    )
    invoke_close_re = re.compile(r'<\s*/\s*invoke\s*>', re.IGNORECASE)

    # Also handle corner-bracket-normalized edge case: <invoke name=X>
    invoke_open_re2 = re.compile(
        r'<\s*invoke\s+[^>]*\bname\s*=\s*([^\s>]+)[^>]*>',
        re.IGNORECASE,
    )

    while True:
        m = invoke_open_re.search(result)
        if not m:
            break

        tool_name = m.group(1)
        block_start = m.end()

        # Find matching </invoke> — depth-counted (nested <invoke> not expected but be safe)
        depth = 1
        pos = block_start
        block_end = -1
        while pos < len(result) and depth > 0:
            nested_open = invoke_open_re.match(result, pos)
            nested_close = invoke_close_re.match(result, pos)
            if nested_open:
                depth += 1
                pos = nested_open.end()
                continue
            if nested_close:
                depth -= 1
                if depth == 0:
                    block_end = nested_close.start()
                    tag_end = nested_close.end()
                    break
                pos = nested_close.end()
                continue
            pos += 1

        if block_end == -1:
            # No closing tag — broken DSML, skip this <invoke>
            result = result[:m.start()] + result[m.end():]
            continue

        block_content = result[block_start:block_end]

        # Extract <parameter name="key" string="true|false">value</parameter>
        params: list = []
        param_re = re.compile(
            r'<\s*parameter\s+'
            r'(?:[^>]*?\bname\s*=\s*"([^"]+)")'
            r'(?:[^>]*?\bstring\s*=\s*"(true|false)")?'
            r'[^>]*>'
            r'(.*?)'
            r'<\s*/\s*parameter\s*>',
            re.DOTALL | re.IGNORECASE,
        )
        for pm in param_re.finditer(block_content):
            key = pm.group(1)
            is_str = pm.group(2) != "false"  # default to string=true
            raw_val = pm.group(3).strip()
            if is_str:
                params.append((key, json.dumps(raw_val, ensure_ascii=False)))
            else:
                # Try to parse as number, fall back to raw
                try:
                    val = int(raw_val)
                except ValueError:
                    try:
                        val = float(raw_val)
                    except ValueError:
                        val = raw_val  # keep as-is, unquoted
                params.append((key, str(val)))

        if params:
            args_str = ", ".join(f"{k}={v}" for k, v in params)
            action = f"\nAction: {_resolve_tool_name(tool_name)}({args_str})\n"
        else:
            action = f"\nAction: {_resolve_tool_name(tool_name)}()\n"

        result = result[:m.start()] + action + result[tag_end:]

    return result


def _strip_native_tool_tokens(text: str) -> str:
    """Strip native tool call tokens and convert to ReAct Action: format.

    Handles GLM 4.7, Qwen, DeepSeek, Mistral native formats:
      <think>...</think>           — reasoning tokens
      <tool_call>{json}</tool_call> — JSON tool calls (depth-counting extract)
      <tool>name</tool><parameter>  — XML tool calls
      <tool_use>...</tool_use>      — Anthropic-style XML (GLM imitation)
      <invoke name="X">            — DSML (DeepSeek non-native) parameter blocks
      bare function calls           — prepends Action: for known tools
      bare JSON {"name":...,"arguments":...} — fallback parsing

    Safety hardening:
      - Markdown code fences (```) are stripped BEFORE parsing so LLM
        "example" tool calls don't get executed.
      - Nested same-name XML tags use depth-counting _extract_tag().
      - DSML corner brackets 〈〉 (U+300C/U+300D) are normalized to <>.
    """
    # ── Safety: strip markdown code fences first ──
    text = _strip_markdown_fences(text)

    # ── Normalize DSML corner brackets to standard angle brackets ──
    text = _normalize_dsml_brackets(text)

    # Strip reasoning tokens leaked into content
    text = _strip_thinking_tags(text)

    def _json_tool_call_to_action(json_str: str) -> str:
        try:
            data = json.loads(json_str.strip())
            name = data.get("name", "")
            args = data.get("arguments", {})
            if name and isinstance(args, dict):
                args_str = ", ".join(f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in args.items())
                return f"\nAction: {name}({args_str})\n"
        except (json.JSONDecodeError, AttributeError):
            pass
        return ""

    def _xml_params_to_action(tool_name: str, params_block: str) -> str:
        params = re.findall(r'<(\w+)>(.*?)</\1>', params_block, re.DOTALL)
        if tool_name and params:
            args_str = ", ".join(f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in params)
            return f"\nAction: {tool_name}({args_str})\n"
        elif tool_name:
            return f"\nAction: {tool_name}()\n"
        return ""

    def _func_call_to_action(content: str) -> str:
        content = content.strip()
        if re.match(r'^\w+\s*\(', content):
            return f"\nAction: {content}\n"
        return content

    # Pattern 0a: <tool_use>...</tool_use> — Anthropic-style / GLM imitation XML
    text = _convert_tool_use_xml(text, _xml_params_to_action)

    # Pattern 0a.5: DSML <invoke> blocks — DeepSeek non-native parameter format
    # Must run BEFORE the <tool_calls> strip below (DSML also wraps in <tool_calls>)
    text = _convert_dsml_invoke(text)

    # Pattern 0b: DeepSeek tool_call JSON blocks (non-native tool call mode)
    # Format: <tool_call">{"name": "...", "arguments": {...}}</tool_call">
    # May be wrapped in <tool_calls>...</tool_calls> for multiple calls.
    # Uses depth-counting _extract_tag when blocks are properly paired.
    # Strip outer <tool_calls> wrapper first (keeps inner <tool_call"> blocks)
    text = re.sub(r'<tool_calls>\s*', '', text)
    text = re.sub(r'\s*</tool_calls>', '', text)

    # Use depth-counting extraction for <tool_call> blocks with proper </tool_call> close
    while True:
        block, tag_start, tag_end = _extract_tag(text, 'tool_call', with_positions=True)
        if block is None:
            break
        # Try JSON first
        action = _json_tool_call_to_action(block)
        if action:
            text = text[:tag_start] + action + text[tag_end:]
        else:
            # Not JSON — try as direct function call
            fc = _func_call_to_action(block)
            text = text[:tag_start] + fc + text[tag_end:]

    # Handle truncated: <tool_call"> without closing tag (end-of-stream truncation)
    text = re.sub(
        r'<tool_call">\s*([^{]*?\{.*?\}?)\s*$',
        lambda m: _json_tool_call_to_action(m.group(1))
        or _func_call_to_action(m.group(1)),
        text,
        flags=re.DOTALL,
    )

    # Pattern 0c: <tool_call>func(args)</tool_call> — direct function call inside tag
    text = re.sub(
        r'<tool_call>\s*(\w+\s*\([^<]*\))\s*(?:</tool_call>)?',
        lambda m: _func_call_to_action(m.group(1)),
        text, flags=re.DOTALL
    )

    # Pattern 1: JSON-based bare tool calls — {"name": "...", "arguments": {...}}
    # The previous naive regex couldn't handle nested braces in arguments.
    # Now use a JSON-aware extractor that counts brace depth.
    text = _extract_bare_json_tool_calls(text, _json_tool_call_to_action)

    # Pattern 2: GLM-style XML tool calls
    text = _convert_all_glm_tool_calls(text, _xml_params_to_action)

    # Pattern 3: Strip remaining special tokens
    native_tokens = [
        'tool_call_begin', 'tool_call_end',
        'tool_calls_section_begin', 'tool_calls_section_end',
        '<|tool_call|>', '<|tool_calls|>',
        '<|start_header_id|>tool_call<|end_header_id|>',
    ]
    for token in native_tokens:
        text = text.replace(token, '')

    text = re.sub(r'<\|(?:tool_call|tool_calls|functions)[^|]*\|>', '', text)
    text = re.sub(r'</?(?:tool_call|tool_calls|tool|invoke|action|execute|func\w*|p(?:ar|aram)\w*)>', '', text)

    # Pattern 4: Two-line "Action: tool_name\nAction Input: {...}" → single-line
    # Common in LangChain/OpenAI format; LLM may output this instead of Action: tool(args)
    # Also handles variants: "Action Input:", "Action input:", "arguments:"
    def _merge_two_line_action(m: re.Match) -> str:
        tool_name = _resolve_tool_name(m.group(1))
        args_block = m.group(2)
        # Try JSON first
        try:
            data = json.loads(args_block.strip())
            if isinstance(data, dict):
                args_str = ", ".join(
                    f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in data.items()
                )
                return f"\nAction: {tool_name}({args_str})\n"
        except (json.JSONDecodeError, AttributeError):
            pass
        # Fallback: treat as raw string arg
        return f"\nAction: {tool_name}(command={json.dumps(args_block.strip(), ensure_ascii=False)})\n"

    text = re.sub(
        r'(?:^|\n)\s*[Aa]ction\s*:\s*(\w+)\s*\n+\s*[Aa]ction\s*[Ii]nput\s*:\s*(.*?)(?=\n\s*(?:[Aa]ction|Thought|Observation|Final|$))',
        _merge_two_line_action,
        text,
        flags=re.DOTALL,
    )

    # Pattern 4b: "Action: tool_name\nAction: {json}" — LLM variant where the
    # second line uses "Action:" instead of "Action Input:" before JSON args.
    # Without this fixup, the bare `Action: tool_name` line (no `(`) is silently
    # dropped by parse_all_actions and the tool call never executes — observed in
    # tb-gen runs where todo_update(status='approved') vanished and the agent
    # got stuck reviewing the same task 50 turns until TODO_STAGNATION fired.
    # Only triggers when the second-line content starts with `{` (JSON object).
    _two_line_json_re = re.compile(
        r'(?:^|\n)\s*[Aa]ction\s*:\s*(\w+)\s*\n+\s*[Aa]ction\s*:\s*(?=\{)'
    )
    _out: List[str] = []
    _pos = 0
    while True:
        _m = _two_line_json_re.search(text, _pos)
        if not _m:
            _out.append(text[_pos:])
            break
        _out.append(text[_pos:_m.start()])
        _tool = _resolve_tool_name(_m.group(1))
        _json_start = _m.end()
        # Walk balanced braces (string- and escape-aware) to find the JSON end
        _depth = 0
        _in_str = False
        _esc = False
        _i = _json_start
        while _i < len(text):
            _c = text[_i]
            if _esc:
                _esc = False
            elif _c == '\\':
                _esc = True
            elif _c == '"' and not _esc:
                _in_str = not _in_str
            elif not _in_str:
                if _c == '{':
                    _depth += 1
                elif _c == '}':
                    _depth -= 1
                    if _depth == 0:
                        _i += 1
                        break
            _i += 1
        if _depth != 0:
            _out.append(_m.group(0))
            _pos = _m.end()
            continue
        _json_block = text[_json_start:_i]
        try:
            _data = json.loads(_json_block)
        except (json.JSONDecodeError, AttributeError):
            _data = None
        if isinstance(_data, dict):
            _args = ", ".join(
                f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in _data.items()
            )
            _out.append(f"\nAction: {_tool}({_args})\n")
        else:
            _out.append(_m.group(0))
        _pos = _i
    text = ''.join(_out)

    # Pattern 5: Bare function calls without Action: prefix (Qwen / GLM style)
    # First split inline tool calls: "tool1(...) tool2(...)" → separate lines
    _tools_pattern = '|'.join(re.escape(t) for t in KNOWN_TOOLS)
    text = re.sub(
        r'\)\s+(' + _tools_pattern + r')\s*\(',
        r')\nAction: \1(',
        text,
    )
    # Then catch remaining bare calls at line start
    text = re.sub(
        r'^(\s*)(' + _tools_pattern + r')\s*\(',
        r'\1Action: \2(',
        text,
        flags=re.MULTILINE
    )

    return text.strip()


# ---------------------------------------------------------------------------
# Bare JSON tool call extraction (brace-depth counting)
# ---------------------------------------------------------------------------

def _extract_bare_json_tool_calls(
    text: str,
    to_action: Callable[[str], str],
) -> str:
    """Extract bare JSON tool calls like {"name":"...","arguments":{...}}.

    Uses brace-depth counting to correctly handle nested JSON objects in
    the arguments field, unlike naive regex that fails on nested braces.
    """
    # Find patterns that look like tool-call JSON: {"name": "...", "arguments":
    # Use regex to locate candidate starts, then count braces for the full object.
    pattern = re.compile(
        r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*',
    )

    result = text
    offset = 0
    while offset < len(result):
        m = pattern.search(result, offset)
        if not m:
            break

        # Count braces from the opening { to the matching }
        start = m.start()
        depth = 0
        in_str = False
        escaped = False
        end = start
        for i in range(start, len(result)):
            c = result[i]
            if escaped:
                escaped = False
                continue
            if c == '\\':
                escaped = True
                continue
            if c == '"' and not escaped:
                in_str = not in_str
                continue
            if not in_str:
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

        if end > start:
            json_str = result[start:end]
            action = to_action(json_str)
            if action:
                result = result[:start] + action + result[end:]
                offset = start + len(action)
                continue

        offset = m.end()

    return result


# ---------------------------------------------------------------------------
# _extract_annotation_ranges
# ---------------------------------------------------------------------------

def _extract_annotation_ranges(text: str) -> List[Tuple[int, int, str]]:
    """Extract @parallel/@sequential annotation ranges from text.

    Returns:
        List of (start_pos, end_pos, hint_type) tuples.
    """
    hint_ranges: List[Tuple[int, int, str]] = []

    for match in re.finditer(
        r'@parallel\s*\n(.*?)\n\s*@end_parallel',
        text, re.DOTALL | re.MULTILINE
    ):
        hint_ranges.append((match.start(1), match.end(1), "parallel"))

    for match in re.finditer(
        r'@sequential\s*\n(.*?)\n\s*@end_sequential',
        text, re.DOTALL | re.MULTILINE
    ):
        hint_ranges.append((match.start(1), match.end(1), "sequential"))

    return hint_ranges


# ---------------------------------------------------------------------------
# parse_all_actions
# ---------------------------------------------------------------------------

def parse_all_actions(
    text: str,
    debug: bool = False,
) -> List[Tuple[str, str, Optional[str]]]:
    """Parse all 'Action: Tool(args)' occurrences from LLM text.

    Args:
        text:  Raw LLM output (may contain Thought/Action/Observation blocks).
        debug: Print debug information to stdout.

    Returns:
        List of (tool_name, args_str, hint) tuples where hint is
        "parallel", "sequential", or None.
    """
    # Convert XML-style tool calls (<tool_use>, <tool_call>, etc.) before parsing
    text = _strip_native_tool_tokens(text)
    text = sanitize_action_text(text)
    hint_ranges = _extract_annotation_ranges(text)

    if debug and hint_ranges:
        print(f"[DEBUG] Found {len(hint_ranges)} annotation blocks")
        for start, end, hint in hint_ranges:
            print(f"  - {hint}: chars {start}-{end}")

    actions: List[Tuple[str, str]] = []
    action_positions: List[int] = []
    start_pos = 0
    pattern = r"(?:\*\*|__)?(?:Action|tool_call)(?:\*\*|__)?::*\s*[`*_]*\s*(\w+)\s*[`*_]*\s*\("

    if debug:
        print(f"[DEBUG] parse_all_actions input length: {len(text)}")

    while True:
        match = re.search(pattern, text[start_pos:], re.DOTALL | re.IGNORECASE)
        if not match:
            break

        tool_name = _resolve_tool_name(match.group(1))
        match_start = start_pos + match.end()

        paren_count = 1
        in_single_quote = in_double_quote = False
        in_triple_single = in_triple_double = False
        i = match_start

        while i < len(text) and paren_count > 0:
            if not in_single_quote and not in_double_quote:
                if i + 2 < len(text):
                    if text[i:i+3] == '"""':
                        if not in_triple_single:
                            if not in_triple_double:
                                # Opening triple-quote
                                in_triple_double = True
                            else:
                                # Potential closing - check context
                                after = i + 3
                                while after < len(text) and text[after] in ' \t\n\r':
                                    after += 1
                                if after >= len(text) or text[after] in ',)':
                                    in_triple_double = False
                                # else: embedded triple-quote, keep state
                        i += 3
                        continue
                    elif text[i:i+3] == "'''":
                        if not in_triple_double:
                            if not in_triple_single:
                                # Opening triple-quote
                                in_triple_single = True
                            else:
                                # Potential closing - check context
                                after = i + 3
                                while after < len(text) and text[after] in ' \t\n\r':
                                    after += 1
                                if after >= len(text) or text[after] in ',)':
                                    in_triple_single = False
                                # else: embedded triple-quote, keep state
                        i += 3
                        continue

            char = text[i]
            if char == '\\':
                i += 2
                continue

            if not in_triple_single and not in_triple_double:
                if char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                elif char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote

            if not (in_single_quote or in_double_quote or in_triple_single or in_triple_double):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1

            i += 1

        if paren_count == 0:
            args_str = text[match_start:i-1]
            actions.append((tool_name, args_str))
            action_positions.append(start_pos + match.start())
            start_pos = i
        else:
            next_action_match = re.search(pattern, text[match_start:], re.DOTALL)

            if i >= len(text) and not next_action_match:
                # Truncated at end — auto-recover
                if debug:
                    print(f"[DEBUG] Action '{tool_name}' truncated at end of text, attempting recovery")
                args_str = text[match_start:]
                if args_str:
                    if in_double_quote:       args_str += '"'
                    elif in_single_quote:     args_str += "'"
                    elif in_triple_double:    args_str += '"""'
                    elif in_triple_single:    args_str += "'''"
                    actions.append((tool_name, args_str))
                    action_positions.append(start_pos + match.start())
                break

            if debug:
                print(f"[DEBUG] parse_all_actions: Unmatched parens for {tool_name}, skipping")

            if next_action_match:
                start_pos = match_start + next_action_match.start()
            else:
                start_pos = len(text)

    # Deduplicate (preserve order)
    unique_actions: List[Tuple[str, str]] = []
    unique_positions: List[int] = []
    seen: set = set()
    for idx, (tname, astr) in enumerate(actions):
        sig = (tname, astr.strip())
        if sig not in seen:
            seen.add(sig)
            unique_actions.append((tname, astr))
            unique_positions.append(action_positions[idx] if idx < len(action_positions) else 0)

    if debug and len(unique_actions) != len(actions):
        print(f"[DEBUG] Deduplicated: {len(actions)} -> {len(unique_actions)}")

    # Assign hints
    actions_with_hints: List[Tuple[str, str, Optional[str]]] = []
    for idx, (tname, astr) in enumerate(unique_actions):
        pos = unique_positions[idx]
        hint: Optional[str] = None
        for range_start, range_end, hint_type in hint_ranges:
            if range_start <= pos < range_end:
                hint = hint_type
                break
        actions_with_hints.append((tname, astr, hint))
        if debug and hint:
            print(f"[DEBUG] Action '{tname}' has hint: {hint}")

    return actions_with_hints


# ---------------------------------------------------------------------------
# parse_implicit_actions
# ---------------------------------------------------------------------------

def parse_implicit_actions(
    text: str,
    debug: bool = False,
) -> List[Tuple[str, str]]:
    """Parse implicit tool calls in Command R+ format.

    Pattern: to=repo_browser.tool_name ... <|message|>{ json_args }
    """
    actions: List[Tuple[str, str]] = []
    pattern = r"to=(?:[\w\.]+\.)?(\w+).*?<\|message\|>\s*(\{.*?\})"

    for match in re.finditer(pattern, text, re.DOTALL):
        tool_name = match.group(1)
        json_str = match.group(2)
        try:
            args_dict = json.loads(json_str)
            args_str = ", ".join(f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in args_dict.items())
            actions.append((tool_name, args_str))
            if debug:
                print(f"[DEBUG] Parsed implicit action: {tool_name}({args_str})")
        except Exception as e:
            if debug:
                print(f"[DEBUG] Failed to parse implicit JSON: {e}")

    return actions


# ---------------------------------------------------------------------------
# parse_tool_arguments
# ---------------------------------------------------------------------------

def parse_tool_arguments(args_str: str) -> Tuple[List[Any], Dict[str, Any]]:
    """Safely parse tool arguments from string.

    Supports: key="value", key='value', key=123, key=triple-quoted-string
    Returns: (positional_args, keyword_args)
    """
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}

    args_str = args_str.strip()
    if not args_str:
        return args, kwargs

    i = 0
    while i < len(args_str):
        while i < len(args_str) and args_str[i] in ' ,\n':
            i += 1
        if i >= len(args_str):
            break

        key_match = re.match(r'(\w+)\s*=\s*', args_str[i:])
        if key_match:
            key = key_match.group(1)
            i += key_match.end()
            value, chars_consumed = parse_value(args_str[i:])
            kwargs[key] = value
            if chars_consumed == 0:
                break
            i += chars_consumed
        else:
            value, chars_consumed = parse_value(args_str[i:])
            if chars_consumed == 0:
                break
            args.append(value)
            i += chars_consumed

    return args, kwargs


# ---------------------------------------------------------------------------
# parse_value
# ---------------------------------------------------------------------------

def parse_value(text: str) -> Tuple[Any, int]:
    """Parse a single value from the start of text.

    Returns:
        (parsed_value, chars_consumed)
        Returns (None, 0) if no value can be parsed.
    """
    text = text.lstrip()
    if not text:
        return None, 0

    # Triple-quoted strings - char-by-char scan with escape processing and
    # context-aware closing.  A closing delimiter is only recognised when the
    # triple-quote is followed by a comma, closing paren, or end-of-string
    # (after skipping whitespace/newlines).  This prevents inner triple-quotes
    # (e.g. Python docstrings) from prematurely terminating the value.
    #
    # FIX (BUG_REPORT.md): escape sequences are now properly unescaped instead
    # of being skipped raw.  Previously \" stayed as \" in the output, causing
    # write_file / replace_in_file to corrupt Python source files.
    if len(text) >= 3 and (text[:3] == '"""' or text[:3] == "'''"):
        quote3 = text[:3]
        j = 3
        value = ""
        while j < len(text):
            # Handle escape sequences — unescape them into the value
            if text[j] == '\\' and j + 1 < len(text):
                esc = text[j + 1]
                if esc == 'n':
                    value += '\n'
                elif esc == 't':
                    value += '\t'
                elif esc == 'r':
                    value += '\r'
                elif esc == 'b':
                    value += '\b'
                elif esc == 'f':
                    value += '\f'
                elif esc == '\\':
                    value += '\\'
                elif esc == '"':
                    value += '"'
                elif esc == "'":
                    value += "'"
                elif esc == 'u' and j + 5 < len(text):
                    # \uXXXX unicode escape
                    _hex = text[j+2:j+6]
                    try:
                        value += chr(int(_hex, 16))
                        j += 6
                        continue
                    except (ValueError, OverflowError):
                        value += esc  # malformed, keep as-is
                else:
                    value += esc
                j += 2
                continue
            # Potential closing triple-quote
            if j + 2 < len(text) and text[j:j+3] == quote3:
                # Peek past the quote to check context
                after = j + 3
                # Skip whitespace and newlines after potential closing quote
                while after < len(text) and text[after] in ' \t\n\r':
                    after += 1
                # Closing if end-of-string, comma, or closing paren
                if after >= len(text) or text[after] in ',)':
                    return value, j + 3
                # Otherwise embedded triple-quote — keep as literal chars
                value += quote3
                j += 3
                continue
            value += text[j]
            j += 1
        # Auto-close: treat rest of text as the string value
        return value, len(text)

    # Regular quoted strings
    if text[0] in '"\'':
        quote = text[0]
        i = 1
        value = ""
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                next_char = text[i + 1]
                if next_char == 'n':
                    value += '\n'
                elif next_char == 't':
                    value += '\t'
                elif next_char == 'r':
                    value += '\r'
                elif next_char == 'b':
                    value += '\b'
                elif next_char == 'f':
                    value += '\f'
                elif next_char == '\\':
                    value += '\\'
                elif next_char == quote:
                    value += quote
                elif next_char == 'u' and i + 5 < len(text):
                    # \uXXXX unicode escape (produced by json.dumps)
                    _hex = text[i+2:i+6]
                    try:
                        value += chr(int(_hex, 16))
                        i += 6
                        continue
                    except (ValueError, OverflowError):
                        value += next_char  # malformed, keep as-is
                else:
                    value += next_char
                i += 2
            elif text[i] == quote:
                return value, i + 1
            else:
                value += text[i]
                i += 1
        # Auto-close: treat rest of text as the string value instead of crashing.
        # This handles truncated LLM output where the closing quote was cut off.
        return value, len(text)

    # JSON list or dict
    if text.startswith('[') or text.startswith('{'):
        try:
            decoder = json.JSONDecoder()
            value, end_pos = decoder.raw_decode(text)
            return value, end_pos
        except json.JSONDecodeError:
            pass

    # Number or identifier
    match = re.search(r'^([^,)\s]+)', text)
    if match:
        value_str = match.group(1)
        try:
            if '.' in value_str:
                return float(value_str), len(value_str)
            else:
                return int(value_str), len(value_str)
        except ValueError:
            return value_str, len(value_str)

    return None, 0

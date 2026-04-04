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
    'analyze_verilog_module', 'find_signal_usage', 'find_module_definition',
    'extract_module_hierarchy', 'generate_module_testbench', 'find_potential_issues',
    'analyze_timing_paths', 'generate_module_docs', 'suggest_optimizations',
})


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

def _strip_native_tool_tokens(text: str) -> str:
    """Strip native tool call tokens and convert to ReAct Action: format.

    Handles GLM 4.7, Qwen, DeepSeek, Mistral native formats:
      <think>...</think>           — reasoning tokens
      <tool_call>{json}</tool_call> — JSON tool calls
      <tool>name</tool><parameter>  — XML tool calls
      bare function calls           — prepends Action: for known tools
    """
    # Strip reasoning tokens leaked into content
    text = _strip_thinking_tags(text)

    def _json_tool_call_to_action(json_str: str) -> str:
        try:
            data = json.loads(json_str.strip())
            name = data.get("name", "")
            args = data.get("arguments", {})
            if name and isinstance(args, dict):
                args_str = ", ".join(f'{k}={json.dumps(v)}' for k, v in args.items())
                return f"\nAction: {name}({args_str})\n"
        except (json.JSONDecodeError, AttributeError):
            pass
        return ""

    def _xml_params_to_action(tool_name: str, params_block: str) -> str:
        params = re.findall(r'<(\w+)>(.*?)</\1>', params_block, re.DOTALL)
        if tool_name and params:
            args_str = ", ".join(f'{k}={json.dumps(v)}' for k, v in params)
            return f"\nAction: {tool_name}({args_str})\n"
        elif tool_name:
            return f"\nAction: {tool_name}()\n"
        return ""

    def _func_call_to_action(content: str) -> str:
        content = content.strip()
        if re.match(r'^\w+\s*\(', content):
            return f"\nAction: {content}\n"
        return content

    # Pattern 0: <tool_call>func(args)</tool_call> — direct function call
    text = re.sub(
        r'<tool_call>\s*(\w+\s*\([^<]*\))\s*(?:</tool_call>)?',
        lambda m: _func_call_to_action(m.group(1)),
        text, flags=re.DOTALL
    )

    # Pattern 1: JSON-based tool calls
    text = re.sub(
        r'<tool_call>\s*(\{.*\})\s*</tool_call>',
        lambda m: _json_tool_call_to_action(m.group(1)),
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\s*\}',
        lambda m: _json_tool_call_to_action(m.group(0)),
        text
    )

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
    text = re.sub(r'</?(?:tool_call|tool|action|execute|func\w*|p(?:ar|aram)\w*)>', '', text)

    # Pattern 4: Bare function calls without Action: prefix (Qwen / GLM style)
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

        tool_name = match.group(1)
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
                            in_triple_double = not in_triple_double
                            i += 3
                            continue
                    elif text[i:i+3] == "'''":
                        if not in_triple_double:
                            in_triple_single = not in_triple_single
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
            args_str = ", ".join(f'{k}={json.dumps(v)}' for k, v in args_dict.items())
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

    # Triple-quoted strings
    if text.startswith('"""') or text.startswith("'''"):
        quote = text[:3]
        end_pos = text.find(quote, 3)
        if end_pos == -1:
            raise ValueError("Unclosed triple-quote string")
        return text[3:end_pos], end_pos + 3

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
                elif next_char == '\\':
                    value += '\\'
                elif next_char == quote:
                    value += quote
                else:
                    value += next_char
                i += 2
            elif text[i] == quote:
                return value, i + 1
            else:
                value += text[i]
                i += 1
        raise ValueError("Unclosed string")

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

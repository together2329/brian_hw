# Bug Report: replace_in_file / write_file Quote Escaping

## Severity
**Critical** — corrupts Python source files, making them un-parseable by Python.

## Status
**✅ FIXED** — 2025-04-27

## Symptom
Both `replace_in_file` and `write_file` tools escape `"` (double-quote) characters
inside their content arguments. After applying, docstrings like:

    """Tracks a single /run invocation."""

become:

    \"\"\"Tracks a single /run invocation.\"\"\"

causing:

    SyntaxError: unexpected character after line continuation character

## Reproduction
1. Open any Python file containing triple-quoted docstrings.
2. Call `replace_in_file` or `write_file` on it.
3. Observe all `"` become `\"` and all `\n` become `\\n`.

## Workaround
Use `execute_command` with shell heredocs to write Python patching scripts.
The shell heredoc passes raw strings without escaping.

## Affected Files (this session)
- `core/agent_server.py` — corrupted 3 times, restored via `git checkout` each time
- `_gen_rtl_test.py` — generator script worked because it used single quotes
- `tests/test_rtl_pipeline.py` — corrupted once, fixed via `_gen_rtl_test.py` generator
- `_gen_cancel_test.py` — corrupted once

## Root Cause
Two issues in the non-native tool call path (`action_parser.py` + `llm_client.py`):

1. **`parse_value()` triple-quote handler** (`action_parser.py`): escape sequences like `\"`
   were skipped (`j += 2`) but NOT unescaped. The raw `text[3:j]` slice preserved `\"`
   literally in the output value, causing write_file to write `\"` instead of `"`.

2. **`json.dumps(v)`** in `llm_client.py` (4 places): missing `ensure_ascii=False`,
   causing Unicode characters to be mangled (e.g., `é` → `\u00e9`).

## Fix
- **`core/action_parser.py`**: `parse_value()` triple-quote handler now builds the value
  character-by-character, properly unescaping: `\"` → `"`, `\\` → `\`, `\n` → newline,
  `\t` → tab, `\r`, `\b`, `\f`, `\uXXXX` → unicode char.
- **`core/action_parser.py`**: regular string handler also gained `\r`, `\b`, `\f`, `\uXXXX`.
- **`src/llm_client.py`**: all 4 `json.dumps(v)` → `json.dumps(v, ensure_ascii=False)`.
- **Note**: native mode (`ENABLE_NATIVE_TOOL_CALLS=true`) was already fixed via
  `pre_parsed_kwargs` bypass (react_loop.py line 961).

## Verification
- 17 new round-trip tests pass (json.dumps → parse_value → original value)
- 57 existing tests pass (zero regressions)

## Workaround that worked
```bash
cat > _patch.py << 'ENDOFPY'
...Python code that reads/writes files...
ENDOFPY
python3 _patch.py
```

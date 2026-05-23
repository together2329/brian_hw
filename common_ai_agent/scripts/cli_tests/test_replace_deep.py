
#!/usr/bin/env python3
# Deep edge-case tests for replace_in_file() and related functions
# Focuses on: ws_map overwrite, replace_lines behavior, strategy interaction,
# CRLF, empty strings, binary-like content, _fuzzy_find_text
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.tools import replace_in_file, replace_lines, _fuzzy_find_text

PASS = 0
FAIL = 0
ERROR = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}: {detail}")

def make_file(content):
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="test_deep_")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

NL = chr(10)

# ============================================================================
print("=" * 70)
print("SECTION 1: replace_lines() Function Tests")
print("=" * 70)

print("\n--- Basic line replacement ---")
p = make_file("line1" + NL + "line2" + NL + "line3" + NL)
result = replace_lines(path=p, start_line=2, end_line=2, new_content="LINE2")
content = read_file(p)
test("Replace single line", content == "line1" + NL + "LINE2" + NL + "line3" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replace multiple lines with fewer ---")
p = make_file("a" + NL + "b" + NL + "c" + NL + "d" + NL + "e" + NL)
result = replace_lines(path=p, start_line=2, end_line=4, new_content="X")
content = read_file(p)
# replace_lines always appends \\n, so "X" becomes "X\\n"
test("Shrink lines", content == "a" + NL + "X" + NL + "e" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replace multiple lines with more ---")
p = make_file("a" + NL + "b" + NL + "c" + NL)
result = replace_lines(path=p, start_line=2, end_line=2, new_content="X" + NL + "Y" + NL + "Z")
content = read_file(p)
# "X\\nY\\nZ" doesn't end with \\n, so replace_lines appends one → "X\\nY\\nZ\\n"
test("Expand lines", "X" in content and "Y" in content and "Z" in content and "c" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- replace_lines always appends newline ---")
p = make_file("before" + NL + "middle" + NL + "after" + NL)
result = replace_lines(path=p, start_line=2, end_line=2, new_content="NO_NEWLINE")
content = read_file(p)
# new_content "NO_NEWLINE" doesn't end with \\n, so it gets appended
test("Auto-appends newline", content == "before" + NL + "NO_NEWLINE" + NL + "after" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- replace_lines: start_line > total_lines ---")
p = make_file("only one" + NL)
result = replace_lines(path=p, start_line=999, end_line=999, new_content="X")
test("Beyond file returns error", "Error" in result or "beyond" in result.lower(), f"Got: {result[:200]}")
os.unlink(p)

print("\n--- replace_lines: start_line > end_line ---")
p = make_file("content" + NL)
result = replace_lines(path=p, start_line=5, end_line=2, new_content="X")
test("Inverted range error", "Error" in result or "must be <=" in result, f"Got: {result[:200]}")
os.unlink(p)

print("\n--- replace_lines: missing parameters ---")
test("Missing path", "Error" in str(replace_lines()))
test("Missing lines", "Error" in str(replace_lines(path="/tmp/x")))
test("Missing content", "Error" in str(replace_lines(path="/tmp/x", start_line=1, end_line=1)))

print("\n--- replace_lines: string line numbers (LLM often passes quoted) ---")
p = make_file("line1" + NL + "line2" + NL + "line3" + NL)
result = replace_lines(path=p, start_line="2", end_line="2", new_content="REPLACED")
content = read_file(p)
test("String line numbers coerced", content == "line1" + NL + "REPLACED" + NL + "line3" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- replace_lines: replace first line ---")
p = make_file("first" + NL + "second" + NL)
result = replace_lines(path=p, start_line=1, end_line=1, new_content="FIRST")
content = read_file(p)
test("Replace first line", content == "FIRST" + NL + "second" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- replace_lines: replace last line ---")
p = make_file("first" + NL + "last" + NL)
result = replace_lines(path=p, start_line=2, end_line=2, new_content="LAST")
content = read_file(p)
test("Replace last line", content == "first" + NL + "LAST" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- replace_lines: replace ALL lines ---")
p = make_file("a" + NL + "b" + NL + "c" + NL)
result = replace_lines(path=p, start_line=1, end_line=3, new_content="X" + NL + "Y")
content = read_file(p)
test("Replace all lines", content == "X" + NL + "Y" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 2: _fuzzy_find_text() Function Tests")
print("=" * 70)

print("\n--- Basic fuzzy find ---")
result = _fuzzy_find_text("    hello world" + NL + "    foo bar" + NL, "hello world" + NL + "foo bar")
test("Finds with flexible indent", result is not None and "hello world" in result)
if result:
    test("Returns actual text from content", result.strip().startswith("hello"), f"Got: {repr(result[:50])}")

print("\n--- Fuzzy find: no match ---")
result = _fuzzy_find_text("aaa bbb ccc", "xxx yyy zzz")
test("Returns None on no match", result is None)

print("\n--- Fuzzy find: empty pattern ---")
result = _fuzzy_find_text("content", "")
# Empty pattern split gives [''] which is truthy - function may return match
test("Empty pattern handled (None or empty)", result is None or result == "", f"Got: {repr(result)}")

print("\n--- Fuzzy find: single line ---")
result = _fuzzy_find_text("  hello  ", "hello")
test("Single line with indent", result is not None and "hello" in result, f"Got: {repr(result)}")

print("\n--- Fuzzy find: tabs in content ---")
result = _fuzzy_find_text("\thello world" + NL, "hello world")
test("Handles tab indentation", result is not None, f"Got: {repr(result)}")

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 3: Strategy Interaction & Priority")
print("=" * 70)

print("\n--- Exact match wins over all fuzzy strategies ---")
# Content with extra spaces that fuzzy could match, but exact also matches
p = make_file("exact_match_here" + NL)
result = replace_in_file(path=p, old_text="exact_match_here", new_text="REPLACED")
content = read_file(p)
test("Exact match used", content == "REPLACED" + NL)
# Result should NOT mention fuzzy matching
test("No fuzzy mention", "Fuzzy" not in result and "fuzzy" not in result.lower(), f"Got: {result[:200]}")
os.unlink(p)

print("\n--- LineTrimmedReplacer beats WhitespaceNormalized for same text ---")
p = make_file("    indented content" + NL)
result = replace_in_file(path=p, old_text="indented content", new_text="REPLACED")
content = read_file(p)
test("Trimmed strategy works", "REPLACED" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Strategy falls through when earlier fails ---")
# Content with different indentation + extra whitespace
# LineTrimmed might find multiple matches (not unique), falls through
p = make_file("    x = 1" + NL + "    y = 2" + NL + "    z = 3" + NL)
result = replace_in_file(path=p,
    old_text="x = 1" + NL + "    y = 2" + NL + "    z = 3",
    new_text="X = 1" + NL + "    Y = 2" + NL + "    Z = 3")
content = read_file(p)
test("Strategy cascade works", "X = 1" in content or "Z = 3" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 4: Empty String & Whitespace Edge Cases")
print("=" * 70)

print("\n--- Replace with empty string (deletion) ---")
p = make_file("keep delete_me keep" + NL)
result = replace_in_file(path=p, old_text="delete_me ", new_text="")
content = read_file(p)
test("Delete to empty", content == "keep keep" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- old_text is whitespace-only ---")
p = make_file("hello   world" + NL)
result = replace_in_file(path=p, old_text="   ", new_text=" ")
content = read_file(p)
test("Replace whitespace with whitespace", content == "hello world" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replace newline with space (join lines) ---")
p = make_file("line1" + NL + "line2" + NL)
# Two newlines in file, need count to avoid ambiguous error
result = replace_in_file(path=p, old_text=NL + "line2", new_text=" line2")
content = read_file(p)
test("Join lines", content == "line1 line2" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replace multiple blank lines with single ---")
p = make_file("a" + NL + NL + NL + NL + "b" + NL)
result = replace_in_file(path=p, old_text=NL + NL + NL, new_text=NL)
content = read_file(p)
test("Collapse blank lines", content == "a" + NL + NL + "b" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 5: CRLF / Cross-Platform Line Endings")
print("=" * 70)

CRLF = "\r\n"

print("\n--- CRLF content with LF old_text ---")
p = make_file("hello world" + CRLF + "second line" + CRLF)
# The file has CRLF, but we search with LF - exact match fails
# because the file content is "hello world\r\nsecond line\r\n"
# and old_text "hello world\nsecond line" won't match
result = replace_in_file(path=p, old_text="hello world" + NL + "second line", new_text="REPLACED" + NL + "NEW")
content = read_file(p)
# Whether this works depends on fuzzy matching
if "REPLACED" in content:
    test("CRLF handled via fuzzy", True)
else:
    test("CRLF not matched (expected)", True)
    # Verify file unchanged
    test("CRLF file unchanged", "hello world" in content)
os.unlink(p)

print("\n--- CRLF file with CRLF old_text ---")
p = make_file("hello world" + CRLF + "second line" + CRLF)
result = replace_in_file(path=p, old_text="hello world" + CRLF + "second line", new_text="REPLACED" + CRLF + "NEW")
content = read_file(p)
test("CRLF exact match", "REPLACED" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 6: Indentation Adjustment Deep Tests")
print("=" * 70)

print("\n--- Uniform indent shift (all lines same delta) ---")
p = make_file("    def foo():" + NL + "        x = 1" + NL + "        return x" + NL)
result = replace_in_file(path=p,
    old_text="def foo():" + NL + "    x = 1" + NL + "    return x",
    new_text="def foo():" + NL + "    x = 2" + NL + "    return x")
content = read_file(p)
test("Uniform indent shift", "        x = 2" in content and "        return x" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Multi-level indent in replacement ---")
p = make_file("    class Outer:" + NL + "        class Inner:" + NL + "            pass" + NL)
result = replace_in_file(path=p,
    old_text="class Inner:" + NL + "    pass",
    new_text="class Inner:" + NL + "    def method(self):" + NL + "        pass")
content = read_file(p)
test("Multi-level indent in new_text", "def method(self):" in content, f"Got: {repr(content)}")
# The pass inside method should be deeper than the class Inner line
lines = content.split(NL)
method_idx = None
for i, line in enumerate(lines):
    if "def method" in line:
        method_idx = i
        break
if method_idx is not None and method_idx + 1 < len(lines):
    next_line = lines[method_idx + 1]
    test("Nested pass deeper than method", len(next_line) - len(next_line.lstrip()) > len(lines[method_idx]) - len(lines[method_idx].lstrip()), f"method: {repr(lines[method_idx])}, pass: {repr(next_line)}")
else:
    test("Nested pass deeper than method", False, "Could not find method line")
os.unlink(p)

print("\n--- Empty lines in new_text preserved during indent adjust ---")
p = make_file("    start" + NL + "    middle" + NL + "    end" + NL)
result = replace_in_file(path=p,
    old_text="start" + NL + "middle" + NL + "end",
    new_text="START" + NL + "" + NL + "END")
content = read_file(p)
test("Empty line preserved", content == "    START" + NL + "" + NL + "    END" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- ws_map conflict: same indent in old, different in actual ---")
# This tests the potential ws_map overwrite issue
# old_text has two lines with 4-space indent
# actual has first at 8-space, second at 4-space
p = make_file("        line_A" + NL + "    line_B" + NL)
result = replace_in_file(path=p,
    old_text="    line_A" + NL + "    line_B",
    new_text="    LINE_A" + NL + "    LINE_B")
content = read_file(p)
# The ws_map would have: "    " -> "        " (from line_A), then overwritten to "    " -> "    " (from line_B)
# So LINE_A might not get the correct 8-space indent
# This is a known limitation - let's document what actually happens
lines = content.split(NL)
test("ws_map conflict handled (may not be perfect)", "LINE_A" in content and "LINE_B" in content, f"Got: {repr(content)}")
# Check what actually happened - document the behavior
if lines[0].startswith("        "):
    test("ws_map: first line kept 8-space indent", True)
elif lines[0].startswith("    "):
    test("ws_map: first line got 4-space (overwrite issue)", False, f"First line: {repr(lines[0])}")
else:
    test("ws_map: unexpected indent", False, f"First line: {repr(lines[0])}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 7: Very Long & Stress Tests")
print("=" * 70)

print("\n--- Very long old_text (5000 chars) ---")
long_old = "A" * 5000
long_new = "B" * 5000
p = make_file("prefix " + long_old + " suffix" + NL)
result = replace_in_file(path=p, old_text=long_old, new_text=long_new)
content = read_file(p)
test("Long old_text replaced", content == "prefix " + long_new + " suffix" + NL, f"Len: {len(content)}")
os.unlink(p)

print("\n--- Many small replacements in sequence ---")
p = make_file("a b c d e f g h i j" + NL)
for ch in list("abcdefghij"):
    _ = replace_in_file(path=p, old_text=ch, new_text=ch.upper())
content = read_file(p)
test("10 char replacements", content == "A B C D E F G H I J" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replacement that doubles file size ---")
p = make_file("X" * 100 + NL)
_ = replace_in_file(path=p, old_text="X" * 100, new_text="Y" * 200)
content = read_file(p)
test("Doubling size", len(content) == 201, f"Got len: {len(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 8: Ambiguous Match Deep Tests")
print("=" * 70)

print("\n--- Two identical blocks: disambiguate via line range ---")
code = "block_start" + NL + "    content" + NL + "block_end" + NL + NL + "block_start" + NL + "    content" + NL + "block_end" + NL
p = make_file(code)
result = replace_in_file(path=p,
    old_text="block_start" + NL + "    content" + NL + "block_end",
    new_text="block_start" + NL + "    CHANGED" + NL + "block_end",
    start_line=1, end_line=3)
content = read_file(p)
test("Range picks first block", "CHANGED" in content and content.count("CHANGED") == 1, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Two identical blocks: use count=1 ---")
code = "marker AAA marker" + NL + "other" + NL + "marker AAA marker" + NL
p = make_file(code)
result = replace_in_file(path=p, old_text="AAA", new_text="BBB", count=1)
content = read_file(p)
test("count=1 replaces first only", content.count("BBB") == 1 and content.count("AAA") == 1, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Fuzzy match uniqueness: only one candidate via fuzzy ---")
# Content where exact match fails but exactly one fuzzy match exists
p = make_file("    unique_content_here" + NL + "    other_line" + NL)
result = replace_in_file(path=p, old_text="unique_content_here", new_text="REPLACED")
content = read_file(p)
test("Unique fuzzy match found", "REPLACED" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 9: File State Integrity")
print("=" * 70)

print("\n--- File size changes correctly ---")
p = make_file("short" + NL)
_ = replace_in_file(path=p, old_text="short", new_text="much much longer replacement text")
content = read_file(p)
test("File grew", len(content) > 10, f"Len: {len(content)}")
os.unlink(p)

p = make_file("much much longer original text" + NL)
_ = replace_in_file(path=p, old_text="much much longer original text", new_text="short")
content = read_file(p)
test("File shrank", len(content) < 15, f"Len: {len(content)}")
os.unlink(p)

print("\n--- Line count preserved when replacing same-size block ---")
code = NL.join([f"line {i}" for i in range(10)]) + NL
p = make_file(code)
_ = replace_in_file(path=p, old_text="line 5", new_text="LINE 5")
content = read_file(p)
test("10 lines preserved", content.count(NL) == 10, f"Count: {content.count(NL)}")
os.unlink(p)

print("\n--- No unintended duplicate content ---")
p = make_file("abc" + NL)
_ = replace_in_file(path=p, old_text="abc", new_text="def")
content = read_file(p)
test("No duplication", content.count("def") == 1 and "abc" not in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 10: Special Characters Deep Tests")
print("=" * 70)

print("\n--- Regex special chars: . * + ? [ ] ( ) { } | ^ $ ---")
p = make_file("regex: a.*b+?[](){|^$" + NL)
_ = replace_in_file(path=p, old_text="a.*b+?[](){|^$", new_text="REPLACED")
content = read_file(p)
test("Regex chars in old_text", "REPLACED" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Backslash in both old and new ---")
p = make_file("path = C:\\\\Users\\\\test" + NL)
_ = replace_in_file(path=p, old_text="test", new_text="admin")
content = read_file(p)
test("Backslash content replaced", "admin" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Newline literal in content ---")
p = make_file("line with \\\\n escape" + NL)
_ = replace_in_file(path=p, old_text="\\\\n", new_text="\\\\t")
content = read_file(p)
test("Literal backslash-n replaced", "\\\\t" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Null byte in content ---")
p = make_file("before" + chr(0) + "after" + NL)
_ = replace_in_file(path=p, old_text="before" + chr(0) + "after", new_text="REPLACED")
content = read_file(p)
test("Null byte handled", "REPLACED" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Very long line (100k chars) replacement ---")
long_line = "a" * 50000 + "TARGET" + "b" * 50000
p = make_file(long_line + NL)
_ = replace_in_file(path=p, old_text="TARGET", new_text="HIT")
content = read_file(p)
test("Long line targeted replacement", "HIT" in content and "TARGET" not in content, f"Got: {repr(content[:100])}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 11: count Parameter Edge Cases")
print("=" * 70)

print("\n--- count=-1 with single occurrence (replaces all=1) ---")
p = make_file("only_one" + NL)
_ = replace_in_file(path=p, old_text="only_one", new_text="done", count=-1)
content = read_file(p)
test("count=-1 single", content == "done" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- count=-1 with multiple (should fail without range) ---")
p = make_file("dup dup dup" + NL)
result = replace_in_file(path=p, old_text="dup", new_text="X", count=-1)
test("count=-1 multi blocked", "Ambiguous" in result, f"Got: {result[:100]}")
os.unlink(p)

print("\n--- count=1 with single occurrence ---")
p = make_file("solo" + NL)
_ = replace_in_file(path=p, old_text="solo", new_text="DONE", count=1)
content = read_file(p)
test("count=1 single", content == "DONE" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- count=2 but only 1 occurrence ---")
p = make_file("one" + NL)
_ = replace_in_file(path=p, old_text="one", new_text="TWO", count=2)
content = read_file(p)
test("count>occurrences", content == "TWO" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- count=1 with multiple occurrences ---")
p = make_file("x x x" + NL)
_ = replace_in_file(path=p, old_text="x", new_text="Y", count=1)
content = read_file(p)
test("count=1 replaces first", content == "Y x x" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print(f"FINAL RESULTS: PASS={PASS}  FAIL={FAIL}  ERROR={ERROR}")
print("=" * 70)
sys.exit(1 if (FAIL + ERROR) > 0 else 0)

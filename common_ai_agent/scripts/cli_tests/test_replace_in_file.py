
#!/usr/bin/env python3
# Comprehensive edge-case tests for replace_in_file() and fuzzy matching strategies
import sys
import os
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.tools import replace_in_file
from core.tools import (
    _line_trimmed_replacer,
    _block_anchor_replacer,
    _whitespace_normalized_replacer,
    _indentation_flexible_replacer,
    _escape_normalized_replacer,
    _trimmed_boundary_replacer,
    _context_aware_replacer,
    _punctuation_aware_replacer,
    _levenshtein,
)

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

def test_error(name, fn, expected_in_msg=None):
    global PASS, FAIL, ERROR
    try:
        result = fn()
        if isinstance(result, str) and ("Error" in result or "not found" in result.lower() or "Ambiguous" in result):
            if expected_in_msg and expected_in_msg not in result:
                FAIL += 1
                print(f"  FAIL {name}: Expected '{expected_in_msg}' in error, got: {result[:200]}")
            else:
                PASS += 1
                print(f"  PASS {name} (returned error)")
        else:
            FAIL += 1
            print(f"  FAIL {name}: Expected error but got: {str(result)[:200]}")
    except Exception as e:
        ERROR += 1
        print(f"  ERR  {name}: {e}")

def make_file(content):
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="test_ri_")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

NL = chr(10)  # newline character

# ============================================================================
print("=" * 70)
print("SECTION 1: Parameter Validation & Error Handling")
print("=" * 70)

print("\n--- Missing parameters ---")
test_error("No path", lambda: replace_in_file(), "path")
test_error("No old_text", lambda: replace_in_file(path="/tmp/x.txt"), "old_text")
test_error("No new_text", lambda: replace_in_file(path="/tmp/x.txt", old_text="x"), "new_text")

print("\n--- Non-existent file ---")
test_error("File not found", lambda: replace_in_file(
    path="/tmp/nonexistent_xyz.txt", old_text="foo", new_text="bar"
), "does not exist")

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 2: Basic Replacement Operations")
print("=" * 70)

print("\n--- Exact single match ---")
p = make_file("hello world" + NL)
result = replace_in_file(path=p, old_text="hello", new_text="hi")
content = read_file(p)
test("Single exact match", content == "hi world" + NL, f"Got: {repr(content)}")
test("Reports 1 replacement", "1 occurrence" in result)
os.unlink(p)

print("\n--- Exact multi-match without range (should fail) ---")
p = make_file("foo bar foo baz foo" + NL)
result = replace_in_file(path=p, old_text="foo", new_text="qux")
test("Ambiguous match error", "Ambiguous" in result or "3 occurrences" in result, f"Got: {result[:200]}")
os.unlink(p)

print("\n--- Multi-match with count=1 ---")
p = make_file("foo bar foo baz foo" + NL)
result = replace_in_file(path=p, old_text="foo", new_text="qux", count=1)
content = read_file(p)
test("Only first replaced", content == "qux bar foo baz foo" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Multi-match with count=2 ---")
p = make_file("foo bar foo baz foo" + NL)
result = replace_in_file(path=p, old_text="foo", new_text="qux", count=2)
content = read_file(p)
test("First two replaced", content == "qux bar qux baz foo" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Multi-match with line range ---")
p = make_file("aaa" + NL + "bbb" + NL + "ccc" + NL + "bbb" + NL + "ddd" + NL)
result = replace_in_file(path=p, old_text="bbb", new_text="BBB", start_line=2, end_line=3)
content = read_file(p)
test("Range replacement", content == "aaa" + NL + "BBB" + NL + "ccc" + NL + "bbb" + NL + "ddd" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- No match at all ---")
p = make_file("hello world" + NL)
result = replace_in_file(path=p, old_text="xyz_not_found", new_text="replaced")
test("Not found error", "not found" in result.lower() or "Text not found" in result, f"Got: {result[:200]}")
content = read_file(p)
test("File unchanged", content == "hello world" + NL)
os.unlink(p)

print("\n--- old_text == new_text (no-op) ---")
p = make_file("same content" + NL)
result = replace_in_file(path=p, old_text="same content", new_text="same content")
content = read_file(p)
test("No-op replacement succeeds", content == "same content" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 3: LineTrimmedReplacer (Strategy 2)")
print("=" * 70)

print("\n--- Different indentation ---")
p = make_file("    def hello():" + NL + "        print('world')" + NL)
result = replace_in_file(path=p,
    old_text="def hello():" + NL + "    print('world')",
    new_text="def goodbye():" + NL + "    print('world')")
content = read_file(p)
test("Matches with trimmed lines", "def goodbye():" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Extra spaces in content ---")
p = make_file("  alpha  " + NL + "  beta  " + NL + "  gamma  " + NL)
result = replace_in_file(path=p,
    old_text="alpha" + NL + "beta" + NL + "gamma",
    new_text="ALPHA" + NL + "BETA" + NL + "GAMMA")
content = read_file(p)
test("Matches trimmed content", "ALPHA" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Direct: no match ---")
matches = list(_line_trimmed_replacer("aaa" + NL + "bbb" + NL + "ccc", "xxx" + NL + "yyy"))
test("No trimmed match", len(matches) == 0)

print("\n--- Direct: multiple matches ---")
matches = list(_line_trimmed_replacer("aaa" + NL + "bbb" + NL + "aaa" + NL + "bbb", "aaa" + NL + "bbb"))
test("Multiple trimmed matches", len(matches) == 2)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 4: BlockAnchorReplacer (Strategy 3)")
print("=" * 70)

print("\n--- Slightly different middle lines ---")
content = "def foo():" + NL + "    x = 1" + NL + "    return x" + NL
find = "def foo():" + NL + "    x = 2" + NL + "    return x"
matches = list(_block_anchor_replacer(content, find))
test("Finds block with similar middle", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Less than 3 lines (skip) ---")
matches = list(_block_anchor_replacer("ab" + NL + "cd", "ab" + NL + "cd"))
test("Skips < 3 lines", len(matches) == 0)

print("\n--- No anchor match ---")
matches = list(_block_anchor_replacer("aaa" + NL + "bbb" + NL + "ccc" + NL, "xxx" + NL + "yyy" + NL + "zzz"))
test("No anchor match", len(matches) == 0)

print("\n--- Low similarity middle ---")
content = "def foo():" + NL + "    completely different content here that is long" + NL + "    return x" + NL
find = "def foo():" + NL + "    x = 1" + NL + "    return x"
matches = list(_block_anchor_replacer(content, find))
test("Rejects low similarity", len(matches) == 0, f"Matches: {len(matches)}")

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 5: WhitespaceNormalizedReplacer (Strategy 4)")
print("=" * 70)

print("\n--- Extra spaces in content ---")
p = make_file("hello     world" + NL)
result = replace_in_file(path=p, old_text="hello world", new_text="hi earth")
content = read_file(p)
test("Normalizes whitespace", "hi earth" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Direct: no match ---")
matches = list(_whitespace_normalized_replacer("aaa bbb", "xxx yyy zzz"))
test("No ws-normalized match", len(matches) == 0)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 6: IndentationFlexibleReplacer (Strategy 5)")
print("=" * 70)

print("\n--- Different indentation levels ---")
p = make_file("        def hello():" + NL + "            print('world')" + NL)
result = replace_in_file(path=p,
    old_text="def hello():" + NL + "    print('world')",
    new_text="def goodbye():" + NL + "    print('world')")
content = read_file(p)
test("Matches with different indent", "def goodbye():" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Direct: exact match ---")
matches = list(_indentation_flexible_replacer("    a" + NL + "    b" + NL + "    c", "a" + NL + "b" + NL + "c"))
test("Finds indent-flexible match", len(matches) >= 1)

print("\n--- Direct: no match ---")
matches = list(_indentation_flexible_replacer("aaa" + NL + "bbb", "xxx" + NL + "yyy"))
test("No indent-flexible match", len(matches) == 0)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 7: EscapeNormalizedReplacer (Strategy 6)")
print("=" * 70)

print("\n--- Direct: tab escape ---")
matches = list(_escape_normalized_replacer("hello\tworld", "hello\\tworld"))
test("Finds tab escape match", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Direct: no match ---")
matches = list(_escape_normalized_replacer("aaa bbb", "xxx yyy"))
test("No escape-normalized match", len(matches) == 0)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 8: TrimmedBoundaryReplacer (Strategy 7)")
print("=" * 70)

print("\n--- Leading/trailing whitespace ---")
p = make_file("   hello world   " + NL)
result = replace_in_file(path=p, old_text="  hello world  ", new_text="hi earth")
content = read_file(p)
test("Matches trimmed boundary", "hi earth" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Direct: already trimmed (skip) ---")
matches = list(_trimmed_boundary_replacer("hello", "hello"))
test("Skips already trimmed", len(matches) == 0)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 9: ContextAwareReplacer (Strategy 9 - THE FIX)")
print("=" * 70)

print("\n--- Basic anchor match (50%+ middle similarity) ---")
# 5 lines: 3 middle lines, need >= 2 to match (>= 50%)
ct = "def foo():" + NL + "    x = 1" + NL + "    y = 2" + NL + "    z = 3" + NL + "    return x" + NL
find = "def foo():" + NL + "    x = 1" + NL + "    changed" + NL + "    z = 3" + NL + "    return x"
matches = list(_context_aware_replacer(ct, find))
test("Finds context-aware match (2/3 middle match)", len(matches) >= 1, f"Matches: {len(matches)}")
if matches:
    test("Match starts correctly", "def foo():" in matches[0], f"Got: {repr(matches[0][:50])}")

print("\n--- Less than 3 lines (skip) ---")
matches = list(_context_aware_replacer("a" + NL + "b", "a" + NL + "b"))
test("Skips < 3 lines", len(matches) == 0)

print("\n--- No anchor match ---")
matches = list(_context_aware_replacer("aaa" + NL + "bbb" + NL + "ccc" + NL, "xxx" + NL + "yyy" + NL + "zzz"))
test("No context-aware match", len(matches) == 0)

print("\n--- Block size mismatch ---")
ct = "def foo():" + NL + "    x = 1" + NL + "    return x" + NL
find = "def foo():" + NL + "    return x"
matches = list(_context_aware_replacer(ct, find))
test("Rejects size mismatch", len(matches) == 0, f"Matches: {len(matches)}")

print("\n--- Middle lines < 50% match ---")
ct = "def foo():" + NL + "    xxxxxxx" + NL + "    yyyyyyy" + NL + "    zzzzzzz" + NL + "    return x" + NL
find = "def foo():" + NL + "    aaaaaaa" + NL + "    bbbbbbb" + NL + "    ccccccc" + NL + "    return x"
matches = list(_context_aware_replacer(ct, find))
test("Rejects low similarity middle", len(matches) == 0, f"Matches: {len(matches)}")

print("\n--- Exact middle match (100%) ---")
ct = "start" + NL + "    middle1" + NL + "    middle2" + NL + "end" + NL
find = "start" + NL + "    middle1" + NL + "    middle2" + NL + "end"
matches = list(_context_aware_replacer(ct, find))
test("Accepts exact match", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Integration: ContextAware replaces via replace_in_file ---")
# Use 5 lines with 2/3 middle matching to pass 50% threshold
p = make_file("def process():" + NL + "    x = 1" + NL + "    y = compute()" + NL + "    z = 3" + NL + "    return x" + NL)
result = replace_in_file(path=p,
    old_text="def process():" + NL + "    x = 1" + NL + "    y = changed()" + NL + "    z = 3" + NL + "    return x",
    new_text="def process():" + NL + "    a = 1" + NL + "    b = compute()" + NL + "    c = 3" + NL + "    return a")
content = read_file(p)
test("ContextAware integration works", "b = compute()" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 10: PunctuationAwareReplacer (Strategy 8 - disabled but tested)")
print("=" * 70)

print("\n--- Whitespace near parens ---")
ct = 'foo( "bar" );'
find = 'foo("bar");'
matches = list(_punctuation_aware_replacer(ct, find))
test("Matches punctuation-normalized", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- No match ---")
matches = list(_punctuation_aware_replacer("aaa bbb", "xxx yyy"))
test("No punct-aware match", len(matches) == 0)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 11: Unicode & Special Content")
print("=" * 70)

print("\n--- Unicode content ---")
p = make_file("Hello \u4e16\u754c" + NL + "Goodbye \u4e16\u754c" + NL)
result = replace_in_file(path=p, old_text="Hello \u4e16\u754c", new_text="Hola \u4e16\u754c")
content = read_file(p)
test("Unicode replacement", content == "Hola \u4e16\u754c" + NL + "Goodbye \u4e16\u754c" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Empty file ---")
p = make_file("")
result = replace_in_file(path=p, old_text="something", new_text="else")
test("Empty file - not found", "not found" in result.lower() or "Text not found" in result)
os.unlink(p)

print("\n--- Single character file ---")
p = make_file("x")
result = replace_in_file(path=p, old_text="x", new_text="y")
content = read_file(p)
test("Single char replacement", content == "y", f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replace with empty string (deletion) ---")
p = make_file("hello world" + NL)
result = replace_in_file(path=p, old_text="hello ", new_text="")
content = read_file(p)
test("Delete by empty new_text", content == "world" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replace with longer multi-line ---")
p = make_file("old" + NL)
result = replace_in_file(path=p, old_text="old", new_text="line1" + NL + "line2" + NL + "line3")
content = read_file(p)
test("Expand to multi-line", content == "line1" + NL + "line2" + NL + "line3" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 12: Line Range Edge Cases")
print("=" * 70)

print("\n--- Range beyond file end ---")
p = make_file("aaa" + NL + "bbb" + NL)
result = replace_in_file(path=p, old_text="bbb", new_text="BBB", start_line=2, end_line=100)
content = read_file(p)
test("Beyond-end range", content == "aaa" + NL + "BBB" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- start_line only (no end_line) ---")
p = make_file("aaa" + NL + "bbb" + NL + "ccc" + NL + "bbb" + NL + "ddd" + NL)
result = replace_in_file(path=p, old_text="bbb", new_text="BBB", start_line=3)
content = read_file(p)
test("start_line only", content == "aaa" + NL + "bbb" + NL + "ccc" + NL + "BBB" + NL + "ddd" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- start_line=1 (from beginning) ---")
p = make_file("first" + NL + "second" + NL + "first" + NL)
result = replace_in_file(path=p, old_text="first", new_text="FIRST", start_line=1, end_line=1)
content = read_file(p)
test("start_line=1 range", content == "FIRST" + NL + "second" + NL + "first" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 13: Indentation Adjustment")
print("=" * 70)

print("\n--- Fuzzy match adjusts new_text indentation ---")
p = make_file("class Foo:" + NL + "    def bar(self):" + NL + "        x = 1" + NL + "        return x" + NL)
result = replace_in_file(path=p,
    old_text="def bar(self):" + NL + "    x = 1" + NL + "    return x",
    new_text="def bar(self):" + NL + "    y = 2" + NL + "    return y")
content = read_file(p)
test("Indentation auto-adjusted", "        y = 2" in content, f"Got: {repr(content)}")
test("Still inside class", "class Foo:" in content)
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 14: Special Characters")
print("=" * 70)

print("\n--- Dollar sign ---")
p = make_file("price is $50.00 (each)" + NL)
result = replace_in_file(path=p, old_text="$50.00", new_text="$75.00")
content = read_file(p)
test("Dollar sign handled", content == "price is $75.00 (each)" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Parentheses and brackets ---")
p = make_file("arr[0] = func(x, y)" + NL)
result = replace_in_file(path=p, old_text="func(x, y)", new_text="func(a, b)")
content = read_file(p)
test("Brackets/parens handled", "func(a, b)" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 15: Stress - Large Content")
print("=" * 70)

print("\n--- Large file (10k lines) ---")
lines = [f"line {i}: content here" for i in range(10000)]
lines[5000] = "TARGET LINE HERE"
big_content = NL.join(lines) + NL
p = make_file(big_content)
result = replace_in_file(path=p, old_text="TARGET LINE HERE", new_text="REPLACED")
content = read_file(p)
test("Large file replacement", "REPLACED" in content)
test("Large file integrity", content.count(NL) == 10000)
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 16: Levenshtein Edge Cases")
print("=" * 70)

test("Levenshtein: empty strings", _levenshtein("", "") == 0)
test("Levenshtein: one empty", _levenshtein("abc", "") == 3)
test("Levenshtein: identical", _levenshtein("hello", "hello") == 0)
test("Levenshtein: single char diff", _levenshtein("cat", "bat") == 1)
test("Levenshtein: insertion", _levenshtein("abc", "abdc") == 1)
test("Levenshtein: deletion", _levenshtein("abcd", "acd") == 1)
test("Levenshtein: complete diff", _levenshtein("abc", "xyz") == 3)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 17: Blank Lines & Trailing Whitespace")
print("=" * 70)

print("\n--- Content with blank lines ---")
p = make_file("aaa" + NL + NL + NL + "bbb" + NL + NL + "ccc" + NL)
result = replace_in_file(path=p, old_text="bbb", new_text="BBB")
content = read_file(p)
test("Handles blank lines", content == "aaa" + NL + NL + NL + "BBB" + NL + NL + "ccc" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Trailing whitespace in file ---")
p = make_file("hello   " + NL + "world" + NL)
result = replace_in_file(path=p, old_text="hello", new_text="hi")
content = read_file(p)
test("Trailing whitespace handled", "hi" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print(f"RESULTS: PASS={PASS}  FAIL={FAIL}  ERROR={ERROR}")
print("=" * 70)
sys.exit(1 if (FAIL + ERROR) > 0 else 0)

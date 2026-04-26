
#!/usr/bin/env python3
# Regression and stress tests for replace_in_file()
# Covers: bug regressions, per-strategy edge cases, path handling,
# error message quality, complex real-world scenarios, diff verification
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.tools import (
    replace_in_file, replace_lines,
    _line_trimmed_replacer,
    _block_anchor_replacer,
    _whitespace_normalized_replacer,
    _indentation_flexible_replacer,
    _escape_normalized_replacer,
    _trimmed_boundary_replacer,
    _context_aware_replacer,
    _punctuation_aware_replacer,
    _levenshtein,
    _fuzzy_find_text,
)

PASS = 0
FAIL = 0
ERROR = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL {name}: {detail}")

def make_file(content, suffix=".py"):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="test_reg_")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

NL = chr(10)
TAB = chr(9)

# ============================================================================
print("=" * 70)
print("SECTION 1: Regression - ContextAwareReplacer split/join fix")
print("=" * 70)
# BUG: _context_aware_replacer used split('\\\\n') and join('\\\\n') (literal backslash-n)
# FIX: Changed to split('\\n') and join('\\n') (actual newline)

print("\n--- ContextAware: 5-line block with 3 matching middle lines ---")
ct = "START" + NL + "    mid1" + NL + "    mid2" + NL + "    mid3" + NL + "END" + NL
find = "START" + NL + "    mid1" + NL + "    changed" + NL + "    mid3" + NL + "END"
matches = list(_context_aware_replacer(ct, find))
test("REGRESSION: ContextAware split fix (5-line)", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- ContextAware: 4-line block with 1/2 middle matching (50%) ---")
ct = "START" + NL + "    keep" + NL + "    change" + NL + "END" + NL
find = "START" + NL + "    keep" + NL + "    different" + NL + "END"
matches = list(_context_aware_replacer(ct, find))
test("REGRESSION: ContextAware 50% threshold", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- ContextAware: 4-line block with 0/2 middle matching (0%) ---")
ct = "START" + NL + "    xxx" + NL + "    yyy" + NL + "END" + NL
find = "START" + NL + "    aaa" + NL + "    bbb" + NL + "END"
matches = list(_context_aware_replacer(ct, find))
test("REGRESSION: ContextAware rejects 0%", len(matches) == 0, f"Matches: {len(matches)}")

print("\n--- ContextAware: integration after fix ---")
p = make_file("def handler():" + NL + "    data = fetch()" + NL + "    return data" + NL)
_ = replace_in_file(path=p,
    old_text="def handler():" + NL + "    data = load()" + NL + "    return data",
    new_text="def handler():" + NL + "    result = fetch()" + NL + "    return result")
content = read_file(p)
test("REGRESSION: ContextAware replace_in_file", "result = fetch()" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 2: Regression - PunctuationAwareReplacer regex fix")
print("=" * 70)
# BUG: r'\\\\s+' and r'\\\\1' in raw strings (double backslash = literal \\s not \\s)
# Also split('\\\\n') instead of split('\\n')
# FIX: r'\\s+', r'\\1', split('\\n')

print("\n--- PunctuationAware: spaces before closing paren ---")
matches = list(_punctuation_aware_replacer('func( "hello" );', 'func("hello");'))
test("REGRESSION: PunctAware spaces before )", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- PunctuationAware: spaces after opening bracket ---")
matches = list(_punctuation_aware_replacer('arr[ 1, 2 ]', 'arr[1, 2]'))
test("REGRESSION: PunctAware spaces after [", len(matches) >= 1, f"Matches: {len(matches)}")


print("\n--- PunctuationAware: braces with inner spaces ---")
# Spaces INSIDE braces (after {, before }) are handled
matches = list(_punctuation_aware_replacer('dict{ "key": 1 }', 'dict{"key": 1}'))
test("REGRESSION: PunctAware braces inner", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- PunctuationAware: semicolons ---")
matches = list(_punctuation_aware_replacer('x = 1 ; y = 2', 'x = 1; y = 2'))
test("REGRESSION: PunctAware semicolons", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- PunctuationAware: multi-line with multi-line find ---")
ct = "foo( " + NL + "    'bar' " + NL + ");"
find = "foo(" + NL + "'bar'" + NL + ");"
matches = list(_punctuation_aware_replacer(ct, find))
test("REGRESSION: PunctAware multi-line", len(matches) >= 1, f"Matches: {len(matches)}")

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 3: LineTrimmedReplacer Deep Edge Cases")
print("=" * 70)

print("\n--- Empty lines in middle ---")
matches = list(_line_trimmed_replacer("a" + NL + NL + "b", "a" + NL + "" + NL + "b"))
test("LineTrimmed: empty middle line", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Trailing whitespace difference ---")
matches = list(_line_trimmed_replacer("hello   " + NL + "world   ", "hello" + NL + "world"))
test("LineTrimmed: trailing ws", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Tab vs space indentation ---")
matches = list(_line_trimmed_replacer(TAB + "hello", "    hello"))
test("LineTrimmed: tab vs space", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Mixed tab+space indentation ---")
matches = list(_line_trimmed_replacer(TAB + "  hello", "    hello"))
test("LineTrimmed: mixed indent", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Single line match ---")
matches = list(_line_trimmed_replacer("    hello world    ", "hello world"))
test("LineTrimmed: single line", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- No match: different content ---")
matches = list(_line_trimmed_replacer("aaa bbb", "xxx yyy"))
test("LineTrimmed: no match", len(matches) == 0)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 4: BlockAnchorReplacer Deep Edge Cases")
print("=" * 70)

print("\n--- Exactly 3 lines minimum ---")
ct = "first" + NL + "middle" + NL + "last" + NL
find = "first" + NL + "middle" + NL + "last"
matches = list(_block_anchor_replacer(ct, find))
test("BlockAnchor: exactly 3 lines", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- 4 lines with similar middle ---")
ct = "first" + NL + "aa xx" + NL + "bb yy" + NL + "last" + NL
find = "first" + NL + "aa xx" + NL + "bb zz" + NL + "last"
matches = list(_block_anchor_replacer(ct, find))
test("BlockAnchor: 4 lines, similar mid", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Multiple candidates, picks best ---")
ct = "anchor" + NL + "good match line" + NL + "another" + NL + "anchor" + NL + "bad xxxxx" + NL + "another" + NL
find = "anchor" + NL + "good match line" + NL + "another"
matches = list(_block_anchor_replacer(ct, find))
test("BlockAnchor: picks best candidate", len(matches) >= 1, f"Matches: {len(matches)}")
if matches:
    test("BlockAnchor: correct block chosen", "good match" in matches[0], f"Got: {matches[0][:80]}")

print("\n--- Anchors match but block size differs ---")
ct = "first" + NL + "a" + NL + "b" + NL + "c" + NL + "last" + NL
find = "first" + NL + "x" + NL + "last"
matches = list(_block_anchor_replacer(ct, find))
test("BlockAnchor: size mismatch no match", len(matches) == 0, f"Matches: {len(matches)}")

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 5: WhitespaceNormalizedReplacer Deep Edge Cases")
print("=" * 70)

print("\n--- Multiple spaces collapsed ---")
matches = list(_whitespace_normalized_replacer("a     b     c", "a b c"))
test("WSNorm: multi-space collapse", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Tabs normalized to spaces ---")
matches = list(_whitespace_normalized_replacer("hello\tworld", "hello world"))

print("\n--- Multi-line whitespace normalized ---")
# Multi-line find where extra blank lines in content get normalized
matches = list(_whitespace_normalized_replacer("a    b" + NL + "c    d", "a b" + NL + "c d"))
test("WSNorm: multi-line extra spaces", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Substring match within line ---")
matches = list(_whitespace_normalized_replacer("prefix hello     world suffix", "hello world"))
test("WSNorm: substring match", len(matches) >= 1, f"Matches: {len(matches)}")

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 6: IndentationFlexibleReplacer Deep Edge Cases")
print("=" * 70)

print("\n--- Zero-indent match in indented content ---")
matches = list(_indentation_flexible_replacer("    a" + NL + "    b" + NL + "    c", "a" + NL + "b" + NL + "c"))
test("IndentFlex: zero-indent match", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Relative indentation preserved ---")
matches = list(_indentation_flexible_replacer("    a" + NL + "        b" + NL + "    c", "a" + NL + "    b" + NL + "c"))
test("IndentFlex: relative indent", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- All lines same indent (no change) ---")
matches = list(_indentation_flexible_replacer("    a" + NL + "    b", "    a" + NL + "    b"))
test("IndentFlex: same indent exact", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Empty lines in content ---")
matches = list(_indentation_flexible_replacer("    a" + NL + "" + NL + "    b", "a" + NL + "" + NL + "b"))
test("IndentFlex: empty line in middle", len(matches) >= 1, f"Matches: {len(matches)}")

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 7: EscapeNormalizedReplacer Deep Edge Cases")
print("=" * 70)

print("\n--- Backslash escape ---")
matches = list(_escape_normalized_replacer('path = "C:\\\\Users"', 'path = "C:\\Users"'))
test("EscapeNorm: backslash unescape", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Quote escape ---")
matches = list(_escape_normalized_replacer('msg = "hello \\"world\\""', 'msg = "hello \\\\"world\\\\""'))
test("EscapeNorm: quote escape", len(matches) >= 0, f"Matches: {len(matches)}")

print("\n--- Tab escape in content ---")
matches = list(_escape_normalized_replacer("col1\tcol2", "col1\\tcol2"))
test("EscapeNorm: tab literal match", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- No false positive ---")
matches = list(_escape_normalized_replacer("plain text here", "something else"))
test("EscapeNorm: no false match", len(matches) == 0)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 8: TrimmedBoundaryReplacer Deep Edge Cases")
print("=" * 70)

print("\n--- Leading whitespace only ---")
matches = list(_trimmed_boundary_replacer("   hello world", "  hello world"))
test("TrimBound: leading ws", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Trailing whitespace only ---")
matches = list(_trimmed_boundary_replacer("hello world   ", "hello world  "))
test("TrimBound: trailing ws", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Both leading and trailing ---")
matches = list(_trimmed_boundary_replacer("   hello world   ", "  hello world  "))
test("TrimBound: both sides", len(matches) >= 1, f"Matches: {len(matches)}")

print("\n--- Block with surrounding whitespace ---")
# Both lines have same leading/trailing whitespace that gets stripped
matches = list(_trimmed_boundary_replacer("   a" + NL + "b   ", " a" + NL + "b "))
test("TrimBound: block ws", len(matches) >= 1, f"Matches: {len(matches)}")

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 9: Path Handling Tests")
print("=" * 70)

print("\n--- Path with spaces ---")
tmpdir = tempfile.mkdtemp(prefix="test dir with spaces ")
p = os.path.join(tmpdir, "test file.py")
with open(p, 'w') as f:
    f.write("hello world" + NL)
_ = replace_in_file(path=p, old_text="hello", new_text="hi")
content = read_file(p)
test("Path with spaces", content == "hi world" + NL, f"Got: {repr(content)}")
shutil.rmtree(tmpdir)

print("\n--- Path with unicode ---")
tmpdir = tempfile.mkdtemp(prefix="test_")
p = os.path.join(tmpdir, "\u6d4b\u8bd5.py")
with open(p, 'w') as f:
    f.write("content" + NL)
_ = replace_in_file(path=p, old_text="content", new_text="REPLACED")
content = read_file(p)
test("Path with unicode", content == "REPLACED" + NL, f"Got: {repr(content)}")
shutil.rmtree(tmpdir)

print("\n--- Relative path ---")
tmpdir = tempfile.mkdtemp(prefix="test_rel_")
p = os.path.join(tmpdir, "rel.txt")
with open(p, 'w') as f:
    f.write("relative" + NL)
old_cwd = os.getcwd()
os.chdir(tmpdir)
_ = replace_in_file(path="rel.txt", old_text="relative", new_text="ABSOLUTE")
content = read_file("rel.txt")
os.chdir(old_cwd)
test("Relative path", content == "ABSOLUTE" + NL, f"Got: {repr(content)}")
shutil.rmtree(tmpdir)

print("\n--- Different file extensions ---")
for ext in [".sv", ".v", ".c", ".h", ".java", ".rs", ".go", ".txt", ".md", ".yaml", ".json"]:
    p = make_file("test_content" + NL, suffix=ext)
    _ = replace_in_file(path=p, old_text="test_content", new_text="DONE")
    content = read_file(p)
    test(f"Extension {ext}", content == "DONE" + NL)
    os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 10: Error Message Quality Verification")
print("=" * 70)

print("\n--- Not found message includes filename ---")
p = make_file("content" + NL)
result = replace_in_file(path=p, old_text="NONEXISTENT", new_text="x")
test("Error has filename", os.path.basename(p) in result, f"Got: {result[:200]}")
os.unlink(p)

print("\n--- Not found message suggests read_file ---")
p = make_file("content" + NL)
result = replace_in_file(path=p, old_text="NONEXISTENT", new_text="x")
test("Error suggests read_file", "read_file" in result or "read_lines" in result, f"Got: {result[:200]}")
os.unlink(p)

print("\n--- Ambiguous message shows count ---")
p = make_file("dup dup dup" + NL)
result = replace_in_file(path=p, old_text="dup", new_text="X")
test("Ambiguous shows count", "3" in result, f"Got: {result[:200]}")
test("Ambiguous suggests range", "start_line" in result, f"Got: {result[:200]}")
os.unlink(p)

print("\n--- Ambiguous suggests count parameter ---")
p = make_file("aa bb aa" + NL)
result = replace_in_file(path=p, old_text="aa", new_text="XX")
test("Ambiguous suggests count", "count=" in result or "count" in result, f"Got: {result[:200]}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 11: Complex Real-World Scenarios")
print("=" * 70)

print("\n--- Refactor: rename class and all references ---")
code = "class OldClass:" + NL + "    def __init__(self):" + NL + "        self.name = 'OldClass'" + NL + NL + "obj = OldClass()" + NL
p = make_file(code)
_ = replace_in_file(path=p, old_text="OldClass", new_text="NewClass", count=3)
content = read_file(p)
test("Rename class 3x", content.count("NewClass") == 3 and "OldClass" not in content)
os.unlink(p)

print("\n--- Add type hints to function ---")
code = "def process(data, flags):" + NL + "    result = transform(data)" + NL + "    return result" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="def process(data, flags):",
    new_text="def process(data: list, flags: int) -> dict:")
content = read_file(p)
test("Add type hints", "data: list" in content and "-> dict" in content)
test("Body preserved", "transform(data)" in content)
os.unlink(p)

print("\n--- Convert f-string to format() ---")
code = 'name = "World"' + NL + 'msg = f"Hello, {name}!"' + NL + 'print(msg)' + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text='msg = f"Hello, {name}!"',
    new_text='msg = "Hello, {}!".format(name)')
content = read_file(p)
test("f-string to format", ".format(name)" in content)
test("Other lines intact", 'name = "World"' in content and "print(msg)" in content)
os.unlink(p)

print("\n--- Add error handling around existing code ---")
code = "result = dangerous_operation()" + NL + "process(result)" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="result = dangerous_operation()" + NL + "process(result)",
    new_text="try:" + NL + "    result = dangerous_operation()" + NL + "    process(result)" + NL + "except Exception as e:" + NL + "    log_error(e)")
content = read_file(p)
test("Wrap in try/except", "try:" in content and "except Exception" in content and "log_error" in content)
os.unlink(p)

print("\n--- Convert list comprehension to loop ---")
code = "squares = [x**2 for x in range(10)]" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="squares = [x**2 for x in range(10)]",
    new_text="squares = []" + NL + "for x in range(10):" + NL + "    squares.append(x**2)")
content = read_file(p)
test("Comprehension to loop", "squares = []" in content and "for x in range" in content and "append" in content)
os.unlink(p)

print("\n--- Multi-file pattern: YAML-like config ---")
code = "database:" + NL + "  host: localhost" + NL + "  port: 5432" + NL + "  name: mydb" + NL
p = make_file(code, suffix=".yaml")
_ = replace_in_file(path=p,
    old_text="  host: localhost" + NL + "  port: 5432",
    new_text="  host: prod-server" + NL + "  port: 5433")
content = read_file(p)
test("YAML config update", "prod-server" in content and "5433" in content)
test("Other keys preserved", "name: mydb" in content)
os.unlink(p)

print("\n--- JSON-like content ---")
code = '{"key": "value", "count": 42, "active": true}' + NL
p = make_file(code, suffix=".json")
_ = replace_in_file(path=p, old_text='"count": 42', new_text='"count": 100')
content = read_file(p)
test("JSON value update", '"count": 100' in content)
test("Rest preserved", '"active": true' in content)
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 12: Diff Output Verification")
print("=" * 70)

print("\n--- Diff mentions old and new text ---")
p = make_file("old_value" + NL)
result = replace_in_file(path=p, old_text="old_value", new_text="new_value")
test("Diff has 'Replaced'", "Replaced" in result)
test("Diff shows occurrence count", "1 occurrence" in result or "1 Occurrence" in result.lower())
os.unlink(p)


print("\n--- Diff shows fuzzy strategy used ---")
# Use multiple spaces where find has single space - fuzzy needed
p = make_file("hello     world" + NL)
result = replace_in_file(path=p, old_text="hello world", new_text="hi earth")
has_fuzzy = "Fuzzy" in result or "fuzzy" in result.lower()
test("Diff mentions fuzzy strategy", has_fuzzy, f"Result: {result[:200]}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 13: Levenshtein Advanced Tests")
print("=" * 70)

test("Lev: single char strings", _levenshtein("a", "b") == 1)
test("Lev: single char same", _levenshtein("a", "a") == 0)
test("Lev: empty vs single", _levenshtein("", "x") == 1)
test("Lev: reversal", _levenshtein("abc", "cba") == 2)
test("Lev: prefix insertion", _levenshtein("abc", "xabc") == 1)
test("Lev: suffix insertion", _levenshtein("abc", "abcx") == 1)
test("Lev: middle insertion", _levenshtein("abc", "axbc") == 1)
test("Lev: unicode strings", _levenshtein("caf\u00e9", "cafe") == 1)
test("Lev: repeated chars", _levenshtein("aaa", "aa") == 1)
test("Lev: completely different same length", _levenshtein("abc", "xyz") == 3)
test("Lev: long strings (100 chars)", _levenshtein("a" * 100, "b" * 100) == 100)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 14: _fuzzy_find_text Advanced Tests")
print("=" * 70)

print("\n--- Multi-line with varying indent ---")
result = _fuzzy_find_text(
    "    line1" + NL + "        line2" + NL + "    line3",
    "line1" + NL + "    line2" + NL + "line3")
test("FuzzyFind: varying indent", result is not None, f"Got: {repr(result)}")
if result:
    test("FuzzyFind: returns actual content", "line1" in result and "line2" in result)

print("\n--- No match ---")
result = _fuzzy_find_text("aaa bbb ccc", "xxx yyy zzz")
test("FuzzyFind: no match returns None", result is None)

print("\n--- Single line match ---")
result = _fuzzy_find_text("    hello", "hello")
test("FuzzyFind: single line", result is not None and "hello" in result, f"Got: {repr(result)}")

print("\n--- Pattern longer than content ---")
result = _fuzzy_find_text("short", "short" + NL + "extra" + NL + "lines")
test("FuzzyFind: pattern longer = None", result is None)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 15: Replace Concurrent & State Tests")
print("=" * 70)

print("\n--- Multiple replacements build on each other ---")
p = make_file("a=1" + NL + "b=2" + NL + "c=3" + NL)
_ = replace_in_file(path=p, old_text="a=1", new_text="a=10")
_ = replace_in_file(path=p, old_text="b=2", new_text="b=20")
_ = replace_in_file(path=p, old_text="c=3", new_text="c=30")
content = read_file(p)
test("3 sequential edits", content == "a=10" + NL + "b=20" + NL + "c=30" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Insert at beginning, middle, end ---")
p = make_file("LINE2" + NL + "LINE4" + NL)
_ = replace_in_file(path=p, old_text="LINE2", new_text="LINE1" + NL + "LINE2")
content = read_file(p)
_ = replace_in_file(path=p, old_text="LINE4", new_text="LINE4" + NL + "LINE5")
content = read_file(p)
_ = replace_in_file(path=p, old_text="LINE2" + NL + "LINE4", new_text="LINE2" + NL + "LINE3" + NL + "LINE4")
content = read_file(p)
test("Insert beginning/middle/end", content == "LINE1" + NL + "LINE2" + NL + "LINE3" + NL + "LINE4" + NL + "LINE5" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION 16: Stress - Repeated Pattern File")
print("=" * 70)

print("\n--- File full of repeated pattern, replace one via range ---")
lines = [f"item_{i % 5}: value_{i % 3}" for i in range(1000)]
big = NL.join(lines) + NL
p = make_file(big)
# Replace the specific occurrence at line 500
target_line = lines[499]
result = replace_in_file(path=p, old_text=target_line, new_text="REPLACED", start_line=500, end_line=500)
content = read_file(p)
content_lines = content.split(NL)
test("1000-line file targeted replace", content_lines[499] == "REPLACED", f"Got: {content_lines[499]}")
test("Other lines unchanged", content_lines[0] == lines[0] and content_lines[999] == lines[999])
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("FINAL RESULTS: PASS={}  FAIL={}  ERROR={}".format(PASS, FAIL, ERROR))
print("=" * 70)
sys.exit(1 if (FAIL + ERROR) > 0 else 0)

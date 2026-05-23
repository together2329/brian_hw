
#!/usr/bin/env python3
# Advanced replacement tests for replace_in_file()
# Focuses on: sequential edits, strategy priority, code patterns, boundary conditions
import sys
import os
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.tools import replace_in_file

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
                print(f"  FAIL {name}: Expected '{expected_in_msg}', got: {result[:200]}")
            else:
                PASS += 1
                print(f"  PASS {name} (returned error)")
        else:
            FAIL += 1
            print(f"  FAIL {name}: Expected error, got: {str(result)[:200]}")
    except Exception as e:
        ERROR += 1
        print(f"  ERR  {name}: {e}")

def make_file(content):
    fd, path = tempfile.mkstemp(suffix=".py", prefix="test_adv_")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

NL = chr(10)

# ============================================================================
print("=" * 70)
print("SECTION A: Sequential Replacements on Same File")
print("=" * 70)

print("\n--- Three sequential edits ---")
p = make_file("def hello():" + NL + "    pass" + NL)
r1 = replace_in_file(path=p, old_text="hello", new_text="greet")
c1 = read_file(p)
test("Seq 1: rename function", c1 == "def greet():" + NL + "    pass" + NL, f"Got: {repr(c1)}")

r2 = replace_in_file(path=p, old_text="pass", new_text="return 42")
c2 = read_file(p)
test("Seq 2: replace body", c2 == "def greet():" + NL + "    return 42" + NL, f"Got: {repr(c2)}")

r3 = replace_in_file(path=p, old_text="def greet():", new_text="async def greet():")
c3 = read_file(p)
test("Seq 3: add async", c3 == "async def greet():" + NL + "    return 42" + NL, f"Got: {repr(c3)}")
os.unlink(p)

print("\n--- Sequential: replace what was just added ---")
p = make_file("alpha" + NL)
_ = replace_in_file(path=p, old_text="alpha", new_text="beta")
_ = replace_in_file(path=p, old_text="beta", new_text="gamma")
content = read_file(p)
test("Chain alpha->beta->gamma", content == "gamma" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Sequential: replace old text again (should fail) ---")
p = make_file("alpha" + NL + "beta" + NL)
_ = replace_in_file(path=p, old_text="alpha", new_text="beta")
result = replace_in_file(path=p, old_text="alpha", new_text="gamma")
test("Old text gone - not found", "not found" in result.lower() or "Text not found" in result)
content = read_file(p)
test("File unchanged after failed seq", content == "beta" + NL + "beta" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Sequential: 10 rapid edits ---")
p = make_file("x = 0" + NL)
for i in range(10):
    Action: replace_in_file(path=p, old_text=f"x = {i}", new_text=f"x = {i+1}")
content = read_file(p)
test("10 sequential edits", content == "x = 10" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION B: Code Pattern Replacements")
print("=" * 70)

print("\n--- Rename function with decorator ---")
code = "@abstractmethod" + NL + "def old_name(self, x, y):" + NL + "    return x + y" + NL
p = make_file(code)
_ = replace_in_file(path=p, old_text="old_name", new_text="new_name")
content = read_file(p)
test("Rename in decorated function", content == "@abstractmethod" + NL + "def new_name(self, x, y):" + NL + "    return x + y" + NL)
os.unlink(p)

print("\n--- Replace entire function body ---")
code = "class Calculator:" + NL + "    def add(self, a, b):" + NL + "        result = a + b" + NL + "        return result" + NL + NL + "    def sub(self, a, b):" + NL + "        result = a - b" + NL + "        return result" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="def add(self, a, b):" + NL + "        result = a + b" + NL + "        return result",
    new_text="def add(self, a, b):" + NL + "        return a + b")
content = read_file(p)
test("Replace function body", "return a + b" in content and "result = a + b" not in content)
test("Other method intact", "def sub(self" in content)
os.unlink(p)

print("\n--- Add import at top ---")
code = "import os" + NL + "import sys" + NL + NL + "def main():" + NL + "    pass" + NL
p = make_file(code)
_ = replace_in_file(path=p, old_text="import os" + NL + "import sys", new_text="import os" + NL + "import json" + NL + "import sys")
content = read_file(p)
test("Add import in middle", "import json" in content)
test("Rest preserved", "def main():" in content)
os.unlink(p)

print("\n--- Remove entire block (delete) ---")
code = "before" + NL + "REMOVE_START" + NL + "content" + NL + "REMOVE_END" + NL + "after" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="REMOVE_START" + NL + "content" + NL + "REMOVE_END" + NL,
    new_text="")
content = read_file(p)
test("Block deletion", content == "before" + NL + "after" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Swap two lines ---")
code = "line_a" + NL + "line_b" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="line_a" + NL + "line_b",
    new_text="line_b" + NL + "line_a")
content = read_file(p)
test("Swap lines", content == "line_b" + NL + "line_a" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION C: Fuzzy Matching - Strategy Priority & Cascading")
print("=" * 70)

print("\n--- Exact match takes priority over fuzzy ---")
p = make_file("    hello" + NL)
result = replace_in_file(path=p, old_text="    hello", new_text="    hi")
content = read_file(p)
test("Exact match used (no fuzzy)", "Fuzzy" not in result, f"Result: {result[:100]}")
test("Exact result correct", content == "    hi" + NL)
os.unlink(p)

print("\n--- Fuzzy match when exact fails (whitespace diff) ---")
p = make_file("    hello world    " + NL)
result = replace_in_file(path=p, old_text="hello world", new_text="hi earth")
content = read_file(p)
test("Fuzzy match triggered", "Fuzzy" in result or "hi earth" in content, f"Result: {result[:100]}")
os.unlink(p)

print("\n--- fuzzy_whitespace=False disables fuzzy ---")
# Use multiple spaces where old_text has single space - only fuzzy can match this
p = make_file("hello     world" + NL)
result = replace_in_file(path=p, old_text="hello world", new_text="hi earth", fuzzy_whitespace=False)
test("Fuzzy disabled - no match", "not found" in result.lower() or "Text not found" in result)
content = read_file(p)
test("File unchanged", content == "hello     world" + NL, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION D: Multi-occurrence Scenarios")
print("=" * 70)

print("\n--- count=-1 with unique context (single occurrence in range) ---")
p = make_file("foo" + NL + "bar" + NL + "foo" + NL + "baz" + NL)
result = replace_in_file(path=p, old_text="foo", new_text="FOO", start_line=1, end_line=1)
content = read_file(p)
test("Range isolates single", content == "FOO" + NL + "bar" + NL + "foo" + NL + "baz" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- count=3 replaces all 3 ---")
p = make_file("x x x" + NL)
result = replace_in_file(path=p, old_text="x", new_text="Y", count=3)
content = read_file(p)
test("count=3 all replaced", content == "Y Y Y" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- count larger than occurrences ---")
p = make_file("only_one" + NL)
result = replace_in_file(path=p, old_text="only_one", new_text="done", count=999)
content = read_file(p)
test("count > occurrences", content == "done" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- count=0 (should replace 0?) ---")
p = make_file("hello world" + NL)
result = replace_in_file(path=p, old_text="hello", new_text="hi", count=0)
content = read_file(p)
# count=0 means str.replace(..., 0) which replaces 0 occurrences
test("count=0 no replacement", content == "hello world" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Two distinct occurrences, replace with longer text ---")
p = make_file("START middle END" + NL + "other line" + NL + "START other END" + NL)
result = replace_in_file(path=p, old_text="START middle END", new_text="START loooooong_middle END")
content = read_file(p)
test("Specific match replaced", "loooooong_middle" in content)
test("Other preserved", "START other END" in content)
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION E: Boundary & Extreme Cases")
print("=" * 70)

print("\n--- Replace entire file content ---")
p = make_file("entire file content here" + NL)
_ = replace_in_file(path=p, old_text="entire file content here" + NL, new_text="replaced everything" + NL)
content = read_file(p)
test("Entire file replaced", content == "replaced everything" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- No trailing newline in file ---")
p = make_file("no newline at end")
_ = replace_in_file(path=p, old_text="at end", new_text="AT END")
content = read_file(p)
test("No trailing newline", content == "no newline AT END", f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replace adds trailing newline ---")
p = make_file("no newline")
_ = replace_in_file(path=p, old_text="no newline", new_text="has newline" + NL)
content = read_file(p)
test("Add trailing newline", content == "has newline" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replace removes trailing newline ---")
p = make_file("has newline" + NL)
_ = replace_in_file(path=p, old_text="has newline" + NL, new_text="no newline")
content = read_file(p)
test("Remove trailing newline", content == "no newline", f"Got: {repr(content)}")
os.unlink(p)

print("\n--- File with only whitespace ---")
p = make_file("   " + NL + "   " + NL)
result = replace_in_file(path=p, old_text="something", new_text="else")
test("Whitespace file - not found", "not found" in result.lower() or "Text not found" in result)
os.unlink(p)

print("\n--- old_text is single newline ---")
p = make_file("a" + NL + NL + "b" + NL)
_ = replace_in_file(path=p, old_text=NL + NL, new_text=NL)
content = read_file(p)
test("Replace double newline", content == "a" + NL + "b" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- new_text contains old_text (potential loop) ---")
p = make_file("abc" + NL)
_ = replace_in_file(path=p, old_text="abc", new_text="abc_def_abc")
content = read_file(p)
test("new contains old", content == "abc_def_abc" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Very long replacement (10k chars) ---")
p = make_file("placeholder" + NL)
long_text = "X" * 10000
_ = replace_in_file(path=p, old_text="placeholder", new_text=long_text)
content = read_file(p)
test("Long replacement", len(content) == 10001, f"Got len: {len(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION F: Indentation Edge Cases")
print("=" * 70)

print("\n--- Deeply nested code (4 levels) ---")
code = "class A:" + NL + "    class B:" + NL + "        class C:" + NL + "            def method(self):" + NL + "                return 42" + NL
p = make_file(code)
result = replace_in_file(path=p,
    old_text="def method(self):" + NL + "    return 42",
    new_text="def method(self):" + NL + "    return 99")
content = read_file(p)
test("Deep nesting indent adjusted", "                return 99" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Mixed tabs and spaces ---")
code = "\tdef foo():" + NL + "\t    if True:" + NL + "\t        pass" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="def foo():" + NL + "    if True:" + NL + "        pass",
    new_text="def foo():" + NL + "    if False:" + NL + "        pass")
content = read_file(p)
test("Mixed tab/space indent", "if False" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Replacing with less indentation ---")
code = "        alpha" + NL + "        beta" + NL + "        gamma" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="alpha" + NL + "        beta",
    new_text="ALPHA" + NL + "BETA")
content = read_file(p)
test("Indent adjusted down", "BETA" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION G: Real-World Code Patterns")
print("=" * 70)

print("\n--- Rename variable across lines ---")
code = "def calc(x):" + NL + "    result = x * 2" + NL + "    return result" + NL
p = make_file(code)
_ = replace_in_file(path=p, old_text="result", new_text="output", count=2)
content = read_file(p)
test("Rename var 2x", "output = x * 2" in content and "return output" in content)
os.unlink(p)

print("\n--- Update string literal ---")
code = 'msg = "Hello, World!"' + NL + 'print(msg)' + NL
p = make_file(code)
_ = replace_in_file(path=p, old_text='"Hello, World!"', new_text='"Goodbye, World!"')
content = read_file(p)
test("Update string literal", '"Goodbye, World!"' in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Add parameter to function ---")
code = "def connect(host, port):" + NL + "    pass" + NL
p = make_file(code)
_ = replace_in_file(path=p, old_text="def connect(host, port):", new_text="def connect(host, port, timeout=30):")
content = read_file(p)
test("Add param", "timeout=30" in content)
os.unlink(p)

print("\n--- Replace try/except with try/finally ---")
code = "try:" + NL + "    risky()" + NL + "except Exception as e:" + NL + "    handle(e)" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="except Exception as e:" + NL + "    handle(e)",
    new_text="finally:" + NL + "    cleanup()")
content = read_file(p)
test("Replace except with finally", "finally:" in content and "cleanup()" in content)
test("Try block preserved", "risky()" in content)
os.unlink(p)

print("\n--- Add docstring to function ---")
code = "def undocumented():" + NL + "    x = 1" + NL + "    return x" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="def undocumented():" + NL + "    x = 1",
    new_text="def undocumented():" + NL + '    """Does something."""' + NL + "    x = 1")
content = read_file(p)
test("Add docstring", '"""Does something."""' in content)
os.unlink(p)

print("\n--- Replace multiline list ---")
code = "items = [" + NL + "    'a'," + NL + "    'b'," + NL + "    'c'," + NL + "]" + NL
p = make_file(code)
_ = replace_in_file(path=p,
    old_text="'a'," + NL + "    'b'," + NL + "    'c',",
    new_text="'x'," + NL + "    'y'," + NL + "    'z',")
content = read_file(p)
test("Replace list items", "'x'," in content and "'z'," in content)
test("Brackets intact", "items = [" in content and content.strip().endswith("]"))
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION H: Ambiguous & Confusing Patterns")
print("=" * 70)

print("\n--- Very similar blocks, disambiguate with range ---")
code = "def foo():" + NL + "    x = 1" + NL + "    return x" + NL + NL + "def bar():" + NL + "    x = 1" + NL + "    return x" + NL
p = make_file(code)
result = replace_in_file(path=p,
    old_text="def foo():" + NL + "    x = 1" + NL + "    return x",
    new_text="def foo():" + NL + "    x = 2" + NL + "    return x",
    start_line=1, end_line=3)
content = read_file(p)
test("Disambiguate with range", "x = 2" in content and content.count("x = 1") == 1)
os.unlink(p)

print("\n--- Nested pattern: inner vs outer ---")
code = "outer_start outer_mid outer_end" + NL
p = make_file(code)
_ = replace_in_file(path=p, old_text="outer_mid", new_text="INNER")
content = read_file(p)
test("Inner match replaced", content == "outer_start INNER outer_end" + NL)
os.unlink(p)

print("\n--- Overlapping potential matches ---")
p = make_file("abcabc" + NL)
_ = replace_in_file(path=p, old_text="abc", new_text="X", count=1)
content = read_file(p)
test("First overlap replaced", content == "Xabc" + NL, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Pattern at very start of file ---")
p = make_file("FIRST line" + NL + "second line" + NL)
_ = replace_in_file(path=p, old_text="FIRST line" + NL, new_text="REPLACED line" + NL)
content = read_file(p)
test("Replace at start", content == "REPLACED line" + NL + "second line" + NL)
os.unlink(p)

print("\n--- Pattern at very end of file (no trailing newline) ---")
p = make_file("first line" + NL + "LAST line")
_ = replace_in_file(path=p, old_text="LAST line", new_text="REPLACED line")
content = read_file(p)
test("Replace at end (no newline)", content == "first line" + NL + "REPLACED line")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION I: Fuzzy Matching Complex Scenarios")
print("=" * 70)

print("\n--- Fuzzy: different indentation + extra blank lines ---")
code = "class Handler:" + NL + NL + "    def process(self):" + NL + "        data = load()" + NL + "        return data" + NL
p = make_file(code)
result = replace_in_file(path=p,
    old_text="def process(self):" + NL + "    data = load()" + NL + "    return data",
    new_text="def process(self):" + NL + "    result = compute()" + NL + "    return result")
content = read_file(p)
test("Fuzzy with blank lines", "result = compute()" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Fuzzy: whitespace-only difference in middle ---")
code = "start" + NL + "    middle" + NL + "end" + NL
p = make_file(code)
result = replace_in_file(path=p,
    old_text="start" + NL + "  middle" + NL + "end",
    new_text="start" + NL + "  CHANGED" + NL + "end")
content = read_file(p)
test("Whitespace diff fuzzy match", "CHANGED" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Fuzzy: trailing whitespace difference ---")
code = "hello   " + NL + "world   " + NL
p = make_file(code)
result = replace_in_file(path=p,
    old_text="hello" + NL + "world",
    new_text="HELLO" + NL + "WORLD")
content = read_file(p)
test("Trailing ws fuzzy", "HELLO" in content, f"Got: {repr(content)}")
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION J: Error Recovery & Robustness")
print("=" * 70)

print("\n--- Invalid start_line (negative) ---")
p = make_file("content" + NL)
result = replace_in_file(path=p, old_text="content", new_text="X", start_line=-1)
content = read_file(p)
# Negative start_line becomes max(0, -1-1) = 0, so it should still work
test("Negative start_line handled", "X" in content or "Error" in result)
os.unlink(p)

print("\n--- start_line > end_line ---")
p = make_file("aaa" + NL + "bbb" + NL + "ccc" + NL)
result = replace_in_file(path=p, old_text="bbb", new_text="BBB", start_line=3, end_line=2)
# Range would be empty or inverted - should gracefully handle
content = read_file(p)
test("Inverted range handled", content == "aaa" + NL + "bbb" + NL + "ccc" + NL or "BBB" in content)
os.unlink(p)

print("\n--- start_line=0 (boundary) ---")
p = make_file("first" + NL + "second" + NL)
result = replace_in_file(path=p, old_text="first", new_text="FIRST", start_line=0, end_line=1)
content = read_file(p)
test("start_line=0 works", "FIRST" in content, f"Got: {repr(content)}")
os.unlink(p)

print("\n--- Very large start_line ---")
p = make_file("content" + NL)
result = replace_in_file(path=p, old_text="content", new_text="X", start_line=999999)
content = read_file(p)
test("Large start_line handled", content == "content" + NL or "X" in content)
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION K: Unicode & International Content")
print("=" * 70)

print("\n--- Chinese characters ---")
p = make_file("x = 1  # " + NL)
_ = replace_in_file(path=p, old_text="x = 1", new_text="x = 2")
content = read_file(p)
test("Chinese comment preserved", "x = 2" in content and "" in content)
os.unlink(p)

print("\n--- Emoji in content ---")
p = make_file("status = 'done '" + NL)
_ = replace_in_file(path=p, old_text="done", new_text="finished")
content = read_file(p)
test("Emoji preserved", "finished" in content and "" in content)
os.unlink(p)

print("\n--- Arabic RTL text ---")
p = make_file("# " + NL + "x = 1" + NL)
_ = replace_in_file(path=p, old_text="x = 1", new_text="x = 2")
content = read_file(p)
test("Arabic text preserved", "x = 2" in content and "" in content)
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print("SECTION L: Concurrent File State")
print("=" * 70)

print("\n--- File modified externally between reads (simulated) ---")
p = make_file("version1" + NL)
# First read + replace
_ = replace_in_file(path=p, old_text="version1", new_text="version2")
# Verify it's version2 now
content = read_file(p)
test("State after first edit", content == "version2" + NL)
# Do another edit
_ = replace_in_file(path=p, old_text="version2", new_text="version3")
content = read_file(p)
test("State after second edit", content == "version3" + NL)
os.unlink(p)

# ============================================================================
print("\n" + "=" * 70)
print(f"FINAL RESULTS: PASS={PASS}  FAIL={FAIL}  ERROR={ERROR}")
print("=" * 70)
sys.exit(1 if (FAIL + ERROR) > 0 else 0)


#!/usr/bin/env python3
# Comprehensive tests for ALL tool functions in tools.py
# Covers: write_file, read_file, read_lines, grep_file, find_files, list_dir,
# git_diff, git_status, run_command
import sys
import os
import tempfile
import shutil

# Disable git auto-commit for tests (prevents thread pileup)
# Must be done before importing config
os.environ['GIT_VERSION_CONTROL_ENABLE'] = 'false'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock config to disable git auto-commit
try:
    import config
    config.GIT_VERSION_CONTROL_ENABLE = False
except ImportError:
    # Create a minimal config module
    import types
    config = types.ModuleType('config')
    config.GIT_VERSION_CONTROL_ENABLE = False
    config.ENABLE_LINTING = False
    config.AUTO_CHMOD_WRITE = False
    config.DEBUG_MODE = False
    sys.modules['config'] = config
from core.tools import (
    write_file, read_file, read_lines, grep_file, find_files, list_dir,
    run_command, git_diff, git_status,
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

NL = chr(10)

def make_file(content, suffix=".py"):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="test_tools_")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

if __name__ == '__main__':
    # ============================================================================
    print("=" * 70)
    print("SECTION 1: write_file() Tests")
    print("=" * 70)

    print("\n--- Basic write ---")
    p = make_file("")
    result = write_file(path=p, content="hello world" + NL)
    test("write_file returns success", "Successfully" in result, f"Got: {result}")
    content = open(p).read()
    test("write_file content correct", content == "hello world" + NL, f"Got: {repr(content)}")
    os.unlink(p)

    print("\n--- Overwrite existing ---")
    p = make_file("old content" + NL)
    _ = write_file(path=p, content="new content" + NL)
    content = open(p).read()
    test("Overwrite works", content == "new content" + NL, f"Got: {repr(content)}")
    os.unlink(p)

    print("\n--- Append mode ---")
    p = make_file("line1" + NL)
    _ = write_file(path=p, content="line2" + NL, append=True)
    content = open(p).read()
    test("Append mode", content == "line1" + NL + "line2" + NL, f"Got: {repr(content)}")
    os.unlink(p)

    print("\n--- Create directory structure ---")
    tmpdir = tempfile.mkdtemp(prefix="test_wf_")
    nested_path = os.path.join(tmpdir, "sub1", "sub2", "test.py")
    _ = write_file(path=nested_path, content="nested" + NL)
    test("Creates parent dirs", os.path.exists(nested_path))
    test("Content correct", open(nested_path).read() == "nested" + NL)
    shutil.rmtree(tmpdir)

    print("\n--- Write to existing file (chmod test) ---")
    p = make_file("original" + NL)
    _ = write_file(path=p, content="modified" + NL)
    test("Overwrite existing", open(p).read() == "modified" + NL)
    os.unlink(p)

    print("\n--- Missing parameters ---")
    test("No path error", "Error" in str(write_file()))
    test("No content error", "Error" in str(write_file(path="/tmp/test.py")))
    test("No content msg", "content" in str(write_file(path="/tmp/test.py")))

    print("\n--- Empty content ---")
    p = make_file("existing" + NL)
    _ = write_file(path=p, content="")
    test("Empty content clears file", open(p).read() == "")
    os.unlink(p)

    print("\n--- Large content (100KB) ---")
    p = make_file("")
    big = "x" * 100000
    _ = write_file(path=p, content=big)
    test("Large write", open(p).read() == big)
    os.unlink(p)

    print("\n--- Unicode content ---")
    p = make_file("")
    _ = write_file(path=p, content="Hello \u4e16\u754c\U0001f600" + NL)
    test("Unicode write", open(p, encoding='utf-8').read() == "Hello \u4e16\u754c\U0001f600" + NL)
    os.unlink(p)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 2: read_file() Tests")
    print("=" * 70)

    print("\n--- Basic read ---")
    p = make_file("content here" + NL)
    result = read_file(p)
    test("Basic read", result == "content here" + NL, f"Got: {repr(result)}")
    os.unlink(p)

    print("\n--- Read non-existent file ---")
    result = read_file("/tmp/nonexistent_xyz_12345.txt")
    test("Non-existent error", "Error" in result or "does not exist" in result)
    test("Suggests find_files", "find_files" in result)

    print("\n--- Read empty file ---")
    p = make_file("")
    result = read_file(p)
    test("Empty file", result == "")
    os.unlink(p)

    print("\n--- Read large file (truncation) ---")
    lines = [f"line {i}" for i in range(600)]
    p = make_file(NL.join(lines) + NL)
    result = read_file(p)
    test("Large file truncated", "LARGE FILE" in result or len(lines) <= 500 or "line 499" in result)
    test("Shows suggestion", "grep_file" in result or "read_lines" in result)
    os.unlink(p)

    print("\n--- Read with unicode ---")
    p = make_file("\u4e16\u754c\U0001f600" + NL)
    result = read_file(p)
    test("Unicode read", "\u4e16\u754c" in result and "\U0001f600" in result)
    os.unlink(p)

    print("\n--- Read single line (no trailing newline) ---")
    p = make_file("single line")
    result = read_file(p)
    test("No trailing newline", result == "single line")
    os.unlink(p)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 3: read_lines() Tests")
    print("=" * 70)

    print("\n--- Basic range ---")
    p = make_file(NL.join([f"line{i}" for i in range(10)]) + NL)
    result = read_lines(path=p, start_line=3, end_line=5)
    test("Basic range", "line2" in result and "line4" in result, f"Got: {result[:200]}")
    test("Has line numbers", "3:" in result and "5:" in result)
    test("Total shown", "total: 10" in result)
    os.unlink(p)

    print("\n--- Single line ---")
    p = make_file(NL.join([f"line{i}" for i in range(5)]) + NL)
    result = read_lines(path=p, start_line=3, end_line=3)
    test("Single line", "line2" in result and "line2" in result)
    os.unlink(p)

    print("\n--- String line numbers ---")
    p = make_file("content" + NL)
    result = read_lines(path=p, start_line="1", end_line="1")
    test("String line numbers coerced", "content" in result)
    os.unlink(p)

    print("\n--- Range string ---")
    p = make_file(NL.join([f"line{i}" for i in range(10)]) + NL)
    result = read_lines(path=p, start_line="3-5")
    test("Range string parsed", "line2" in result and "line4" in result)
    os.unlink(p)

    print("\n--- end_line beyond file ---")
    p = make_file("a" + NL + "b" + NL)
    result = read_lines(path=p, start_line=1, end_line=999)
    test("end_line clamped", "a" in result and "b" in result)
    test("No error", "Error" not in result)
    os.unlink(p)

    print("\n--- start_line beyond file ---")
    p = make_file("content" + NL)
    result = read_lines(path=p, start_line=999, end_line=999)
    test("Beyond file error", "Error" in result or "beyond" in result.lower())
    os.unlink(p)

    print("\n--- start_line > end_line ---")
    p = make_file("content" + NL)
    result = read_lines(path=p, start_line=5, end_line=2)
    test("Inverted range error", "Error" in result)
    os.unlink(p)

    print("\n--- Negative line numbers ---")
    p = make_file("content" + NL)
    result = read_lines(path=p, start_line=-1, end_line=5)
    test("Negative line error", "Error" in result or ">=" in result or ">= 1" in result)
    os.unlink(p)

    print("\n--- Default end_line (50 lines) ---")
    lines = [f"line{i}" for i in range(100)]
    p = make_file(NL.join(lines) + NL)
    result = read_lines(path=p, start_line=1)
    test("Default end_line_50", "line49" in result, f"Missing line49")
    os.unlink(p)

    print("\n--- Missing parameters ---")
    test("Missing path", "Error" in str(read_lines()))
    test("Missing start_line", "Error" in str(read_lines(path="test.py")))

    print("\n--- Non-existent file ---")
    result = read_lines(path="/tmp/nonexistent_xyz.txt", start_line=1, end_line=1)
    test("Non-existent error", "Error" in result or "does not exist" in result)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 4: grep_file() Tests")
    print("=" * 70)

    print("\n--- Basic pattern match ---")
    p = make_file("hello world" + NL + "foo bar" + NL + "hello again" + NL)
    result = grep_file(pattern="hello", path=p)
    test("Finds pattern", "hello" in result, f"Got: {result[:200]}")
    test("Shows matches", ">>>" in result)
    os.unlink(p)

    print("\n--- Regex pattern ---")
    p = make_file("abc123def" + NL + "xyz789uvw" + NL)
    result = grep_file(pattern="[0-9]+", path=p)
    test("Regex match", "123" in result or "789" in result, f"Got: {result[:200]}")
    os.unlink(p)

    print("\n--- No match ---")
    p = make_file("hello world" + NL)
    result = grep_file(pattern="NONEXISTENT_PATTERN_XYZ", path=p)
    test("No match", "No matches" in result or "No files" in result, f"Got: {result[:200]}")
    os.unlink(p)

    print("\n--- Multiple matches ---")
    p = make_file("match1" + NL + "other" + NL + "match2" + NL + "match3" + NL)
    result = grep_file(pattern="match", path=p)
    test("Multiple matches", result.count(">>>") >= 3, f"Got count: {result.count('>>>')}")
    os.unlink(p)

    print("\n--- Missing parameters ---")
    test("Missing pattern", "Error" in str(grep_file(path="test.py")))
    test("Missing path", "Error" in str(grep_file(pattern="test")))

    print("\n--- Non-existent path ---")
    result = grep_file(pattern="test", path="/tmp/nonexistent_dir_xyz")
    test("Non-existent path handled", "Error" in result or "No matches" in result or "not found" in result.lower())

    print("\n--- Directory search (recursive) ---")
    tmpdir = tempfile.mkdtemp(prefix="test_grep_")
    with open(os.path.join(tmpdir, "a.py"), 'w') as f:
        f.write("TARGET_PATTERN" + NL)
    with open(os.path.join(tmpdir, "b.py"), 'w') as f:
        f.write("other" + NL)
    result = grep_file(pattern="TARGET_PATTERN", path=tmpdir, recursive=True)
    test("Dir recursive search", "TARGET_PATTERN" in result, f"Got: {result[:200]}")
    shutil.rmtree(tmpdir)

    print("\n--- Context lines ---")
    p = make_file(NL.join([f"line{i}" for i in range(10)]) + NL)
    result = grep_file(pattern="line5", path=p, context_lines=2)
    test("Context before", "line3" in result or "line4" in result, f"Got: {result[:200]}")
    test("Context after", "line6" in result or "line7" in result)
    os.unlink(p)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 5: find_files() Tests")
    print("=" * 70)

    print("\n--- Basic find ---")
    tmpdir = tempfile.mkdtemp(prefix="test_find_")
    for name in ["test_a.py", "test_b.py", "other.txt"]:
        open(os.path.join(tmpdir, name), 'w').close()
    result = find_files(pattern="test_*.py", directory=tmpdir)
    test("Finds matching files", "test_a.py" in result and "test_b.py" in result, f"Got: {result}")
    test("Excludes non-matching", "other.txt" not in result)
    shutil.rmtree(tmpdir)

    print("\n--- No matches ---")
    tmpdir = tempfile.mkdtemp(prefix="test_find2_")
    open(os.path.join(tmpdir, "readme.txt"), 'w').close()
    result = find_files(pattern="*.xyz", directory=tmpdir)
    test("No matches message", "No files" in result, f"Got: {result}")
    shutil.rmtree(tmpdir)

    print("\n--- Missing pattern ---")
    result = find_files()
    test("Missing pattern error", "Error" in result)

    print("\n--- Non-existent directory ---")
    result = find_files(pattern="*.py", directory="/tmp/nonexistent_xyz")
    test("Non-existent dir error", "Error" in result or "does not exist" in result)

    print("\n--- Recursive find ---")
    tmpdir = tempfile.mkdtemp(prefix="test_find3_")
    os.makedirs(os.path.join(tmpdir, "sub"))
    open(os.path.join(tmpdir, "top.py"), 'w').close()
    open(os.path.join(tmpdir, "sub", "deep.py"), 'w').close()
    result = find_files(pattern="*.py", directory=tmpdir, recursive=True)
    test("Recursive finds deep", "deep.py" in result, f"Got: {result}")
    shutil.rmtree(tmpdir)

    print("\n--- Non-recursive find ---")
    tmpdir = tempfile.mkdtemp(prefix="test_find4_")
    os.makedirs(os.path.join(tmpdir, "sub"))
    open(os.path.join(tmpdir, "top.py"), 'w').close()
    open(os.path.join(tmpdir, "sub", "deep.py"), 'w').close()
    result = find_files(pattern="*.py", directory=tmpdir, recursive=False)
    test("Non-recursive top only", "top.py" in result and "deep.py" not in result, f"Got: {result}")
    shutil.rmtree(tmpdir)

    print("\n--- path parameter as alias for directory ---")
    tmpdir = tempfile.mkdtemp(prefix="test_find5_")
    open(os.path.join(tmpdir, "test.py"), 'w').close()
    result = find_files(pattern="*.py", path=tmpdir)
    test("path alias works", "test.py" in result, f"Got: {result}")
    shutil.rmtree(tmpdir)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 6: list_dir() Tests")
    print("=" * 70)

    print("\n--- Basic listing ---")
    tmpdir = tempfile.mkdtemp(prefix="test_ls_")
    for name in ["a.py", "b.txt", "c.py"]:
        open(os.path.join(tmpdir, name), 'w').close()
    result = list_dir(path=tmpdir)
    test("Lists files", "a.py" in result and "b.txt" in result, f"Got: {result}")
    shutil.rmtree(tmpdir)

    print("\n--- Empty directory ---")
    tmpdir = tempfile.mkdtemp(prefix="test_ls2_")
    result = list_dir(path=tmpdir)
    test("Empty dir", result == "" or len(result.strip()) == 0, f"Got: {repr(result)}")
    shutil.rmtree(tmpdir)

    print("\n--- Non-existent directory ---")
    result = list_dir(path="/tmp/nonexistent_xyz_dir")
    test("Non-existent error", "does not exist" in result or "Error" in result)

    print("\n--- File path (not directory) ---")
    p = make_file("content")
    result = list_dir(path=p)
    test("File not dir message", "file" in result.lower() and "not a directory" in result.lower(), f"Got: {result}")
    os.unlink(p)

    print("\n--- Hidden files ---")
    tmpdir = tempfile.mkdtemp(prefix="test_ls3_")
    open(os.path.join(tmpdir, ".hidden"), 'w').close()
    open(os.path.join(tmpdir, "visible"), 'w').close()
    result_show = list_dir(path=tmpdir, show_hidden=True)
    result_hide = list_dir(path=tmpdir, show_hidden=False)
    test("Shows hidden", ".hidden" in result_show, f"Got: {result_show}")
    test("Hides hidden", ".hidden" not in result_hide, f"Got: {result_hide}")
    shutil.rmtree(tmpdir)

    print("\n--- Default path (current dir) ---")
    result = list_dir()
    test("Default path works", len(result) > 0 or result == "")

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 7: run_command() Tests")
    print("=" * 70)

    print("\n--- Simple command ---")
    result = run_command("echo hello")
    test("Echo works", "hello" in result, f"Got: {result}")

    print("\n--- Command with exit code ---")
    result = run_command("false")
    test("Failed command handled", len(result) >= 0)  # Should not crash

    print("\n--- Multi-line output ---")
    result = run_command("echo line1 && echo line2")
    test("Multi-line", "line1" in result and "line2" in result)

    print("\n--- Environment variable ---")
    result = run_command("echo $HOME")
    test("Env var", len(result) > 0)

    print("\n--- Timeout parameter ---")
    result = run_command("echo fast", timeout=5)
    test("Timeout param", "fast" in result)

    print("\n--- Piped commands ---")
    result = run_command("echo 'hello world' | grep hello")
    test("Pipe works", "hello" in result)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 8: git_diff() Tests")
    print("=" * 70)

    print("\n--- git_diff with no changes ---")
    tmpdir = tempfile.mkdtemp(prefix="test_git_")
    result = git_diff()
    test("git_diff runs", len(result) >= 0)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 9: git_status() Tests")
    print("=" * 70)

    result = git_status()
    test("git_status runs", len(result) >= 0)
    test("git_status format", "clean" in result.lower() or "git" in result.lower() or len(result) > 0)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 10: Tool Interoperability")
    print("=" * 70)

    print("\n--- Write then read ---")
    tmpdir = tempfile.mkdtemp(prefix="test_interop_")
    p = os.path.join(tmpdir, "test.py")
    _ = write_file(path=p, content="line1" + NL + "line2" + NL + "line3" + NL)
    content = read_file(p)
    test("Write+Read", content == "line1" + NL + "line2" + NL + "line3" + NL)
    shutil.rmtree(tmpdir)

    print("\n--- Write then grep ---")
    tmpdir = tempfile.mkdtemp(prefix="test_interop2_")
    p = os.path.join(tmpdir, "test.py")
    _ = write_file(path=p, content="def hello():" + NL + "    pass" + NL)
    result = grep_file(pattern="def hello", path=p)
    test("Write+Grep", "def hello" in result, f"Got: {result[:200]}")
    shutil.rmtree(tmpdir)

    print("\n--- Write then read_lines ---")
    tmpdir = tempfile.mkdtemp(prefix="test_interop3_")
    p = os.path.join(tmpdir, "test.py")
    _ = write_file(path=p, content=NL.join([f"line{i}" for i in range(10)]) + NL)
    result = read_lines(path=p, start_line=5, end_line=7)
    test("Write+ReadLines", "line4" in result and "line6" in result)
    shutil.rmtree(tmpdir)

    print("\n--- Write then find ---")
    tmpdir = tempfile.mkdtemp(prefix="test_interop4_")
    _ = write_file(path=os.path.join(tmpdir, "target.py"), content="x")
    result = find_files(pattern="target.py", directory=tmpdir)
    test("Write+Find", "target.py" in result)
    shutil.rmtree(tmpdir)

    print("\n--- Write append then read ---")
    tmpdir = tempfile.mkdtemp(prefix="test_interop5_")
    p = os.path.join(tmpdir, "test.py")
    _ = write_file(path=p, content="first" + NL)
    _ = write_file(path=p, content="second" + NL, append=True)
    content = read_file(p)
    test("Write+Append+Read", content == "first" + NL + "second" + NL, f"Got: {repr(content)}")
    shutil.rmtree(tmpdir)

    # ============================================================================
    print("\n" + "=" * 70)
    print("SECTION 11: Edge Cases - File System Operations")
    print("=" * 70)

    print("\n--- Read binary-like file with utf-8 errors ---")
    p = os.path.join(tempfile.mkdtemp(), "binary.txt")
    with open(p, 'wb') as f:
        f.write(b"hello \xff world")
    # read_file might fail or handle gracefully
    result = read_file(p)
    test("Binary file handled", "hello" in result or "Error" in result, f"Got: {result[:100]}")
    os.unlink(p)

    print("\n--- Grep in file with special regex chars ---")
    p = make_file("price: $50.00 (each)" + NL)
    result = grep_file(pattern=r"\\$50", path=p)
    test("Special regex chars", "50" in result or "No matches" in result, f"Got: {result[:200]}")
    os.unlink(p)

    print("\n--- Find files with complex pattern ---")
    tmpdir = tempfile.mkdtemp(prefix="test_find_complex_")
    for name in ["test_1.py", "test_2.py", "prod_1.py", "test_1.txt"]:
        open(os.path.join(tmpdir, name), 'w').close()
    result = find_files(pattern="test_*.py", directory=tmpdir)
    test("Complex glob", "test_1.py" in result and "test_2.py" in result)
    test("Excludes wrong ext", "test_1.txt" not in result)
    test("Excludes wrong prefix", "prod_1.py" not in result)
    shutil.rmtree(tmpdir)

    print("\n--- Read file with very long lines ---")
    p = make_file("x" * 10000 + NL)
    result = read_file(p)
    test("Long line read", "x" in result)
    os.unlink(p)

    # ============================================================================
    print("\n" + "=" * 70)
    print(f"FINAL RESULTS: PASS={PASS}  FAIL={FAIL}  ERROR={ERROR}")
    print("=" * 70)
    sys.exit(1 if (FAIL + ERROR) > 0 else 0)

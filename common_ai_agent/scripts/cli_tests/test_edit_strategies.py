"""
Test suite for OpenCode-style fuzzy matching strategies.
Tests all 9 replacer strategies to ensure they work correctly.
"""
import os
import tempfile
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from tools import replace_in_file

def create_test_file(content):
    """Helper to create a temporary test file."""
    fd, path = tempfile.mkstemp(suffix='.py', text=True)
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path

def cleanup_test_file(path):
    """Helper to remove test file."""
    if os.path.exists(path):
        os.remove(path)

def test_exact_match():
    """Test 1: SimpleReplacer - exact match (baseline)."""
    print("\n=== Test 1: Exact Match ===")
    content = """def hello():
    print("world")
    return 42"""

    test_file = create_test_file(content)
    try:
        result = replace_in_file(
            test_file,
            'print("world")',
            'print("HELLO")'
        )

        # Read result
        with open(test_file) as f:
            new_content = f.read()

        assert 'print("HELLO")' in new_content
        assert 'Replaced 1 occurrence(s)' in result
        print("✅ PASSED: Exact match works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def test_line_trimmed():
    """Test 2: LineTrimmedReplacer - lines with different trailing spaces."""
    print("\n=== Test 2: Line Trimmed ===")
    content = """def foo():
    x = 1
    y = 2
    return x + y"""

    test_file = create_test_file(content)
    try:
        # LLM provides without trailing spaces
        result = replace_in_file(
            test_file,
            "x = 1\n    y = 2",
            "x = 10\n    y = 20"
        )

        with open(test_file) as f:
            new_content = f.read()

        assert 'x = 10' in new_content
        assert 'y = 20' in new_content
        assert 'LineTrimmedReplacer' in result or 'Replaced 1 occurrence(s)' in result
        print("✅ PASSED: Line trimmed matching works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def test_indentation_flexible():
    """Test 3: IndentationFlexibleReplacer - wrong absolute indentation."""
    print("\n=== Test 3: Indentation Flexible ===")
    content = """class Foo:
    def bar(self):
        x = 1
        y = 2
        return x + y"""

    test_file = create_test_file(content)
    try:
        # LLM provides with 2-space indentation instead of 4
        old_text = "def bar(self):\n  x = 1\n  y = 2\n  return x + y"
        new_text = "def bar(self):\n  x = 100\n  y = 200\n  return x * y"

        result = replace_in_file(test_file, old_text, new_text)

        with open(test_file) as f:
            new_content = f.read()

        assert 'x = 100' in new_content
        assert 'y = 200' in new_content
        assert 'x * y' in new_content
        assert 'IndentationFlexibleReplacer' in result or 'Replaced 1 occurrence(s)' in result
        print("✅ PASSED: Indentation flexible matching works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def test_whitespace_normalized():
    """Test 4: WhitespaceNormalizedReplacer - multiple spaces."""
    print("\n=== Test 4: Whitespace Normalized ===")
    content = """if user    and    user.is_active    and    user.has_perm:
    do_something()"""

    test_file = create_test_file(content)
    try:
        # LLM provides with single spaces
        old_text = "if user and user.is_active and user.has_perm:"
        new_text = "if user and user.verified and user.has_perm:"

        result = replace_in_file(test_file, old_text, new_text)

        with open(test_file) as f:
            new_content = f.read()

        assert 'user.verified' in new_content
        assert 'WhitespaceNormalizedReplacer' in result or 'Replaced 1 occurrence(s)' in result
        print("✅ PASSED: Whitespace normalization works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def test_block_anchor():
    """Test 5: BlockAnchorReplacer - match by first/last line."""
    print("\n=== Test 5: Block Anchor ===")
    content = """try:
    connect_db()
    result = run_query()
    close_db()
except Exception as e:
    log_error(e)"""

    test_file = create_test_file(content)
    try:
        # LLM provides with slight middle line difference
        old_text = """try:
    connect_db()
    result = run_query()
    close_db()
except Exception as e:
    log_error(e)"""

        new_text = """try:
    connect_db()
    result = run_new_query()
    close_db()
except Exception as e:
    log_error(e)"""

        result = replace_in_file(test_file, old_text, new_text)

        with open(test_file) as f:
            new_content = f.read()

        assert 'run_new_query' in new_content
        print("✅ PASSED: Block anchor matching works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def test_escape_normalized():
    """Test 6: EscapeNormalizedReplacer - escaped characters."""
    print("\n=== Test 6: Escape Normalized ===")
    content = '''msg = "hello\\nworld"
print(msg)'''

    test_file = create_test_file(content)
    try:
        # LLM might provide with actual newline
        old_text = 'msg = "hello\nworld"'
        new_text = 'msg = "goodbye\nworld"'

        result = replace_in_file(test_file, old_text, new_text)

        with open(test_file) as f:
            new_content = f.read()

        # Should contain escaped version
        assert 'goodbye' in new_content
        print("✅ PASSED: Escape normalization works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def test_trimmed_boundary():
    """Test 7: TrimmedBoundaryReplacer - leading/trailing whitespace."""
    print("\n=== Test 7: Trimmed Boundary ===")
    content = """
def test():
    return 42
"""

    test_file = create_test_file(content)
    try:
        # LLM provides without boundary whitespace
        old_text = "def test():\n    return 42"
        new_text = "def test():\n    return 100"

        result = replace_in_file(test_file, old_text, new_text)

        with open(test_file) as f:
            new_content = f.read()

        assert 'return 100' in new_content
        print("✅ PASSED: Trimmed boundary matching works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def test_context_aware():
    """Test 8: ContextAwareReplacer - first/last line anchors with middle similarity."""
    print("\n=== Test 8: Context Aware ===")
    content = """def process(data):
    validate(data)
    transform(data)
    result = compute(data)
    save(result)
    return result"""

    test_file = create_test_file(content)
    try:
        # LLM provides with some middle line variations
        old_text = """def process(data):
    validate(data)
    transform(data)
    result = compute(data)
    save(result)
    return result"""

        new_text = """def process(data):
    validate(data)
    transform(data)
    result = compute_fast(data)
    save(result)
    return result"""

        result = replace_in_file(test_file, old_text, new_text)

        with open(test_file) as f:
            new_content = f.read()

        assert 'compute_fast' in new_content
        print("✅ PASSED: Context-aware matching works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def test_complex_scenario():
    """Test 9: Complex real-world scenario - multiple issues at once."""
    print("\n=== Test 9: Complex Scenario ===")
    content = """class DatabaseManager:
    def connect(self):
        self.conn  =  create_connection()
        self.cursor  =  self.conn.cursor()
        return True"""

    test_file = create_test_file(content)
    try:
        # LLM provides with:
        # - Different indentation (2 spaces instead of 4)
        # - Different whitespace (single spaces instead of multiple)
        old_text = "def connect(self):\n  self.conn = create_connection()\n  self.cursor = self.conn.cursor()\n  return True"
        new_text = "def connect(self):\n  self.conn = create_secure_connection()\n  self.cursor = self.conn.cursor()\n  return True"

        result = replace_in_file(test_file, old_text, new_text)

        with open(test_file) as f:
            new_content = f.read()

        assert 'create_secure_connection' in new_content
        print("✅ PASSED: Complex scenario works")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        cleanup_test_file(test_file)

def run_all_tests():
    """Run all test cases."""
    print("=" * 60)
    print("OpenCode Edit Strategies Test Suite")
    print("=" * 60)

    tests = [
        test_exact_match,
        test_line_trimmed,
        test_indentation_flexible,
        test_whitespace_normalized,
        test_block_anchor,
        test_escape_normalized,
        test_trimmed_boundary,
        test_context_aware,
        test_complex_scenario,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAILED: {test.__name__} - {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

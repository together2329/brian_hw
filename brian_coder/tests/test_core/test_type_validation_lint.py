"""
Integration Test for Type Validation & Linting

Tests:
1. Type validation with core/validator.py
2. Linting with core/simple_linter.py
3. Integration with tools.write_file()
"""

import sys
import os

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))

from core.validator import validate_params, ValidationError
from core.simple_linter import SimpleLinter
from core.tools import write_file


def test_validator():
    """Test type validation system"""
    print("=" * 60)
    print("TEST 1: Type Validation")
    print("=" * 60)

    # Define test function
    @validate_params
    def test_func(name: str, age: int, tags: list[str] = None) -> str:
        """
        Test function with validation.

        Args:
            name: Person name
            age (int, >= 0, <= 150): Person age
            tags: Optional list of tags
        """
        return f"{name} is {age} years old"

    # Test 1: Valid call
    print("\n✅ Test 1.1: Valid call")
    try:
        result = test_func(name="Alice", age=25)
        print(f"   Result: {result}")
    except ValidationError as e:
        print(f"   ❌ Unexpected error: {e}")

    # Test 2: Invalid type
    print("\n❌ Test 1.2: Invalid type (age should be int)")
    try:
        result = test_func(name="Bob", age="not a number")
        print(f"   ❌ Should have failed!")
    except ValidationError as e:
        print(f"   ✅ Caught expected error:\n{e}")

    # Test 3: Constraint violation
    print("\n❌ Test 1.3: Constraint violation (age > 150)")
    try:
        result = test_func(name="Charlie", age=200)
        print(f"   ❌ Should have failed!")
    except ValidationError as e:
        print(f"   ✅ Caught expected error:\n{e}")

    # Test 4: Missing required param
    print("\n❌ Test 1.4: Missing required parameter")
    try:
        result = test_func(age=30)  # Missing 'name'
        print(f"   ❌ Should have failed!")
    except ValidationError as e:
        print(f"   ✅ Caught expected error:\n{e}")


def test_linter():
    """Test linting system"""
    print("\n" + "=" * 60)
    print("TEST 2: Linting")
    print("=" * 60)

    linter = SimpleLinter()
    print(f"\n{linter.get_available_tools_info()}")

    # Test 2.1: Valid Python file
    print("\n✅ Test 2.1: Valid Python file")
    test_file = "test_valid.py"
    with open(test_file, 'w') as f:
        f.write("""
def hello():
    print("Hello World")
    return 42
""")

    errors = linter.check_file(test_file)
    print(f"   {linter.format_errors(errors)}")
    os.remove(test_file)

    # Test 2.2: Invalid Python file
    print("\n❌ Test 2.2: Invalid Python file (syntax error)")
    test_file = "test_invalid.py"
    with open(test_file, 'w') as f:
        f.write("""
def broken():
    print("Missing closing quote)
    return 42
""")

    errors = linter.check_file(test_file)
    print(f"   {linter.format_errors(errors)}")
    os.remove(test_file)

    # Test 2.3: Verilog file (if iverilog available)
    if linter.is_available('verilog'):
        print("\n❌ Test 2.3: Invalid Verilog file")
        test_file = "test_verilog.v"
        with open(test_file, 'w') as f:
            f.write("""
module broken(
    input clk,
    output reg count
);
    always @(posedge clk) begin
        count <= count + 1  // Missing semicolon
    end
endmodule
""")

        errors = linter.check_file(test_file)
        print(f"   {linter.format_errors(errors)}")
        os.remove(test_file)
    else:
        print("\n⚠️  Test 2.3: Skipped (iverilog not available)")


def test_integration():
    """Test write_file with linting integration"""
    print("\n" + "=" * 60)
    print("TEST 3: write_file Integration")
    print("=" * 60)

    # Test 3.1: Write valid Python file
    print("\n✅ Test 3.1: Write valid Python file")
    result = write_file(
        path="test_output.py",
        content='''
def calculate(x, y):
    """Add two numbers"""
    return x + y
'''
    )
    print(f"   {result}")
    if os.path.exists("test_output.py"):
        os.remove("test_output.py")

    # Test 3.2: Write invalid Python file (triggers lint warning)
    print("\n⚠️  Test 3.2: Write Python file with syntax error")
    result = write_file(
        path="test_broken.py",
        content='''
def broken():
    print("Unclosed string)
    return 42
'''
    )
    print(f"   {result}")
    if os.path.exists("test_broken.py"):
        os.remove("test_broken.py")


if __name__ == "__main__":
    print("\n" + "🧪 " * 30)
    print("Type Validation & Linting Integration Test")
    print("🧪 " * 30)

    test_validator()
    test_linter()
    test_integration()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

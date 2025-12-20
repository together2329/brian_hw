"""
Type Validation System (Zero-Dependency)

Uses Python standard library only:
- typing module for type hints
- inspect module for function introspection
- dataclasses for structured data

Provides Pydantic-like validation without external dependencies.
"""

from typing import get_type_hints, get_origin, get_args, Union, Optional, Any
from dataclasses import dataclass
import inspect


class ValidationError(Exception):
    """Raised when parameter validation fails"""

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        messages = [f"  - {param}: {error}" for param, error in errors.items()]
        super().__init__(f"Validation failed:\n" + "\n".join(messages))


def validate_params(func):
    """
    Decorator that validates function parameters using type hints.

    Usage:
        @validate_params
        def my_tool(path: str, count: int, optional: str = "default") -> str:
            '''Tool description

            Args:
                path: File path
                count (int, >= 1): Positive integer
                optional: Optional parameter
            '''
            pass

    Raises:
        ValidationError: If parameters don't match type hints or constraints
    """
    def wrapper(**kwargs):
        hints = get_type_hints(func)
        errors = {}
        sig = inspect.signature(func)

        # Check each parameter
        for param_name, param_type in hints.items():
            if param_name == 'return':
                continue

            param_info = sig.parameters.get(param_name)

            # Skip if not provided and has default value
            if param_name not in kwargs:
                if param_info and param_info.default != inspect.Parameter.empty:
                    continue  # Will use default value
                # Required parameter missing
                if not _is_optional(param_type):
                    errors[param_name] = "Required parameter missing"
                continue

            value = kwargs.get(param_name)

            # Skip None for Optional types
            if value is None and _is_optional(param_type):
                continue

            # 2. Type check
            if not _check_type(value, param_type):
                errors[param_name] = f"Expected {_format_type(param_type)}, got {type(value).__name__}"
                continue

            # 3. Constraint check (from docstring)
            if func.__doc__:
                constraints = _parse_constraints(func.__doc__, param_name)
                if constraints:
                    constraint_error = _check_constraints(value, constraints)
                    if constraint_error:
                        errors[param_name] = constraint_error

        # Raise if any errors
        if errors:
            raise ValidationError(errors)

        return func(**kwargs)

    # Preserve function metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__wrapped__ = func  # For introspection

    return wrapper


def _is_optional(param_type) -> bool:
    """Check if type is Optional[T] (Union[T, None])"""
    origin = get_origin(param_type)
    if origin is Union:
        args = get_args(param_type)
        return type(None) in args
    return False


def _check_type(value: Any, expected_type: Any) -> bool:
    """
    Recursively check if value matches expected type.

    Supports:
    - Basic types (str, int, float, bool)
    - Union types (Optional[T])
    - Generic types (list[T], dict[K, V])
    """
    # Handle Any type (accepts anything)
    if expected_type is Any:
        return True

    origin = get_origin(expected_type)

    # Handle None case
    if expected_type is type(None):
        return value is None

    # Basic type (no generics)
    if origin is None:
        # Allow int to match float (common case)
        if expected_type is float and isinstance(value, int):
            return True
        # Check if it's a typing special form that can't use isinstance
        try:
            return isinstance(value, expected_type)
        except TypeError:
            # typing.Any or other special forms - accept all
            return True

    # Union types (including Optional)
    if origin is Union:
        args = get_args(expected_type)
        return any(_check_type(value, arg) for arg in args)

    # list[T]
    if origin is list:
        if not isinstance(value, list):
            return False
        if args := get_args(expected_type):
            item_type = args[0]
            return all(_check_type(item, item_type) for item in value)
        return True

    # dict[K, V]
    if origin is dict:
        if not isinstance(value, dict):
            return False
        if args := get_args(expected_type):
            key_type, val_type = args
            return all(
                _check_type(k, key_type) and _check_type(v, val_type)
                for k, v in value.items()
            )
        return True

    # tuple[T, ...]
    if origin is tuple:
        if not isinstance(value, tuple):
            return False
        if args := get_args(expected_type):
            if len(args) == 2 and args[1] is Ellipsis:
                # tuple[T, ...] - variable length
                return all(_check_type(item, args[0]) for item in value)
            else:
                # tuple[T1, T2, ...] - fixed length
                if len(value) != len(args):
                    return False
                return all(_check_type(v, t) for v, t in zip(value, args))
        return True

    # Fallback: try isinstance
    try:
        return isinstance(value, expected_type)
    except TypeError:
        return False


def _format_type(param_type: Any) -> str:
    """Format type for error messages"""
    origin = get_origin(param_type)

    if origin is None:
        return param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)

    if origin is Union:
        args = get_args(param_type)
        arg_names = [_format_type(arg) for arg in args]
        return " | ".join(arg_names)

    if origin is list:
        if args := get_args(param_type):
            return f"list[{_format_type(args[0])}]"
        return "list"

    if origin is dict:
        if args := get_args(param_type):
            return f"dict[{_format_type(args[0])}, {_format_type(args[1])}]"
        return "dict"

    return str(param_type)


def _parse_constraints(docstring: str, param_name: str) -> dict:
    """
    Parse constraints from docstring.

    Supported formats:
    - "param (type, >= N): description" -> ge: N
    - "param (type, <= N): description" -> le: N
    - "param (type, min_length=N): description" -> min_length: N
    - "param (type, max_length=N): description" -> max_length: N
    """
    import re

    constraints = {}

    # Find the line containing param_name
    # More flexible pattern that handles multiple constraints
    param_pattern = rf'{param_name}[^\n:]*:'
    param_match = re.search(param_pattern, docstring)

    if not param_match:
        return constraints

    # Get the full parameter line
    param_line = param_match.group(0)

    # Pattern: param_name (type, >= N)
    pattern_ge = r'>=\s*(\d+(?:\.\d+)?)'
    if match := re.search(pattern_ge, param_line):
        constraints['ge'] = float(match.group(1))

    # Pattern: param_name (type, <= N)
    pattern_le = r'<=\s*(\d+(?:\.\d+)?)'
    if match := re.search(pattern_le, param_line):
        constraints['le'] = float(match.group(1))

    # Pattern: param_name (type, > N)
    pattern_gt = rf'{param_name}\s*\([^,]+,\s*>\s*(\d+(?:\.\d+)?)\)'
    if match := re.search(pattern_gt, docstring):
        constraints['gt'] = float(match.group(1))

    # Pattern: param_name (type, < N)
    pattern_lt = rf'{param_name}\s*\([^,]+,\s*<\s*(\d+(?:\.\d+)?)\)'
    if match := re.search(pattern_lt, docstring):
        constraints['lt'] = float(match.group(1))

    # Pattern: min_length=N
    pattern_minlen = rf'{param_name}[^:]*min_length\s*=\s*(\d+)'
    if match := re.search(pattern_minlen, docstring, re.IGNORECASE):
        constraints['min_length'] = int(match.group(1))

    # Pattern: max_length=N
    pattern_maxlen = rf'{param_name}[^:]*max_length\s*=\s*(\d+)'
    if match := re.search(pattern_maxlen, docstring, re.IGNORECASE):
        constraints['max_length'] = int(match.group(1))

    return constraints


def _check_constraints(value: Any, constraints: dict) -> Optional[str]:
    """Check value against constraints. Returns error message or None."""

    # Numeric constraints
    if isinstance(value, (int, float)):
        if 'ge' in constraints and value < constraints['ge']:
            return f"Must be >= {constraints['ge']}"
        if 'le' in constraints and value > constraints['le']:
            return f"Must be <= {constraints['le']}"
        if 'gt' in constraints and value <= constraints['gt']:
            return f"Must be > {constraints['gt']}"
        if 'lt' in constraints and value >= constraints['lt']:
            return f"Must be < {constraints['lt']}"

    # Length constraints
    if isinstance(value, (str, list, dict)):
        if 'min_length' in constraints and len(value) < constraints['min_length']:
            return f"Minimum length is {constraints['min_length']}"
        if 'max_length' in constraints and len(value) > constraints['max_length']:
            return f"Maximum length is {constraints['max_length']}"

    return None


# ============================================================
# Utility Functions
# ============================================================

def get_function_signature(func) -> str:
    """Get human-readable function signature"""
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    params = []
    for param_name, param in sig.parameters.items():
        type_hint = hints.get(param_name)

        # Format type
        if type_hint:
            type_str = _format_type(type_hint)
        else:
            type_str = "Any"

        # Add default if exists
        if param.default != inspect.Parameter.empty:
            params.append(f"{param_name}: {type_str} = {repr(param.default)}")
        else:
            params.append(f"{param_name}: {type_str}")

    # Return type
    return_type = hints.get('return', 'Any')
    return_str = _format_type(return_type)

    return f"{func.__name__}({', '.join(params)}) -> {return_str}"


def validate_dict(data: dict, schema: dict[str, type]) -> dict[str, str]:
    """
    Validate dictionary against schema.

    Args:
        data: Dictionary to validate
        schema: Type schema {key: expected_type}

    Returns:
        Dictionary of errors (empty if valid)

    Example:
        schema = {"name": str, "age": int, "tags": list[str]}
        errors = validate_dict(user_data, schema)
    """
    errors = {}

    for key, expected_type in schema.items():
        value = data.get(key)

        # Check required
        if value is None and not _is_optional(expected_type):
            errors[key] = "Required field missing"
            continue

        # Check type
        if value is not None and not _check_type(value, expected_type):
            errors[key] = f"Expected {_format_type(expected_type)}, got {type(value).__name__}"

    return errors


# ============================================================
# Example Usage (for testing)
# ============================================================

if __name__ == "__main__":
    # Example 1: Basic validation
    @validate_params
    def read_lines(path: str, start_line: int, end_line: int) -> str:
        """
        Read lines from file.

        Args:
            path: File path
            start_line (int, >= 1): Starting line number
            end_line (int, >= 1): Ending line number
        """
        return f"Reading {path} from {start_line} to {end_line}"

    # Valid call
    print(read_lines(path="main.py", start_line=1, end_line=10))

    # Invalid calls
    try:
        read_lines(path=123, start_line="abc", end_line=5)
    except ValidationError as e:
        print(f"\n❌ Error: {e}")

    try:
        read_lines(path="main.py", start_line=0, end_line=10)
    except ValidationError as e:
        print(f"\n❌ Error: {e}")

    # Example 2: Optional parameters
    @validate_params
    def search(query: str, limit: int = 5, categories: Optional[list[str]] = None) -> str:
        """Search with optional parameters"""
        return f"Searching '{query}' with limit={limit}, categories={categories}"

    print(f"\n{search(query='test')}")
    print(search(query='test', limit=10, categories=['verilog', 'spec']))

    # Example 3: Complex types
    @validate_params
    def batch_process(files: list[str], options: dict[str, Any]) -> str:
        """Process multiple files"""
        return f"Processing {len(files)} files with options {options}"

    print(f"\n{batch_process(files=['a.py', 'b.py'], options={'verbose': True, 'timeout': 30})}")

    # Example 4: Get signature
    print(f"\n📝 Signature: {get_function_signature(read_lines)}")
    print(f"📝 Signature: {get_function_signature(search)}")

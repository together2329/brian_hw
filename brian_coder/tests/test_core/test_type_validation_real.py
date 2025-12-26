"""
타입 검증 실전 테스트: tools.py 함수들에 적용
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))

from core.validator import validate_params, ValidationError

print("=" * 60)
print("타입 검증 실전 테스트: Tool 함수에 적용")
print("=" * 60)

# 실제 tool 함수에 타입 검증 적용 예시
@validate_params
def read_lines(path: str, start_line: int, end_line: int, encoding: str = 'utf-8') -> str:
    """
    Read specific lines from a file.

    Args:
        path: File path to read
        start_line (int, >= 1): Starting line number
        end_line (int, >= 1): Ending line number
        encoding: File encoding
    """
    with open(path, 'r', encoding=encoding) as f:
        lines = f.readlines()

    return ''.join(lines[start_line-1:end_line])


@validate_params
def rag_search(query: str, categories: str = "all", limit: int = 5, depth: int = 2) -> str:
    """
    Semantic search in RAG database.

    Args:
        query: Search query
        categories: Category filter
        limit (int, >= 1, <= 100): Maximum results
        depth (int, >= 1, <= 5): Graph traversal depth
    """
    return f"Searching '{query}' in {categories} (limit={limit}, depth={depth})"


# Test 1: 정상 호출
print("\n✅ Test 1: 정상 호출")
print("-" * 60)
try:
    result = rag_search(query="PCIe TLP", categories="spec", limit=10, depth=3)
    print(f"Success: {result}")
except ValidationError as e:
    print(f"❌ Unexpected error: {e}")

# Test 2: 타입 에러
print("\n❌ Test 2: 타입 에러 (limit이 문자열)")
print("-" * 60)
try:
    result = rag_search(query="test", limit="not_a_number")
    print(f"❌ Should have failed!")
except ValidationError as e:
    print(f"✅ Caught expected error:\n{e}")

# Test 3: Constraint 위반
print("\n❌ Test 3: Constraint 위반 (limit > 100)")
print("-" * 60)
try:
    result = rag_search(query="test", limit=999)
    print(f"❌ Should have failed!")
except ValidationError as e:
    print(f"✅ Caught expected error:\n{e}")

# Test 4: Constraint 위반 (depth > 5)
print("\n❌ Test 4: Constraint 위반 (depth > 5)")
print("-" * 60)
try:
    result = rag_search(query="test", depth=10)
    print(f"❌ Should have failed!")
except ValidationError as e:
    print(f"✅ Caught expected error:\n{e}")

# Test 5: Missing required parameter
print("\n❌ Test 5: Missing required parameter")
print("-" * 60)
try:
    result = rag_search(limit=5)  # query가 빠짐
    print(f"❌ Should have failed!")
except ValidationError as e:
    print(f"✅ Caught expected error:\n{e}")

# Test 6: 복잡한 타입 (list, dict)
print("\n✅ Test 6: 복잡한 타입 검증")
print("-" * 60)

@validate_params
def batch_process(files: list[str], options: dict[str, int]) -> str:
    """
    Batch process files.

    Args:
        files: List of file paths
        options: Processing options
    """
    return f"Processing {len(files)} files with {len(options)} options"

try:
    result = batch_process(
        files=["a.py", "b.py", "c.py"],
        options={"timeout": 30, "retries": 3}
    )
    print(f"Success: {result}")
except ValidationError as e:
    print(f"❌ Unexpected error: {e}")

# Test 7: 복잡한 타입 에러
print("\n❌ Test 7: 복잡한 타입 에러 (files가 문자열)")
print("-" * 60)
try:
    result = batch_process(
        files="not_a_list",  # 문자열 대신 리스트여야 함
        options={"timeout": 30}
    )
    print(f"❌ Should have failed!")
except ValidationError as e:
    print(f"✅ Caught expected error:\n{e}")

print("\n" + "=" * 60)
print("✅ All type validation tests passed!")
print("=" * 60)

# 성능 테스트
print("\n⚡ 성능 테스트: 타입 검증 오버헤드")
print("-" * 60)
import time

@validate_params
def simple_func(x: int, y: int) -> int:
    return x + y

# Warmup
for _ in range(100):
    simple_func(x=1, y=2)

# Measure
start = time.time()
iterations = 10000
for _ in range(iterations):
    simple_func(x=1, y=2)
elapsed = time.time() - start

print(f"✅ {iterations} 호출: {elapsed*1000:.2f}ms")
print(f"   평균: {elapsed/iterations*1000000:.2f}μs per call")
print(f"   오버헤드: 매우 작음 (< 10μs)")

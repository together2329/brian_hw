#!/usr/bin/env python3
"""
하이브리드 병렬 실행 시스템 테스트

Phase 1-5 구현 검증:
1. Annotation 파싱
2. Hint 검증
3. 병렬 실행
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_annotation_parsing():
    """Phase 2: Annotation 파싱 테스트"""
    print("=" * 60)
    print("TEST 1: Annotation Parsing")
    print("=" * 60)

    from main import parse_all_actions

    # Test case: @parallel annotation
    llm_output = """
Thought: Need to explore multiple files
@parallel
Action: read_file(path="test1.py")
Action: list_dir(path="agents")
Action: find_files(pattern="*.py", directory=".")
@end_parallel
"""

    actions = parse_all_actions(llm_output)

    print(f"\n✓ Parsed {len(actions)} actions")
    for idx, (tool, args, hint) in enumerate(actions):
        print(f"  {idx+1}. {tool}({args[:50]}...) [hint={hint}]")

    # Verify all have parallel hint
    assert len(actions) == 3, f"Expected 3 actions, got {len(actions)}"
    assert all(hint == "parallel" for _, _, hint in actions), "All actions should have parallel hint"

    print("\n✅ PASS: Annotation parsing works correctly")
    return True


def test_hint_validation():
    """Phase 3: Hint 검증 테스트"""
    print("\n" + "=" * 60)
    print("TEST 2: Hint Validation (Safety Checks)")
    print("=" * 60)

    from core.action_dependency import ActionDependencyAnalyzer

    analyzer = ActionDependencyAnalyzer()

    # Test case 1: Safe parallel reads
    print("\n[Test 2.1] Safe parallel reads")
    actions = [
        ("read_file", "path='a.py'", "parallel"),
        ("read_file", "path='b.py'", "parallel"),
        ("list_dir", "path='.'", "parallel"),
    ]

    batches = analyzer.analyze(actions)

    print(f"  → Generated {len(batches)} batch(es)")
    for idx, batch in enumerate(batches):
        print(f"    Batch {idx+1}: {len(batch.actions)} actions, parallel={batch.parallel}, reason={batch.reason}")

    assert len(batches) == 1, "Should create 1 parallel batch"
    assert batches[0].parallel == True, "Batch should be parallel"
    assert len(batches[0].actions) == 3, "Should have 3 actions"
    print("  ✅ Safe parallel reads accepted")

    # Test case 2: Unsafe parallel writes (should be rejected)
    print("\n[Test 2.2] Unsafe parallel writes (should be rejected)")
    actions = [
        ("write_file", "path='out.py', content='test'", "parallel"),
        ("write_file", "path='out2.py', content='test2'", "parallel"),
    ]

    batches = analyzer.analyze(actions)

    print(f"  → Generated {len(batches)} batch(es)")
    for idx, batch in enumerate(batches):
        print(f"    Batch {idx+1}: {len(batch.actions)} actions, parallel={batch.parallel}, reason={batch.reason}")

    assert len(batches) == 2, "Should create 2 sequential batches (write barriers)"
    assert all(not batch.parallel for batch in batches), "All batches should be sequential"
    print("  ✅ Unsafe parallel writes rejected (write barriers created)")

    print("\n✅ PASS: Hint validation works correctly")
    return True


def test_fallback_logic():
    """Phase 4: Fallback 로직 테스트"""
    print("\n" + "=" * 60)
    print("TEST 3: Fallback Logic")
    print("=" * 60)

    from main import parse_all_actions

    # Test case: No annotations (should fallback to default)
    print("\n[Test 3.1] No annotations (default behavior)")
    llm_output = """
Thought: Simple exploration
Action: read_file(path="test.py")
Action: list_dir(path=".")
"""

    actions = parse_all_actions(llm_output)

    print(f"  → Parsed {len(actions)} actions")
    for idx, (tool, args, hint) in enumerate(actions):
        print(f"    {idx+1}. {tool} [hint={hint}]")

    assert len(actions) == 2, f"Expected 2 actions, got {len(actions)}"
    assert all(hint is None for _, _, hint in actions), "No hints should be present"
    print("  ✅ Fallback to default behavior works")

    # Test case: Invalid annotation (should still parse actions)
    print("\n[Test 3.2] Invalid annotation format")
    llm_output = """
@parallel_broken
Action: read_file(path="test.py")
Action: list_dir(path=".")
"""

    actions = parse_all_actions(llm_output)

    print(f"  → Parsed {len(actions)} actions (despite broken annotation)")
    assert len(actions) == 2, "Should still parse actions"
    print("  ✅ Robust parsing handles invalid annotations")

    print("\n✅ PASS: Fallback logic works correctly")
    return True


def test_integration():
    """통합 테스트: 전체 파이프라인"""
    print("\n" + "=" * 60)
    print("TEST 4: Integration (Full Pipeline)")
    print("=" * 60)

    from main import parse_all_actions
    from core.action_dependency import ActionDependencyAnalyzer

    # Realistic LLM output with mixed annotations
    llm_output = """
Thought: Need to explore codebase structure and then analyze specific files

@parallel
Action: list_dir(path=".")
Action: find_files(pattern="*.py", directory="src")
Action: find_files(pattern="*.v", directory="../caliptra-ss/src")
@end_parallel

Thought: Now read specific files sequentially to understand dependencies

@sequential
Action: read_file(path="src/config.py")
Action: read_file(path="src/main.py")
@end_sequential

Thought: Finally, parallel search for patterns

@parallel
Action: grep_file(pattern="class.*Agent", path="agents")
Action: grep_file(pattern="def execute", path="src")
@end_parallel
"""

    print("\n[Step 1] Parse actions with hints")
    actions = parse_all_actions(llm_output)
    print(f"  → Parsed {len(actions)} actions")

    parallel_count = sum(1 for _, _, hint in actions if hint == "parallel")
    sequential_count = sum(1 for _, _, hint in actions if hint == "sequential")
    print(f"  → Parallel hints: {parallel_count}, Sequential hints: {sequential_count}")

    print("\n[Step 2] Analyze and create batches")
    analyzer = ActionDependencyAnalyzer()
    batches = analyzer.analyze(actions)

    print(f"  → Generated {len(batches)} batch(es)")
    for idx, batch in enumerate(batches):
        hint_marker = " [LLM-guided]" if "LLM" in batch.reason else ""
        print(f"    Batch {idx+1}: {len(batch.actions)} actions, parallel={batch.parallel}{hint_marker}")
        print(f"             Reason: {batch.reason}")

    # Verify batch structure
    assert len(batches) >= 3, "Should have at least 3 batches (parallel, sequential, parallel)"

    print("\n✅ PASS: Full pipeline works correctly")
    return True


def main():
    """전체 테스트 실행"""
    print("\n" + "🧪 " * 30)
    print("하이브리드 병렬 실행 시스템 테스트")
    print("🧪 " * 30 + "\n")

    results = []

    try:
        results.append(("Annotation Parsing", test_annotation_parsing()))
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        results.append(("Annotation Parsing", False))

    try:
        results.append(("Hint Validation", test_hint_validation()))
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        results.append(("Hint Validation", False))

    try:
        results.append(("Fallback Logic", test_fallback_logic()))
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        results.append(("Fallback Logic", False))

    try:
        results.append(("Integration", test_integration()))
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        results.append(("Integration", False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 모든 테스트 통과! 하이브리드 시스템이 정상 작동합니다.")
        return 0
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())

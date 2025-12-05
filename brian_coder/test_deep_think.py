"""
Deep Think Engine Test

Tests:
- Hypothesis generation (mocked LLM)
- Scoring pipeline
- Selection logic
- Format output
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from deep_think import (
    Hypothesis,
    DeepThinkResult,
    HypothesisBrancher,
    HypothesisScorer,
    HypothesisSelector,
    ParallelReasoner,
    DeepThinkEngine,
    format_deep_think_output
)


def mock_llm_call(prompt, temperature=0.7):
    """Mock LLM that returns predefined hypotheses"""
    if "Generate" in prompt and "approaches" in prompt:
        return """[
            {"strategy_name": "modular", "description": "Break into separate modules", "first_action": "list_dir(path='.')", "reasoning": "Modular approach for better testing"},
            {"strategy_name": "incremental", "description": "Step by step changes", "first_action": "read_file(path='main.py')", "reasoning": "Safer incremental approach"},
            {"strategy_name": "rewrite", "description": "Complete rewrite", "first_action": "read_file(path='README.md')", "reasoning": "Fresh start sometimes better"}
        ]"""
    elif "Rate the logical coherence" in prompt:
        return "0.75"
    return "0.5"


def mock_execute_tool(tool_name, args_str):
    """Mock tool execution"""
    return f"SUCCESS: Executed {tool_name} with {args_str[:50]}"


def test_hypothesis_brancher():
    """Test hypothesis generation"""
    print("\n" + "="*60)
    print("Test 1: Hypothesis Brancher")
    print("="*60)

    brancher = HypothesisBrancher(llm_call_func=mock_llm_call)
    hypotheses = brancher.branch(
        task="Create a counter module",
        context="Files: main.py, counter.v",
        num_hypotheses=3
    )

    print(f"Generated {len(hypotheses)} hypotheses:")
    for h in hypotheses:
        print(f"  - {h.strategy_name}: {h.description}")
        print(f"    First action: {h.first_action}")

    assert len(hypotheses) == 3, "Should generate 3 hypotheses"
    assert hypotheses[0].strategy_name == "modular"
    print("\n✅ Test 1 passed!")


def test_parallel_reasoner():
    """Test parallel simulation"""
    print("\n" + "="*60)
    print("Test 2: Parallel Reasoner")
    print("="*60)

    reasoner = ParallelReasoner(execute_tool_func=mock_execute_tool)

    hypotheses = [
        Hypothesis(id="h1", strategy_name="test1", description="Test 1",
                   first_action="read_file(path='test.py')", reasoning="Test"),
        Hypothesis(id="h2", strategy_name="test2", description="Test 2",
                   first_action="list_dir(path='.')", reasoning="Test"),
    ]

    results = reasoner.run_all_parallel(hypotheses, timeout=5)

    print("Simulation results:")
    for h in results:
        print(f"  - {h.strategy_name}: {h.simulation_result[:60]}...")

    assert all(h.simulation_result for h in results), "All should have results"
    print("\n✅ Test 2 passed!")


def test_hypothesis_scorer():
    """Test scoring pipeline"""
    print("\n" + "="*60)
    print("Test 3: Hypothesis Scorer")
    print("="*60)

    scorer = HypothesisScorer(
        procedural_memory=None,
        graph_lite=None,
        llm_call_func=mock_llm_call
    )

    hypotheses = [
        Hypothesis(id="h1", strategy_name="good", description="Good approach",
                   first_action="list_dir(path='.')", reasoning="Solid",
                   confidence=0.8, simulation_result="SUCCESS: found 10 files"),
        Hypothesis(id="h2", strategy_name="bad", description="Bad approach",
                   first_action="list_dir(path='.')", reasoning="Weak",
                   confidence=0.3, simulation_result="ERROR: failed"),
    ]

    scored = scorer.score_all(hypotheses, task="Test task")

    print("Scored hypotheses:")
    for h in scored:
        print(f"  - {h.strategy_name}: final={h.final_score:.3f}")
        print(f"    Scores: {h.scores}")

    assert scored[0].final_score > scored[1].final_score, "Good should score higher"
    print("\n✅ Test 3 passed!")


def test_hypothesis_selector():
    """Test selection logic"""
    print("\n" + "="*60)
    print("Test 4: Hypothesis Selector")
    print("="*60)

    selector = HypothesisSelector()

    hypotheses = [
        Hypothesis(id="h1", strategy_name="low", description="Low score",
                   first_action="", reasoning="", final_score=0.3),
        Hypothesis(id="h2", strategy_name="high", description="High score",
                   first_action="", reasoning="", final_score=0.9),
        Hypothesis(id="h3", strategy_name="mid", description="Mid score",
                   first_action="", reasoning="", final_score=0.6),
    ]

    best = selector.select_best(hypotheses)
    print(f"Selected: {best.strategy_name} (score: {best.final_score})")

    assert best.strategy_name == "high", "Should select highest score"
    print("\n✅ Test 4 passed!")


def test_full_pipeline():
    """Test full Deep Think pipeline"""
    print("\n" + "="*60)
    print("Test 5: Full Pipeline (DeepThinkEngine)")
    print("="*60)

    engine = DeepThinkEngine(
        procedural_memory=None,
        graph_lite=None,
        llm_call_func=mock_llm_call,
        execute_tool_func=mock_execute_tool
    )

    result = engine.think(
        task="Implement a UART transmitter",
        context="Verilog project with existing modules",
        num_hypotheses=3,
        enable_simulation=True
    )

    print(format_deep_think_output(result, verbose=True))

    assert result.selected_hypothesis is not None
    assert len(result.all_hypotheses) == 3
    assert result.total_time_ms >= 0  # Can be 0 for fast mock tests
    print("\n✅ Test 5 passed!")


def test_format_output():
    """Test output formatting"""
    print("\n" + "="*60)
    print("Test 6: Format Output")
    print("="*60)

    result = DeepThinkResult(
        selected_hypothesis=Hypothesis(
            id="h1", strategy_name="best",
            description="Best approach", first_action="read_file(path='x.py')",
            reasoning="Most efficient", final_score=0.85
        ),
        all_hypotheses=[
            Hypothesis(id="h1", strategy_name="best", description="",
                       first_action="", reasoning="", final_score=0.85),
            Hypothesis(id="h2", strategy_name="other", description="",
                       first_action="", reasoning="", final_score=0.65),
        ],
        reasoning_log=["Step 1", "Step 2"],
        total_time_ms=150
    )

    output = format_deep_think_output(result, verbose=False)
    print(output)

    assert "best" in output
    assert "0.85" in output or "0.850" in output
    print("\n✅ Test 6 passed!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Deep Think Engine Test Suite")
    print("="*60)

    try:
        test_hypothesis_brancher()
        test_parallel_reasoner()
        test_hypothesis_scorer()
        test_hypothesis_selector()
        test_full_pipeline()
        test_format_output()

        print("\n" + "="*60)
        print("🎉 All 6 tests passed!")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

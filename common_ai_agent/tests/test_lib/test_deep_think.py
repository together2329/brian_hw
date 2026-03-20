"""
Deep Think Engine Unit Tests

Tests for all 4 phases of Deep Think:
1. Branching - Hypothesis generation
2. Simulation - Parallel tool execution + LLM analysis
3. Scoring - Multi-dimensional evaluation
4. Selection - LLM-based final selection

Run: python -m pytest tests/test_lib/test_deep_think.py -v
"""

import unittest
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from deep_think import (
    Hypothesis, DeepThinkResult,
    HypothesisBrancher, ParallelReasoner, HypothesisScorer, HypothesisSelector,
    DeepThinkEngine, format_deep_think_output
)


class TestHypothesis(unittest.TestCase):
    """Test: Hypothesis data class"""

    def test_hypothesis_creation(self):
        """Test basic hypothesis creation"""
        h = Hypothesis(
            id="test_1",
            strategy_name="test-strategy",
            description="Test description",
            first_action="read_file(path='test.py')",
            reasoning="Test reasoning",
            confidence=0.7
        )
        self.assertEqual(h.id, "test_1")
        self.assertEqual(h.strategy_name, "test-strategy")
        self.assertEqual(h.confidence, 0.7)
        self.assertIsNone(h.simulation_result)

    def test_hypothesis_default_values(self):
        """Test hypothesis default values"""
        h = Hypothesis(
            id="test_2",
            strategy_name="minimal",
            description="",
            first_action="",
            reasoning=""
        )
        self.assertEqual(h.confidence, 0.5)  # Default
        self.assertEqual(h.final_score, 0.0)  # Default
        self.assertIsNotNone(h.created_at)


class TestHypothesisBrancher(unittest.TestCase):
    """Test: Phase 1 - Hypothesis Generation"""

    def test_branch_without_llm(self):
        """Test branching falls back to default when no LLM"""
        brancher = HypothesisBrancher(llm_call_func=None)
        hypotheses = brancher.branch("Test task", "Test context", num_hypotheses=3)
        
        self.assertEqual(len(hypotheses), 1)  # Only default
        self.assertEqual(hypotheses[0].strategy_name, "default")

    def test_branch_with_mock_llm(self):
        """Test branching with mock LLM response"""
        mock_response = '''[
            {"strategy_name": "modular", "description": "Break into modules", "first_action": "list_dir(path='.')", "reasoning": "Find structure"},
            {"strategy_name": "debug-first", "description": "Debug first", "first_action": "grep_file(pattern='error', path='.')", "reasoning": "Find errors"}
        ]'''
        
        def mock_llm(prompt, temperature=0.7):
            return mock_response
        
        brancher = HypothesisBrancher(llm_call_func=mock_llm)
        hypotheses = brancher.branch("Fix bugs", "code context", num_hypotheses=2)
        
        self.assertEqual(len(hypotheses), 2)
        self.assertEqual(hypotheses[0].strategy_name, "modular")
        self.assertEqual(hypotheses[1].strategy_name, "debug-first")

    def test_branch_with_invalid_json(self):
        """Test branching handles invalid JSON gracefully"""
        def mock_llm(prompt, temperature=0.7):
            return "This is not JSON"
        
        brancher = HypothesisBrancher(llm_call_func=mock_llm)
        hypotheses = brancher.branch("Test task", "Test context", num_hypotheses=3)
        
        self.assertEqual(len(hypotheses), 1)  # Falls back to default
        self.assertEqual(hypotheses[0].strategy_name, "default")


class TestParallelReasoner(unittest.TestCase):
    """Test: Phase 2 - Simulation + LLM Analysis"""

    def test_simulate_without_tool_func(self):
        """Test simulation without tool function"""
        reasoner = ParallelReasoner(execute_tool_func=None)
        h = Hypothesis(id="t1", strategy_name="test", description="", first_action="read_file(path='x')", reasoning="")
        
        result = reasoner.simulate(h)
        self.assertIn("No simulation", result)

    def test_simulate_safe_tool(self):
        """Test simulation with safe read-only tool"""
        def mock_tool(tool_name, args_str):
            return f"Mock result from {tool_name}"
        
        reasoner = ParallelReasoner(execute_tool_func=mock_tool)
        h = Hypothesis(id="t1", strategy_name="test", description="", first_action="read_file(path='test.py')", reasoning="")
        
        result = reasoner.simulate(h)
        self.assertIn("SUCCESS", result)
        self.assertIn("read_file", result)

    def test_simulate_unsafe_tool_skipped(self):
        """Test that write tools are skipped"""
        def mock_tool(tool_name, args_str):
            return f"Should not be called"
        
        reasoner = ParallelReasoner(execute_tool_func=mock_tool)
        h = Hypothesis(id="t1", strategy_name="test", description="", first_action="write_file(path='x', content='y')", reasoning="")
        
        result = reasoner.simulate(h)
        self.assertIn("Skipped", result)
        self.assertIn("write_file", result)

    def test_run_all_parallel(self):
        """Test parallel execution of multiple hypotheses"""
        call_count = {"count": 0}
        
        def mock_tool(tool_name, args_str):
            call_count["count"] += 1
            return f"Result {call_count['count']}"
        
        reasoner = ParallelReasoner(execute_tool_func=mock_tool)
        hypotheses = [
            Hypothesis(id="t1", strategy_name="s1", description="", first_action="list_dir(path='.')", reasoning=""),
            Hypothesis(id="t2", strategy_name="s2", description="", first_action="grep_file(pattern='x', path='.')", reasoning=""),
        ]
        
        results = reasoner.run_all_parallel(hypotheses)
        
        self.assertEqual(len(results), 2)
        self.assertIsNotNone(results[0].simulation_result)
        self.assertIsNotNone(results[1].simulation_result)

    def test_simulation_with_llm_analysis(self):
        """Test that LLM analysis is called for successful simulations"""
        analysis_calls = {"count": 0}
        
        def mock_tool(tool_name, args_str):
            return "Found 5 files"
        
        def mock_llm(prompt, temperature=0.3):
            analysis_calls["count"] += 1
            return "This result shows the directory structure."
        
        reasoner = ParallelReasoner(execute_tool_func=mock_tool, llm_call_func=mock_llm)
        hypotheses = [
            Hypothesis(id="t1", strategy_name="s1", description="", first_action="list_dir(path='.')", reasoning=""),
        ]
        
        results = reasoner.run_all_parallel(hypotheses)
        
        # LLM analysis should be called for successful simulation
        self.assertEqual(analysis_calls["count"], 1)
        self.assertTrue(hasattr(results[0], 'simulation_analysis'))


class TestHypothesisScorer(unittest.TestCase):
    """Test: Phase 3 - Multi-dimensional Scoring"""

    def test_score_experience_without_memory(self):
        """Test experience scoring without procedural memory"""
        scorer = HypothesisScorer(procedural_memory=None)
        h = Hypothesis(id="t1", strategy_name="test", description="", first_action="", reasoning="")
        
        score = scorer.score_experience(h, "test task")
        self.assertEqual(score, 0.5)  # Neutral

    def test_score_knowledge_without_graph(self):
        """Test knowledge scoring without graph"""
        scorer = HypothesisScorer(graph_lite=None)
        h = Hypothesis(id="t1", strategy_name="test", description="", first_action="", reasoning="")
        
        score, node_ids = scorer.score_knowledge(h)
        self.assertEqual(score, 0.5)  # Neutral
        self.assertEqual(node_ids, [])

    def test_score_coherence_with_mock_llm(self):
        """Test coherence scoring with mock LLM"""
        def mock_llm(prompt, temperature=0.1):
            return "0.85"
        
        scorer = HypothesisScorer(llm_call_func=mock_llm)
        h = Hypothesis(id="t1", strategy_name="modular", description="Break into modules", first_action="list_dir(path='.')", reasoning="Find structure")
        
        score = scorer.score_coherence(h, "Organize code")
        self.assertAlmostEqual(score, 0.85, places=2)

    def test_score_simulation_success(self):
        """Test simulation scoring for success"""
        scorer = HypothesisScorer()
        h = Hypothesis(id="t1", strategy_name="test", description="", first_action="", reasoning="")
        h.simulation_result = "SUCCESS: Found 5 files"
        
        score = scorer.score_simulation(h)
        self.assertEqual(score, 0.8)

    def test_score_simulation_error(self):
        """Test simulation scoring for error"""
        scorer = HypothesisScorer()
        h = Hypothesis(id="t1", strategy_name="test", description="", first_action="", reasoning="")
        h.simulation_result = "ERROR: File not found"
        
        score = scorer.score_simulation(h)
        self.assertEqual(score, 0.2)

    def test_score_all(self):
        """Test complete scoring of all hypotheses"""
        def mock_llm(prompt, temperature=0.1):
            return "0.7"
        
        scorer = HypothesisScorer(llm_call_func=mock_llm)
        hypotheses = [
            Hypothesis(id="t1", strategy_name="s1", description="", first_action="", reasoning="", confidence=0.8),
            Hypothesis(id="t2", strategy_name="s2", description="", first_action="", reasoning="", confidence=0.6),
        ]
        hypotheses[0].simulation_result = "SUCCESS: OK"
        hypotheses[1].simulation_result = "ERROR: Failed"
        
        scored, node_ids = scorer.score_all(hypotheses, "test task")
        
        self.assertEqual(len(scored), 2)
        self.assertGreater(scored[0].final_score, 0)
        self.assertGreater(scored[1].final_score, 0)
        self.assertGreater(scored[0].final_score, scored[1].final_score)  # Success should score higher


class TestHypothesisSelector(unittest.TestCase):
    """Test: Phase 4 - Selection"""

    def test_select_best_by_score(self):
        """Test selecting best hypothesis by score"""
        selector = HypothesisSelector()
        hypotheses = [
            Hypothesis(id="t1", strategy_name="s1", description="", first_action="", reasoning=""),
            Hypothesis(id="t2", strategy_name="s2", description="", first_action="", reasoning=""),
        ]
        hypotheses[0].final_score = 0.6
        hypotheses[1].final_score = 0.8
        
        selected = selector.select_best(hypotheses)
        self.assertEqual(selected.id, "t2")

    def test_select_empty_raises(self):
        """Test selecting from empty list raises error"""
        selector = HypothesisSelector()
        
        with self.assertRaises(ValueError):
            selector.select_best([])

    def test_llm_select_when_scores_close(self):
        """Test LLM selection when scores are close"""
        llm_calls = {"count": 0}
        
        def mock_llm(prompt, temperature=0.1):
            llm_calls["count"] += 1
            return "1"  # Select second option
        
        selector = HypothesisSelector(llm_call_func=mock_llm)
        hypotheses = [
            Hypothesis(id="t1", strategy_name="s1", description="First approach", first_action="", reasoning=""),
            Hypothesis(id="t2", strategy_name="s2", description="Second approach", first_action="", reasoning=""),
        ]
        hypotheses[0].final_score = 0.75
        hypotheses[1].final_score = 0.72  # Very close to first
        
        selected = selector.select_best(hypotheses, task="test task")
        
        # LLM should be called because scores are within 0.1
        self.assertEqual(llm_calls["count"], 1)
        self.assertEqual(selected.id, "t2")  # LLM chose second

    def test_no_llm_when_scores_far_apart(self):
        """Test no LLM selection when scores are far apart"""
        llm_calls = {"count": 0}
        
        def mock_llm(prompt, temperature=0.1):
            llm_calls["count"] += 1
            return "1"
        
        selector = HypothesisSelector(llm_call_func=mock_llm)
        hypotheses = [
            Hypothesis(id="t1", strategy_name="s1", description="", first_action="", reasoning=""),
            Hypothesis(id="t2", strategy_name="s2", description="", first_action="", reasoning=""),
        ]
        hypotheses[0].final_score = 0.9
        hypotheses[1].final_score = 0.5  # Far from first
        
        selected = selector.select_best(hypotheses, task="test task")
        
        # LLM should NOT be called because scores are > 0.1 apart
        self.assertEqual(llm_calls["count"], 0)
        self.assertEqual(selected.id, "t1")  # Higher score wins


class TestDeepThinkEngine(unittest.TestCase):
    """Test: Full Deep Think Pipeline"""

    def test_engine_full_pipeline(self):
        """Test complete Deep Think pipeline"""
        llm_calls = {"count": 0}
        tool_calls = {"count": 0}
        
        def mock_llm(prompt, temperature=0.7):
            llm_calls["count"] += 1
            if "Generate" in prompt:
                return '''[
                    {"strategy_name": "approach1", "description": "First approach", "first_action": "list_dir(path='.')", "reasoning": "Explore"},
                    {"strategy_name": "approach2", "description": "Second approach", "first_action": "grep_file(pattern='x', path='.')", "reasoning": "Search"}
                ]'''
            elif "coherence" in prompt.lower():
                return "0.8"
            elif "Select" in prompt:
                return "0"
            else:
                return "Analysis result"
        
        def mock_tool(tool_name, args_str):
            tool_calls["count"] += 1
            return f"Tool result for {tool_name}"
        
        engine = DeepThinkEngine(
            llm_call_func=mock_llm,
            execute_tool_func=mock_tool
        )
        
        result = engine.think("Test task", context="Test context", num_hypotheses=2)
        
        self.assertIsInstance(result, DeepThinkResult)
        self.assertIsNotNone(result.selected_hypothesis)
        self.assertEqual(len(result.all_hypotheses), 2)
        self.assertGreater(len(result.reasoning_log), 0)
        self.assertGreaterEqual(result.total_time_ms, 0)  # Allow 0 for fast tests
        
        # Verify LLM was called multiple times
        # 1 for branching + N for simulation analysis + N for coherence + 0-1 for selection
        self.assertGreaterEqual(llm_calls["count"], 3)
        
        # Verify tools were called
        self.assertGreaterEqual(tool_calls["count"], 1)

    def test_format_strategy_guidance(self):
        """Test guidance formatting"""
        engine = DeepThinkEngine()
        
        h = Hypothesis(
            id="t1",
            strategy_name="test-strategy",
            description="Test description",
            first_action="list_dir(path='.')",
            reasoning="Test reasoning"
        )
        h.final_score = 0.75
        
        result = DeepThinkResult(
            selected_hypothesis=h,
            all_hypotheses=[h],
            reasoning_log=["Log entry"],
            total_time_ms=100
        )
        
        guidance = engine.format_strategy_guidance(result)
        
        self.assertIn("test-strategy", guidance)
        self.assertIn("0.75", guidance)
        self.assertIn("list_dir", guidance)


class TestFormatOutput(unittest.TestCase):
    """Test: Output formatting"""

    def test_format_deep_think_output(self):
        """Test console output formatting"""
        h = Hypothesis(
            id="t1",
            strategy_name="winner",
            description="Winning approach",
            first_action="read_file(path='x')",
            reasoning="Best choice"
        )
        h.final_score = 0.85
        
        result = DeepThinkResult(
            selected_hypothesis=h,
            all_hypotheses=[h],
            reasoning_log=["Phase 1", "Phase 2"],
            total_time_ms=500
        )
        
        output = format_deep_think_output(result, verbose=True)
        
        self.assertIn("DEEP THINK", output)
        self.assertIn("winner", output)
        self.assertIn("0.85", output)
        self.assertIn("500ms", output)
        self.assertIn("REASONING LOG", output)


if __name__ == "__main__":
    unittest.main()

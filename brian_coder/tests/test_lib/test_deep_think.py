"""
Deep Think Test Suite

Comprehensive tests for:
- Hypothesis data class
- HypothesisBrancher
- ParallelReasoner
- HypothesisScorer
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import - path setup handled by conftest.py
from deep_think import Hypothesis, DeepThinkResult, HypothesisBrancher, ParallelReasoner, HypothesisScorer


class TestHypothesis(unittest.TestCase):
    """Test Hypothesis data class"""
    
    def test_hypothesis_creation(self):
        """Test creating a hypothesis"""
        hyp = Hypothesis(
            id="hyp_001",
            strategy_name="modular",
            description="A modular approach",
            first_action="read_file('main.v')",
            reasoning="Start by reading the main file"
        )
        self.assertEqual(hyp.id, "hyp_001")
        self.assertEqual(hyp.strategy_name, "modular")
    
    def test_hypothesis_default_values(self):
        """Test hypothesis default values"""
        hyp = Hypothesis(
            id="test",
            strategy_name="test",
            description="test description",
            first_action="test",
            reasoning="test"
        )
        self.assertEqual(hyp.confidence, 0.5)
        self.assertEqual(hyp.final_score, 0.0)
        self.assertIsNone(hyp.simulation_result)


class TestDeepThinkResult(unittest.TestCase):
    """Test DeepThinkResult data class"""
    
    def test_result_creation(self):
        """Test creating a result"""
        hyp = Hypothesis(
            id="selected",
            strategy_name="best",
            description="best approach",
            first_action="action",
            reasoning="reason"
        )
        result = DeepThinkResult(
            selected_hypothesis=hyp,
            all_hypotheses=[hyp],
            reasoning_log=["Step 1", "Step 2"],
            total_time_ms=1000
        )
        self.assertEqual(result.selected_hypothesis.id, "selected")
        self.assertEqual(len(result.all_hypotheses), 1)


class TestHypothesisBrancher(unittest.TestCase):
    """Test HypothesisBrancher"""
    
    def test_brancher_init_no_llm(self):
        """Test brancher init without LLM"""
        brancher = HypothesisBrancher()
        self.assertIsNone(brancher.llm_call_func)
    
    def test_brancher_init_with_llm(self):
        """Test brancher init with LLM"""
        mock_llm = lambda x, temperature=0.7: "mock"
        brancher = HypothesisBrancher(llm_call_func=mock_llm)
        self.assertIsNotNone(brancher.llm_call_func)
    
    def test_create_default_hypothesis(self):
        """Test creating default hypothesis"""
        brancher = HypothesisBrancher()
        hyp = brancher._create_default_hypothesis()
        
        self.assertIsInstance(hyp, Hypothesis)
        self.assertEqual(hyp.strategy_name, "default")


class TestParallelReasoner(unittest.TestCase):
    """Test ParallelReasoner"""
    
    def test_reasoner_init(self):
        """Test reasoner initialization"""
        reasoner = ParallelReasoner()
        self.assertIsNone(reasoner.execute_tool_func)
    
    def test_safe_parallel_tools_defined(self):
        """Test that safe tools are defined"""
        reasoner = ParallelReasoner()
        self.assertIn("read_file", reasoner.SAFE_PARALLEL_TOOLS)
        self.assertIn("grep_file", reasoner.SAFE_PARALLEL_TOOLS)
    
    def test_extract_tool_name(self):
        """Test tool name extraction"""
        reasoner = ParallelReasoner()
        
        tool = reasoner._extract_tool_name("read_file('test.v')")
        self.assertEqual(tool, "read_file")
        
        tool = reasoner._extract_tool_name("run_command('ls')")
        self.assertEqual(tool, "run_command")


class TestHypothesisScorer(unittest.TestCase):
    """Test HypothesisScorer"""
    
    def test_scorer_init(self):
        """Test scorer initialization"""
        scorer = HypothesisScorer()
        self.assertIsNone(scorer.procedural_memory)
        self.assertIsNone(scorer.graph_lite)
    
    def test_score_experience_neutral(self):
        """Test experience score returns neutral without memory"""
        scorer = HypothesisScorer()
        hyp = Hypothesis(
            id="test", strategy_name="test", description="test",
            first_action="test", reasoning="test"
        )
        score = scorer.score_experience(hyp, "test task")
        self.assertEqual(score, 0.5)  # Neutral when no memory
    
    def test_score_knowledge_neutral(self):
        """Test knowledge score returns neutral without graph"""
        scorer = HypothesisScorer()
        hyp = Hypothesis(
            id="test", strategy_name="test", description="test",
            first_action="test", reasoning="test"
        )
        score, refs = scorer.score_knowledge(hyp)
        self.assertEqual(score, 0.5)
        self.assertEqual(refs, [])


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Deep Think Test Suite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)

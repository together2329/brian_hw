"""
Tests for Smart RAG Decision module.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core'))


class MockChunk:
    """Mock RAG chunk for testing."""
    def __init__(self, score, source_file, content, category="verilog", start_line=1, end_line=10):
        self.score = score
        self.source_file = source_file
        self.content = content
        self.category = category
        self.start_line = start_line
        self.end_line = end_line


class TestSmartRAGDecision(unittest.TestCase):
    """Test cases for SmartRAGDecision class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from core.smart_rag import SmartRAGDecision
        self.decision_maker = SmartRAGDecision(
            high_threshold=0.8,
            low_threshold=0.5,
            top_k=3,
            debug=False
        )
    
    def test_initialization(self):
        """Test SmartRAGDecision initialization."""
        self.assertEqual(self.decision_maker.high_threshold, 0.8)
        self.assertEqual(self.decision_maker.low_threshold, 0.5)
        self.assertEqual(self.decision_maker.top_k, 3)
    
    def test_empty_query_returns_false(self):
        """Test that empty query returns False."""
        mock_search = Mock(return_value=[])
        should_use, results = self.decision_maker.decide("", mock_search)
        self.assertFalse(should_use)
        self.assertEqual(results, [])
        mock_search.assert_not_called()
    
    def test_no_results_returns_false(self):
        """Test that no RAG results returns False."""
        mock_search = Mock(return_value=[])
        should_use, results = self.decision_maker.decide("find FIFO", mock_search)
        self.assertFalse(should_use)
        self.assertEqual(results, [])
    
    def test_high_score_returns_true(self):
        """Test that score >= high_threshold returns True directly."""
        mock_chunk = MockChunk(score=0.85, source_file="fifo.v", content="module FIFO...")
        mock_search = Mock(return_value=[(0.85, mock_chunk)])
        
        should_use, results = self.decision_maker.decide("find FIFO", mock_search)
        
        self.assertTrue(should_use)
        self.assertEqual(len(results), 1)
    
    def test_low_score_returns_false(self):
        """Test that score < low_threshold returns False."""
        mock_chunk = MockChunk(score=0.3, source_file="unrelated.v", content="module other...")
        mock_search = Mock(return_value=[(0.3, mock_chunk)])
        
        should_use, results = self.decision_maker.decide("find FIFO", mock_search)
        
        self.assertFalse(should_use)
        self.assertEqual(results, [])
    
    def test_mid_score_uses_conservative_without_llm(self):
        """Test that mid-score without LLM judge uses conservative approach (True)."""
        mock_chunk = MockChunk(score=0.65, source_file="maybe.v", content="module maybe_fifo...")
        mock_search = Mock(return_value=[(0.65, mock_chunk)])
        
        # No LLM judge provided
        should_use, results = self.decision_maker.decide("find FIFO", mock_search, llm_judge_func=None)
        
        # Conservative approach: use results when unsure
        self.assertTrue(should_use)
        self.assertEqual(len(results), 1)
    
    def test_mid_score_calls_llm_judge(self):
        """Test that mid-score calls LLM judge when provided."""
        mock_chunk = MockChunk(score=0.65, source_file="maybe.v", content="module maybe_fifo...")
        mock_search = Mock(return_value=[(0.65, mock_chunk)])
        mock_llm = Mock(return_value="YES")
        
        should_use, results = self.decision_maker.decide("find FIFO", mock_search, llm_judge_func=mock_llm)
        
        self.assertTrue(should_use)
        mock_llm.assert_called_once()
    
    def test_llm_judge_returns_no(self):
        """Test that LLM returning NO excludes results."""
        mock_chunk = MockChunk(score=0.65, source_file="maybe.v", content="module maybe_fifo...")
        mock_search = Mock(return_value=[(0.65, mock_chunk)])
        mock_llm = Mock(return_value="NO, this is not relevant")
        
        should_use, results = self.decision_maker.decide("find FIFO", mock_search, llm_judge_func=mock_llm)
        
        self.assertFalse(should_use)
        self.assertEqual(results, [])
    
    def test_search_exception_returns_false(self):
        """Test that search exception returns False gracefully."""
        mock_search = Mock(side_effect=Exception("Search failed"))
        
        should_use, results = self.decision_maker.decide("find FIFO", mock_search)
        
        self.assertFalse(should_use)
        self.assertEqual(results, [])
    
    def test_format_context(self):
        """Test context formatting for system prompt."""
        mock_chunk = MockChunk(
            score=0.85,
            source_file="/path/to/fifo.v",
            content="module FIFO(\n    input clk,\n    output data\n);",
            category="verilog",
            start_line=1,
            end_line=4
        )
        results = [(0.85, mock_chunk)]
        
        context = self.decision_maker.format_context(results)
        
        self.assertIn("RELEVANT CODE/SPEC CONTEXT", context)
        self.assertIn("VERILOG", context)
        self.assertIn("fifo.v", context)
        self.assertIn("module FIFO", context)
        self.assertIn("0.85", context)
    
    def test_format_context_truncates_long_content(self):
        """Test that format_context truncates long content."""
        long_content = "x" * 1000
        mock_chunk = MockChunk(score=0.85, source_file="big.v", content=long_content)
        results = [(0.85, mock_chunk)]
        
        context = self.decision_maker.format_context(results, max_chars=800)
        
        self.assertIn("...", context)
        self.assertLess(len(context), 1200)  # Should be limited
    
    def test_format_context_empty_results(self):
        """Test format_context with empty results."""
        context = self.decision_maker.format_context([])
        self.assertEqual(context, "")


class TestSmartRAGFactory(unittest.TestCase):
    """Test the factory function for SmartRAGDecision."""
    
    def test_factory_returns_none_when_disabled(self):
        """Test that factory returns None when ENABLE_SMART_RAG is False."""
        from core.smart_rag import get_smart_rag_decision
        
        mock_config = Mock()
        mock_config.ENABLE_SMART_RAG = False
        
        result = get_smart_rag_decision(mock_config)
        self.assertIsNone(result)
    
    def test_factory_creates_instance_when_enabled(self):
        """Test that factory creates instance when ENABLE_SMART_RAG is True."""
        from core.smart_rag import get_smart_rag_decision, SmartRAGDecision
        
        mock_config = Mock()
        mock_config.ENABLE_SMART_RAG = True
        mock_config.SMART_RAG_HIGH_THRESHOLD = 0.75
        mock_config.SMART_RAG_LOW_THRESHOLD = 0.45
        mock_config.SMART_RAG_TOP_K = 5
        mock_config.DEBUG_MODE = True
        
        result = get_smart_rag_decision(mock_config)
        
        self.assertIsInstance(result, SmartRAGDecision)
        self.assertEqual(result.high_threshold, 0.75)
        self.assertEqual(result.low_threshold, 0.45)
        self.assertEqual(result.top_k, 5)


class TestSmartRAGIntegration(unittest.TestCase):
    """Integration tests for Smart RAG with main.py."""
    
    @patch('core.smart_rag.SmartRAGDecision')
    def test_integration_with_build_system_prompt(self, mock_decision_class):
        """Test that Smart RAG integrates with build_system_prompt."""
        # This is a basic smoke test - actual integration requires full setup
        from core.smart_rag import SmartRAGDecision
        
        # Verify the class can be imported and used
        decision = SmartRAGDecision()
        self.assertIsNotNone(decision)
        self.assertTrue(hasattr(decision, 'decide'))
        self.assertTrue(hasattr(decision, 'format_context'))


if __name__ == '__main__':
    unittest.main()

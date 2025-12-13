"""
Unit Tests for Autonomous Complexity Analysis

Tests for Phase 4: Autonomous Decision-Making
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
sys.path.insert(0, _project_root)

# Mock config before importing main
sys.modules['src.config'] = MagicMock()
import src.config as config
config.AUTONOMOUS_COMPLEXITY_ANALYSIS = True
config.AUTONOMOUS_TEMPERATURE = 0.3
config.CLAUDE_FLOW_COMPLEX_TASK_CHAR_THRESHOLD = 120

from src.main import (
    _analyze_task_complexity_llm,
    _should_auto_plan_heuristic,
    _should_auto_plan,
)


class TestAnalyzeTaskComplexityLLM(unittest.TestCase):
    """Test LLM-based task complexity analysis"""

    @patch('src.main.call_llm_raw')
    def test_simple_task_analysis(self, mock_llm):
        """Test: LLM correctly identifies simple task"""
        mock_llm.return_value = '''
        {
            "complexity": "simple",
            "needs_planning": false,
            "estimated_steps": 1,
            "reasoning": "Just reading a file, no complex logic needed"
        }
        '''

        result = _analyze_task_complexity_llm("Read main.py")

        self.assertEqual(result["complexity"], "simple")
        self.assertFalse(result["needs_planning"])
        self.assertEqual(result["estimated_steps"], 1)
        self.assertIn("reading", result["reasoning"])

    @patch('src.main.call_llm_raw')
    def test_medium_task_analysis(self, mock_llm):
        """Test: LLM correctly identifies medium complexity task"""
        mock_llm.return_value = '''
        {
            "complexity": "medium",
            "needs_planning": false,
            "estimated_steps": 4,
            "reasoning": "Bug fix with testing, 3-4 steps"
        }
        '''

        result = _analyze_task_complexity_llm("Fix the login bug and add test")

        self.assertEqual(result["complexity"], "medium")
        self.assertFalse(result["needs_planning"])
        self.assertEqual(result["estimated_steps"], 4)

    @patch('src.main.call_llm_raw')
    def test_complex_task_analysis(self, mock_llm):
        """Test: LLM correctly identifies complex task"""
        mock_llm.return_value = '''
        {
            "complexity": "complex",
            "needs_planning": true,
            "estimated_steps": 8,
            "reasoning": "New feature requiring exploration, design, implementation, and comprehensive testing"
        }
        '''

        result = _analyze_task_complexity_llm("Design and implement async FIFO with full testbench")

        self.assertEqual(result["complexity"], "complex")
        self.assertTrue(result["needs_planning"])
        self.assertEqual(result["estimated_steps"], 8)
        self.assertIn("exploration", result["reasoning"])

    @patch('src.main.call_llm_raw')
    def test_llm_error_handling(self, mock_llm):
        """Test: Graceful handling when LLM returns error"""
        mock_llm.return_value = "Error calling LLM: timeout"

        result = _analyze_task_complexity_llm("Some task")

        self.assertEqual(result["complexity"], "unknown")
        self.assertFalse(result["needs_planning"])
        self.assertEqual(result["estimated_steps"], 0)

    @patch('src.main.call_llm_raw')
    def test_invalid_json_handling(self, mock_llm):
        """Test: Graceful handling when LLM returns invalid JSON"""
        mock_llm.return_value = "This is not JSON at all"

        result = _analyze_task_complexity_llm("Some task")

        self.assertEqual(result["complexity"], "unknown")
        self.assertFalse(result["needs_planning"])

    @patch('src.main.call_llm_raw')
    def test_llm_exception_handling(self, mock_llm):
        """Test: Exception handling during LLM call"""
        mock_llm.side_effect = Exception("Network error")

        result = _analyze_task_complexity_llm("Some task")

        self.assertEqual(result["complexity"], "unknown")
        self.assertFalse(result["needs_planning"])


class TestShouldAutoPlanHeuristic(unittest.TestCase):
    """Test heuristic-based auto plan decision"""

    def test_multiline_text_triggers_plan(self):
        """Test: Multi-line text triggers plan mode"""
        task = "Implement feature\nwith tests\nand documentation"

        result = _should_auto_plan_heuristic(task)

        self.assertTrue(result)

    def test_long_text_triggers_plan(self):
        """Test: Long text (>120 chars) triggers plan mode"""
        task = "a" * 121  # 121 characters

        result = _should_auto_plan_heuristic(task)

        self.assertTrue(result)

    def test_keyword_matching_triggers_plan(self):
        """Test: Multiple keywords trigger plan mode"""
        task = "implement new feature with test"  # "implement" + "test" = 2 keywords

        result = _should_auto_plan_heuristic(task)

        self.assertTrue(result)

    def test_simple_task_no_plan(self):
        """Test: Simple task doesn't trigger plan mode"""
        task = "read main.py"

        result = _should_auto_plan_heuristic(task)

        self.assertFalse(result)

    def test_empty_task_no_plan(self):
        """Test: Empty task doesn't trigger plan mode"""
        result = _should_auto_plan_heuristic("")

        self.assertFalse(result)

    def test_plan_execution_command_no_plan(self):
        """Test: Plan execution commands don't trigger plan mode"""
        with patch('src.main._looks_like_execute_plan_request', return_value=True):
            result = _should_auto_plan_heuristic("execute plan")

            self.assertFalse(result)


class TestShouldAutoPlan(unittest.TestCase):
    """Test integrated auto plan decision (with LLM or heuristic)"""

    @patch('src.main.config')
    @patch('src.main._analyze_task_complexity_llm')
    def test_uses_llm_when_enabled(self, mock_analyze, mock_config):
        """Test: Uses LLM analysis when AUTONOMOUS_COMPLEXITY_ANALYSIS=true"""
        mock_config.AUTONOMOUS_COMPLEXITY_ANALYSIS = True
        mock_analyze.return_value = {
            "complexity": "complex",
            "needs_planning": True,
            "estimated_steps": 8,
            "reasoning": "Complex task"
        }

        result = _should_auto_plan("Design new system")

        # Should call LLM analysis
        mock_analyze.assert_called_once_with("Design new system")
        # Should return LLM decision
        self.assertTrue(result)

    @patch('src.main.config')
    @patch('src.main._should_auto_plan_heuristic')
    def test_uses_heuristic_when_disabled(self, mock_heuristic, mock_config):
        """Test: Uses heuristic when AUTONOMOUS_COMPLEXITY_ANALYSIS=false"""
        mock_config.AUTONOMOUS_COMPLEXITY_ANALYSIS = False
        mock_heuristic.return_value = True

        result = _should_auto_plan("implement feature")

        # Should call heuristic
        mock_heuristic.assert_called_once()
        # Should return heuristic decision
        self.assertTrue(result)

    @patch('src.main.config')
    @patch('src.main._analyze_task_complexity_llm')
    @patch('src.main._should_auto_plan_heuristic')
    def test_fallback_to_heuristic_on_llm_failure(self, mock_heuristic, mock_analyze, mock_config):
        """Test: Falls back to heuristic when LLM returns unknown"""
        mock_config.AUTONOMOUS_COMPLEXITY_ANALYSIS = True
        mock_analyze.return_value = {
            "complexity": "unknown",
            "needs_planning": False,
            "estimated_steps": 0,
            "reasoning": "LLM error"
        }
        mock_heuristic.return_value = True

        result = _should_auto_plan("some task")

        # Should try LLM first
        mock_analyze.assert_called_once()
        # Should fallback to heuristic
        mock_heuristic.assert_called_once()
        # Should return heuristic result
        self.assertTrue(result)

    @patch('src.main.config')
    @patch('src.main._analyze_task_complexity_llm')
    def test_respects_llm_no_planning_decision(self, mock_analyze, mock_config):
        """Test: Respects LLM decision of no planning needed"""
        mock_config.AUTONOMOUS_COMPLEXITY_ANALYSIS = True
        mock_analyze.return_value = {
            "complexity": "simple",
            "needs_planning": False,
            "estimated_steps": 1,
            "reasoning": "Simple read operation"
        }

        result = _should_auto_plan("read file.py")

        # Should return False (no planning)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()

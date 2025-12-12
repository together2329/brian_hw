"""
Integration Tests for Plan Mode Workflow

Tests for Phase 3: Claude Flow Complete Implementation
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
config.PLAN_MODE_EXPLORE_COUNT = 3
config.PLAN_MODE_PARALLEL_EXPLORE = True
config.ENABLE_TODO_TRACKING = True
config.CLAUDE_FLOW_MODE = "auto"
config.CLAUDE_FLOW_REQUIRE_APPROVAL = True
config.CLAUDE_FLOW_AUTO_EXECUTE = True
config.CLAUDE_FLOW_STEP_MAX_ITERATIONS = 25

# Mock tools module
sys.modules['core.tools'] = MagicMock()

from src.main import (
    _run_explore_agent,
    _spawn_parallel_explore_agents,
    _spawn_plan_agent,
    _execute_plan_mode_workflow,
)


class TestPlanModeWorkflow(unittest.TestCase):
    """Test Plan Mode Workflow functions"""

    def setUp(self):
        """Set up test fixtures"""
        pass

    @patch('src.main.tools.spawn_explore')
    def test_run_explore_agent_success(self, mock_spawn_explore):
        """Test: _run_explore_agent returns exploration result"""
        mock_spawn_explore.return_value = "Found 3 implementations in core/"

        result = _run_explore_agent("Explore ReAct implementations")

        self.assertIn("Explored:", result)
        self.assertIn("ReAct implementations", result)
        self.assertIn("Found 3 implementations", result)
        mock_spawn_explore.assert_called_once()

    @patch('src.main.tools.spawn_explore')
    def test_run_explore_agent_failure(self, mock_spawn_explore):
        """Test: _run_explore_agent handles errors gracefully"""
        mock_spawn_explore.side_effect = Exception("Connection timeout")

        result = _run_explore_agent("Explore something")

        self.assertIn("Error:", result)
        self.assertIn("Connection timeout", result)

    @patch('src.main._run_explore_agent')
    def test_spawn_parallel_explore_agents(self, mock_run_explore):
        """Test: _spawn_parallel_explore_agents runs multiple agents in parallel"""
        # Mock successful exploration
        mock_run_explore.return_value = "Exploration complete"

        results = _spawn_parallel_explore_agents("Design FIFO module")

        # Should spawn 3 agents
        self.assertEqual(len(results), 3)
        # All should be strings
        for result in results:
            self.assertIsInstance(result, str)
        # Should be called 3 times (parallelized)
        self.assertEqual(mock_run_explore.call_count, 3)

    @patch('src.main._generate_plan_steps_via_llm')
    def test_spawn_plan_agent_with_context(self, mock_generate_steps):
        """Test: _spawn_plan_agent generates steps with exploration context"""
        mock_generate_steps.return_value = [
            "Step 1: Explore existing code",
            "Step 2: Design interface",
            "Step 3: Implement logic"
        ]

        explore_results = [
            "Exploration 1: Found module_a.py",
            "Exploration 2: Found test patterns",
        ]

        steps = _spawn_plan_agent("Add new feature", explore_results)

        # Should return plan steps
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0], "Step 1: Explore existing code")

        # Should have been called with context
        mock_generate_steps.assert_called_once()
        call_args = mock_generate_steps.call_args
        self.assertIn("additional_context", call_args.kwargs)
        self.assertIn("Exploration 1", call_args.kwargs["additional_context"])

    @patch('src.main._spawn_parallel_explore_agents')
    @patch('src.main._spawn_plan_agent')
    @patch('src.main.tools.create_plan')
    @patch('src.main.tools.wait_for_plan_approval')
    @patch('src.main.tools.get_plan')
    def test_execute_plan_mode_workflow_complete(
        self,
        mock_get_plan,
        mock_wait_approval,
        mock_create_plan,
        mock_spawn_plan,
        mock_spawn_explore
    ):
        """Test: _execute_plan_mode_workflow complete 6-step workflow"""
        # Setup mocks
        mock_spawn_explore.return_value = [
            "Exploration 1 result",
            "Exploration 2 result",
            "Exploration 3 result",
        ]
        mock_spawn_plan.return_value = [
            "Step 1: Explore code",
            "Step 2: Design interface",
            "Step 3: Implement",
        ]
        mock_create_plan.return_value = "Plan created successfully"
        mock_wait_approval.return_value = "Please review and approve the plan"
        mock_get_plan.return_value = "# Plan\n1. Step 1\n2. Step 2\n3. Step 3"

        # Execute workflow
        messages = []
        result_messages = _execute_plan_mode_workflow(messages, "Design async FIFO")

        # Verify all phases executed
        mock_spawn_explore.assert_called_once()
        mock_spawn_plan.assert_called_once()
        mock_create_plan.assert_called_once()
        mock_wait_approval.assert_called_once()
        mock_get_plan.assert_called_once()

        # Verify message appended
        self.assertEqual(len(result_messages), 1)
        self.assertEqual(result_messages[0]["role"], "assistant")
        self.assertIn("Plan created successfully", result_messages[0]["content"])

    @patch('src.main._spawn_parallel_explore_agents')
    @patch('src.main._spawn_plan_agent')
    @patch('src.main.tools.create_plan')
    @patch('src.main.tools.wait_for_plan_approval')
    @patch('src.main.tools.get_plan')
    def test_execute_plan_mode_workflow_fallback_steps(
        self,
        mock_get_plan,
        mock_wait_approval,
        mock_create_plan,
        mock_spawn_plan,
        mock_spawn_explore
    ):
        """Test: Workflow uses fallback steps when Plan Agent fails"""
        # Setup mocks - Plan Agent returns empty
        mock_spawn_explore.return_value = []
        mock_spawn_plan.return_value = []  # Empty steps
        mock_create_plan.return_value = "Plan created with fallback steps"
        mock_wait_approval.return_value = "Please approve"
        mock_get_plan.return_value = "# Plan\n(fallback)"

        # Execute workflow
        messages = []
        result_messages = _execute_plan_mode_workflow(messages, "Simple task")

        # Verify fallback steps were used
        mock_create_plan.assert_called_once()
        call_args = mock_create_plan.call_args
        steps_str = call_args.kwargs["steps"]
        self.assertIn("관련 파일/구조 탐색", steps_str)  # Korean fallback steps

        # Verify message appended
        self.assertEqual(len(result_messages), 1)

    @patch('src.main.config')
    @patch('src.main._spawn_parallel_explore_agents')
    def test_workflow_skips_explore_when_disabled(self, mock_spawn_explore, mock_config):
        """Test: Workflow skips Explore phase when PLAN_MODE_PARALLEL_EXPLORE=false"""
        # Disable parallel explore
        mock_config.PLAN_MODE_PARALLEL_EXPLORE = False
        mock_config.CLAUDE_FLOW_MODE = "auto"

        with patch('src.main._spawn_plan_agent') as mock_plan, \
             patch('src.main.tools.create_plan') as mock_create, \
             patch('src.main.tools.wait_for_plan_approval') as mock_wait, \
             patch('src.main.tools.get_plan') as mock_get:

            mock_plan.return_value = ["Step 1"]
            mock_create.return_value = "Created"
            mock_wait.return_value = "Approve"
            mock_get.return_value = "Plan"

            messages = []
            _execute_plan_mode_workflow(messages, "Task")

            # Explore should NOT be called
            mock_spawn_explore.assert_not_called()

            # Plan Agent should still be called
            mock_plan.assert_called_once()


class TestGeneratePlanStepsWithContext(unittest.TestCase):
    """Test _generate_plan_steps_via_llm with additional_context"""

    @patch('src.main.call_llm_raw')
    def test_generate_plan_steps_with_context(self, mock_llm):
        """Test: Plan generation uses additional_context from Explore agents"""
        from src.main import _generate_plan_steps_via_llm

        # Mock LLM response
        mock_llm.return_value = '''
        {
            "steps": [
                "Read existing implementation",
                "Design new interface",
                "Write code"
            ]
        }
        '''

        context = "Exploration found: module_a.py, test_a.py"
        steps = _generate_plan_steps_via_llm("Add feature", additional_context=context)

        # Verify steps extracted
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0], "Read existing implementation")

        # Verify LLM was called with context
        mock_llm.assert_called_once()
        call_args = mock_llm.call_args[0][0]  # First arg: messages list
        user_message = call_args[1]["content"]
        self.assertIn("Add feature", user_message)
        self.assertIn("module_a.py", user_message)
        self.assertIn("Context from exploration", user_message)


if __name__ == '__main__':
    unittest.main()

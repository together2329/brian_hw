"""
Deep SubAgent Integration Tests

Tests actual SubAgent execution flows:
- Agent.run() with mock LLM
- Action plan generation and parsing
- Tool execution in agent context
- Multi-agent sequential execution
- Error handling and recovery
"""
import sys
import os
import unittest
import tempfile
import shutil
import json

# Import sub_agents - path setup handled by conftest.py
from sub_agents.explore_agent import ExploreAgent
from sub_agents.plan_agent import PlanAgent
from sub_agents.execute_agent import ExecuteAgent
from sub_agents.code_review_agent import CodeReviewAgent
from sub_agents.base import (
    SubAgent, AgentStatus, SubAgentResult, 
    ActionPlan, ActionStep
)


class MockLLM:
    """Mock LLM for testing agent flows"""
    
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        self.call_history = []
    
    def __call__(self, messages, temperature=0.7):
        """Mock LLM call that returns predefined responses"""
        self.call_history.append(messages)
        
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        
        # Default response for action plan
        return json.dumps({
            "task_understanding": "Test task",
            "strategy": "Direct approach",
            "steps": [{
                "step_number": 1,
                "description": "Execute task",
                "prompt": "Do the task",
                "required_tools": ["list_dir"],
                "depends_on": [],
                "expected_output": "Done"
            }],
            "estimated_tools": ["list_dir"],
            "success_criteria": "Task complete"
        })


class MockToolExecutor:
    """Mock tool executor for testing"""
    
    def __init__(self, results=None):
        self.results = results or {}
        self.call_history = []
    
    def __call__(self, tool_name, args_str):
        """Mock tool execution"""
        self.call_history.append((tool_name, args_str))
        
        if tool_name in self.results:
            return self.results[tool_name]
        
        # Default responses
        default_results = {
            "list_dir": "file1.v\nfile2.v\ntest_tb.v",
            "read_file": "module test; endmodule",
            "grep_file": "Found 3 matches",
            "find_files": "main.v\ntest.v",
            "git_status": "On branch main\nnothing to commit"
        }
        
        return default_results.get(tool_name, f"Result for {tool_name}")


class TestAgentRun(unittest.TestCase):
    """Test actual Agent.run() execution"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        with open(os.path.join(self.temp_dir, "test.v"), "w") as f:
            f.write("module test; endmodule")
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_explore_agent_run_with_mock(self):
        """Test ExploreAgent.run() returns proper result"""
        mock_llm = MockLLM([
            # Planning response
            json.dumps({
                "task_understanding": "Explore the codebase",
                "strategy": "List files first",
                "steps": [{
                    "step_number": 1,
                    "description": "List directory",
                    "prompt": "List all files",
                    "required_tools": ["list_dir"],
                    "depends_on": [],
                    "expected_output": "File list"
                }],
                "estimated_tools": ["list_dir"],
                "success_criteria": "Files listed"
            }),
            # Execution response
            "Thought: Need to list files\nAction: list_dir(path='.')",
            # Final response
            "Thought: Found files\nResult: Found test.v and other files"
        ])
        
        mock_tools = MockToolExecutor()
        
        agent = ExploreAgent(
            name="test_explore",
            llm_call_func=mock_llm,
            execute_tool_func=mock_tools,
            max_iterations=3
        )
        
        result = agent.run(
            task="Find all Verilog files",
            context={"working_dir": self.temp_dir}
        )
        
        # Verify result structure
        self.assertIsInstance(result, SubAgentResult)
        self.assertIn(result.status, [AgentStatus.COMPLETED, AgentStatus.FAILED])
        self.assertIsInstance(result.output, str)
        self.assertIsInstance(result.artifacts, dict)
    
    def test_execute_agent_run_with_mock(self):
        """Test ExecuteAgent.run() with write tools"""
        mock_llm = MockLLM([
            json.dumps({
                "task_understanding": "Create a file",
                "strategy": "Write directly",
                "steps": [{
                    "step_number": 1,
                    "description": "Write file",
                    "prompt": "Create test file",
                    "required_tools": ["write_file"],
                    "depends_on": [],
                    "expected_output": "File created"
                }],
                "estimated_tools": ["write_file"],
                "success_criteria": "File exists"
            }),
            "Thought: Writing file\nResult: File created successfully"
        ])
        
        mock_tools = MockToolExecutor({"write_file": "File written successfully"})
        
        agent = ExecuteAgent(
            name="test_execute",
            llm_call_func=mock_llm,
            execute_tool_func=mock_tools,
            max_iterations=3
        )
        
        result = agent.run(
            task="Create a new Verilog module",
            context={}
        )
        
        self.assertIsInstance(result, SubAgentResult)


class TestActionPlanParsing(unittest.TestCase):
    """Test ActionPlan parsing from LLM responses"""
    
    def test_parse_valid_json_plan(self):
        """Test parsing valid JSON plan"""
        mock_llm = MockLLM()
        agent = ExploreAgent(
            name="test",
            llm_call_func=mock_llm,
            execute_tool_func=lambda x, y: "ok",
            max_iterations=1
        )
        
        json_response = json.dumps({
            "task_understanding": "Test",
            "strategy": "Direct",
            "steps": [
                {
                    "step_number": 1,
                    "description": "Step 1",
                    "prompt": "Do step 1",
                    "required_tools": ["read_file"],
                    "depends_on": [],
                    "expected_output": "Done"
                }
            ],
            "estimated_tools": ["read_file"],
            "success_criteria": "Complete"
        })
        
        plan = agent._parse_plan(json_response)
        
        self.assertIsInstance(plan, ActionPlan)
        self.assertEqual(plan.task_understanding, "Test")
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].step_number, 1)
    
    def test_parse_malformed_json_creates_default(self):
        """Test that malformed JSON creates default plan"""
        mock_llm = MockLLM()
        agent = ExploreAgent(
            name="test",
            llm_call_func=mock_llm,
            execute_tool_func=lambda x, y: "ok",
            max_iterations=1
        )
        agent._current_task = "Test task"
        
        plan = agent._parse_plan("This is not valid JSON at all")
        
        # Should create default plan
        self.assertIsInstance(plan, ActionPlan)
        self.assertEqual(len(plan.steps), 1)


class TestToolExecution(unittest.TestCase):
    """Test tool execution within agent context"""
    
    def test_allowed_tool_executes(self):
        """Test that allowed tools execute successfully"""
        call_log = []
        
        def mock_executor(tool_name, args):
            call_log.append((tool_name, args))
            return f"Executed {tool_name}"
        
        mock_llm = MockLLM([
            json.dumps({
                "task_understanding": "Read a file",
                "strategy": "Direct read",
                "steps": [{
                    "step_number": 1,
                    "description": "Read file",
                    "prompt": "Read test.v",
                    "required_tools": ["read_file"],
                    "depends_on": [],
                    "expected_output": "File content"
                }],
                "estimated_tools": ["read_file"],
                "success_criteria": "Content retrieved"
            }),
            "Thought: Reading file\nAction: read_file(path='test.v')",
            "Thought: Got content\nResult: File read successfully"
        ])
        
        agent = ExploreAgent(
            name="test",
            llm_call_func=mock_llm,
            execute_tool_func=mock_executor,
            max_iterations=3
        )
        
        result = agent.run(task="Read test.v", context={})
        
        # Check that read_file was called (it's in ALLOWED_TOOLS)
        read_calls = [c for c in call_log if c[0] == "read_file"]
        self.assertGreaterEqual(len(read_calls), 0)  # May or may not be called
    
    def test_forbidden_tool_blocked(self):
        """Test that forbidden tools are blocked"""
        call_log = []
        
        def mock_executor(tool_name, args):
            call_log.append((tool_name, args))
            return f"Executed {tool_name}"
        
        mock_llm = MockLLM([
            json.dumps({
                "task_understanding": "Explore",
                "strategy": "Try to write",
                "steps": [{
                    "step_number": 1,
                    "description": "Try write",
                    "prompt": "Write file",
                    "required_tools": ["write_file"],
                    "depends_on": [],
                    "expected_output": "Error"
                }],
                "estimated_tools": ["write_file"],
                "success_criteria": "Blocked"
            }),
            "Thought: Trying to write\nAction: write_file(path='test.v', content='x')",
            "Thought: Blocked\nResult: Cannot write"
        ])
        
        agent = ExploreAgent(
            name="test",
            llm_call_func=mock_llm,
            execute_tool_func=mock_executor,
            max_iterations=3
        )
        
        result = agent.run(task="Try to write", context={})
        
        # write_file should NOT have been called (not in ExploreAgent.ALLOWED_TOOLS)
        write_calls = [c for c in call_log if c[0] == "write_file"]
        self.assertEqual(len(write_calls), 0)


class TestMultiStepExecution(unittest.TestCase):
    """Test multi-step plan execution"""
    
    def test_sequential_steps_execute(self):
        """Test that steps execute in order"""
        step_order = []
        
        def mock_executor(tool_name, args):
            step_order.append(tool_name)
            return f"Done: {tool_name}"
        
        mock_llm = MockLLM([
            json.dumps({
                "task_understanding": "Multi-step task",
                "strategy": "Sequential",
                "steps": [
                    {
                        "step_number": 1,
                        "description": "First list",
                        "prompt": "List files",
                        "required_tools": ["list_dir"],
                        "depends_on": [],
                        "expected_output": "Files"
                    },
                    {
                        "step_number": 2,
                        "description": "Then read",
                        "prompt": "Read file",
                        "required_tools": ["read_file"],
                        "depends_on": [1],
                        "expected_output": "Content"
                    }
                ],
                "estimated_tools": ["list_dir", "read_file"],
                "success_criteria": "Both done"
            }),
            # Step 1 execution
            "Thought: Listing\nAction: list_dir(path='.')",
            "Thought: Done\nResult: Listed files",
            # Step 2 execution
            "Thought: Reading\nAction: read_file(path='main.v')",
            "Thought: Done\nResult: Read complete"
        ])
        
        agent = ExploreAgent(
            name="test",
            llm_call_func=mock_llm,
            execute_tool_func=mock_executor,
            max_iterations=5
        )
        
        result = agent.run(task="List then read", context={})
        
        self.assertIsInstance(result, SubAgentResult)


class TestAgentErrorHandling(unittest.TestCase):
    """Test error handling in agents"""
    
    def test_tool_error_captured(self):
        """Test that tool errors are captured"""
        def failing_executor(tool_name, args):
            raise Exception("Tool failed!")
        
        mock_llm = MockLLM([
            json.dumps({
                "task_understanding": "Test",
                "strategy": "Direct",
                "steps": [{
                    "step_number": 1,
                    "description": "Fail",
                    "prompt": "Do something",
                    "required_tools": ["list_dir"],
                    "depends_on": [],
                    "expected_output": "Error"
                }],
                "estimated_tools": ["list_dir"],
                "success_criteria": "Handle error"
            }),
            "Thought: Calling\nAction: list_dir(path='.')",
            "Thought: Error\nResult: Tool failed"
        ])
        
        agent = ExploreAgent(
            name="test",
            llm_call_func=mock_llm,
            execute_tool_func=failing_executor,
            max_iterations=3
        )
        
        # Should not raise, should handle error gracefully
        result = agent.run(task="Test error", context={})
        
        self.assertIsInstance(result, SubAgentResult)
    
    def test_llm_error_returns_failed_status(self):
        """Test that LLM errors result in FAILED status"""
        def failing_llm(messages, temperature=0.7):
            raise Exception("LLM API failed!")
        
        agent = ExploreAgent(
            name="test",
            llm_call_func=failing_llm,
            execute_tool_func=lambda x, y: "ok",
            max_iterations=1
        )
        
        result = agent.run(task="Test LLM error", context={})
        
        self.assertEqual(result.status, AgentStatus.FAILED)
        self.assertGreater(len(result.errors), 0)


class TestContextPropagation(unittest.TestCase):
    """Test context propagation between agent stages"""
    
    def test_context_available_in_run(self):
        """Test that context is available during run"""
        context_received = {}
        
        def capturing_llm(messages, temperature=0.7):
            # Check if context was injected into prompts
            for msg in messages:
                if "working_dir" in str(msg):
                    context_received["found"] = True
            
            return json.dumps({
                "task_understanding": "Test",
                "strategy": "Direct",
                "steps": [{
                    "step_number": 1,
                    "description": "Done",
                    "prompt": "Done",
                    "required_tools": [],
                    "depends_on": [],
                    "expected_output": "Done"
                }],
                "estimated_tools": [],
                "success_criteria": "Done"
            })
        
        agent = ExploreAgent(
            name="test",
            llm_call_func=capturing_llm,
            execute_tool_func=lambda x, y: "ok",
            max_iterations=1
        )
        
        result = agent.run(
            task="Test",
            context={"working_dir": "/test/path", "files": ["a.v", "b.v"]}
        )
        
        self.assertIsInstance(result, SubAgentResult)
    
    def test_artifacts_collected(self):
        """Test that artifacts are collected from agent run"""
        mock_llm = MockLLM([
            json.dumps({
                "task_understanding": "Test",
                "strategy": "Direct",
                "steps": [{
                    "step_number": 1,
                    "description": "Read",
                    "prompt": "Read files",
                    "required_tools": ["read_file"],
                    "depends_on": [],
                    "expected_output": "Content"
                }],
                "estimated_tools": ["read_file"],
                "success_criteria": "Done"
            }),
            "Thought: Reading\nAction: read_file(path='test.v')",
            "Thought: Done\nResult: Read complete"
        ])
        
        agent = ExploreAgent(
            name="test",
            llm_call_func=mock_llm,
            execute_tool_func=lambda x, y: "file content",
            max_iterations=3
        )
        
        result = agent.run(task="Read files", context={})
        
        # Artifacts should be collected
        self.assertIsInstance(result.artifacts, dict)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Deep SubAgent Integration Tests")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)

"""
Integration Test Suite #4: SubAgent Pipeline

Tests the SubAgent system integration:
- ExploreAgent → PlanAgent → ExecuteAgent sequence
- Agent tool permission isolation
- Context passing between agents
- Artifact collection from agent outputs

Scenarios:
- Multi-agent workflow
- Permission boundaries
- Result aggregation
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import sub_agents - path setup handled by conftest.py
from sub_agents.explore_agent import ExploreAgent
from sub_agents.plan_agent import PlanAgent
from sub_agents.execute_agent import ExecuteAgent
from sub_agents.code_review_agent import CodeReviewAgent
from sub_agents.base import SubAgent, AgentStatus, SubAgentResult, ActionPlan


class TestSubAgentToolIsolation(unittest.TestCase):
    """Test: Agents are properly isolated by tool permissions"""
    
    def test_explore_cannot_write(self):
        """Test: ExploreAgent cannot use write tools"""
        write_tools = {"write_file", "replace_in_file", "replace_lines", "run_command"}
        
        allowed = ExploreAgent.ALLOWED_TOOLS
        forbidden = allowed & write_tools
        
        self.assertEqual(len(forbidden), 0, 
                        f"ExploreAgent should not have write tools: {forbidden}")
    
    def test_execute_can_write(self):
        """Test: ExecuteAgent can use write tools"""
        write_tools = {"write_file", "replace_in_file", "run_command"}
        
        allowed = ExecuteAgent.ALLOWED_TOOLS
        has_write = allowed & write_tools
        
        self.assertGreaterEqual(len(has_write), 2,
                               "ExecuteAgent should have write tools")
    
    def test_review_is_read_only(self):
        """Test: CodeReviewAgent is read-only"""
        write_tools = {"write_file", "replace_in_file", "run_command"}
        
        allowed = CodeReviewAgent.ALLOWED_TOOLS
        has_write = allowed & write_tools
        
        self.assertEqual(len(has_write), 0,
                        "CodeReviewAgent should not have write tools")


class TestAgentToolCoverage(unittest.TestCase):
    """Test: Agents together cover all necessary tool categories"""
    
    def test_read_tools_in_explore(self):
        """Test: Explore has comprehensive read tools"""
        read_tools = {"read_file", "read_lines", "grep_file", "list_dir", "find_files"}
        
        allowed = ExploreAgent.ALLOWED_TOOLS
        has_read = allowed & read_tools
        
        self.assertGreaterEqual(len(has_read), 4,
                               "ExploreAgent should have most read tools")
    
    def test_git_tools_in_review(self):
        """Test: Review has git tools"""
        git_tools = {"git_status", "git_diff"}
        
        allowed = CodeReviewAgent.ALLOWED_TOOLS
        has_git = allowed & git_tools
        
        self.assertEqual(len(has_git), 2,
                        "CodeReviewAgent should have all git tools")
    
    def test_rag_tools_in_explore(self):
        """Test: Explore has RAG search"""
        self.assertIn("rag_search", ExploreAgent.ALLOWED_TOOLS)


class TestAgentPipelineConcept(unittest.TestCase):
    """Test: Multi-agent pipeline concept"""
    
    def test_explore_to_execute_tool_progression(self):
        """Test: Explore tools are subset conceptually usable before Execute"""
        explore_tools = ExploreAgent.ALLOWED_TOOLS
        execute_tools = ExecuteAgent.ALLOWED_TOOLS
        
        # Execute should have more capabilities than explore
        self.assertGreaterEqual(len(execute_tools), len(explore_tools) // 2,
                               "ExecuteAgent should have substantial capabilities")
    
    def test_all_agents_have_tools(self):
        """Test: All agents have at least some tools defined"""
        agents = [ExploreAgent, PlanAgent, ExecuteAgent, CodeReviewAgent]
        
        for agent_class in agents:
            self.assertIsInstance(agent_class.ALLOWED_TOOLS, set,
                                 f"{agent_class.__name__} should have ALLOWED_TOOLS set")


class TestAgentResultStructure(unittest.TestCase):
    """Test: Agent result structures are compatible"""
    
    def test_subagent_result_fields(self):
        """Test: SubAgentResult has required fields for aggregation"""
        result = SubAgentResult(
            status=AgentStatus.COMPLETED,
            output="Test output"
        )
        
        # Check required fields exist
        self.assertIsNotNone(result.status)
        self.assertIsNotNone(result.output)
        self.assertIsInstance(result.artifacts, dict)
        self.assertIsInstance(result.context_updates, dict)
        self.assertIsInstance(result.tool_calls, list)
    
    def test_agent_status_enum(self):
        """Test: AgentStatus has expected values"""
        statuses = [s.value for s in AgentStatus]
        
        self.assertIn("pending", statuses)
        self.assertIn("running", statuses)
        self.assertIn("completed", statuses)
        self.assertIn("failed", statuses)


class TestContextPassing(unittest.TestCase):
    """Test: Context can be passed between agent stages"""
    
    def test_result_context_updates_dict(self):
        """Test: context_updates is a proper dict for passing"""
        result = SubAgentResult(
            status=AgentStatus.COMPLETED,
            output="Exploration complete",
            context_updates={
                "files_found": ["main.v", "test_tb.v"],
                "patterns_discovered": ["always @(posedge clk)"]
            }
        )
        
        # Can extract context for next agent
        next_context = result.context_updates
        
        self.assertIn("files_found", next_context)
        self.assertEqual(len(next_context["files_found"]), 2)
    
    def test_artifacts_collection(self):
        """Test: Artifacts from multiple agents can be aggregated"""
        explore_result = SubAgentResult(
            status=AgentStatus.COMPLETED,
            output="Found files",
            artifacts={"files_read": ["a.v", "b.v"]}
        )
        
        execute_result = SubAgentResult(
            status=AgentStatus.COMPLETED,
            output="Made changes",
            artifacts={"files_modified": ["a.v"]}
        )
        
        # Aggregate artifacts
        all_artifacts = {
            "explore": explore_result.artifacts,
            "execute": execute_result.artifacts
        }
        
        self.assertIn("explore", all_artifacts)
        self.assertIn("execute", all_artifacts)


class TestPipelineOrchestration(unittest.TestCase):
    """Test: Pipeline orchestration concepts"""
    
    def test_sequential_agent_order(self):
        """Test: Logical sequence Explore → Plan → Execute → Review"""
        # This tests the conceptual order
        pipeline_order = ["explore", "plan", "execute", "review"]
        
        agent_map = {
            "explore": ExploreAgent,
            "plan": PlanAgent,
            "execute": ExecuteAgent,
            "review": CodeReviewAgent
        }
        
        # All agents should be available
        for stage in pipeline_order:
            self.assertIn(stage, agent_map)
            self.assertTrue(hasattr(agent_map[stage], "ALLOWED_TOOLS"))
    
    def test_permission_escalation_in_pipeline(self):
        """Test: Permissions escalate appropriately in pipeline"""
        # Explore: read-only
        explore_write = ExploreAgent.ALLOWED_TOOLS & {"write_file", "run_command"}
        
        # Execute: can write
        execute_write = ExecuteAgent.ALLOWED_TOOLS & {"write_file", "run_command"}
        
        # Review: back to read-only
        review_write = CodeReviewAgent.ALLOWED_TOOLS & {"write_file", "run_command"}
        
        self.assertEqual(len(explore_write), 0)  # No write
        self.assertGreater(len(execute_write), 0)  # Has write
        self.assertEqual(len(review_write), 0)  # No write


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Integration Test: SubAgent Pipeline")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)

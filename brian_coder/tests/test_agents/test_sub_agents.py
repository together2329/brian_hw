"""
Sub Agent Test Suite

Comprehensive tests for:
- ExploreAgent
- PlanAgent
- ExecuteAgent
- CodeReviewAgent
- SubAgent base class
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


class TestExploreAgent(unittest.TestCase):
    """Test ExploreAgent"""
    
    def test_explore_agent_allowed_tools_read_only(self):
        """Test that only read-only tools are allowed"""
        self.assertIn("read_file", ExploreAgent.ALLOWED_TOOLS)
        self.assertIn("grep_file", ExploreAgent.ALLOWED_TOOLS)
        self.assertIn("list_dir", ExploreAgent.ALLOWED_TOOLS)
        
        # Should NOT include write tools
        self.assertNotIn("write_file", ExploreAgent.ALLOWED_TOOLS)
        self.assertNotIn("run_command", ExploreAgent.ALLOWED_TOOLS)
    
    def test_explore_agent_has_rag_search(self):
        """Test that ExploreAgent can use RAG search"""
        self.assertIn("rag_search", ExploreAgent.ALLOWED_TOOLS)


class TestPlanAgent(unittest.TestCase):
    """Test PlanAgent"""
    
    def test_plan_agent_allowed_tools_defined(self):
        """Test PlanAgent has allowed tools defined"""
        # PlanAgent should have some allowed tools (may be empty or inherited)
        self.assertIsInstance(PlanAgent.ALLOWED_TOOLS, set)


class TestExecuteAgent(unittest.TestCase):
    """Test ExecuteAgent"""
    
    def test_execute_agent_allowed_tools(self):
        """Test ExecuteAgent has write tools"""
        # Execute agent should allow write operations
        self.assertIn("write_file", ExecuteAgent.ALLOWED_TOOLS)
        self.assertIn("run_command", ExecuteAgent.ALLOWED_TOOLS)
    
    def test_execute_agent_has_replace_tools(self):
        """Test ExecuteAgent has replace tools"""
        self.assertIn("replace_in_file", ExecuteAgent.ALLOWED_TOOLS)


class TestCodeReviewAgent(unittest.TestCase):
    """Test CodeReviewAgent"""
    
    def test_code_review_agent_allowed_tools(self):
        """Test CodeReviewAgent tools include git and read"""
        # Code review should include git tools
        self.assertIn("git_diff", CodeReviewAgent.ALLOWED_TOOLS)
        self.assertIn("git_status", CodeReviewAgent.ALLOWED_TOOLS)
        self.assertIn("read_file", CodeReviewAgent.ALLOWED_TOOLS)
    
    def test_code_review_agent_no_write(self):
        """Test CodeReviewAgent doesn't have write tools"""
        # Code review is read-only
        self.assertNotIn("write_file", CodeReviewAgent.ALLOWED_TOOLS)


class TestSubAgentToolSets(unittest.TestCase):
    """Test that agent tool sets are properly separated"""
    
    def test_explore_is_read_only(self):
        """Explore agent should only have read-only tools"""
        write_tools = {"write_file", "replace_in_file", "replace_lines", "run_command"}
        intersection = ExploreAgent.ALLOWED_TOOLS & write_tools
        self.assertEqual(len(intersection), 0)
    
    def test_execute_has_write_tools(self):
        """Execute agent should have write capabilities"""
        write_tools = {"write_file", "replace_in_file", "run_command"}
        intersection = ExecuteAgent.ALLOWED_TOOLS & write_tools
        self.assertGreaterEqual(len(intersection), 2)
    
    def test_review_has_git_tools(self):
        """Review agent should have git tools"""
        git_tools = {"git_diff", "git_status"}
        intersection = CodeReviewAgent.ALLOWED_TOOLS & git_tools
        self.assertEqual(len(intersection), 2)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Sub Agent Test Suite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)

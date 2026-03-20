"""
Integration test for Tool Call flow in main.py.
Tests: parse_all_actions -> parse_tool_arguments -> execute_tool
Simulates the actual ReAct agent tool execution flow.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))


class TestToolParsingFlow(unittest.TestCase):
    """Test the tool parsing flow as it happens in main.py."""
    
    def test_parse_single_action(self):
        """Test parsing a single action from LLM response."""
        from main import parse_all_actions
        
        llm_response = """
Thought: I need to read the file to understand its contents.
Action: read_file(path="counter.v")
"""
        actions = parse_all_actions(llm_response)
        
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "read_file")
        self.assertIn("counter.v", actions[0][1])
    
    def test_parse_multiple_actions(self):
        """Test parsing multiple actions from LLM response."""
        from main import parse_all_actions
        
        llm_response = """
Thought: I need to check two files.
Action: read_file(path="file1.v")
Action: read_file(path="file2.v")
"""
        actions = parse_all_actions(llm_response)
        
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0][0], "read_file")
        self.assertEqual(actions[1][0], "read_file")
    
    def test_parse_action_with_multiple_args(self):
        """Test parsing action with multiple arguments."""
        from main import parse_all_actions, parse_tool_arguments
        
        llm_response = """
Thought: I need to search for a pattern.
Action: grep_file(pattern="state_machine", path="pcie.v", context_lines=5)
"""
        actions = parse_all_actions(llm_response)
        
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "grep_file")
        
        # Parse arguments
        args, kwargs = parse_tool_arguments(actions[0][1])
        
        self.assertEqual(kwargs.get("pattern"), "state_machine")
        self.assertEqual(kwargs.get("path"), "pcie.v")
        self.assertEqual(kwargs.get("context_lines"), 5)
    
    def test_parse_action_with_triple_quotes(self):
        """Test parsing action with triple-quoted content."""
        from main import parse_all_actions, parse_tool_arguments
        
        llm_response = '''
Thought: I need to write a file.
Action: write_file(path="test.py", content="""def hello():
    print("Hello World")
""")
'''
        actions = parse_all_actions(llm_response)
        
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "write_file")
        
        # Parse arguments
        args, kwargs = parse_tool_arguments(actions[0][1])
        
        self.assertEqual(kwargs.get("path"), "test.py")
        self.assertIn("def hello():", kwargs.get("content", ""))
    
    def test_sanitize_action_text(self):
        """Test sanitization of common LLM errors."""
        from main import sanitize_action_text
        
        # Test number with trailing quote
        text = 'Action: read_lines(path="test.v", start_line=10", end_line=20")'
        sanitized = sanitize_action_text(text)
        self.assertIn("start_line=10", sanitized)
        self.assertIn("end_line=20", sanitized)
        
        # Test markdown bold removal
        text = '**Action:** read_file(path="test.v")'
        sanitized = sanitize_action_text(text)
        self.assertIn("Action:", sanitized)
        self.assertNotIn("**", sanitized)


class TestToolExecutionFlow(unittest.TestCase):
    """Test the tool execution flow."""
    
    def test_execute_read_file(self):
        """Test executing read_file tool."""
        from main import execute_tool
        
        # Create a temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello World")
            temp_path = f.name
        
        try:
            result = execute_tool("read_file", f'path="{temp_path}"')
            self.assertIn("Hello World", result)
        finally:
            os.unlink(temp_path)
    
    def test_execute_list_dir(self):
        """Test executing list_dir tool."""
        from main import execute_tool
        
        result = execute_tool("list_dir", 'path="."')
        
        # Should list current directory contents
        self.assertIsInstance(result, str)
        # Should not be an error
        self.assertNotIn("Error", result)
    
    def test_execute_nonexistent_tool(self):
        """Test error handling for non-existent tool."""
        from main import execute_tool
        
        result = execute_tool("nonexistent_tool", "")
        
        self.assertIn("Error", result)
        self.assertIn("not found", result)
    
    def test_execute_tool_with_invalid_args(self):
        """Test error handling for invalid arguments."""
        from main import execute_tool
        
        result = execute_tool("read_file", 'path="/nonexistent/path/file.txt"')
        
        # Should return error message, not crash
        self.assertIn("Error", result)


class TestFullReActFlow(unittest.TestCase):
    """Test the full ReAct flow simulation."""
    
    def test_full_flow_parse_and_execute(self):
        """
        Simulate the full flow:
        1. LLM generates response with Action
        2. parse_all_actions extracts tool calls
        3. parse_tool_arguments parses args
        4. execute_tool runs the tool
        """
        from main import parse_all_actions, parse_tool_arguments, execute_tool
        
        # Step 1: Simulated LLM response
        llm_response = """
Thought: I need to list the current directory to find Verilog files.
Action: list_dir(path=".")
"""
        
        # Step 2: Parse actions
        actions = parse_all_actions(llm_response)
        self.assertEqual(len(actions), 1)
        
        tool_name, args_str = actions[0]
        self.assertEqual(tool_name, "list_dir")
        
        # Step 3: Parse arguments
        args, kwargs = parse_tool_arguments(args_str)
        self.assertEqual(kwargs.get("path"), ".")
        
        # Step 4: Execute tool
        result = execute_tool(tool_name, args_str)
        
        # Should return directory listing
        self.assertIsInstance(result, str)
        self.assertNotIn("Error", result)
    
    def test_react_loop_simulation(self):
        """
        Simulate multiple iterations of ReAct loop.
        """
        from main import parse_all_actions, execute_tool
        
        # Iteration 1: Find files
        response1 = 'Thought: Find .v files.\nAction: find_files(pattern="*.v", directory=".")'
        actions1 = parse_all_actions(response1)
        
        if actions1:
            result1 = execute_tool(actions1[0][0], actions1[0][1])
            # Result should mention files found or no files
            self.assertIsInstance(result1, str)
        
        # Iteration 2: List directory
        response2 = 'Thought: Check src directory.\nAction: list_dir(path="src")'
        actions2 = parse_all_actions(response2)
        
        if actions2:
            result2 = execute_tool(actions2[0][0], actions2[0][1])
            self.assertIsInstance(result2, str)
    
    def test_error_recovery_flow(self):
        """
        Test that errors are returned properly, not raised.
        """
        from main import parse_all_actions, execute_tool
        
        # Try to read non-existent file
        response = 'Action: read_file(path="/definitely/not/a/real/file.txt")'
        actions = parse_all_actions(response)
        
        if actions:
            result = execute_tool(actions[0][0], actions[0][1])
            # Should return error message, not crash
            self.assertIn("Error", result)


class TestRAGToolFlow(unittest.TestCase):
    """Test RAG tool execution flow."""
    
    def test_rag_search_execution(self):
        """Test rag_search tool execution."""
        from main import execute_tool
        
        result = execute_tool("rag_search", 'query="pcie state machine", categories="all", limit=3')
        
        # Should return results or "no results" message
        self.assertIsInstance(result, str)
        # Should not crash
        self.assertTrue(len(result) > 0)
    
    def test_rag_status_execution(self):
        """Test rag_status tool execution."""
        from main import execute_tool
        
        result = execute_tool("rag_status", "")
        
        self.assertIsInstance(result, str)
        # Should show database status
        self.assertIn("RAG", result)


if __name__ == '__main__':
    unittest.main()

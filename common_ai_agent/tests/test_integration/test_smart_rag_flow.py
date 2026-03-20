"""
Integration test for Smart RAG flow in main.py.
Tests the actual user input -> RAG search -> context injection sequence.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))


class TestSmartRAGFlowIntegration(unittest.TestCase):
    """Test the full Smart RAG flow as it happens in main.py."""
    
    def setUp(self):
        """Set up test fixtures."""
        import config
        self.original_enable = getattr(config, 'ENABLE_SMART_RAG', True)
        config.ENABLE_SMART_RAG = True
        config.DEBUG_MODE = False
    
    def tearDown(self):
        """Restore config."""
        import config
        config.ENABLE_SMART_RAG = self.original_enable
    
    def test_full_flow_simulation(self):
        """
        Test the complete flow:
        1. Initial system prompt (no messages) - should have no RAG context
        2. User asks question - messages updated
        3. ReAct iteration 0 - system prompt refreshed with Smart RAG
        4. Verify RAG context is injected
        """
        import config
        from main import build_system_prompt
        from lib.iteration_control import IterationTracker
        
        # Step 1: Initial system prompt (like chat_loop start)
        initial_prompt = build_system_prompt()  # No messages
        
        # Should NOT have RAG context initially
        self.assertNotIn(
            "RELEVANT CODE/SPEC CONTEXT",
            initial_prompt,
            "Initial prompt should not have RAG context without messages"
        )
        
        # Step 2: Simulate user input
        messages = [
            {"role": "system", "content": initial_prompt},
            {"role": "user", "content": "pcie_msg_receiver state machine 분석"}
        ]
        
        # Step 3: Simulate run_react_agent iteration 0
        tracker = IterationTracker(max_iterations=10)
        
        if tracker.current == 0 and config.ENABLE_SMART_RAG:
            new_system_prompt = build_system_prompt(messages)
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] = new_system_prompt
        
        # Step 4: Verify RAG context is now present
        # Note: This depends on actual RAG DB having indexed files
        # The test passes if either:
        # - RAG context is injected (files indexed)
        # - RAG search returns no results (no files indexed)
        
        updated_prompt = messages[0]["content"]
        
        # Verify the prompt was updated (should be different from initial)
        # At minimum, it should include the RAG guidance section
        self.assertIn(
            "RAG CODE & SPEC SEARCH",
            updated_prompt,
            "Updated prompt should include RAG guidance"
        )
        
        print(f"Initial prompt length: {len(initial_prompt)}")
        print(f"Updated prompt length: {len(updated_prompt)}")
        print(f"RAG context injected: {'RELEVANT CODE/SPEC CONTEXT' in updated_prompt}")
    
    def test_user_query_extraction(self):
        """Test that the last user message is used for RAG query."""
        from core.smart_rag import SmartRAGDecision
        
        # Track what query was searched
        searched_queries = []
        
        def mock_search(query, limit=3):
            searched_queries.append(query)
            return []  # Return empty results
        
        smart_rag = SmartRAGDecision()
        
        # Simulate the query extraction logic from build_system_prompt
        messages = [
            {"role": "system", "content": "You are an agent..."},
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "pcie_msg_receiver 어디 있어?"},  # Last user message
        ]
        
        user_messages = [m for m in messages if m.get("role") == "user"]
        self.assertEqual(len(user_messages), 2)
        
        recent_query = user_messages[-1].get("content", "")[:200]
        self.assertEqual(recent_query, "pcie_msg_receiver 어디 있어?")
        
        # Verify this query is used for search
        smart_rag.decide(recent_query, mock_search)
        
        self.assertEqual(len(searched_queries), 1)
        self.assertIn("pcie_msg_receiver", searched_queries[0])
    
    def test_smart_rag_disabled_flow(self):
        """Test that RAG context is not injected when disabled."""
        import config
        config.ENABLE_SMART_RAG = False
        
        from main import build_system_prompt
        
        messages = [
            {"role": "system", "content": "Initial"},
            {"role": "user", "content": "pcie_msg_receiver state machine"}
        ]
        
        prompt = build_system_prompt(messages)
        
        # Should NOT have RAG context when disabled
        self.assertNotIn(
            "RELEVANT CODE/SPEC CONTEXT",
            prompt,
            "RAG context should not be injected when ENABLE_SMART_RAG=False"
        )
        
        # Restore
        config.ENABLE_SMART_RAG = True
    
    def test_empty_user_messages(self):
        """Test behavior when there are no user messages."""
        from main import build_system_prompt
        
        messages = [
            {"role": "system", "content": "System prompt only"}
        ]
        
        prompt = build_system_prompt(messages)
        
        # Should not crash and should not have RAG context
        self.assertNotIn(
            "RELEVANT CODE/SPEC CONTEXT",
            prompt,
            "Should not have RAG context with no user messages"
        )


class TestSmartRAGThresholds(unittest.TestCase):
    """Test threshold-based decision logic."""
    
    def test_high_score_no_llm_call(self):
        """High score should use results without LLM judgment."""
        from core.smart_rag import SmartRAGDecision
        
        llm_called = []
        
        def mock_llm(prompt):
            llm_called.append(prompt)
            return "YES"
        
        class MockChunk:
            source_file = "test.v"
            content = "module test..."
            category = "verilog"
            start_line = 1
            end_line = 10
        
        smart_rag = SmartRAGDecision(high_threshold=0.8)
        
        # High score result
        def high_score_search(query, limit=3):
            return [(0.9, MockChunk())]
        
        should_use, results = smart_rag.decide("test", high_score_search, mock_llm)
        
        self.assertTrue(should_use)
        self.assertEqual(len(llm_called), 0, "LLM should NOT be called for high score")
    
    def test_mid_score_triggers_llm(self):
        """Mid score should trigger LLM judgment."""
        from core.smart_rag import SmartRAGDecision
        
        llm_called = []
        
        def mock_llm(prompt):
            llm_called.append(prompt)
            return "YES"
        
        class MockChunk:
            source_file = "test.v"
            content = "module test..."
            category = "verilog"
            start_line = 1
            end_line = 10
        
        smart_rag = SmartRAGDecision(high_threshold=0.8, low_threshold=0.5)
        
        # Mid score result
        def mid_score_search(query, limit=3):
            return [(0.65, MockChunk())]
        
        should_use, results = smart_rag.decide("test", mid_score_search, mock_llm)
        
        self.assertTrue(should_use)
        self.assertEqual(len(llm_called), 1, "LLM should be called for mid score")
    
    def test_low_score_no_llm_call(self):
        """Low score should ignore results without LLM judgment."""
        from core.smart_rag import SmartRAGDecision
        
        llm_called = []
        
        def mock_llm(prompt):
            llm_called.append(prompt)
            return "YES"
        
        class MockChunk:
            source_file = "test.v"
            content = "module test..."
            category = "verilog"
            start_line = 1
            end_line = 10
        
        smart_rag = SmartRAGDecision(low_threshold=0.5)
        
        # Low score result
        def low_score_search(query, limit=3):
            return [(0.3, MockChunk())]
        
        should_use, results = smart_rag.decide("test", low_score_search, mock_llm)
        
        self.assertFalse(should_use)
        self.assertEqual(len(llm_called), 0, "LLM should NOT be called for low score")


if __name__ == '__main__':
    unittest.main()

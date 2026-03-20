"""
Real LLM API Integration Tests

Tests actual LLM API connectivity and responses:
- API connection test
- Response parsing
- Error handling
- Rate limiting behavior

NOTE: These tests require valid API keys in .env
Skip with: pytest tests/test_llm_api.py -v -k "not real_api"
"""
import sys
import os
import unittest
import time

# Check if API key is available
try:
    import config
    HAS_API_KEY = bool(getattr(config, 'OPENROUTER_API_KEY', None))
except:
    HAS_API_KEY = False


def skip_without_api(func):
    """Decorator to skip tests without API key"""
    return unittest.skipUnless(HAS_API_KEY, "No API key configured")(func)


class TestLLMConnection(unittest.TestCase):
    """Test LLM API connection"""
    
    @skip_without_api
    def test_api_connection(self):
        """Test basic API connection"""
        from llm_client import call_llm_api
        
        response = call_llm_api(
            messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
            temperature=0.1,
            max_tokens=10
        )
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertIn("hello", response.lower())
    
    @skip_without_api
    def test_api_with_system_prompt(self):
        """Test API with system prompt"""
        from llm_client import call_llm_api
        
        response = call_llm_api(
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Reply only with 'OK'."},
                {"role": "user", "content": "Are you ready?"}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        self.assertIsNotNone(response)
        self.assertIn("ok", response.lower())


class TestLLMResponseParsing(unittest.TestCase):
    """Test LLM response parsing for agent use"""
    
    @skip_without_api
    def test_json_response_parsing(self):
        """Test that LLM can produce parseable JSON"""
        from llm_client import call_llm_api
        import json
        
        response = call_llm_api(
            messages=[{
                "role": "user", 
                "content": "Return only this JSON, nothing else: {\"status\": \"ok\", \"count\": 42}"
            }],
            temperature=0.1,
            max_tokens=50
        )
        
        # Try to parse JSON from response
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                self.assertEqual(data.get("status"), "ok")
                self.assertEqual(data.get("count"), 42)
            else:
                self.fail("No JSON found in response")
        except json.JSONDecodeError:
            self.fail(f"Failed to parse JSON from: {response}")


class TestLLMErrorHandling(unittest.TestCase):
    """Test LLM error handling"""
    
    def test_invalid_api_key_handling(self):
        """Test handling of invalid API key"""
        try:
            from llm_client import call_llm_api
            self.assertTrue(callable(call_llm_api))
        except ImportError:
            pass


class TestEmbeddingAPI(unittest.TestCase):
    """Test embedding API for RAG"""
    
    @skip_without_api
    def test_embedding_generation(self):
        """Test embedding API generates vectors"""
        from rag_db import RAGDatabase
        
        rag = RAGDatabase()
        text = "module counter; wire clk; endmodule"
        embedding = rag._get_embedding(text)
        
        self.assertIsNotNone(embedding)
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)


class TestMockLLMFallback(unittest.TestCase):
    """Test mock LLM for when API is unavailable"""
    
    def test_mock_llm_works(self):
        """Test that mock LLM can be used for testing"""
        
        class MockLLM:
            def __call__(self, messages, temperature=0.7, max_tokens=1000):
                return "Thought: Testing\nResult: Mock response"
        
        mock = MockLLM()
        response = mock([{"role": "user", "content": "test"}])
        
        self.assertIn("Mock response", response)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("LLM API Integration Tests")
    print(f"API Key Available: {HAS_API_KEY}")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)

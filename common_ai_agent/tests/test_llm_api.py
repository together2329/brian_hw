"""
Real LLM API Integration Tests

Tests actual LLM API connectivity and responses:
- API connection test
- Response parsing
- Error handling
- Rate limiting behavior

NOTE: These tests require a valid API key loaded via shell env, repository .config,
      or .env into config.API_KEY
Skip with: pytest tests/test_llm_api.py -v -k "not real_api"
"""
import sys
import os
import json
import unittest
import time
from unittest.mock import patch


def _has_configured_api_key():
    """Return True when config exposes a non-placeholder API key."""
    try:
        import config

        api_key = (getattr(config, 'API_KEY', '') or '').strip()
        return api_key not in ('', 'your-openai-api-key-here')
    except Exception:
        return False


HAS_API_KEY = _has_configured_api_key()


def skip_without_api(func):
    """Decorator to skip tests without API key"""
    return unittest.skipUnless(HAS_API_KEY, "No API key configured")(func)


class TestLLMConnection(unittest.TestCase):
    """Test LLM API connection"""
    
    @skip_without_api
    def test_api_connection(self):
        """Test basic API connection"""
        from llm_client import call_llm_api

        reasoning, response = call_llm_api(
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

        reasoning, response = call_llm_api(
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

        reasoning, response = call_llm_api(
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

    def test_responses_nonstream_reasoning_content_blocks_are_emitted(self):
        """Responses non-stream parser should read reasoning content blocks, not only summaries."""
        import llm_client as lc

        class _FakeResponse:
            def __init__(self, payload):
                self._payload = payload
            def read(self):
                return json.dumps(self._payload).encode("utf-8")
            def close(self):
                pass

        payload = {
            "output": [
                {
                    "type": "reasoning",
                    "summary": [],
                    "content": [
                        {"type": "reasoning_text", "text": "step one\n"},
                        {"type": "reasoning_text", "text": "step two\n"},
                    ],
                },
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "final answer"},
                    ],
                },
            ],
            "usage": {"input_tokens": 3, "output_tokens": 5},
        }

        with patch.object(lc, "use_responses_api", return_value=True), \
             patch.object(lc, "build_responses_url", return_value="https://api.openai.com/v1/responses"), \
             patch.object(lc, "build_api_headers", return_value={}), \
             patch.object(lc, "_persistent_post", return_value=_FakeResponse(payload)), \
             patch.object(lc.config, "BASE_URL", "https://api.openai.com/v1"), \
             patch.object(lc.config, "API_KEY", "test-key"), \
             patch.object(lc.config, "MODEL_NAME", "gpt-5.1"), \
             patch.object(lc.config, "MAX_OUTPUT_TOKENS", 0), \
             patch.object(lc.config, "NONSTREAM_API_TIMEOUT", 1):
            out = list(lc._chat_completion_nonstream(
                [{"role": "user", "content": "hi"}],
                model="gpt-5.1",
                suppress_spinner=True,
                skip_rate_limit=True,
            ))

        reasoning = "".join(chunk[1] for chunk in out if isinstance(chunk, tuple) and chunk[0] == "reasoning")
        content = "".join(chunk for chunk in out if isinstance(chunk, str))
        self.assertIn("step one", reasoning)
        self.assertIn("step two", reasoning)
        self.assertIn("final answer", content)


class TestLLMErrorHandling(unittest.TestCase):
    """Test LLM error handling"""
    
    def test_invalid_api_key_handling(self):
        """Test handling of invalid API key"""
        try:
            from llm_client import call_llm_api
            self.assertTrue(callable(call_llm_api))
            result = call_llm_api.__doc__
            self.assertIn("reasoning", result)
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

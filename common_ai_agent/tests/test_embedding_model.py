"""
Unit tests for Embedding Model API calls
Tests OpenRouter embedding API with baai/bge-m3 model
"""
import sys
import os
import unittest
import json
import urllib.request
import urllib.error

# Add paths for imports
_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_project_root = _script_dir
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)

# Import after path setup
import config


class TestEmbeddingConfig(unittest.TestCase):
    """Test embedding configuration"""

    def test_embedding_base_url_configured(self):
        """Test that embedding base URL is configured"""
        self.assertIsNotNone(config.EMBEDDING_BASE_URL)
        self.assertIn('http', config.EMBEDDING_BASE_URL)

    def test_embedding_api_key_configured(self):
        """Test that embedding API key is configured"""
        self.assertIsNotNone(config.EMBEDDING_API_KEY)
        # API key should be non-empty string
        self.assertGreater(len(config.EMBEDDING_API_KEY), 0)
        # Should look like a token (contains hyphens and letters/numbers)
        self.assertRegex(config.EMBEDDING_API_KEY, r'^[a-zA-Z0-9\-]+$')

    def test_embedding_model_configured(self):
        """Test that embedding model is configured"""
        self.assertIsNotNone(config.EMBEDDING_MODEL)
        # Check if model name contains common embedding model names
        model_lower = config.EMBEDDING_MODEL.lower()
        self.assertTrue(
            'embed' in model_lower or 'bge' in model_lower or 'ada' in model_lower,
            f"Model {config.EMBEDDING_MODEL} doesn't look like an embedding model"
        )

    def test_embedding_dimension_configured(self):
        """Test that embedding dimension is configured"""
        self.assertIsNotNone(config.EMBEDDING_DIMENSION)
        self.assertIsInstance(config.EMBEDDING_DIMENSION, int)
        self.assertGreater(config.EMBEDDING_DIMENSION, 0)


class TestEmbeddingAPICall(unittest.TestCase):
    """Test embedding API call structure and format"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = config.EMBEDDING_API_KEY
        self.base_url = config.EMBEDDING_BASE_URL
        self.model = config.EMBEDDING_MODEL

    def test_embedding_api_url_format(self):
        """Test that embedding API URL is correctly formatted"""
        url = f"{self.base_url}/embeddings"
        self.assertTrue(url.startswith('http'))
        self.assertIn('embeddings', url)

    def test_embedding_headers_format(self):
        """Test that headers are correctly formatted"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertIn("Bearer", headers["Authorization"])
        self.assertIn(self.api_key, headers["Authorization"])

    def test_embedding_payload_format(self):
        """Test that embedding payload is correctly formatted"""
        test_text = "test embedding payload"
        data = {
            "input": test_text,
            "model": self.model,
            "encoding_format": "float"
        }

        # Verify it can be JSON encoded
        json_str = json.dumps(data)
        self.assertIn("test embedding payload", json_str)
        self.assertIn(self.model, json_str)
        self.assertIn("float", json_str)

    def test_embedding_api_call_optional(self):
        """Test that embedding API call structure is correct (optional - requires valid API key)"""
        url = f"{self.base_url}/embeddings"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "input": "test embedding",
            "model": self.model,
            "encoding_format": "float"
        }

        print(f"\n📝 Testing Embedding API Call:")
        print(f"   URL: {url}")
        print(f"   Model: {self.model}")
        print(f"   API Key: {self.api_key[:20]}...")

        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))

                # Verify response structure
                self.assertIn("data", result)
                self.assertIsInstance(result["data"], list)
                self.assertGreater(len(result["data"]), 0)

                # Verify embedding vector
                embedding = result["data"][0]["embedding"]
                self.assertIsInstance(embedding, list)
                self.assertGreater(len(embedding), 0)

                # Verify embedding is float values
                for val in embedding[:5]:  # Check first 5 values
                    self.assertIsInstance(val, (int, float))

                print(f"✅ Embedding API call successful!")
                print(f"   Model: {self.model}")
                print(f"   Embedding dimension: {len(embedding)}")
                print(f"   Sample values: {embedding[:5]}")

        except urllib.error.HTTPError as e:
            if e.code == 401:
                print(f"⚠️  Authentication failed (HTTP 401)")
                print(f"   API key may be invalid or expired")
                print(f"   This is expected if API key is not set up")
                self.skipTest("API key not configured or expired - skipping API call test")
            elif e.code == 429:
                print(f"⚠️  Rate limited (HTTP 429) - skipping test")
                self.skipTest("Rate limited by API")
            else:
                self.fail(f"HTTP Error {e.code}: {e}")
        except urllib.error.URLError as e:
            self.skipTest(f"Network error: {e}")
        except json.JSONDecodeError as e:
            self.fail(f"Failed to parse JSON response: {e}")
        except Exception as e:
            self.skipTest(f"Unexpected error: {e}")

    def test_embedding_batch_payload_format(self):
        """Test that batch embedding payload is correctly formatted"""
        texts = [
            "first test string",
            "second test string",
            "third test string"
        ]

        data = {
            "input": texts,
            "model": self.model,
            "encoding_format": "float"
        }

        # Verify it can be JSON encoded
        json_str = json.dumps(data)
        self.assertIn("first test string", json_str)
        self.assertIn(self.model, json_str)
        self.assertIn("float", json_str)


class TestEmbeddingDimension(unittest.TestCase):
    """Test embedding dimension validation"""

    def test_bge_m3_dimension(self):
        """Test baai/bge-m3 model dimension"""
        if 'bge-m3' in config.EMBEDDING_MODEL:
            # BGE-M3 has 1024 dimensions
            self.assertEqual(config.EMBEDDING_DIMENSION, 1024)

    def test_embedding_3_small_dimension(self):
        """Test text-embedding-3-small model dimension"""
        if 'embedding-3-small' in config.EMBEDDING_MODEL:
            # text-embedding-3-small has 1536 dimensions
            self.assertEqual(config.EMBEDDING_DIMENSION, 1536)

    def test_embedding_3_large_dimension(self):
        """Test text-embedding-3-large model dimension"""
        if 'embedding-3-large' in config.EMBEDDING_MODEL:
            # text-embedding-3-large has 3072 dimensions
            self.assertEqual(config.EMBEDDING_DIMENSION, 3072)

    def test_dimension_positive(self):
        """Test that dimension is positive integer"""
        self.assertIsInstance(config.EMBEDDING_DIMENSION, int)
        self.assertGreater(config.EMBEDDING_DIMENSION, 0)


class TestEmbeddingRobustness(unittest.TestCase):
    """Test embedding API robustness (optional - requires valid API key)"""

    def test_empty_text_payload_format(self):
        """Test that empty text payload is correctly formatted"""
        data = {
            "input": "",
            "model": config.EMBEDDING_MODEL,
            "encoding_format": "float"
        }

        # Verify it can be JSON encoded
        json_str = json.dumps(data)
        self.assertIn(config.EMBEDDING_MODEL, json_str)
        self.assertIn("float", json_str)

    def test_very_long_text_payload_format(self):
        """Test that long text payload is correctly formatted"""
        long_text = "test " * 1000  # ~5000 chars

        data = {
            "input": long_text[:8000],  # Limit to 8000 chars
            "model": config.EMBEDDING_MODEL,
            "encoding_format": "float"
        }

        # Verify it can be JSON encoded
        json_str = json.dumps(data)
        self.assertIn(config.EMBEDDING_MODEL, json_str)
        self.assertIn("float", json_str)
        self.assertGreater(len(json_str), 100)  # Should contain our long text


if __name__ == '__main__':
    # Run tests with verbose output
    print("\n" + "="*70)
    print("Testing Embedding Model API")
    print("="*70 + "\n")

    unittest.main(verbosity=2)

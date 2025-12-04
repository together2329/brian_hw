"""
Test embedding configuration from config.py
"""
import config

print("="*70)
print("Embedding Configuration Test")
print("="*70)
print()

print("Configuration values from config.py:")
print("-" * 70)
print(f"EMBEDDING_BASE_URL:    {config.EMBEDDING_BASE_URL}")
print(f"EMBEDDING_API_KEY:     {config.EMBEDDING_API_KEY[:20]}..." if len(config.EMBEDDING_API_KEY) > 20 else f"EMBEDDING_API_KEY:     {config.EMBEDDING_API_KEY}")
print(f"EMBEDDING_MODEL:       {config.EMBEDDING_MODEL}")
print(f"EMBEDDING_DIMENSION:   {config.EMBEDDING_DIMENSION}")
print()

print("="*70)
print("Test: Get single embedding using config settings")
print("="*70)
print()

import urllib.request
import json

def get_embedding_from_config(text):
    """Get embedding using config settings"""
    url = f"{config.EMBEDDING_BASE_URL}/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.EMBEDDING_API_KEY}"
    }
    data = {
        "input": text,
        "model": config.EMBEDDING_MODEL,
        "encoding_format": "float"
    }
    json_data = json.dumps(data).encode('utf-8')
    request = urllib.request.Request(url, data=json_data, headers=headers, method='POST')

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['data'][0]['embedding']

test_text = "Hello, this is a test"
print(f"Test text: \"{test_text}\"")
print("Calling API...", end=" ", flush=True)

try:
    embedding = get_embedding_from_config(test_text)
    print("✓ Success")
    print()
    print(f"Embedding dimension: {len(embedding)}")
    print(f"Expected dimension:  {config.EMBEDDING_DIMENSION}")
    print()

    if len(embedding) == config.EMBEDDING_DIMENSION:
        print("✅ Dimension matches configuration!")
    else:
        print("⚠️  Dimension mismatch!")

    print()
    print(f"First 10 values: {embedding[:10]}")

except Exception as e:
    print(f"✗ Failed: {e}")

print()
print("="*70)
print("Configuration test complete!")
print("="*70)

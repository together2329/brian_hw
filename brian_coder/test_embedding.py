"""
Test OpenAI Embedding API with zero-dependency (urllib only)
"""
import urllib.request
import urllib.error
import json
import math
import os

# Load config to get API key
import config

def get_embedding(text, model=None):
    """
    Get embedding vector from OpenAI API using urllib (zero-dependency).

    Args:
        text: Input text to embed
        model: OpenAI embedding model name (default: from config)

    Returns:
        List of floats (embedding vector)
    """
    if model is None:
        model = config.EMBEDDING_MODEL

    url = f"{config.EMBEDDING_BASE_URL}/embeddings"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.EMBEDDING_API_KEY}"
    }

    data = {
        "input": text,
        "model": model,
        "encoding_format": "float"
    }

    json_data = json.dumps(data).encode('utf-8')

    request = urllib.request.Request(
        url,
        data=json_data,
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            embedding = result['data'][0]['embedding']
            return embedding
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {error_body}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise


def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors (pure Python).

    Args:
        vec1, vec2: Lists of floats (same length)

    Returns:
        Float between -1 and 1 (1 = identical, 0 = orthogonal, -1 = opposite)
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same length")

    # Dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))

    # Magnitudes
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    # Cosine similarity
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def main():
    print("="*70)
    print("OpenAI Embedding API Test (Zero-Dependency)")
    print("="*70)
    print()

    # Test cases
    test_texts = [
        "The user prefers snake_case for variable names",
        "Always use snake_case for naming variables",
        "The weather is sunny today",
        "I like to eat pizza for dinner",
        "Variables should be named using camelCase convention"
    ]

    print("Step 1: Generate embeddings for test texts")
    print("-" * 70)

    embeddings = []
    for i, text in enumerate(test_texts):
        print(f"\n[{i+1}] Text: \"{text}\"")
        print(f"    Calling OpenAI API...", end=" ", flush=True)

        try:
            embedding = get_embedding(text)
            embeddings.append(embedding)
            print(f"✓ Success")
            print(f"    Embedding dimension: {len(embedding)}")
            print(f"    First 5 values: {embedding[:5]}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            return

    print("\n" + "="*70)
    print("Step 2: Calculate similarity matrix")
    print("="*70)
    print()

    # Calculate all pairwise similarities
    n = len(embeddings)
    print(f"{'':60s} | ", end="")
    for i in range(n):
        print(f"[{i+1}]   ", end="")
    print()
    print("-" * 70 + "-" * (n * 6))

    for i in range(n):
        # Show text preview (truncated)
        text_preview = test_texts[i][:55] + "..." if len(test_texts[i]) > 55 else test_texts[i]
        print(f"[{i+1}] {text_preview:55s} | ", end="")

        for j in range(n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            print(f"{sim:5.3f} ", end="")
        print()

    print("\n" + "="*70)
    print("Step 3: Analyze results")
    print("="*70)
    print()

    # Find most similar pairs (excluding self-similarity)
    similarities = []
    for i in range(n):
        for j in range(i+1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append((i, j, sim))

    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[2], reverse=True)

    print("Most similar pairs:")
    for i, j, sim in similarities[:3]:
        print(f"\n  Similarity: {sim:.4f}")
        print(f"    [{i+1}] \"{test_texts[i]}\"")
        print(f"    [{j+1}] \"{test_texts[j]}\"")

    print("\n" + "="*70)
    print("Expected Results:")
    print("="*70)
    print("""
  [1] and [2] should have HIGH similarity (~0.85-0.95)
    - Both about snake_case preference

  [1] and [5] should have MEDIUM similarity (~0.65-0.75)
    - Both about naming conventions (but different styles)

  [1] and [3]/[4] should have LOW similarity (~0.40-0.60)
    - Completely different topics (weather, food)

  [3] and [4] should have MEDIUM similarity (~0.50-0.70)
    - Both casual everyday topics (but different)
    """)

    print("="*70)
    print("Test Complete!")
    print("="*70)


if __name__ == "__main__":
    main()

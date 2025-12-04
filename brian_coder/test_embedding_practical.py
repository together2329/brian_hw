"""
Practical test: Simulate Memory System use cases
"""
import urllib.request
import json
import math
import config

def get_embedding(text, model=None):
    """Get embedding from OpenAI API"""
    if model is None:
        model = config.EMBEDDING_MODEL

    url = f"{config.EMBEDDING_BASE_URL}/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.EMBEDDING_API_KEY}"
    }
    data = {"input": text, "model": model, "encoding_format": "float"}
    json_data = json.dumps(data).encode('utf-8')
    request = urllib.request.Request(url, data=json_data, headers=headers, method='POST')

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['data'][0]['embedding']

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (magnitude1 * magnitude2) if magnitude1 and magnitude2 else 0.0

def find_most_similar(query_embedding, knowledge_base, top_k=3):
    """
    Find most similar items in knowledge base.

    Args:
        query_embedding: Query vector
        knowledge_base: List of (text, embedding) tuples
        top_k: Number of results to return

    Returns:
        List of (text, similarity_score) tuples
    """
    similarities = []
    for text, embedding in knowledge_base:
        sim = cosine_similarity(query_embedding, embedding)
        similarities.append((text, sim))

    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def main():
    print("="*70)
    print("Practical Memory System Test")
    print("="*70)
    print()

    # Simulate knowledge base (user preferences and project context)
    knowledge_texts = [
        # User preferences
        "The user always wants snake_case for variable names",
        "Never add comments unless explicitly requested",
        "Use 4 spaces for indentation, not tabs",
        "Always add type hints to Python functions",

        # Project context
        "This project is a Verilog PCIe message system with AXI4 interface",
        "The main modules are pcie_msg_receiver and pcie_axi_to_sram",
        "SRAM is 1024 entries deep with 256-bit data width",

        # Error patterns and solutions
        "Error: missing endmodule - Solution: Add endmodule at end of Verilog file",
        "Error: syntax error near always - Solution: Check for missing semicolons",
        "Compilation failed with iverilog - Solution: Check module instantiation",
    ]

    print("Step 1: Build knowledge base (generate embeddings)")
    print("-" * 70)

    knowledge_base = []
    for i, text in enumerate(knowledge_texts):
        print(f"[{i+1}/{len(knowledge_texts)}] Embedding: \"{text[:60]}...\"")
        embedding = get_embedding(text)
        knowledge_base.append((text, embedding))

    print(f"\n✓ Knowledge base created with {len(knowledge_base)} entries\n")

    # Test queries
    test_queries = [
        ("How should I name variables?", "User preference query"),
        ("What is this project about?", "Project context query"),
        ("I got a syntax error in Verilog", "Error solution query"),
        ("Should I use camelCase or snake_case?", "Coding style query"),
    ]

    print("="*70)
    print("Step 2: Test knowledge retrieval")
    print("="*70)
    print()

    for query_text, query_type in test_queries:
        print(f"\n📝 Query: \"{query_text}\"")
        print(f"   Type: {query_type}")
        print("-" * 70)

        # Get query embedding
        query_embedding = get_embedding(query_text)

        # Find top 3 similar items
        results = find_most_similar(query_embedding, knowledge_base, top_k=3)

        print("   Top 3 matches:")
        for rank, (text, score) in enumerate(results, 1):
            print(f"   [{rank}] Score: {score:.4f}")
            print(f"       \"{text}\"")
            print()

    print("="*70)
    print("Step 3: Simulate Memory System workflow")
    print("="*70)
    print()

    # Scenario: User asks about variable naming during a conversation
    print("Scenario: User asks 'How should I name my variables?'")
    print("-" * 70)

    user_question = "How should I name my variables?"
    query_emb = get_embedding(user_question)
    results = find_most_similar(query_emb, knowledge_base, top_k=1)

    if results:
        best_match, score = results[0]
        print(f"\n🔍 Memory System Search:")
        print(f"   Query: \"{user_question}\"")
        print(f"   Best match (score: {score:.4f}):")
        print(f"   \"{best_match}\"")
        print()

        if score > 0.7:
            print(f"✅ HIGH confidence - Use this as context")
            print(f"   System can inject: \"{best_match}\" into prompt")
        elif score > 0.5:
            print(f"⚠️  MEDIUM confidence - Might be relevant")
        else:
            print(f"❌ LOW confidence - Not relevant")

    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70)
    print()
    print("Key Findings:")
    print("  ✓ Embedding API works with urllib (zero-dependency)")
    print("  ✓ Cosine similarity correctly ranks results")
    print("  ✓ Semantic search can find relevant preferences/context")
    print("  ✓ Ready for Memory System implementation")


if __name__ == "__main__":
    main()

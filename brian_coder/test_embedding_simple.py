"""
Simple Embedding Test

Tests:
- Get embeddings for sample texts
- Calculate cosine similarity
- Verify embeddings work correctly
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from graph_lite import GraphLite


def test_embedding_simple():
    """Simple embedding test with sample texts"""
    print("\n" + "="*60)
    print("Simple Embedding Test")
    print("="*60 + "\n")

    # Create graph instance (has embedding methods)
    graph = GraphLite(memory_dir=".test_embedding_simple")

    # Sample texts
    texts = [
        "Verilog counter module with reset",
        "Counter design in Verilog",
        "AXI protocol handshake signals",
        "PCIe TLP message format",
        "Python list comprehension"
    ]

    print("📝 Getting embeddings for sample texts...\n")

    embeddings = []
    for i, text in enumerate(texts, 1):
        try:
            emb = graph.get_embedding(text)
            embeddings.append(emb)
            print(f"✓ Text {i}: \"{text[:40]}...\"")
            print(f"  Embedding dimension: {len(emb)}")
        except Exception as e:
            print(f"❌ Failed to get embedding for text {i}: {e}")
            return

    print("\n" + "="*60)
    print("Similarity Matrix")
    print("="*60 + "\n")

    # Calculate similarities
    print("Comparing all text pairs:\n")

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            similarity = graph.cosine_similarity(embeddings[i], embeddings[j])

            # Color code by similarity
            if similarity > 0.8:
                color = "🟢"  # Very similar
            elif similarity > 0.6:
                color = "🟡"  # Somewhat similar
            else:
                color = "🔴"  # Not similar

            print(f"{color} Similarity: {similarity:.3f}")
            print(f"  Text {i+1}: {texts[i][:40]}...")
            print(f"  Text {j+1}: {texts[j][:40]}...")
            print()

    print("="*60)
    print("Expected behavior:")
    print("  🟢 Text 1 & 2 should be VERY similar (both about Verilog counter)")
    print("  🔴 Text 1 & 5 should be NOT similar (Verilog vs Python)")
    print("="*60 + "\n")

    # Cleanup
    graph.clear()

    print("✅ Test complete!\n")


if __name__ == "__main__":
    try:
        test_embedding_simple()
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

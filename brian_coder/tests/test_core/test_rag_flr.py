
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'brian_coder')))

from brian_coder.core.hybrid_rag import get_hybrid_rag
from brian_coder.src import config

def test_flr():
    print("Testing HybridRAG for query: 'FLR'")
    print(f"Config HYBRID_ALPHA: {getattr(config, 'HYBRID_ALPHA', 'Unknown')}")
    
    hybrid = get_hybrid_rag()
    # Ensure we use the instance that respected the config import
    print(f"Hybrid Weights: Emb={hybrid.alpha_embedding:.2f}, BM25={hybrid.alpha_bm25:.2f}")

    results = hybrid.search("FLR", limit=3)

    if not results:
        print("❌ No results found for 'FLR'.")
        return

    top_score = results[0].score
    print(f"\nTop Result Score: {top_score:.4f}")
    print(f"Content Preview: {results[0].content[:100]}...")
    
    threshold = getattr(config, 'SMART_RAG_HIGH_THRESHOLD', 0.8)
    
    if top_score >= threshold:
        print(f"✅ SUCCESS: Score {top_score:.4f} >= {threshold} (Direct Use)")
    else:
        print(f"⚠️ WARNING: Score {top_score:.4f} < {threshold} (Needs Judge)")

if __name__ == "__main__":
    test_flr()

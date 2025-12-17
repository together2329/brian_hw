#!/usr/bin/env python3
"""
Analyze RRF score calculation to understand why scores are low
"""
import os
import sys

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import config
config.DEBUG_MODE = False

from core.hybrid_rag import get_hybrid_rag
from core.rag_db import get_rag_db
from lib.display import Color

def main():
    print(Color.action("🔍 RRF Score Calculation Analysis"))

    hybrid = get_hybrid_rag()
    rag_db = get_rag_db()

    query = "TLP header format"
    print(f"\n{Color.info('Query:')} \"{query}\"")

    # Get raw results from each source
    print(f"\n{Color.action('Step 1: Raw Embedding Scores')}")
    embedding_results = rag_db.search(query, limit=5)
    for i, (score, chunk) in enumerate(embedding_results[:3], 1):
        print(f"  {i}. Score: {score:.6f} | {chunk.content[:60]}...")

    print(f"\n{Color.action('Step 2: Raw BM25 Scores')}")
    if hybrid.graph_lite:
        bm25_results = hybrid.graph_lite.bm25_search(query, limit=5)
        for i, (score, node) in enumerate(bm25_results[:3], 1):
            content = node.data.get("content", "")[:60]
            print(f"  {i}. Score: {score:.6f} | {content}...")
    else:
        print(Color.warning("  GraphLite not available"))
        bm25_results = []

    # Show RRF calculation
    print(f"\n{Color.action('Step 3: RRF Calculation')}")
    print(f"  RRF Formula: score = weight × 1/(k + rank)")
    print(f"  k = 60 (constant)")
    print(f"  Weights: Embedding=0.4, BM25=0.3, Graph=0.3")

    print(f"\n  Rank 1 scores:")
    emb_rrf = 0.4 * (1.0 / (60 + 1))
    bm25_rrf = 0.3 * (1.0 / (60 + 1))
    print(f"    Embedding: 0.4 × 1/61 = {emb_rrf:.6f}")
    print(f"    BM25:      0.3 × 1/61 = {bm25_rrf:.6f}")
    print(f"    Combined:  {emb_rrf + bm25_rrf:.6f}")

    print(f"\n  Rank 2 scores:")
    emb_rrf2 = 0.4 * (1.0 / (60 + 2))
    bm25_rrf2 = 0.3 * (1.0 / (60 + 2))
    print(f"    Embedding: 0.4 × 1/62 = {emb_rrf2:.6f}")
    print(f"    BM25:      0.3 × 1/62 = {bm25_rrf2:.6f}")

    # Problem analysis
    print(f"\n{Color.error('❌ PROBLEM IDENTIFIED:')}")
    print(f"  1. RRF ignores raw score magnitude")
    print(f"     - Embedding score 1.96 → RRF 0.0066")
    print(f"     - BM25 score 11.986 → RRF 0.0049")
    print(f"     - BM25's 6x advantage is lost!")

    print(f"\n  2. Only rank matters in RRF")
    print(f"     - Top result from any source: 1/(60+1) = 0.0164")
    print(f"     - All top results converge to ~0.011")

    # Solution
    print(f"\n{Color.action('✅ SOLUTIONS:')}")
    print(f"  Option 1: Weighted Sum (instead of RRF)")
    print(f"    - Normalize each source to [0,1]")
    print(f"    - Apply weights: 0.4*emb + 0.3*bm25 + 0.3*graph")
    print(f"    - Preserves raw score differences")

    print(f"\n  Option 2: Adjust RRF k parameter")
    print(f"    - Current k=60 → max score ~0.016")
    print(f"    - Lower k=10 → max score ~0.09")
    print(f"    - Higher k=100 → max score ~0.010")

    print(f"\n  Option 3: Hybrid scoring")
    print(f"    - RRF for rank fusion")
    print(f"    - Boost by raw score: final = RRF × log(raw_score)")

    # Show what weighted sum would look like
    if embedding_results and bm25_results:
        print(f"\n{Color.info('Example with Weighted Sum (Option 1):')}")

        # Get top result from each
        emb_top_score = embedding_results[0][0]
        bm25_top_score = bm25_results[0][0]

        # Normalize to [0,1]
        emb_norm = emb_top_score / max(r[0] for r in embedding_results)
        bm25_norm = bm25_top_score / max(r[0] for r in bm25_results)

        # Weighted sum
        weighted_score = 0.4 * emb_norm + 0.3 * bm25_norm

        print(f"  Embedding: {emb_top_score:.4f} → normalized: {emb_norm:.4f}")
        print(f"  BM25:      {bm25_top_score:.4f} → normalized: {bm25_norm:.4f}")
        print(f"  Weighted:  0.4×{emb_norm:.4f} + 0.3×{bm25_norm:.4f} = {weighted_score:.4f}")
        print(f"  vs RRF:    {emb_rrf + bm25_rrf:.4f}")
        print(f"  Difference: Weighted Sum is {weighted_score/(emb_rrf + bm25_rrf):.1f}x higher!")

if __name__ == "__main__":
    main()

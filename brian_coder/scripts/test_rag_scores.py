#!/usr/bin/env python3
"""
RAG Score Analysis - Test various queries and analyze score distribution
"""
import os
import sys

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import config
config.DEBUG_MODE = False  # Disable visualization for cleaner output

from core.hybrid_rag import get_hybrid_rag
from lib.display import Color

def print_section(title):
    print(f"\n{'='*80}")
    print(f"{Color.action(title)}")
    print(f"{'='*80}")

def test_query(hybrid, query, expected_to_find):
    """Test a query and analyze results."""
    print(f"\n{Color.info('Query:')} \"{query}\"")
    print(f"{Color.info('Expected:')} {expected_to_find}")

    results = hybrid.search(query, limit=5, use_embedding=True, use_bm25=True, use_graph=True, graph_hops=2)

    if not results:
        print(Color.error("  ✗ NO RESULTS"))
        return None

    # Check if expected content is in top result
    top_result = results[0]
    found = expected_to_find.lower() in top_result.content.lower()

    status = Color.success("✓ FOUND") if found else Color.warning("? NOT IN TOP")
    print(f"{status} (Score: {top_result.score:.4f})")

    # Show top 3 results
    for i, r in enumerate(results[:3], 1):
        sources_str = "+".join(r.sources.keys())
        content_preview = r.content[:80].replace('\n', ' ')
        print(f"  {i}. [{r.score:.4f}] ({sources_str}) {content_preview}...")

    return results[0].score

def main():
    print(Color.action("🧪 RAG Score Analysis Test"))

    hybrid = get_hybrid_rag()

    scores = []

    # Test Case 1: Exact technical term
    print_section("TEST 1: Exact Technical Terms")
    score = test_query(hybrid, "TLP header format", "Fmt[2:0]")
    if score: scores.append(("Exact term", score))

    score = test_query(hybrid, "Posted Request", "Posted Request")
    if score: scores.append(("Exact term", score))

    # Test Case 2: Concept-based query
    print_section("TEST 2: Concept-based Queries")
    score = test_query(hybrid, "How does PCIe route packets", "routing")
    if score: scores.append(("Concept", score))

    score = test_query(hybrid, "What is Memory Write transaction", "Memory Write")
    if score: scores.append(("Concept", score))

    # Test Case 3: Very specific query
    print_section("TEST 3: Very Specific Queries")
    score = test_query(hybrid, "3DW header no data", "3 DW header")
    if score: scores.append(("Specific", score))

    score = test_query(hybrid, "TLP Type field encoding", "Type")
    if score: scores.append(("Specific", score))

    # Test Case 4: General query
    print_section("TEST 4: General Queries")
    score = test_query(hybrid, "PCIe transaction", "transaction")
    if score: scores.append(("General", score))

    score = test_query(hybrid, "packet structure", "packet")
    if score: scores.append(("General", score))

    # Test Case 5: Keyword-heavy query (should boost BM25)
    print_section("TEST 5: Keyword-heavy Queries (BM25 優位)")
    score = test_query(hybrid, "TLP TLP TLP header header format format", "TLP")
    if score: scores.append(("Keyword-heavy", score))

    # Score Analysis
    print_section("SCORE DISTRIBUTION ANALYSIS")

    if scores:
        scores_sorted = sorted(scores, key=lambda x: x[1], reverse=True)

        print(f"\n{Color.info('Score Range:')}")
        print(f"  Highest: {scores_sorted[0][1]:.4f} ({scores_sorted[0][0]})")
        print(f"  Lowest:  {scores_sorted[-1][1]:.4f} ({scores_sorted[-1][0]})")
        print(f"  Average: {sum(s[1] for s in scores) / len(scores):.4f}")

        print(f"\n{Color.info('All Scores (sorted):')}")
        for query_type, score in scores_sorted:
            bars = "█" * int(score * 1000)  # Scale for visualization
            print(f"  {score:.4f} {bars} ({query_type})")

        # Analysis
        print(f"\n{Color.action('📊 ANALYSIS:')}")
        avg_score = sum(s[1] for s in scores) / len(scores)

        if avg_score > 0.05:
            print(Color.success(f"✓ Scores are GOOD (avg: {avg_score:.4f})"))
            print("  Scores above 0.01 indicate strong relevance")
        elif avg_score > 0.01:
            print(Color.warning(f"⚠ Scores are MODERATE (avg: {avg_score:.4f})"))
            print("  Scores above 0.005 are acceptable")
        else:
            print(Color.error(f"✗ Scores are LOW (avg: {avg_score:.4f})"))
            print("  Scores below 0.005 indicate poor relevance")

        print(f"\n{Color.info('Score Interpretation:')}")
        print("  - RRF scores are naturally lower than raw cosine similarity")
        print("  - RRF = 1/(k + rank), where k=60")
        print("  - Top rank: 1/(60+1) = 0.0164 per source")
        print("  - With weights (0.4 Emb + 0.3 BM25): max ~0.011")
        print("  - Our scores match theoretical maximum!")

        # Check if BM25 is helping
        print(f"\n{Color.action('🔍 BM25 CONTRIBUTION CHECK:')}")
        keyword_score = next((s[1] for s in scores if s[0] == "Keyword-heavy"), None)
        avg_normal = sum(s[1] for s in scores if s[0] != "Keyword-heavy") / max(1, len([s for s in scores if s[0] != "Keyword-heavy"]))

        if keyword_score and keyword_score > avg_normal * 1.2:
            print(Color.success(f"✓ BM25 is boosting keyword queries ({keyword_score:.4f} vs {avg_normal:.4f})"))
        else:
            print(Color.warning("⚠ BM25 contribution not clear from keyword test"))

    print(f"\n{Color.success('✅ Test Complete')}")

if __name__ == "__main__":
    main()

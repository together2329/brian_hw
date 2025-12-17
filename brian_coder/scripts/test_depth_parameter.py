#!/usr/bin/env python3
"""
Test depth parameter effect on search results

Compares depth=1 (shallow) vs depth=5 (deep) graph traversal
to verify that higher depth finds more related documents.
"""
import os
import sys

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import config
config.DEBUG_MODE = True  # Enable visualization

from core.hybrid_rag import get_hybrid_rag
from lib.display import Color

def test_depth_comparison(query, depth_values=[1, 2, 3, 5]):
    """Test same query with different depth values."""
    print(f"\n{'='*80}")
    print(Color.action(f"Query: \"{query}\""))
    print(f"{'='*80}\n")

    hybrid = get_hybrid_rag()
    results_by_depth = {}

    for depth in depth_values:
        print(Color.info(f"Testing with depth={depth}"))
        print(f"{'-'*80}")

        results = hybrid.search(
            query,
            limit=10,
            use_embedding=True,
            use_bm25=True,
            use_graph=True,
            graph_hops=depth
        )

        results_by_depth[depth] = results

        print(f"Found {len(results)} results")
        if results:
            print(f"Top score: {results[0].score:.4f}")
            print(f"Score range: {results[-1].score:.4f} - {results[0].score:.4f}\n")

        # Show top 3 results
        for i, r in enumerate(results[:3], 1):
            sources_str = "+".join(r.sources.keys())
            distance_str = f"dist={r.distance}" if r.distance > 0 else "direct"
            content_preview = r.content[:60].replace('\n', ' ')
            print(f"  {i}. [{r.score:.4f}] ({sources_str}) {distance_str}")
            print(f"     {content_preview}...\n")

    # Analysis
    print(f"\n{'='*80}")
    print(Color.action("DEPTH COMPARISON ANALYSIS"))
    print(f"{'='*80}\n")

    # Count unique results at each depth
    print(Color.info("Unique Results Count:"))
    for depth in depth_values:
        unique_ids = set(r.id for r in results_by_depth[depth])
        print(f"  depth={depth}: {len(unique_ids)} unique results")

    # Check if higher depth finds more results
    print(f"\n{Color.info('Result Set Overlap:')}")
    depth1_ids = set(r.id for r in results_by_depth[depth_values[0]])
    for depth in depth_values[1:]:
        depth_n_ids = set(r.id for r in results_by_depth[depth])
        new_results = depth_n_ids - depth1_ids
        print(f"  depth={depth} vs depth={depth_values[0]}: +{len(new_results)} new results")

    # Distance distribution
    print(f"\n{Color.info('Distance Distribution (Graph Results):')}")
    for depth in depth_values:
        distances = [r.distance for r in results_by_depth[depth] if r.distance > 0]
        if distances:
            max_dist = max(distances)
            avg_dist = sum(distances) / len(distances)
            print(f"  depth={depth}: {len(distances)} graph results, "
                  f"max_distance={max_dist}, avg_distance={avg_dist:.2f}")
        else:
            print(f"  depth={depth}: no graph results")

    # Score impact
    print(f"\n{Color.info('Score Distribution:')}")
    for depth in depth_values:
        scores = [r.score for r in results_by_depth[depth]]
        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"  depth={depth}: avg_score={avg_score:.4f}, "
                  f"range=[{min(scores):.4f}, {max(scores):.4f}]")

def main():
    print(Color.action("🧪 Depth Parameter Test"))
    print("Testing how depth parameter affects search results\n")

    # Test Case 1: Specific technical term
    test_depth_comparison(
        query="TLP header format",
        depth_values=[1, 2, 3, 5]
    )

    # Test Case 2: Concept-based query
    print(f"\n\n{'#'*80}")
    test_depth_comparison(
        query="PCIe transaction routing",
        depth_values=[1, 2, 3, 5]
    )

    # Conclusion
    print(f"\n\n{'='*80}")
    print(Color.action("📊 CONCLUSION"))
    print(f"{'='*80}\n")

    print(Color.info("Expected Behavior:"))
    print("  1. Higher depth → More results (especially from graph traversal)")
    print("  2. Higher depth → Lower average scores (more distant nodes)")
    print("  3. Higher depth → Greater max_distance in graph results")
    print("  4. depth=1: Only direct matches")
    print("  5. depth=5: Includes nodes up to 5 hops away")

    print(f"\n{Color.info('Usage Recommendations:')}")
    print("  • depth=1-2: Quick searches, narrow focus")
    print("  • depth=3-4: Comprehensive searches (recommended default)")
    print("  • depth=5: Deep exploration, find all related content")

    print(f"\n{Color.success('✅ Test Complete')}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
RAG Quality Testing Script
Tests various RAG features with real queries
"""
import os
import sys

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import config
config.DEBUG_MODE = True  # Enable debug visualization

from core.rag_db import get_rag_db
from core.hybrid_rag import create_hybrid_rag
from core.tools import rag_search, rag_explore
from lib.display import Color

def print_section(title):
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")

def print_results(results, title="Results"):
    print(Color.action(f"\n📋 {title}"))
    if not results:
        print(Color.warning("  (No results)"))
        return

    for i, r in enumerate(results[:5]):
        print(f"\n{i+1}. Score: {r.score:.4f} | Distance: {r.distance}")
        print(f"   ID: {r.id}")
        print(f"   Content: {r.content[:150]}...")
        if r.sources:
            sources = ", ".join([f"{k}:{v:.2f}" for k, v in r.sources.items()])
            print(f"   Sources: {sources}")

def test_basic_search():
    """Test 1: Basic search (depth=2, default)"""
    print_section("TEST 1: Basic Search (depth=2)")

    rag_db = get_rag_db()
    hybrid = create_hybrid_rag(rag_db=rag_db)
    query = "PCIe TLP header format"

    print(Color.info(f"Query: '{query}'"))
    print(Color.info(f"Parameters: limit=5, depth=2"))

    results = hybrid.search(query, limit=5, use_embedding=True, use_bm25=True, use_graph=True, graph_hops=2)
    print_results(results, "Basic Search Results")

    return results

def test_deep_search():
    """Test 2: Deep search (depth=4)"""
    print_section("TEST 2: Deep Search (depth=4)")

    rag_db = get_rag_db()
    hybrid = create_hybrid_rag(rag_db=rag_db)
    query = "PCIe TLP header format"

    print(Color.info(f"Query: '{query}'"))
    print(Color.info(f"Parameters: limit=10, depth=4"))

    results = hybrid.search(query, limit=10, use_embedding=True, use_bm25=True, use_graph=True, graph_hops=4)
    print_results(results, "Deep Search Results (depth=4)")

    return results

def test_follow_references():
    """Test 3: Follow references"""
    print_section("TEST 3: Follow References")

    query = "PCIe TLP header format"

    print(Color.info(f"Query: '{query}'"))
    print(Color.info(f"Parameters: categories='spec', limit=5, depth=2, follow_references=True"))

    # Using rag_search tool which has follow_references parameter
    result_text = rag_search(query, categories="spec", limit=5, depth=2, follow_references=True)

    print(Color.action("\n📋 Follow References Results"))
    print(result_text[:1000])
    print("...")

def test_rag_explore():
    """Test 4: RAG Explore"""
    print_section("TEST 4: RAG Explore")

    # First, get a starting node ID from basic search
    rag_db = get_rag_db()
    hybrid = create_hybrid_rag(rag_db=rag_db)
    initial_results = hybrid.search("TLP header", limit=1)

    if not initial_results:
        print(Color.error("No initial results to explore from"))
        return

    start_node = initial_results[0].id
    print(Color.info(f"Starting node: {start_node}"))
    print(Color.info(f"Parameters: max_depth=3, max_results=10, explore_type='related'"))

    result_text = rag_explore(start_node=start_node, max_depth=3, max_results=10, explore_type="related")

    print(Color.action("\n📋 Explore Results"))
    print(result_text[:1000])
    print("...")

def compare_depth_effect(basic_results, deep_results):
    """Compare depth=2 vs depth=4"""
    print_section("ANALYSIS: Depth Effect Comparison")

    print(f"Basic (depth=2): {len(basic_results)} results")
    print(f"Deep (depth=4):  {len(deep_results)} results")

    basic_ids = set(r.id for r in basic_results)
    deep_ids = set(r.id for r in deep_results)

    new_in_deep = deep_ids - basic_ids
    print(f"\nNew results in deep search: {len(new_in_deep)}")

    if new_in_deep:
        print("\nNew IDs found with depth=4:")
        for i, id in enumerate(list(new_in_deep)[:5], 1):
            result = next(r for r in deep_results if r.id == id)
            print(f"  {i}. {id} (distance={result.distance}, score={result.score:.4f})")

def main():
    print(Color.action("🧪 RAG Quality Testing"))
    print(Color.system("Testing RAG system with transaction_layer.md"))

    # Run tests
    basic_results = test_basic_search()
    deep_results = test_deep_search()
    test_follow_references()
    test_rag_explore()

    # Analysis
    compare_depth_effect(basic_results, deep_results)

    print_section("✅ Testing Complete")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick test of RAG components (BM25, Graph, Embedding)
"""
import os
import sys

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import config
config.DEBUG_MODE = True

from core.rag_db import get_rag_db
from core.hybrid_rag import get_hybrid_rag
from lib.display import Color

def main():
    print(Color.action("🔧 RAG Components Test"))

    # Get instances
    print(Color.info("\n1. Initializing components..."))
    rag_db = get_rag_db()
    hybrid = get_hybrid_rag()

    print(Color.success(f"   ✓ RAG DB: {len(rag_db.chunks)} chunks"))
    print(Color.success(f"   ✓ HybridRAG initialized"))

    if hybrid.graph_lite:
        print(Color.success(f"   ✓ GraphLite: {len(hybrid.graph_lite.nodes)} nodes"))
    else:
        print(Color.warning("   ✗ GraphLite: None"))

    if hybrid.spec_graph:
        stats = hybrid.spec_graph.get_stats()
        print(Color.success(f"   ✓ SpecGraph: {stats['total_nodes']} nodes, {stats['total_edges']} edges"))
    else:
        print(Color.warning("   ✗ SpecGraph: None"))

    # Test search
    print(Color.info("\n2. Testing search with all components..."))
    query = "TLP header format"
    print(Color.info(f"   Query: '{query}'"))

    results = hybrid.search(query, limit=3, use_embedding=True, use_bm25=True, use_graph=True, graph_hops=2)

    print(Color.action("\n📋 Results:"))
    for i, r in enumerate(results, 1):
        sources = [k for k in r.sources.keys()]
        print(f"{i}. Score: {r.score:.4f} | Sources: {', '.join(sources)}")
        print(f"   {r.content[:80]}...")

    print(Color.success("\n✅ Component test complete!"))

if __name__ == "__main__":
    main()

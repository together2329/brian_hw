
import sys
import os

# Add src and core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import config
config.DEBUG_MODE = True  # Force debug mode for internal printing

from rag_db import RAGDatabase
from graph_lite import GraphLite
from spec_graph import SpecGraph, build_spec_graph_from_chunks
from hybrid_rag import HybridRAG

def main():
    query = "TLP Header Format"
    print(f"\n🔍 DEMONSTRATION: Searching for '{query}'\n")
    
    # 1. Initialize Components
    print("1️⃣  Initializing System...")
    rag_db = RAGDatabase()
    graph_lite = GraphLite()
    
    # Build Spec Graph on the fly for demo
    spec_chunks = [c for c in rag_db.chunks.values() if c.category == 'spec']
    print(f"   - Loaded {len(spec_chunks)} spec chunks")
    spec_graph = build_spec_graph_from_chunks(spec_chunks)
    print(f"   - Built SpecGraph with {len(spec_graph.nodes)} nodes and {len(spec_graph.edges)} edges")
    
    hybrid = HybridRAG(rag_db, graph_lite, spec_graph)
    
    # 2. Step-by-Step Search
    print("\n2️⃣  Executing Hybrid Search Steps...")
    
    # Step A: Embedding Search
    print("\n   [Step A] Embedding Search (Vector Similarity)")
    emb_results = rag_db.search(query, limit=3)
    for score, chunk in emb_results:
        print(f"     - {score:.3f}: {chunk.metadata.get('summary', 'No summary')}")
        
    # Step B: BM25 Search
    print("\n   [Step B] BM25 Search (Keyword Matching)")
    bm25_results = graph_lite.bm25_search(query, limit=3)
    for score, node in bm25_results:
        print(f"     - {score:.3f}: {node.data.get('summary', 'No summary')}")
        
    # Step C: Graph Traversal
    print("\n   [Step C] Graph Traversal (Relationship Expansion)")
    if emb_results:
        seed_id = f"spec_{emb_results[0][1].id}"
        print(f"     - Seed Node: {seed_id}")
        related = spec_graph.traverse_related(seed_id, hops=1)
        for node_id, dist, path in related[:3]:
            node = spec_graph.nodes[node_id]
            print(f"     - Found Neighbor: {node.title} (via {path})")
            
    # 3. Final Fusion
    print("\n3️⃣  RRF Fusion & Final Result")
    final_results = hybrid.search(query, limit=5)
    
    print("\n   ✨ Top Result Explanation:")
    if final_results:
        top = final_results[0]
        print(f"      Content: {top.content[:100]}...")
        print(f"      Score: {top.score:.3f}")
        print(f"      Sources: {top.sources} (Validation: Found in {list(top.sources.keys())})")

if __name__ == "__main__":
    main()

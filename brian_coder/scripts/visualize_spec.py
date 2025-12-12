
import sys
import os
from pathlib import Path

# Add src and core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rag_db import RAGDatabase
from spec_graph import SpecGraph

def main():
    print("loading RAG Database...")
    db = RAGDatabase()
    
    spec_chunks = [c for c in db.chunks.values() if c.category == 'spec']
    print(f"Found {len(spec_chunks)} spec chunks.")
    
    if not spec_chunks:
        print("No spec chunks found. Please ensure spec files are indexed.")
        return

    print("\n building Spec Graph...")
    graph = SpecGraph()
    graph.build_from_chunks(spec_chunks)
    
    stats = graph.get_stats()
    print("\n Graph Statistics:")
    for k, v in stats.items():
        print(f"  - {k}: {v}")
        
    print("\n Graph Visualization (Top 30 Nodes):")
    print(graph.visualize_ascii(max_nodes=30))
    
    print("\n Sample Chunk Types:")
    chunk_types = {}
    for c in spec_chunks:
        if c.chunk_type not in chunk_types:
            chunk_types[c.chunk_type] = []
        if len(chunk_types[c.chunk_type]) < 3:
            chunk_types[c.chunk_type].append(c)
            
    for c_type, examples in chunk_types.items():
        print(f"\nType: {c_type}")
        for i, c in enumerate(examples):
            summary = c.metadata.get('summary', 'No summary')
            print(f"  {i+1}. [L{c.level}] {summary[:80]}...")
            if c_type == 'table':
                print(f"     Headers: {c.metadata.get('headers')}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Debug SpecGraph to see why traversal isn't working
"""
import os
import sys

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from core.spec_graph import get_spec_graph
from core.rag_db import get_rag_db
from lib.display import Color

def main():
    print(Color.action("🔍 SpecGraph Debug"))

    # Get instances
    rag_db = get_rag_db()
    spec_graph = get_spec_graph()

    # Show stats
    stats = spec_graph.get_stats()
    print(Color.info(f"\nSpecGraph Stats:"))
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Edges: {stats['total_edges']}")
    print(f"  Sections: {stats['sections']}")
    print(f"  Tables: {stats['tables']}")
    print(f"  Code Blocks: {stats['code_blocks']}")

    # Find a test node
    print(Color.info("\nFinding a test node..."))
    test_chunk_id = None
    for chunk in rag_db.chunks.values():
        if chunk.category == "spec" and "TLP" in chunk.content[:100]:
            test_chunk_id = chunk.id
            print(f"Found chunk: {chunk.id}")
            print(f"Content: {chunk.content[:100]}...")
            break

    if not test_chunk_id:
        print(Color.error("No test chunk found!"))
        return

    # Test traversal
    node_id = f"spec_{test_chunk_id}"
    print(Color.info(f"\nTesting traverse_related('{node_id}', hops=2)"))

    # Check if node exists
    if node_id not in spec_graph.nodes:
        print(Color.error(f"Node '{node_id}' not found in graph!"))
        print(Color.info("Sample node IDs:"))
        for i, nid in enumerate(list(spec_graph.nodes.keys())[:5]):
            print(f"  {i+1}. {nid}")
        return

    print(Color.success(f"Node exists in graph!"))

    # Try traversal
    related = spec_graph.traverse_related(node_id, hops=2)
    print(Color.info(f"Traversal result: {len(related)} nodes"))

    if related:
        print(Color.success("Related nodes:"))
        for i, (nid, distance, path) in enumerate(related[:5], 1):
            print(f"  {i}. {nid} (distance={distance}, path={path})")
    else:
        print(Color.warning("No related nodes found"))

        # Check adjacency
        print(Color.info("\nChecking adjacency list..."))
        if node_id in spec_graph._adjacency:
            neighbors = spec_graph._adjacency[node_id]
            print(f"Found {len(neighbors)} neighbors:")
            for i, (target, edge_type, weight) in enumerate(neighbors[:5], 1):
                print(f"  {i}. {target} (type={edge_type}, weight={weight})")
        else:
            print(Color.error("Node has no neighbors in adjacency list!"))

if __name__ == "__main__":
    main()

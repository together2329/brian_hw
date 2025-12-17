#!/usr/bin/env python3
"""
Debug why SpecGraph has edges but empty adjacency
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from core.spec_graph import get_spec_graph
from lib.display import Color

def main():
    print(Color.action("🔍 Debugging SpecGraph Edge → Adjacency Mismatch"))
    print()

    spec_graph = get_spec_graph()

    print(f"Total nodes: {len(spec_graph.nodes)}")
    print(f"Total edges: {len(spec_graph.edges)}")
    print(f"Adjacency entries: {len(spec_graph._adjacency)}")
    print()

    # Check first 10 edges
    print(Color.info("First 10 Edges:"))
    for i, edge in enumerate(spec_graph.edges[:10], 1):
        source_exists = edge.source_id in spec_graph.nodes
        target_exists = edge.target_id in spec_graph.nodes
        in_adjacency = edge.source_id in spec_graph._adjacency

        print(f"  {i}. {edge.edge_type}: {edge.source_id} → {edge.target_id}")
        print(f"     Source exists: {source_exists}, Target exists: {target_exists}, In adjacency: {in_adjacency}")

        if in_adjacency:
            neighbors = spec_graph._adjacency[edge.source_id]
            has_target = any(t == edge.target_id for t, _, _ in neighbors)
            print(f"     Adjacency neighbors: {len(neighbors)}, Has target: {has_target}")

    # Check adjacency entries
    print(f"\n{Color.info('Adjacency Entries (if any):')}")
    adj_count = 0
    for node_id, neighbors in spec_graph._adjacency.items():
        if neighbors:
            adj_count += 1
            if adj_count <= 5:
                print(f"  {node_id}: {len(neighbors)} neighbors")
                for target, edge_type, weight in neighbors[:2]:
                    print(f"    → {target} ({edge_type})")

    if adj_count == 0:
        print(Color.error("  No adjacency entries found!"))

    # Check if adjacency dict exists but is empty
    print(f"\n{Color.info('Adjacency Dict Details:')}")
    print(f"  Type: {type(spec_graph._adjacency)}")
    print(f"  Total keys: {len(spec_graph._adjacency)}")
    empty_count = sum(1 for v in spec_graph._adjacency.values() if not v)
    print(f"  Empty lists: {empty_count}/{len(spec_graph._adjacency)}")

    # Test add_edge manually
    print(f"\n{Color.action('Manual Edge Test:')}")
    if len(spec_graph.nodes) >= 2:
        node_ids = list(spec_graph.nodes.keys())[:2]
        print(f"  Testing add_edge({node_ids[0]}, {node_ids[1]}, 'test', 1.0)")

        initial_adj = len(spec_graph._adjacency.get(node_ids[0], []))
        spec_graph.add_edge(node_ids[0], node_ids[1], "test", 1.0)
        final_adj = len(spec_graph._adjacency.get(node_ids[0], []))

        print(f"  Before: {initial_adj} neighbors, After: {final_adj} neighbors")

        if final_adj > initial_adj:
            print(Color.success("  ✓ add_edge() works correctly"))
        else:
            print(Color.error("  ✗ add_edge() did not update adjacency"))

if __name__ == "__main__":
    main()

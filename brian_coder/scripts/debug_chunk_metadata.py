#!/usr/bin/env python3
"""
Debug chunk metadata to understand why SpecGraph has no edges
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from core.rag_db import get_rag_db
from core.spec_graph import get_spec_graph
from lib.display import Color

def main():
    print(Color.action("🔍 Debugging Chunk Metadata for SpecGraph"))
    print()

    db = get_rag_db()
    spec_chunks = [chunk for chunk in db.chunks.values() if chunk.category == "spec"]

    print(f"Total spec chunks: {len(spec_chunks)}\n")

    # Check metadata fields
    print(Color.info("Metadata Field Coverage:"))
    has_section_id = sum(1 for c in spec_chunks if c.metadata.get("section_id"))
    has_cross_refs = sum(1 for c in spec_chunks if c.metadata.get("cross_refs"))
    has_parent_section = sum(1 for c in spec_chunks if c.metadata.get("parent_section") or c.metadata.get("parent_h2") or c.metadata.get("parent_h1"))
    has_section_title = sum(1 for c in spec_chunks if c.metadata.get("section_title"))

    print(f"  section_id:      {has_section_id}/{len(spec_chunks)} ({has_section_id/len(spec_chunks)*100:.1f}%)")
    print(f"  cross_refs:      {has_cross_refs}/{len(spec_chunks)} ({has_cross_refs/len(spec_chunks)*100:.1f}%)")
    print(f"  parent_section:  {has_parent_section}/{len(spec_chunks)} ({has_parent_section/len(spec_chunks)*100:.1f}%)")
    print(f"  section_title:   {has_section_title}/{len(spec_chunks)} ({has_section_title/len(spec_chunks)*100:.1f}%)")

    # Show sample metadata
    print(f"\n{Color.info('Sample Chunk Metadata (first 3):')}")
    for i, chunk in enumerate(spec_chunks[:3], 1):
        print(f"\n  Chunk {i} (ID: {chunk.id}):")
        print(f"    Type: {chunk.chunk_type}")
        print(f"    Level: {chunk.level}")
        print(f"    Metadata keys: {list(chunk.metadata.keys())}")
        print(f"    section_id: {chunk.metadata.get('section_id', 'MISSING')}")
        print(f"    cross_refs: {chunk.metadata.get('cross_refs', 'MISSING')}")
        print(f"    parent_section: {chunk.metadata.get('parent_section', 'MISSING')}")
        print(f"    Content preview: {chunk.content[:80]}...")

    # Check SpecGraph stats
    print(f"\n{Color.action('SpecGraph Stats:')}")
    spec_graph = get_spec_graph()
    stats = spec_graph.get_stats()
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  Hierarchy edges: {stats['hierarchy_edges']}")
    print(f"  Cross-ref edges: {stats['cross_ref_edges']}")

    # Check adjacency
    print(f"\n{Color.info('Adjacency Check (first 3 nodes):')}")
    for i, (node_id, node) in enumerate(list(spec_graph.nodes.items())[:3]):
        neighbors = spec_graph._adjacency.get(node_id, [])
        print(f"  Node {i+1}: {node_id}")
        print(f"    Title: {node.title}")
        print(f"    Section ID: {node.section_id}")
        print(f"    Neighbors: {len(neighbors)}")
        if neighbors:
            for target, edge_type, weight in neighbors[:2]:
                print(f"      → {target} ({edge_type}, weight={weight})")

    # Diagnosis
    print(f"\n{Color.action('🔬 DIAGNOSIS:')}")
    if has_section_id == 0:
        print(Color.error("  ✗ PROBLEM: No chunks have section_id metadata"))
        print("    → Hierarchy edges cannot be created (need section_id like '2.1.1')")

    if has_cross_refs == 0:
        print(Color.error("  ✗ PROBLEM: No chunks have cross_refs metadata"))
        print("    → Cross-reference edges cannot be created")

    if has_parent_section == 0:
        print(Color.error("  ✗ PROBLEM: No chunks have parent_section metadata"))
        print("    → Table/code containment edges cannot be created")

    if stats['total_edges'] == 0:
        print(f"\n{Color.warning('  ⚠ RESULT: SpecGraph has 0 edges → Graph traversal cannot work')}")
        print("    → depth parameter has no effect (graph search returns empty)")
        print("    → Only Embedding + BM25 fusion is active")

    print(f"\n{Color.info('💡 SOLUTION:')}")
    print("  To fix graph traversal, chunking needs to extract:")
    print("    1. section_id from headers (e.g., '## 2.1.1 Header')")
    print("    2. cross_refs from text (e.g., 'See Section 3.2')")
    print("    3. parent_section for tables/code blocks")

if __name__ == "__main__":
    main()

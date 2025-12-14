#!/usr/bin/env python3
"""
Check why edges aren't being generated
"""
import os
import sys

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from core.rag_db import get_rag_db
from lib.display import Color

def main():
    print(Color.action("🔍 Edge Generation Debug"))

    rag_db = get_rag_db()
    spec_chunks = [c for c in rag_db.chunks.values() if c.category == "spec"]

    print(Color.info(f"\nTotal spec chunks: {len(spec_chunks)}"))

    # Check section_ids
    section_map = {}
    for chunk in spec_chunks:
        section_id = chunk.metadata.get("section_id", "")
        if section_id:
            node_id = f"spec_{chunk.id}"
            section_map[section_id] = node_id

    print(Color.info(f"Chunks with section_id: {len(section_map)}"))
    print(Color.info("Sample section_ids:"))
    for i, sid in enumerate(list(section_map.keys())[:10], 1):
        print(f"  {i}. {sid}")

    # Check cross_refs
    cross_ref_count = 0
    for chunk in spec_chunks:
        cross_refs = chunk.metadata.get("cross_refs", [])
        if cross_refs:
            cross_ref_count += 1
            if cross_ref_count <= 3:
                print(Color.info(f"\nChunk {chunk.id} has cross_refs:"))
                print(f"  Section ID: {chunk.metadata.get('section_id', '')}")
                print(f"  Cross Refs: {cross_refs}")

    print(Color.info(f"\nChunks with cross_refs: {cross_ref_count}"))

    # Check parent_section
    parent_section_count = 0
    for chunk in spec_chunks:
        parent_section = chunk.metadata.get("parent_section", "") or chunk.metadata.get("parent_h2", "") or chunk.metadata.get("parent_h1", "")
        if parent_section and chunk.chunk_type in ["table", "code_block"]:
            parent_section_count += 1
            if parent_section_count <= 3:
                print(Color.info(f"\n{chunk.chunk_type} {chunk.id} has parent:"))
                print(f"  Parent: '{parent_section}'")

    print(Color.info(f"\nTables/code with parent: {parent_section_count}"))

if __name__ == "__main__":
    main()

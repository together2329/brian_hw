#!/usr/bin/env python3
"""
Check RAG chunk metadata
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
    print(Color.action("🔍 RAG Chunk Metadata Check"))

    rag_db = get_rag_db()

    print(Color.info(f"\nTotal chunks: {len(rag_db.chunks)}"))

    # Sample a few spec chunks
    spec_chunks = [c for c in rag_db.chunks.values() if c.category == "spec"]
    print(Color.info(f"Spec chunks: {len(spec_chunks)}"))

    print(Color.info("\nSample metadata:"))
    for i, chunk in enumerate(spec_chunks[:5], 1):
        print(f"\n{i}. Chunk ID: {chunk.id}")
        print(f"   Type: {chunk.chunk_type}")
        print(f"   Level: {chunk.level}")
        print(f"   Metadata keys: {list(chunk.metadata.keys())}")
        if chunk.metadata:
            for key, value in list(chunk.metadata.items())[:3]:
                print(f"     {key}: {value}")

if __name__ == "__main__":
    main()

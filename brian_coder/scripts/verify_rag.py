#!/usr/bin/env python3
"""
Verifies that the RAG index contains PCIe spec data.
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
    print(Color.action("🔍 RAG Verification"))
    
    rag_db = get_rag_db()
    
    # Check stats first
    stats = rag_db.get_stats()
    spec_count = stats['by_category'].get('spec', 0)
    print(Color.info(f"Spec chunks: {spec_count}"))
    
    if spec_count == 0:
        print(Color.error("❌ No spec chunks found! Indexing might have failed."))
        sys.exit(1)
        
    # Run a test query
    query = "Transaction Layer Packet TLP format"
    print(Color.info(f"\nQuery: '{query}'"))
    
    results = rag_db.search(query, categories="spec", limit=3)
    
    if results:
        print(Color.success(f"✅ Found {len(results)} results:"))
        for score, chunk in results:
            source = os.path.basename(chunk.source_file)
            print(Color.info(f"  - [{source}] (score: {score:.2f})"))
            print(Color.info(f"    {chunk.content[:100]}..."))
    else:
        print(Color.error("❌ No results found for PCIe query!"))
        sys.exit(1)

if __name__ == "__main__":
    main()

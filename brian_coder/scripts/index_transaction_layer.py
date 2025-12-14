#!/usr/bin/env python3
"""
Index only transaction_layer.md for quick testing
"""
import os
import sys

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import config
from core.rag_db import get_rag_db
from lib.display import Color

def main():
    print(Color.action("🔄 Indexing Transaction Layer Only"))

    # Initialize DB
    rag_db = get_rag_db()

    # Path to transaction_layer.md
    pcie_dir = os.path.join(os.path.dirname(project_root), "PCIe", "02_Transaction Layer")
    tx_layer_file = os.path.join(pcie_dir, "transaction_layer.md")

    if not os.path.exists(tx_layer_file):
        print(Color.error(f"❌ File not found: {tx_layer_file}"))
        sys.exit(1)

    print(Color.info(f"File: {tx_layer_file}"))

    # Index the file
    print(Color.action("\n📄 Indexing transaction_layer.md..."))
    rag_db.index_file(tx_layer_file, category="spec")

    # Show stats
    stats = rag_db.get_stats()
    print(Color.action("\n📊 RAG Statistics"))
    print(Color.info(f"Total Chunks: {stats['total_chunks']}"))
    print(Color.info(f"Indexed Files: {stats['indexed_files']}"))

    if stats['by_category']:
        print(Color.info("By Category:"))
        for cat, count in stats['by_category'].items():
            print(f"  - {cat}: {count}")

    print(Color.success("\n✅ Indexing complete!"))

if __name__ == "__main__":
    main()

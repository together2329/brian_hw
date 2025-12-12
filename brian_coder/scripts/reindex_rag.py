#!/usr/bin/env python3
"""
Refreshes the RAG database by re-indexing all source files.
Useful when the index gets corrupted or to force an update.
"""
import os
import sys
import shutil

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
# Add src directory to path (for config.py)
sys.path.insert(0, os.path.join(project_root, "src"))

import config
from core.rag_db import get_rag_db
from lib.display import Color

def main():
    print(Color.action("🔄 RAG Re-indexing Tool"))
    print(Color.system("This will scan and re-index all source files."))
    
    # Initialize DB
    rag_db = get_rag_db()
    
    # Define directories
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pcie_dir = os.path.join(os.path.dirname(project_root), "PCIe")
    
    print(Color.info(f"Project Root: {project_root}"))
    print(Color.info(f"PCIe Spec Dir: {pcie_dir}"))
    
    # Index project files (brian_coder)
    print(Color.action("\n1. Indexing Project Files..."))
    rag_db.index_directory(project_root)
    
    # Index PCIe files
    if os.path.exists(pcie_dir):
        print(Color.action("\n2. Indexing PCIe Specs..."))
        # Force 'spec' category for these files
        rag_db.index_directory(pcie_dir, patterns=["*.md", "*.txt"], category="spec")
    else:
        print(Color.warning(f"\n⚠️  PCIe directory not found at: {pcie_dir}"))
    
    # Show stats
    stats = rag_db.get_stats()
    print(Color.action("\n📊 Final RAG Statistics"))
    print(Color.info(f"Total Chunks: {stats['total_chunks']}"))
    print(Color.info(f"Indexed Files: {stats['indexed_files']}"))
    
    if stats['by_category']:
        print(Color.info("By Category:"))
        for cat, count in stats['by_category'].items():
            print(f"  - {cat}: {count}")
            
    print(Color.success("\n✅ Re-indexing complete!"))

if __name__ == "__main__":
    main()

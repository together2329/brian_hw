import sys
import os
from pathlib import Path
import re

# Setup paths
current_dir = Path(os.getcwd())
sys.path.extend([
    str(current_dir),
    str(current_dir / "brian_coder"),
    str(current_dir / "brian_coder" / "core"),
    str(current_dir / "brian_coder" / "src")
])

try:
    import config
    # Force use of local DB
    config.RAG_DIR = str(current_dir / "brian_coder" / ".brian_rag")
    from rag_db import get_rag_db
    
    db = get_rag_db()
    print(f"Loaded RAG DB from: {db.rag_dir}")
    print(f"Total indexed chunks: {len(db.chunks)}")
    
    query = "Orthogonal Header Content"
    print(f"\n[Keyword Search] Searching for: '{query}'...")
    
    results = []
    for cid, chunk in db.chunks.items():
        if query.lower() in chunk.content.lower():
            results.append(chunk)
            
    print(f"Found {len(results)} matching chunks.\n")
    
    for i, chunk in enumerate(results[:3], 1):
        print(f"--- Result {i} (File: {chunk.source_file}) ---")
        # Find context
        content = chunk.content
        idx = content.lower().find(query.lower())
        start = max(0, idx - 60)
        end = min(len(content), idx + 100)
        context = content[start:end].replace('\n', ' ')
        print(f"...{context}...")
        print("------------------------------------------------")

except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"Error: {e}")

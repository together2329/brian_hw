import sys
import os
from pathlib import Path

# Setup paths
current_dir = Path(os.getcwd())
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "brian_coder"))
sys.path.append(str(current_dir / "brian_coder" / "core"))
sys.path.append(str(current_dir / "brian_coder" / "src"))

try:
    # Initialize RAG
    import config
    config.RAG_DIR = str(current_dir / "brian_coder" / ".brian_rag")
    # Force mock embeddings/LLM if needed, but we want to test real logic if possible
    # Assuming environment is set up for LLM calls from previous context
    
    from rag_db import get_rag_db
    
    print("Initializing RAG Database...")
    db = get_rag_db()
    print(f"Loaded {len(db.chunks)} chunks.")
    
    query = "ohc"
    print(f"\nPerforming RAG search for: '{query}'")
    print("=" * 60)
    
    results = db.search(query, limit=3)
    
    if not results:
        print("No results found.")
    
    for i, (score, chunk) in enumerate(results):
        print(f"\nResult #{i+1} (Score: {score:.4f})")
        print(f"File: {Path(chunk.source_file).name}")
        print(f"Type: {chunk.chunk_type}")
        print("-" * 30)
        snippet = chunk.content.split('\n')[0][:80]
        print(f"Content: {snippet}...")
        print("=" * 60)

    print(f"\nPerforming RAG search for: '{query}' in 'verilog' category")
    print("=" * 60)
    results_v = db.search(query, categories="verilog", limit=3)
    for i, (score, chunk) in enumerate(results_v):
        print(f"\nResult #{i+1} (Score: {score:.4f})")
        print(f"File: {Path(chunk.source_file).name}")
        print(f"Type: {chunk.chunk_type}")
        print("-" * 30)
        snippet = chunk.content.split('\n')[0][:80]
        print(f"Content: {snippet}...")
        print("=" * 60)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

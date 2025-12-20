import sys
import os
from pathlib import Path

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
    # Reload config to pick up new .config file changes
    from importlib import reload
    reload(config)
    config.load_env_file() # Re-parse files
    
    print(f"Model: {config.EMBEDDING_MODEL}")
    print(f"Dim: {config.EMBEDDING_DIMENSION}")
    
    from rag_db import RAGDatabase
    
    db = RAGDatabase(rag_dir=config.RAG_DIR)
    db.clear()
    
    target = "PCIe/02_Transaction Layer/transaction_layer.md"
    print(f"Indexing {target}...")
    db.index_file(target, category="spec")
    db.save()
    
    # Test Search
    print("Testing Search...")
    results = db.search("What is OHC?")
    for r in results:
        print(f"{r[0]:.4f}: {r[1].content[:50]}...")

except Exception as e:
    print(f"Error: {e}")

import sys
import os
from pathlib import Path

# Path setup
current_dir = Path(os.getcwd())
sys.path.extend([
    str(current_dir),
    str(current_dir / "brian_coder"),
    str(current_dir / "brian_coder" / "core"),
    str(current_dir / "brian_coder" / "src")
])

try:
    import config
    # Ensure correct RAG DIR
    config.RAG_DIR = str(current_dir / "brian_coder" / ".brian_rag")
    config.DEBUG_MODE = True # Force debug mode to see more info
    
    print(f"RAG DIR: {config.RAG_DIR}")
    print(f"Embedding API Key present: {bool(config.EMBEDDING_API_KEY or config.API_KEY)}")
    print(f"Embedding Model: {config.EMBEDDING_MODEL}")
    
    from tools import rag_search
    
    query = "What exactly does OHC stand for?"
    print(f"\nSearching for: '{query}'")
    result = rag_search(query)
    print("\nResult:")
    print(result)

except Exception as e:
    print(f"Fatal Error: {e}")
    import traceback
    traceback.print_exc()

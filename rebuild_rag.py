import sys
import os
from pathlib import Path

# Setup paths
current_dir = Path(os.getcwd())
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "brian_coder"))
sys.path.append(str(current_dir / "brian_coder" / "src"))
sys.path.append(str(current_dir / "brian_coder" / "core"))

try:
    import config
    from rag_db import RAGDatabase
    
    # Load config explicitly to be sure
    config.load_env_file()
    
    print(f"RAG_DIR from config: {config.RAG_DIR}")
    
    # Initialize DB
    db = RAGDatabase(rag_dir=config.RAG_DIR)
    
    print(f"Clearing database at {db.rag_dir}...")
    db.clear()
    
    target_file = "PCIe/02_Transaction Layer/transaction_layer.md"
    if not os.path.exists(target_file):
        # correction for path if needed
        target_file = "PCIe/02_Transaction Layer/transaction_layer.md" # user previous output showed this path might be valid or similar
        # Let's check typical location
        if not os.path.exists(target_file):
             # Try glob check or alternative
             target_file = "PCIe/03_Transaction_Layer/transaction_layer.md" 
             
    # Try finding the file if exact path fails
    if not os.path.exists(target_file):
        for root, dirs, files in os.walk("PCIe"):
            for f in files:
                if "transaction_layer.md" in f:
                    target_file = os.path.join(root, f)
                    break

    print(f"Indexing {target_file}...")
    if os.path.exists(target_file):
        chunks = db.index_file(target_file, category="spec")
        db.save()
        print(f"Successfully indexed {chunks} chunks.")
        
        # Verify search
        results = db.search("OHC definition", limit=3)
        print(f"Test Search 'OHC definition': Found {len(results)} results")
        for r in results:
            print(f" - {r[1].content[:100]}...")
            
    else:
        print(f"Error: Could not find transaction_layer.md")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

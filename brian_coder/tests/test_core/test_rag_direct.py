import sys
import os
from pathlib import Path

# Setup paths to simulate running as a module
current_dir = Path(os.getcwd())
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "brian_coder"))
sys.path.append(str(current_dir / "brian_coder" / "core"))
sys.path.append(str(current_dir / "brian_coder" / "src"))

try:
    import config
    config.RAG_DIR = str(current_dir / "brian_coder" / ".brian_rag")
    
    from rag_db import get_rag_db
    
    db = get_rag_db()
    
    print(f"Checking DB at: {db.rag_dir}")
    print(f"Total chunks: {len(db.chunks)}")
    
    found_count = 0
    print("\nScanning chunks for 'Orthogonal Header Content'...")
    
    for cid, chunk in db.chunks.items():
        if "Orthogonal Header Content" in chunk.content:
            found_count += 1
            print(f"\n✅ FOUND in Chunk {cid} ({chunk.source_file}):")
            print("-" * 40)
            # Show context around the term
            start_idx = chunk.content.find("Orthogonal Header Content")
            preview = chunk.content[max(0, start_idx - 50):min(len(chunk.content), start_idx + 100)]
            print(f"...{preview.replace(chr(10), ' ')}...")
            print("-" * 40)
            
    if found_count > 0:
        print(f"\nSUCCESS: Found {found_count} chunk(s) containing the definition.")
    else:
        print("\nFAILURE: Definition not found in any chunk.")
        
except Exception as e:
    print(f"Error: {e}")

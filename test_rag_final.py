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
    # Ensure RAG DIR
    config.RAG_DIR = str(current_dir / "brian_coder" / ".brian_rag")
    # Force use of configured model (Qwen)
    # config.EMBEDDING_MODEL = "text-embedding-3-small"
    
    from rag_db import get_rag_db
    
    db = get_rag_db()
    
    query = "definition of OHC including full name"
    print(f"Querying RAG DB (Model: {config.EMBEDDING_MODEL})...")
    print(f"Query: '{query}'")
    print("-" * 50)
    
    results = db.search(query, limit=3)
    
    found = False
    for score, chunk in results:
        print(f"[Score: {score:.4f}] {chunk.source_file}")
        content = chunk.content.replace("\n", " ")
        # Highlight key phrase
        if "Orthogonal Header Content" in content:
            content = content.replace("Orthogonal Header Content", "**ORTHOGONAL HEADER CONTENT**")
            found = True
        
        # Show snippets
        print(f"...{content[:200]}...")
        print("-" * 50)
        
    if found:
        print("\n✅ SUCCESS: RAG retrieved 'Orthogonal Header Content'. System is fixed.")
    else:
        print("\n❌ WARNING: Full definition not in Top 3. Check embedding quality.")

except Exception as e:
    print(f"Error: {e}")

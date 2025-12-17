import sys
import os

# Get project root
project_root = os.getcwd()

# Insert 'brian_coder' folder into path so 'import src' works
# This is required because rag_db.py does 'from src import ...'
sys.path.insert(0, os.path.join(project_root, "brian_coder"))

# Add src to path so 'import config' works (rag_db uses this as fallback)
sys.path.insert(0, os.path.join(project_root, "brian_coder", "src"))

# Also add project root for local imports if needed
sys.path.append(project_root)

# Force environment variables for clean index
os.environ["ENABLE_RAG_AUTO_INDEX"] = "true"
os.environ["RAG_CHUNK_SIZE"] = "1200"

# Note: We import config via src to ensure it loads correctly
from src import config
from core.rag_db import RAGDatabase

# Trigger indexing
print("Triggering explicit workspace index...")
db = RAGDatabase(rag_dir="brian_coder/.brian_rag")
# Explicitly index the project root
print("Triggering index_directory...")
db.index_directory(project_root)
print("Re-indexing complete.")

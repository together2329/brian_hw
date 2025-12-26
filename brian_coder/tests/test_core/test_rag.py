import sys
import os
from pathlib import Path

# Setup paths to simulate running as a module
current_dir = Path(os.getcwd())
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "brian_coder"))
# CRITICAL: Add core directory so 'import rag_db' works inside tools.py
sys.path.append(str(current_dir / "brian_coder" / "core"))
# CRITICAL: Add src directory so 'import config' works
sys.path.append(str(current_dir / "brian_coder" / "src"))

try:
    # Pre-import config and set RAG_DIR manually to ensure it picks the right DB
    import config
    config.RAG_DIR = str(current_dir / "brian_coder" / ".brian_rag")
    # print(f"DEBUG: Using RAG_DIR = {config.RAG_DIR}")
except ImportError as e:
    print(f"Config import warning: {e}")

from brian_coder.core.tools import rag_search

query = "What exactly does OHC stand for in PCIe spec?"
print(f"Testing RAG Search: '{query}'")
print("-" * 40)
result = rag_search(query)
print(result)
print("-" * 40)

if "Orthogonal Header Content" in result:
    print("\n✅ TEST SUCCESS: Found 'Orthogonal Header Content'!")
else:
    print("\n❌ TEST FAILED: Definition missing.")


import sys
import os

# Add paths
script_dir = os.path.dirname(os.path.abspath(__file__))
brian_coder_path = os.path.join(script_dir, "brian_coder")
sys.path.insert(0, brian_coder_path)

# Manual .env loading to ensure key is present
env_path = os.path.join(brian_coder_path, ".env")
if os.path.exists(env_path):
    print(f"Loading env from: {env_path}")
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip()

from core.rag_db import get_rag_db
from core import tools
import config

def rebuild_pcie_rag():
    print(Color.system("[RAG] Rebuilding Index for PCIe Specs..."))
    
    # Reload config API key from env
    config.API_KEY = os.getenv("LLM_API_KEY", config.API_KEY)

    
    # Check API Key
    key = config.API_KEY
    if not key or key == "your-openai-api-key-here":
        print(Color.warning("CRITICAL: Invalid API Key. Please check .env file."))
        print(f"Current Key: {key}")
        return
    else:
        masked = key[:5] + "..." + key[-4:] if len(key) > 10 else "SHORT"
        print(Color.system(f"API Key loaded: {masked}"))
    
    # Initialize DB (loads new config automatically)
    db = get_rag_db()
    
    # Path to PCIe directory
    pcie_dir = os.path.join(script_dir, "PCIe")
    
    if not os.path.exists(pcie_dir):
        print(Color.warning(f"Directory not found: {pcie_dir}"))
        return

    # Index directory - config now includes PCIe/**/*.md
    # We pass 'spec' category to force it, though config patterns should also capture it.
    print(Color.action(f"Indexing {pcie_dir} with recursive patterns..."))
    
    # Using tools.rag_index to leverage its logic or calling db directly
    # Call db directly for precise control and stats
    
    # 1. Force reload of config patterns (just in case)
    db._load_config_patterns()
    
    # 2. Index
    # We rely on the patterns in .ragconfig which we just updated to "PCIe/**/*.md"
    # But since we are passing a specific directory "PCIe", we might need to be careful 
    # if index_directory uses relative matching.
    # Let's use the explicit patterns from the config for this directory root.
    
    # Bypass config loading issue for now and use explicit patterns
    # We found that _load_config_patterns returns flattened list, and might be falling back to defaults.
    # To ensure we index what we want:
    patterns = ["PCIe/**/*.md"]
    print(f"Using explicit patterns: {patterns}")
    
    # Note: index_directory expects patterns relative to dir_path if possible, or globs.
    # "PCIe/**/*.md" matches from project root. 
    # If we pass project root as dir_path, it works.
    # If we pass PCIe dir, we need "**/*.md".
    
    # Let's index from project root to be safe with the patterns we defined ("PCIe/**/*.md")
    project_root = script_dir
    created = db.index_directory(project_root, patterns=patterns, category="spec")
    
    if created > 0:
        db.save()
        print(Color.success(f"Successfully indexed {created} chunks."))
    else:
        print(Color.warning("No new chunks created (files might be unchanged or patterns mismatch)."))
        
    # Check acronyms
    print(Color.system(f"\n[Acronyms] Total Known: {len(db.known_acronyms)}"))
    
    search_terms = ["RCB", "ACK", "NAK", "DLLP"]
    print("Sampling check:")
    for term in search_terms:
        if term in db.known_acronyms:
            print(f"  ✅ {term}: {db.known_acronyms[term]}")
        else:
            print(f"  ❌ {term}: Not found")

# Helper for colors
class Color:
    @staticmethod
    def system(s): return f"\033[34m{s}\033[0m"
    @staticmethod
    def success(s): return f"\033[32m{s}\033[0m"
    @staticmethod
    def warning(s): return f"\033[33m{s}\033[0m"
    @staticmethod
    def action(s): return f"\033[36m{s}\033[0m"

if __name__ == "__main__":
    rebuild_pcie_rag()

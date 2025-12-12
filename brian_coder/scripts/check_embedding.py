
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../brian_coder')))

try:
    from brian_coder.src import config
    from brian_coder.src import llm_client
    from brian_coder.lib.display import Color
except ImportError:
    # Try alternate path if running from root
    sys.path.insert(0, os.path.abspath('brian_coder'))
    from src import config
    from src import llm_client
    from lib.display import Color

def check_embedding():
    print(Color.system("=== Embedding Configuration Check ==="))
    print(f"Configured Model: {Color.info(config.EMBEDDING_MODEL)}")
    print(f"Configured Base URL: {Color.info(config.EMBEDDING_BASE_URL)}")
    print(f"Configured API Key: {Color.info(config.EMBEDDING_API_KEY[:10] + '...' if config.EMBEDDING_API_KEY else 'None')}")
    print(f"Config Dimension: {Color.info(str(config.EMBEDDING_DIMENSION))}")
    print()

    print(Color.system("=== Live API Test ==="))
    try:
        print("Sending request to embedding API ('test')...")
        emb = llm_client.get_embedding("test")
        dim = len(emb)
        print(f"✅ Received Vector Dimension: {Color.success(str(dim))}")
        print(f"Preview: {emb[:5]}...")
    except Exception as e:
        print(f"❌ API Call Failed: {Color.error(str(e))}")
    
    print()
    print(Color.system("=== Stored RAG Index Check ==="))
    rag_path = Path.home() / ".brian_rag" / "rag_index.json"
    if rag_path.exists():
        try:
            data = json.loads(rag_path.read_text())
            print(f"Index File: {rag_path}")
            print(f"Stored Model Name: {Color.info(data.get('embedding_model', 'Not recorded'))}")
            print(f"Stored Dimension: {Color.info(str(data.get('embedding_dimension', 'Not recorded')))}")
            
            # Check a real chunk if possible
            chunks = data.get("chunks", {})
            if chunks:
                first_chunk = next(iter(chunks.values()))
                actual_stored_dim = len(first_chunk.get("embedding", []))
                print(f"Actual Chunk Dimension: {Color.info(str(actual_stored_dim))}")
            else:
                print("No chunks stored.")
                
        except Exception as e:
            print(f"Failed to read index: {e}")
    else:
        print(f"Index file not found at {rag_path}")

if __name__ == "__main__":
    check_embedding()

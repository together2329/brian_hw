
import sys
import os

# Setup paths
project_root = os.getcwd()
sys.path.insert(0, os.path.join(project_root, "brian_coder"))
sys.path.insert(0, os.path.join(project_root, "brian_coder", "src"))
sys.path.append(project_root)

from core.rag_db import RAGDatabase

def run_live_test():
    print("Initialize RAG Database...")
    db = RAGDatabase(rag_dir="brian_coder/.brian_rag")
    
    queries = [
        ("What is OHC?", "definition_seeking"),
        ("OHC example usage", "example_seeking"),
        ("Table of OHC encodings", "table_seeking")
    ]
    
    for query, expected_intent in queries:
        print(f"\n{'='*60}")
        print(f"🧐 Query: '{query}'")
        print(f"{'='*60}")
        
        # Search directly
        results = db.search(query, limit=3)
        
        for i, (score, chunk) in enumerate(results, 1):
            c_type = chunk.metadata.get("content_type", "unknown").upper()
            imp = chunk.metadata.get("importance", "unknown").upper()
            
            print(f"{i}. [Score: {score:.2f}] Type: {c_type} ({imp})")
            print(f"   Context: {chunk.content[:150].replace(chr(10), ' ')}...")
            print(f"   Source: {os.path.basename(chunk.source_file)}")
            print("-" * 30)

if __name__ == "__main__":
    run_live_test()

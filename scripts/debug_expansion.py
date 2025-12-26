
import sys
import os

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(root_dir, 'brian_coder', 'src'))
sys.path.insert(0, os.path.join(root_dir, 'brian_coder'))

import config
from brian_coder.core.rag_db import get_rag_db

def test_expansion():
    print("Initializing RAG DB...")
    # Mock llm_client slightly to see what it *would* receive? 
    # Actually let's just run it against the real LLM since we have the key.
    
    db = get_rag_db()
    # Force extraction just in case
    db._extract_known_acronyms()
    
    queries = ["ts", "ohc", "tlp", "dl_down"]
    
    print(f"\n[Known Acronyms Count]: {len(db.known_acronyms)}")
    if "TS" in db.known_acronyms:
        print(f"TS definition: {db.known_acronyms['TS']}")
    else:
        print("TS NOT in known acronyms!")

    print("\n--- Testing Expansion ---")
    for q in queries:
        print(f"\nInput: '{q}'")
        expanded = db._expand_query_cognitively(q)
        print(f"Output: '{expanded}'")
        
        if q == "ts" and "Trailer" not in expanded:
            print("❌ FAILED to expand 'ts'")
        elif q == "ohc" and "Orthogonal" not in expanded:
            print("❌ FAILED to expand 'ohc'")
        else:
            print("✅ Expanded correctly")

if __name__ == "__main__":
    test_expansion()

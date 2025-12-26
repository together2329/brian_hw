
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
    db = get_rag_db()
    db._extract_known_acronyms()
    
    # Test cases that require specific tokens
    queries = ["ts", "what is ohc?", "tell me about tlp packet", "random stuff"]
    
    print(f"\n[Known Acronyms Count]: {len(db.known_acronyms)}")

    print("\n--- Testing Expansion with Filtering ---")
    for q in queries:
        print(f"\nInput: '{q}'")
        # We want to see what context is actually injected (simulate logic)
        relevant = []
        q_lower = q.lower()
        for k, v in db.known_acronyms.items():
            # Check strict word match for acronym to avoid "ts" matching "tests"
            # Simple tokenization
            tokens = q_lower.replace("?", " ").replace(".", " ").split()
            if k.lower() in tokens:
                relevant.append(f"'{k}' -> '{v} ({k})'")
        
        print(f"Would Inject ({len(relevant)}): {relevant}")
        
        # Real call
        expanded = db._expand_query_cognitively(q)
        print(f"Output: '{expanded}'")
        
        if "ts" in q and "Trailer" not in expanded:
             print("❌ FAILED 'ts'")
        elif "ohc" in q and "Orthogonal" not in expanded:
             print("❌ FAILED 'ohc'")

if __name__ == "__main__":
    test_expansion()

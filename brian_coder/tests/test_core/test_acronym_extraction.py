
import sys
import os
import re
from collections import Counter

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'brian_coder')))

try:
    from brian_coder.core.rag_db import get_rag_db
except ImportError:
    # Handle import if needed
    pass

def extract_acronyms():
    print("Initializing RAG DB to scan for acronyms...")
    rag_db = get_rag_db()
    
    print(f"RAG Dir: {rag_db.rag_dir}")
    print(f"Index Path: {rag_db.index_path}")
    
    if rag_db.index_path.exists():
        print(f"Index file exists, size: {rag_db.index_path.stat().st_size} bytes")
    else:
        print("❌ Index file NOT found.")
    
    # Force load if empty
    if not rag_db.chunks:
        print("Chunks empty, attempting explicit load...")
        # Since _load_index might be internal, let's try standard search which triggers load or reindex
        # Or look for public load method. 
        # Actually _load_index is usually called in init.
        # If it failed silently, maybe path is wrong.
        # Try calling it:
        try:
            rag_db._load()
            print(f"Loaded {len(rag_db.chunks)} chunks.")
        except Exception as e:
            print(f"Load failed: {e}")
    
    # Regex for "Full Name (Acronym)"
    # Captures: "Orthogonal Header Content (OHC)"
    # Constraints: Acronym 2-6 caps, Full Name 1-5 words starting with caps
    pattern = r'([A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){0,5})\s+\(([A-Z]{2,6})\)'
    
    acronyms = Counter()
    mappings = {}
    
    print(f"Scanning {len(rag_db.chunks)} chunks...")
    
    for chunk in rag_db.chunks.values():
        matches = re.findall(pattern, chunk.content)
        for full, short in matches:
            # Filter matches where letters don't align commonly
            # (Simple heuristic: Acronym chars should roughly appear in Full name)
            # giving benefit of doubt for now
            
            mappings[short] = full
            acronyms[short] += 1
            
    print("\n--- Extracted Acronyms ---")
    for short, count in acronyms.most_common():
        print(f"{short}: {mappings[short]} (Found {count} times)")
        
    print("\n--- Check Specific Targets ---")
    print(f"OHC: {mappings.get('OHC', 'Not Found')}")
    print(f"TS: {mappings.get('TS', 'Not Found')}")
    print(f"TLP: {mappings.get('TLP', 'Not Found')}")

if __name__ == "__main__":
    extract_acronyms()

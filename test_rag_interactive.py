
import sys
import os
import readline  # For better input handling

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'brian_coder')))

try:
    from brian_coder.core.hybrid_rag import get_hybrid_rag
    from brian_coder.src import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure you are running this from the project root.")
    sys.exit(1)

# ANSI Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header():
    print(f"\n{BOLD}{BLUE}=== Brian Coder RAG Interactive Tester ==={RESET}")
    print(f"Config Loaded:")
    print(f"  - HYBRID_ALPHA: {getattr(config, 'HYBRID_ALPHA', 'Unknown')} (Should be 0.8)")
    print(f"  - HIGH THRESHOLD: {getattr(config, 'SMART_RAG_HIGH_THRESHOLD', 'Unknown')} (Should be 0.75)")
    print(f"{BLUE}=========================================={RESET}\n")

def main():
    print_header()
    
    print("Initializing RAG System... (this may take a moment)")
    hybrid = get_hybrid_rag()
    print(f"{GREEN}RAG Initialized!{RESET}")
    print(f"Internal Weights: Emb={hybrid.alpha_embedding:.2f}, BM25={hybrid.alpha_bm25:.2f}, Graph={hybrid.alpha_graph:.2f}")

    print("\nType a query to search (or 'exit'/'quit' to stop).")

    while True:
        try:
            query = input(f"\n{BOLD}Query > {RESET}").strip()
        except KeyboardInterrupt:
            print("\nExiting...")
            break

        if query.lower() in ('exit', 'quit'):
            break
        
        if not query:
            continue

        print(f"Searching for '{query}'...")
        try:
            results = hybrid.search(query, limit=3)
        except Exception as e:
            print(f"{RED}Search failed: {e}{RESET}")
            continue

        if not results:
            print(f"{YELLOW}No results found.{RESET}")
            continue

        threshold = getattr(config, 'SMART_RAG_HIGH_THRESHOLD', 0.75)
        top_score = results[0].score

        # Decision simulation
        if top_score >= threshold:
            decision = f"{GREEN}✅ Use Directly{RESET}"
        elif top_score > getattr(config, 'SMART_RAG_LOW_THRESHOLD', 0.0):
            decision = f"{YELLOW}⚠️ Ask Judge{RESET}"
        else:
            decision = f"{RED}❌ Ignore{RESET}"

        print(f"\nTop Score: {BOLD}{top_score:.4f}{RESET} -> {decision}")
        
        print(f"\n{BOLD}Results:{RESET}")
        for i, r in enumerate(results):
            score_color = GREEN if r.score >= threshold else YELLOW
            print(f"{i+1}. [{score_color}{r.score:.4f}{RESET}] {BOLD}{os.path.basename(r.source_file)}{RESET}")
            print(f"   Sources: {r.sources}")
            content_preview = r.content.replace('\n', ' ')[:150]
            print(f"   Content: {content_preview}...")
            print("-" * 40)

if __name__ == "__main__":
    main()

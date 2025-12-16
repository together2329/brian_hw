
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'brian_coder')))

try:
    from brian_coder.core.hybrid_rag import get_hybrid_rag
    from brian_coder.src import config
except ImportError:
    # If standard import fails, try direct from src (fixes local script issues)
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'brian_coder', 'src')))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'brian_coder', 'core')))
    import config
    from hybrid_rag import get_hybrid_rag

# ANSI Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_result(name, passed, detail=""):
    color = GREEN if passed else RED
    symbol = "✅" if passed else "❌"
    print(f"{symbol} {BOLD}{name:<30}{RESET} {color}{'PASSED' if passed else 'FAILED'}{RESET} {detail}")

def check_config():
    print(f"\n{BOLD}1. Configuration Check{RESET}")
    
    alpha = getattr(config, 'HYBRID_ALPHA', 0.0)
    thresh = getattr(config, 'SMART_RAG_HIGH_THRESHOLD', 0.0)
    
    # HYBRID_ALPHA should be 0.8
    chk1 = (alpha == 0.8)
    print_result("HYBRID_ALPHA == 0.8", chk1, f"(Got {alpha})")
    
    # THRESHOLD should be 0.55
    chk2 = (thresh == 0.55)
    print_result("HIGH_THRESHOLD == 0.55", chk2, f"(Got {thresh})")
    
    return chk1 and chk2

def check_queries(hybrid):
    print(f"\n{BOLD}2. Retrieval Quality Check{RESET}")
    
    test_cases = [
        {"query": "ohc", "expect_high": True, "min_score": 0.55, "desc": "Definition (Orthogonal Header Content)"},
        {"query": "TLP", "expect_high": True, "min_score": 0.55, "desc": "Common Acronym (Transaction Layer Packet)"},
        {"query": "Ack", "expect_high": True, "min_score": 0.45, "desc": "Short Term (Acknowledge)"},
        {"query": "xyz_nonexistent_123", "expect_high": False, "max_score": 0.45, "desc": "Noise/Non-existent"},
    ]
    
    passed_count = 0
    
    for case in test_cases:
        query = case["query"]
        print(f"\n   Checking: '{query}' ({case['desc']})...")
        try:
            results = hybrid.search(query, limit=1)
        except Exception as e:
            print_result(f"Query '{query}'", False, f"Exception: {e}")
            continue
            
        if not results:
            if not case.get("expect_high"):
                print_result(f"Query '{query}'", True, "Correctly found no results")
                passed_count += 1
            else:
                print_result(f"Query '{query}'", False, "No results found")
            continue
            
        score = results[0].score
        content = results[0].content.replace('\n', ' ')[:60]
        
        # Validation
        passed = True
        msg = f"(Score: {score:.4f})"
        
        if case.get("expect_high"):
            if score < case["min_score"]:
                passed = False
                msg += f" < Min {case['min_score']}"
        else:
             if score > case.get("max_score", 1.0):
                 passed = False
                 msg += f" > Max {case.get('max_score')}"
                 
        print_result(f"Query '{query}'", passed, msg)
        print(f"      Matched: {content}...")
        
        if passed:
            passed_count += 1

    return passed_count == len(test_cases)

def main():
    print(f"{BOLD}=== RAG System Health Check ==={RESET}")
    
    # 1. Config
    if not check_config():
        print(f"\n{RED}CRITICAL: Configuration mismatch. Fix .config file.{RESET}")
        
    # Initialize
    print("\nInitializing Search Engine...")
    try:
        hybrid = get_hybrid_rag()
    except Exception as e:
        print(f"{RED}Failed to init HybridRAG: {e}{RESET}")
        sys.exit(1)
        
    print(f"   Weights: Emb={hybrid.alpha_embedding:.2f}, BM25={hybrid.alpha_bm25:.2f}")

    # 2. Queries
    queries_ok = check_queries(hybrid)
    
    print(f"\n{BOLD}=== Summary ==={RESET}")
    if queries_ok:
        print(f"{GREEN}ALL SYSTEMS GO. RAG is healthy.{RESET}")
    else:
        print(f"{YELLOW}Some checks failed. Review scores.{RESET}")

if __name__ == "__main__":
    main()

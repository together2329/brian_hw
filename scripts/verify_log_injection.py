
import sys
import os
import io
from contextlib import redirect_stdout

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'brian_coder')))

try:
    from brian_coder.src import config
    from brian_coder.src import main as agent_main
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def verify_logs():
    print("Verifying SmartRAG Debug Logs...")
    
    # 1. Enable Debug Mode & Smart RAG
    print("Configuring settings...")
    # Access config through main module logic if possible, or force both
    config.DEBUG_MODE = True
    config.ENABLE_SMART_RAG = True
    config.SMART_RAG_HIGH_THRESHOLD = 0.55
    
    # Also set on main's imported config if accessible
    if hasattr(agent_main, 'config'):
        print(f"Setting DEBUG_MODE on agent_main.config: {agent_main.config}")
        agent_main.config.DEBUG_MODE = True
        agent_main.config.ENABLE_SMART_RAG = True
    else:
        print("Warning: agent_main.config not found")
    
    # 2. Mock Messages
    messages = [
        {"role": "user", "content": "What is ohc?"}
    ]
    
    # 3. Capture Output
    print("Calling build_system_prompt...")
    f = io.StringIO()
    with redirect_stdout(f):
        # We need to ensure main.hybrid_rag is initialized because build_system_prompt uses it
        # But main.py initializes it globally on import? 
        # Actually main.py has: hybrid_rag = None, initialized in main() or init_rag()
        # let's try to init it manually
        
        try:
            from brian_coder.core.hybrid_rag import get_hybrid_rag
            agent_main.hybrid_rag = get_hybrid_rag()
        except:
             pass

        try:
            prompt = agent_main.build_system_prompt(messages)
        except Exception as e:
            print(f"Error building prompt: {e}")
            
    output = f.getvalue()
    
    # 4. Analyze Output
    print("\n--- Captured Output ---")
    print(output[:500] + "..." if len(output) > 500 else output)
    print("-----------------------\n")
    
    if "[SmartRAG] Injected Context Preview" in output:
        print("✅ SUCCESS: Found injected context log!")
        if "Orthogonal Header Content" in output:
             print("✅ SUCCESS: Context content looks correct!")
    else:
        print("❌ FAILED: Log missing.")
        print("Debug output dump:")
        print(output)

if __name__ == "__main__":
    verify_logs()

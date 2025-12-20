
import sys
import os

def check_paths():
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Script Location: {os.path.abspath(__file__)}")
    
    # Calculate expected paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming this script is in project root
    lib_path = os.path.join(script_dir, "brian_coder", "lib")
    
    print(f"\nExpected Lib Path: {lib_path}")
    print(f"Exists? {os.path.exists(lib_path)}")
    
    print("\nCurrent sys.path:")
    for p in sys.path:
        print(f"  - {p}")

    print("\n--- Attempting Imports ---")
    try:
        from brian_coder.lib import display
        print("✅ Success: import brian_coder.lib.display")
    except ImportError as e:
        print(f"❌ Failed: import brian_coder.lib.display ({e})")
        
    try:
        sys.path.append(os.path.join(script_dir, "brian_coder"))
        from lib import display
        print("✅ Success: import lib.display (after path append)")
    except ImportError as e:
        print(f"❌ Failed: import lib.display ({e})")

if __name__ == "__main__":
    check_paths()

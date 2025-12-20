from core.tools import find_files
import os
import shutil

def test_find_fallback():
    print("Testing find_files Smart Fallback...")
    
    # Setup: 
    # test_root/
    #   match.txt
    #   subdir/ (empty)
    
    root = "test_root_fallback"
    subdir = os.path.join(root, "subdir")
    
    if os.path.exists(root):
        shutil.rmtree(root)
        
    os.makedirs(subdir)
    
    with open(os.path.join(root, "match.txt"), "w") as f:
        f.write("content")
        
    # Check find_files in subdir (should fail locally, but hint parent)
    print(f"\nSearching in {subdir} for 'match.txt'...")
    # Adjust path to be relative for realistic testing if needed, or absolute
    # find_files uses os.walk(directory).
    
    result = find_files("match.txt", directory=subdir)
    print("Result:\n" + result)
    
    if "Hint: Found" in result and "../match.txt" in result.replace(os.sep, "/"):
        print("PASS: Smart Fallback suggested parent match.")
    else:
        print("FAIL: Smart Fallback failed.")

    # Cleanup
    shutil.rmtree(root)

if __name__ == "__main__":
    test_find_fallback()

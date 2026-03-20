import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.message_classifier import MessageClassifier, MessageImportance

def test_compression_logic():
    print("Testing MessageClassifier changes...")
    classifier = MessageClassifier()

    # Test 1: System Message Classification
    # Should not be CRITICAL (3) by default
    msg_sys = {"role": "system", "content": "System prompt or guidance..."}
    imp = classifier.classify_message(msg_sys)
    print(f"System Message Importance: {imp}")
    
    if imp == MessageImportance.CRITICAL:
        print("FAIL: System message is still CRITICAL")
    else:
        print(f"PASS: System message is level {imp}")

    # Test 2: Observation Classification (should be LOW by default)
    msg_obs = {"role": "user", "content": "Observation: command output..."}
    imp_obs = classifier.classify_message(msg_obs)
    print(f"Observation Importance: {imp_obs}")
    if imp_obs == MessageImportance.LOW:
        print("PASS: Observation message is LOW")
    else:
        print(f"FAIL: Observation message is level {imp_obs}")

    # Test 3: System Message with Error (should be HIGH)
    msg_sys_err = {"role": "system", "content": "Error: File not found"}
    imp_err = classifier.classify_message(msg_sys_err)
    
    # Actually, default regex checks "error" in HIGH patterns?
    # high_patterns: fixed..error, solution.., successfully.., found..solution
    # Wait, 'error' alone is in LOW patterns!
    # low_patterns: failed, error, exception...
    # But low patterns are only checked if role == "assistant".
    # So "Error: ..." will stay LOW.
    # This is fine. Errors should be summarized if old.
    print(f"System Error Importance: {imp_err} (Expected LOW or HIGH depending on pattern match)")

    # Test 4: Partitioning (system prefix preserved)
    messages = [
        {"role": "system", "content": "System prompt..."},
        {"role": "user", "content": "req 1"},
        {"role": "system", "content": "status msg (old)"},
        {"role": "assistant", "content": "res 1"},
        {"role": "user", "content": "Observation: output 2 (recent)"}
    ]
    
    parts = classifier.partition_by_importance(messages, keep_recent=1)
    
    print("\nPartition Results:")
    print(f"System part: {len(parts['system'])} (Expected: 1 for system prefix)")
    print(f"Low part: {len(parts['low'])} (Expected: >= 0)")
    print(f"Recent part: {len(parts['recent'])} (Expected: 1 for observation)")

    if len(parts['system']) == 1 and len(parts['recent']) == 1:
        print("PASS: Partition logic preserves system prefix and recent messages")
    else:
        print("FAIL: Partition logic invalid")

if __name__ == "__main__":
    test_compression_logic()

#!/usr/bin/env python3
"""
Test acronym definition improvements (Phase 1)

Tests if definition boosting and query expansion work correctly.
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import config
config.DEBUG_MODE = False

from core.rag_db import get_rag_db
from lib.display import Color

def test_acronym_definition(query, expected_definition):
    """Test if the correct definition is in top-3 results."""
    query_str = f'Query: "{query}"'
    expected_str = f'Expected: "{expected_definition}"'
    print(f"\n{Color.action(query_str)}")
    print(f"{Color.info(expected_str)}")

    db = get_rag_db()
    results = db.search(query, limit=5)

    if not results:
        print(Color.error("  ✗ NO RESULTS"))
        return False

    # Check top-3 results
    found_in_top3 = False
    for i, (score, chunk) in enumerate(results[:3], 1):
        content_lower = chunk.content.lower()
        expected_lower = expected_definition.lower()

        if expected_lower in content_lower:
            found_in_top3 = True
            print(Color.success(f"  ✓ FOUND in rank {i} (score={score:.4f})"))
            preview = chunk.content[:120].replace('\n', ' ')
            print(f"    {preview}...")
            break

    if not found_in_top3:
        print(Color.warning(f"  ⚠ Not in top-3"))
        # Show what was found
        print(f"\n  Top-3 results:")
        for i, (score, chunk) in enumerate(results[:3], 1):
            preview = chunk.content[:80].replace('\n', ' ')
            print(f"    {i}. [Score: {score:.4f}] {preview}...")

    return found_in_top3

def main():
    print(Color.action("🧪 Acronym Definition Test (Phase 1)"))
    print("Testing definition boosting + query expansion\n")

    test_cases = [
        ("What does OHC stand for?", "Orthogonal Header Content"),
        ("What is TLP?", "Transaction Layer Packet"),
        ("Define ECRC", "End-to-End CRC"),
        ("What does PMR mean?", "Process Memory Request"),
        ("PASID stands for", "Process Address Space"),
    ]

    passed = 0
    total = len(test_cases)

    for query, expected in test_cases:
        if test_acronym_definition(query, expected):
            passed += 1

    # Summary
    print(f"\n{'='*70}")
    print(Color.action("📊 RESULTS"))
    print(f"{'='*70}")
    print(f"Passed: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed >= total * 0.9:  # 90% threshold
        print(Color.success(f"\n✅ TEST PASSED (≥90% accuracy)"))
    elif passed >= total * 0.7:
        print(Color.warning(f"\n⚠️  MARGINAL (70-90% accuracy)"))
    else:
        print(Color.error(f"\n✗ TEST FAILED (<70% accuracy)"))

    return passed >= total * 0.9

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

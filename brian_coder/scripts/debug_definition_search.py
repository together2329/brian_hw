#!/usr/bin/env python3
"""
Debug why definition search isn't working as expected
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from core.rag_db import get_rag_db
from lib.display import Color

def debug_query(query, expected_def):
    print(f"\n{'='*80}")
    print(Color.action(f"Query: '{query}'"))
    print(Color.info(f"Expected: '{expected_def}'"))
    print(f"{'='*80}\n")

    db = get_rag_db()

    # Search raw
    print(Color.action("Step 1: Raw search results"))
    results = db.search(query, limit=10)

    if not results:
        print(Color.error("No results found!"))
        return

    print(f"Found {len(results)} results\n")

    # Check each result
    found_definition = False
    for i, (score, chunk) in enumerate(results, 1):
        content_lower = chunk.content.lower()
        expected_lower = expected_def.lower()

        # Check if definition is in this chunk
        has_expected = expected_lower in content_lower

        # Check for definition keywords
        definition_keywords = ["stands for", "indicates the presence of", "refers to", "is defined as", "means", "represents"]
        has_def_keyword = any(kw in content_lower for kw in definition_keywords)

        marker = ""
        if has_expected and has_def_keyword:
            marker = Color.success("✓ PERFECT")
            found_definition = True
        elif has_expected:
            marker = Color.warning("⚠ HAS_DEF")
        elif has_def_keyword:
            marker = Color.info("⚡ HAS_KEYWORD")

        print(f"{i}. [Score: {score:.4f}] {marker}")
        preview = chunk.content[:100].replace('\n', ' ')
        print(f"   {preview}...")

        if i <= 5 or (has_expected and has_def_keyword):
            print(f"   File: {chunk.source_file}")
            if has_expected:
                print(f"   → Contains '{expected_def}'")
            if has_def_keyword:
                keywords = [kw for kw in definition_keywords if kw in content_lower]
                print(f"   → Has keyword: {keywords}")
        print()

    if not found_definition:
        print(Color.warning("\n💡 PROBLEM: No chunk found with both definition and keyword"))
        print("   Possible causes:")
        print("   1. Definition not in indexed chunks")
        print("   2. Definition doesn't use expected keywords")
        print("   3. Definition chunk has low embedding score")

def main():
    print(Color.action("🔍 Definition Search Debugger"))
    print()

    test_cases = [
        ("What is TLP?", "Transaction Layer Packet"),
        ("Define ECRC", "End-to-End CRC"),
    ]

    for query, expected in test_cases:
        debug_query(query, expected)

if __name__ == "__main__":
    main()

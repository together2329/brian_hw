#!/usr/bin/env python3
"""
Convert open-skills SKILL.md to brian_coder format

Usage:
  python convert_open_skill.py open-skills/skills/public/pdf-text-replace
"""

import sys
from pathlib import Path
import re


def extract_keywords_from_description(description):
    """Extract keywords from description using heuristics"""
    # Common words to extract
    important_words = []

    # Split description into words
    words = re.findall(r'\b[a-z]+\b', description.lower())

    # Filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                  'to', 'for', 'of', 'with', 'by', 'from', 'this', 'that',
                  'is', 'are', 'be', 'have', 'has', 'when', 'should', 'need'}

    for word in words:
        if word not in stop_words and len(word) > 3:
            if word not in important_words:
                important_words.append(word)
                if len(important_words) >= 8:  # Limit to 8 keywords
                    break

    return important_words


def detect_file_patterns(content):
    """Detect file patterns from content"""
    patterns = []

    # Look for file extensions mentioned
    extensions = re.findall(r'\*\.(\w+)', content)
    patterns.extend([f"*.{ext}" for ext in extensions])

    # Common patterns based on skill name
    if 'pdf' in content.lower():
        patterns.append("*.pdf")
    if 'image' in content.lower() or 'photo' in content.lower():
        patterns.extend(["*.jpg", "*.png", "*.jpeg", "*.gif"])

    return list(set(patterns))  # Remove duplicates


def convert_skill(skill_dir):
    """Convert open-skills SKILL.md to brian_coder format"""

    skill_path = Path(skill_dir)
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        print(f"❌ SKILL.md not found in {skill_dir}")
        return

    # Read original
    content = skill_md.read_text(encoding='utf-8')

    # Parse frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            body = parts[2].strip()
        else:
            print("❌ Invalid SKILL.md format")
            return
    else:
        print("❌ No frontmatter found")
        return

    # Extract name and description
    name_match = re.search(r'name:\s*(.+)', frontmatter)
    desc_match = re.search(r'description:\s*(.+)', frontmatter)

    if not name_match or not desc_match:
        print("❌ Name or description missing")
        return

    name = name_match.group(1).strip()
    description = desc_match.group(1).strip()

    # Extract/guess keywords and file patterns
    keywords = extract_keywords_from_description(description)
    file_patterns = detect_file_patterns(content)

    # Determine required tools
    requires_tools = ["run_command"]
    if 'python' in content.lower():
        requires_tools.append("write_file")

    # Priority based on skill type
    priority = 60  # Default

    # Build new frontmatter
    new_frontmatter = f"""---
name: {name}
description: {description}
priority: {priority}
activation:
  keywords: {keywords}
  file_patterns: {file_patterns}
  auto_detect: true
requires_tools: {requires_tools}
---"""

    # Combine
    new_content = new_frontmatter + "\n\n" + body

    # Save to new file
    output_path = skill_path / "SKILL_BRIAN.md"
    output_path.write_text(new_content, encoding='utf-8')

    print("=" * 80)
    print(f"✅ Converted: {name}")
    print("=" * 80)
    print()
    print("📄 Original frontmatter:")
    print("-" * 80)
    print(frontmatter)
    print()
    print("📄 New frontmatter (brian_coder format):")
    print("-" * 80)
    print(new_frontmatter)
    print()
    print(f"💾 Saved to: {output_path}")
    print()
    print("📋 Summary:")
    print(f"  - Keywords: {len(keywords)} extracted")
    print(f"  - File patterns: {len(file_patterns)} detected")
    print(f"  - Required tools: {requires_tools}")
    print()
    print("⚠️  Manual review recommended:")
    print("  1. Check if keywords are appropriate")
    print("  2. Adjust priority (60 is default)")
    print("  3. Add more specific file patterns if needed")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_open_skill.py <skill_directory>")
        print()
        print("Example:")
        print("  python convert_open_skill.py open-skills/skills/public/pdf-text-replace")
        sys.exit(1)

    skill_dir = sys.argv[1]
    convert_skill(skill_dir)


if __name__ == "__main__":
    main()

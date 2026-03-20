#!/usr/bin/env python3
"""
Test if open-skills can be loaded by common_ai_agent skill system
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common_ai_agent'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common_ai_agent', 'src'))

from core.skill_system.loader import SkillLoader
from pathlib import Path


def test_open_skills():
    """Test loading open-skills"""

    print("=" * 80)
    print("OPEN-SKILLS 호환성 테스트")
    print("=" * 80)
    print()

    # Point to open-skills directory
    open_skills_dir = Path("open-skills/skills/public")

    if not open_skills_dir.exists():
        print("❌ open-skills 디렉토리를 찾을 수 없습니다.")
        return

    print(f"📁 open-skills 경로: {open_skills_dir.absolute()}")
    print()

    # Create loader pointing to open-skills
    loader = SkillLoader(
        user_skills_dir=None,  # Don't use default
        builtin_skills_dir=open_skills_dir
    )

    # List available skills
    available = loader.list_available_skills()
    print(f"✓ 발견된 skills: {available}")
    print()

    # Try to load each skill
    for skill_name in available:
        print(f"{'='*80}")
        print(f"Skill: {skill_name}")
        print(f"{'='*80}")

        skill = loader.load_skill(skill_name)

        if skill:
            print(f"✅ 로드 성공!")
            print(f"  Name: {skill.name}")
            print(f"  Description: {skill.description}")
            print(f"  Priority: {skill.priority}")
            print(f"  Keywords: {skill.activation.keywords}")
            print(f"  File patterns: {skill.activation.file_patterns}")
            print(f"  Auto-detect: {skill.activation.auto_detect}")
            print(f"  Required tools: {skill.requires_tools}")
            print(f"  Content length: {len(skill.content)} chars")
            print()

            # Show content preview
            print("  Content preview (first 300 chars):")
            print("  " + "-" * 70)
            for line in skill.content[:300].split('\n'):
                print(f"  {line}")
            print("  ...")
            print()

            # Check if it would activate
            print("  ❗ 문제점:")
            if not skill.activation.keywords:
                print("    - Keywords 없음 (자동 activation 불가)")
            if not skill.activation.file_patterns:
                print("    - File patterns 없음 (파일 기반 activation 불가)")
            if skill.priority == 50:
                print("    - Priority가 기본값 (50) - 명시되지 않음")

        else:
            print(f"❌ 로드 실패")

        print()


def show_format_difference():
    """Show format difference"""

    print("=" * 80)
    print("포맷 비교")
    print("=" * 80)
    print()

    print("📄 open-skills SKILL.md 포맷:")
    print("-" * 80)
    print("""---
name: pdf-text-replace
description: Replace text in fillable PDF forms...
---

# PDF Text Replace Skill
...
""")

    print()
    print("📄 common_ai_agent SKILL.md 포맷:")
    print("-" * 80)
    print("""---
name: pdf-text-replace
description: Replace text in fillable PDF forms...
priority: 70                        # ← 추가 필요
activation:                         # ← 추가 필요
  keywords: [pdf, form, text, replace]
  file_patterns: ["*.pdf"]
  auto_detect: true
requires_tools: [run_command, write_file]  # ← 추가 필요
---

# PDF Text Replace Skill
...
""")

    print()
    print("⚠️  차이점:")
    print("  - open-skills: 단순 (name, description만)")
    print("  - common_ai_agent: 상세 (priority, activation, requires_tools 필요)")
    print()
    print("💡 해결 방법:")
    print("  1. open-skills SKILL.md를 common_ai_agent 포맷으로 변환")
    print("  2. 또는 common_ai_agent loader에 기본값 추가 (현재 구현됨)")
    print()


def main():
    test_open_skills()
    show_format_difference()

    print("=" * 80)
    print("결론")
    print("=" * 80)
    print()
    print("✅ open-skills SKILL.md를 common_ai_agent가 읽을 수 있습니다!")
    print("   (loader가 없는 필드는 기본값으로 채웁니다)")
    print()
    print("⚠️  하지만 문제점:")
    print("   1. keywords가 없어서 자동 activation 불가")
    print("   2. file_patterns가 없어서 파일 기반 activation 불가")
    print("   3. MCP 스크립트 실행 로직이 common_ai_agent에는 없음")
    print()
    print("🔧 사용하려면:")
    print("   1. open-skills SKILL.md에 activation 섹션 추가")
    print("   2. common_ai_agent에 MCP 스크립트 실행 기능 추가")
    print("   3. 또는 프롬프트만 활용 (스크립트 없이)")
    print()


if __name__ == "__main__":
    main()

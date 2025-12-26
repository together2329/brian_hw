#!/usr/bin/env python3
"""
Skill Activation 기준 상세 설명

실제 예시로 어떻게 점수가 계산되는지 보여줍니다.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder', 'src'))

import config
from core.skill_system import get_skill_registry, get_skill_activator


def explain_scoring():
    """점수 계산 방식 설명"""

    print("=" * 80)
    print("SKILL ACTIVATION 기준")
    print("=" * 80)
    print()

    print("📊 점수 계산 방식:")
    print()
    print("  총점 = (Keyword 점수 × 50%) + (File Pattern 점수 × 30%) + (Tool 점수 × 20%)")
    print()
    print("  1️⃣  Keyword Matching (50% - 가장 중요)")
    print("     - 사용자 메시지에서 skill의 keywords가 몇 개 매칭되는지")
    print("     - 완전 매칭: 1점, 부분 매칭: 0.5점")
    print("     - 최대 10개 키워드까지만 계산 (희석 방지)")
    print()
    print("  2️⃣  File Pattern Matching (30%)")
    print("     - 메시지에 파일명이 있고, skill의 file_patterns와 매칭되는지")
    print("     - 예: 'counter.v' → *.v 패턴 매칭")
    print()
    print("  3️⃣  Tool Requirements (20%)")
    print("     - skill이 요구하는 tool들이 사용 가능한지")
    print("     - Sub-agent 모드에서만 의미 있음 (일반 모드는 보너스 0.1점)")
    print()
    print("  ⚠️  최소 조건:")
    print("     - Keyword, File Pattern, Tool 중 최소 1개는 매칭되어야 함")
    print("     - 모두 0점이면 → 강제로 0점 (완전히 무관한 대화 차단)")
    print()
    print("  🎯 Threshold:")
    print(f"     - 현재 설정: {config.SKILL_ACTIVATION_THRESHOLD}")
    print("     - 총점이 이 값 이상이면 skill 활성화")
    print()


def show_examples():
    """실제 예시로 설명"""

    print("=" * 80)
    print("실제 예시")
    print("=" * 80)
    print()

    activator = get_skill_activator()
    registry = get_skill_registry()

    test_cases = [
        {
            "context": "Find verilog signal definition in counter.v",
            "description": "영어, verilog + signal 키워드 + *.v 파일"
        },
        {
            "context": "axi_awready 신호가 어디 있어? counter.v 파일 확인",
            "description": "한글, 키워드 없지만 *.v 파일 있음"
        },
        {
            "context": "PCIe TLP header format in specification?",
            "description": "PCIe + TLP + spec 키워드"
        },
        {
            "context": "Create testbench for AXI module",
            "description": "testbench + AXI 키워드"
        },
        {
            "context": "Hello, how are you?",
            "description": "일반 대화 (관련 없음)"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        context = test["context"]

        print(f"예시 {i}: {test['description']}")
        print(f"메시지: \"{context}\"")
        print()

        # Get all skills and calculate scores
        all_scores = []
        for skill_name in registry.list_skills():
            skill = registry.get_skill(skill_name)

            # Calculate individual scores
            kw_score = activator._keyword_match_score(skill.activation.keywords, context)
            file_score = activator._file_pattern_match_score(skill.activation.file_patterns, context)
            total = activator._calculate_activation_score(skill, context, None)

            if total > 0:
                all_scores.append({
                    'name': skill_name,
                    'kw': kw_score,
                    'file': file_score,
                    'total': total,
                    'activated': total >= config.SKILL_ACTIVATION_THRESHOLD
                })

        if all_scores:
            # Sort by total score
            all_scores.sort(key=lambda x: x['total'], reverse=True)

            print("  점수 상세:")
            for s in all_scores:
                status = "✅ ACTIVATE" if s['activated'] else "❌ Skip"
                print(f"    {s['name']:25s} → {status}")
                print(f"      Keyword: {s['kw']:.3f} × 0.5 = {s['kw']*0.5:.3f}")
                print(f"      File:    {s['file']:.3f} × 0.3 = {s['file']*0.3:.3f}")
                print(f"      Bonus:   0.100 (keyword match bonus)")
                print(f"      Total:   {s['total']:.3f} {'≥' if s['activated'] else '<'} {config.SKILL_ACTIVATION_THRESHOLD} (threshold)")
        else:
            print("  ❌ 모든 skill: 0.000점 (완전히 무관)")

        print()
        print("-" * 80)
        print()


def show_skill_keywords():
    """각 skill의 keywords 확인"""

    print("=" * 80)
    print("각 Skill의 Keywords")
    print("=" * 80)
    print()

    registry = get_skill_registry()

    for skill_name in registry.list_skills():
        skill = registry.get_skill(skill_name)

        print(f"🔧 {skill.name} (priority: {skill.priority})")
        print(f"   Keywords ({len(skill.activation.keywords)}개):")

        # Group by 5
        keywords = skill.activation.keywords
        for i in range(0, len(keywords), 5):
            group = keywords[i:i+5]
            print(f"     {', '.join(group)}")

        print(f"   File patterns: {skill.activation.file_patterns}")
        print(f"   Required tools: {skill.requires_tools}")
        print()


def main():
    explain_scoring()
    show_examples()
    show_skill_keywords()

    print("=" * 80)
    print("💡 Tip: Threshold를 조정하려면")
    print("=" * 80)
    print()
    print("  환경변수로 조정:")
    print("    export SKILL_ACTIVATION_THRESHOLD=0.2  # 더 엄격")
    print("    export SKILL_ACTIVATION_THRESHOLD=0.1  # 더 민감")
    print()
    print("  또는 config.py에서 기본값 변경")
    print()


if __name__ == "__main__":
    main()

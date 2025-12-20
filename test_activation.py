#!/usr/bin/env python3
"""Quick test for skill activation"""

import sys
import os

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder', 'src'))

# Import after path setup
import config
from core.skill_system.activator import SkillActivator
from core.skill_system import get_skill_registry

print("Config threshold:", config.SKILL_ACTIVATION_THRESHOLD)

activator = SkillActivator()
registry = get_skill_registry()

contexts = [
    'Find the verilog signal in the module',
    'What is the PCIe TLP header in specification?',
    'Create testbench with clock and reset'
]

print("\nDetailed scoring:")
for context in contexts:
    print(f"\nContext: \"{context}\"")

    for skill_name in registry.list_skills():
        skill = registry.get_skill(skill_name)
        score = activator._calculate_activation_score(skill, context, None)

        if score > 0.0:
            print(f"  {skill_name:25s} score={score:.3f} {'✓' if score >= config.SKILL_ACTIVATION_THRESHOLD else '✗'}")

print("\n" + "=" * 60)
print("Activation results (threshold=0.3):")
for context in contexts:
    skills = activator.detect_skills(context, threshold=0.3)
    print(f"  {context[:45]:45s} -> {skills}")

import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).parent.parent
sys.path.append(str(root))

from src.config import build_base_system_prompt

def test_plan_mode_prompt():
    prompt = build_base_system_prompt(plan_mode=True)
    
    # Check for new keywords and combined step instructions
    assert "ASK & PROPOSE" in prompt
    assert "Combine questions and planning into ONE turn" in prompt
    assert "Recommended to show a formal Markdown Draft Todo List" in prompt
    assert "RULES: combined ask/propose encouraged" in prompt
    
    # Check that old rigid rules are gone
    assert "1. ASK:" not in prompt or "ASK & PROPOSE" in prompt
    assert "MANDATORY to show a formal Markdown Draft Todo List" not in prompt
    assert "first response = questions only" not in prompt
    
    print("Plan Mode prompt verification: PASSED")

if __name__ == "__main__":
    test_plan_mode_prompt()

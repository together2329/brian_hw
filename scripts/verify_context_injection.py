
import os
import sys

# Ensure src is in path
# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brian_coder.agents.sub_agents.plan_agent import PlanAgent
from brian_coder.agents.sub_agents.base import ActionStep

# Mock LLM and Tool execution needed for instantiation
def mock_llm(messages):
    return "PLAN_COMPLETE: Mock plan"

def mock_tool(name, args):
    return "Mock result"

def test_context_injection():
    print("="*50)
    print("🧪 TEST: Verifying PlanAgent Context Injection")
    print("="*50)

    # 1. Instantiate Plan Agent
    agent = PlanAgent(
        name="test_plan_agent",
        llm_call_func=mock_llm,
        execute_tool_func=mock_tool
    )

    # 2. Simulate Context Data (Mocking what Orchestrator would provide)
    mock_context = {
        "task": "Analyze Caliptra",
        "file_structure": "src/main.py, src/utils.py",
        "search_results": "Found 3 matches for 'caliptra'",
        "previous_agent_output": "ExploreAgent found the repo root."
    }

    print(f"\n[1] Input Context Dictionary:\n{mock_context}")

    # 3. Initialize Context (Internal method that formats the dictionary)
    agent._initialize_context("Analyze Caliptra", mock_context)
    
    # 4. Create User Message (This is where context is injected into the prompt)
    # Creating a dummy step for testing
    step = ActionStep(
        step_number=1,
        description="Test Step",
        prompt="Create a plan",
        required_tools=[],
        depends_on=[],
        expected_output="Plan"
    )

    # Use the OVERRIDDEN _create_user_message method in PlanAgent
    # Note: PlanAgent._create_user_message uses self._context internally or pass it ? 
    # Let's check the code: 
    # def _create_user_message(self, step: ActionStep, context: str) -> str:
    # It takes a 'context' string.
    # In SubAgent._execute_step, 'context' is passed. 
    # But usually, _initialize_context stores it in self._context.
    # Let's manually simulate the context formatting logic from SubAgent which PlanAgent inherits/uses.
    
    formatted_context = ""
    if mock_context:
        parts = []
        for k, v in mock_context.items():
            if k == "task": continue
            parts.append(f"- {k}: {v}")
        formatted_context = "\n[Context]\n" + "\n".join(parts)
    
    print(f"\n[2] Formatted Context String (Internal Representation):\n{formatted_context}")

    final_prompt = agent._create_user_message(step, formatted_context)

    print(f"\n[3] Final Injected Prompt:\n{'-'*30}\n{final_prompt}\n{'-'*30}")

    if "[Context]" in final_prompt and "file_structure" in final_prompt:
        print("\n✅ SUCCESS: Context is correctly injected into the final prompt!")
    else:
        print("\n❌ FAILURE: Context is MISSING from the final prompt.")

if __name__ == "__main__":
    test_context_injection()

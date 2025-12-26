
import sys
import os
from unittest.mock import MagicMock

# Add paths to make imports work
# Add paths to make imports work
# Add paths to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../brian_coder')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.sub_agents.plan_agent import PlanAgent
from lib.display import Color

def inspect_plan_agent_input():
    """
    Simulates how PlanAgent constructs its prompt to see exactly what the LLM sees.
    """
    print(Color.system("--- Inspecting PlanAgent Input Construction ---"))
    
    # 1. Define the user task (what caused the issue)
    task = "analyze caliptra submodule hierachy and want to add debugging module at top level"
    
    # 2. Define the context (simulating the noise from the logs)
    # The logs showed a lot of previous plan history and 'files not found' errors
    context = """
user: You have an approved implementation plan. Execute the steps in order.

# Plan
## Task
analyze caplitra_ss
## Generated
2025-12-21 21:28:39

---
We need to revise the plan. We have discovered that listed files don't exist.
... [lots of history about file searching failures] ...
"""
    
    # 3. Create agent and spying mock for LLM call
    mock_llm = MagicMock(return_value="Thought: ...\nPLAN_COMPLETE: ...")
    agent = PlanAgent(
        name="debug_plan",
        llm_call_func=mock_llm,
        execute_tool_func=lambda x,y: "tool output"
    )
    
    # 4. Trigger draft_plan to see prompt construction
    agent.draft_plan(task, context=context)
    
    # 5. Extract and print the actual prompt sent to LLM
    call_args = mock_llm.call_args
    if call_args:
        messages = call_args[0][0] # First arg is messages list
        print(Color.info("\n[System Message]:"))
        print(messages[0]['content'])
        
        print(Color.info("\n[User Message]:"))
        print(messages[1]['content'])
        
        # specific check: is the Task buried?
        user_msg = messages[1]['content']
        task_idx = user_msg.find("Task:")
        context_idx = user_msg.find("Context:")
        
        print(Color.warning("\n[Analysis]:"))
        print(f"Task appears at index: {task_idx}")
        print(f"Context appears at index: {context_idx}")
        
        if context_idx < task_idx:
            print("WARNING: Context appears BEFORE Task. Large context might be overshadowing the Task.")
        else:
            print("Task appears BEFORE Context (Good).")
            
        if len(context) > 1000 and "debugging module" not in context:
             print("Context is large and likely irrelevant to the new 'debugging module' request.")

if __name__ == "__main__":
    inspect_plan_agent_input()

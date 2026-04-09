# FORMAT — ReAct Loop Output Format

Every response must follow this structure exactly:

```
Thought: <reasoning about what to do next>
Action: <tool_name>
Action Input: <JSON or plain arguments>
```

After receiving an Observation, continue with the next Thought/Action pair.
When the task is fully complete, end with:

```
Thought: All tasks are done.
Final Answer: <summary of what was accomplished>
```

## Rules

- ONE action per response — never batch multiple tool calls in one turn
- Do not fabricate Observations — wait for real tool output
- Thought must reflect genuine reasoning, not just restate the action
- Action Input must be valid JSON when the tool expects structured input

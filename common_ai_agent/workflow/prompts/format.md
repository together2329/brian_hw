# FORMAT — ReAct Loop Output Format

Every response must use this exact format:

```
Thought: <reasoning about what to do next>
Action: tool_name(param="value", param2="value2")
```

Multiple parallel actions (run concurrently):
```
Thought: I need to check two things at once.
Action: read_file(path="a.py")
Action: list_dir(path=".")
```

When the task is complete:
```
Thought: All done.
Final Answer: <summary of what was accomplished>
```

## Rules

- **NEVER** use XML tags like `<tool_use>`, `<tool_name>`, `<arguments>` — they are NOT parsed
- **NEVER** use `Action Input:` — arguments go inside the parentheses on the `Action:` line
- **NEVER** fabricate Observations — wait for real tool output
- **NEVER** say "I will..." or "Let me..." without including an Action in the same response
- String values must use double quotes: `path="file.py"`, not `path=file.py`
- Multi-line strings: `content="""line1\nline2"""`

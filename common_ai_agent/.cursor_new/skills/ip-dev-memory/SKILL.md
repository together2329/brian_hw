---
name: ip-dev-memory
description: Keep an IP development session resumable by initializing <ip>/wiki and <ip>/.git, logging stage decisions, and committing IP-local snapshots.
---

# IP Development Memory

Use this skill whenever a hardware IP is being created, debugged, verified, or
closed and the work needs to continue across LLM sessions.

## Workflow

1. Identify the IP folder.
2. Initialize memory and IP-local git:

   ```bash
   python3 scripts/ip_dev_memory.py init <ip>
   ```

3. Read the existing memory before editing:

   ```bash
   sed -n '1,220p' <ip>/wiki/llm_memory.md
   git -C <ip> log --oneline -5
   ```

4. After each stage boundary, write a memory entry:

   ```bash
   python3 scripts/ip_dev_memory.py log <ip> \
     --stage <req|rtl|lint|tb|sim|coverage|formal|signoff> \
     --title "<short event>" \
     --body "<what changed, what remains, what evidence was inspected>" \
     --evidence <ip>/<artifact>
   ```

5. Snapshot the IP folder:

   ```bash
   python3 scripts/ip_dev_memory.py snapshot <ip> --message "<stage>: <short summary>"
   ```

6. Before final completion, check both wiki and git:

   ```bash
   python3 scripts/ip_dev_memory.py check <ip> --require-git
   ```

## Output expectation

When reporting completion, include:

```text
Memory:
  wiki: <ip>/wiki/llm_memory.md
  git: <ip>/.git, latest snapshot <hash or "no new snapshot">
```

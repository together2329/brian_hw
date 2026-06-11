---
name: ip-dev-memory
description: Keep an IP development session resumable by initializing <ip>/wiki and <ip>/.git, logging stage decisions, and committing IP-local snapshots.
---

# IP Development Memory

Use this skill whenever a hardware IP is being created, debugged, verified, or
closed and the work needs to continue across LLM sessions.

## Start

Run this before editing the target IP:

```bash
python3 scripts/ip_dev_memory.py init <ip>
```

This is idempotent. If `<ip>/.git/` does not exist, it initializes an IP-local
git repository and local git identity.

Then read:

```bash
sed -n '1,220p' <ip>/wiki/llm_memory.md
git -C <ip> log --oneline -5
```

## During Work

After a meaningful requirement, RTL, TB, sim, coverage, formal, or signoff
stage boundary:

```bash
python3 scripts/ip_dev_memory.py log <ip> \
  --stage <stage> \
  --title "<short event>" \
  --body "<decision, result, next action>" \
  --evidence <ip>/<artifact>
```

After source, testbench, or evidence changes:

```bash
python3 scripts/ip_dev_memory.py snapshot <ip> --message "<stage>: <short summary>"
```

## Finish

Before claiming completion:

```bash
python3 scripts/ip_dev_memory.py check <ip> --require-git
```

Include this in the final ROCEV report when relevant:

```text
Memory:
  wiki: <ip>/wiki/llm_memory.md
  git: <ip>/.git, latest snapshot <hash or "no new snapshot">
```

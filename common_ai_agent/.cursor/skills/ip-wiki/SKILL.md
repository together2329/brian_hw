---
name: ip-wiki
description: Maintain the per-IP wiki under <ip>/wiki — init the skeleton, append dated history entries while developing, create design pages, and gate frontmatter/link integrity. Use whenever finishing a stage, making a design decision, or hitting a gotcha on an IP.
---

# Atlas IP Wiki

Every IP carries its own wiki (`<ip>/wiki/`) shaped like `doc/wiki`
(frontmatter + `[[link]]`), so design decisions and trial-and-error accumulate
as git history next to the artifacts they explain.

## Commands

```bash
python3 .cursor/scripts/ip_wiki.py init  <ip_dir>                                  # 골격 (멱등)
python3 .cursor/scripts/ip_wiki.py log   <ip_dir> --title "..." --stage sim --body "..."
python3 .cursor/scripts/ip_wiki.py page  <ip_dir> <name> --title "..." --tags a,b
python3 .cursor/scripts/ip_wiki.py check <ip_dir>                                  # rc 0/1 게이트
```

## When to log (mandatory moments)

- A stage Validation gate passes or fails 3× (rocev-chain stages: req/rtl/tb/sim)
- A design decision is made (also create a `page` if it deserves its own doc)
- A gotcha/trap is discovered (the next agent must not rediscover it)

Entry style: title = outcome ("sim 28/28 PASS"), body = evidence pointer
(gate output line, artifact path). Newest first; the helper handles dating.

## Rules

- `log.md` is append-only history — never rewrite past entries.
- `check` must PASS before claiming the wiki updated; broken `[[links]]` and
  missing frontmatter are failures, not style issues.
- The wiki explains *why*; artifacts under `sim/`, `verify/` stay the *what*.

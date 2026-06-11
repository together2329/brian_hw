---
name: rocev-ip-audit
description: Audit multiple hardware IP directories for ROCEV evidence coverage. Use when the user asks to check many IPs, compare evidence quality, or build seminar examples from local artifacts.
---

# ROCEV IP Audit

Use the repo script instead of hand-counting files.

```bash
python3 .codex_ref/scripts/rocev_ip_audit.py --limit 10 --markdown
```

For one IP:

```bash
python3 .codex_ref/scripts/rocev_ip_audit.py pwm_gen_cx1 --markdown
```

## How To Read The Result

- `closed`: enough evidence for a basic local closure call.
- `partial`: useful evidence exists, but some important evidence is missing or blocked.
- `open`: requirement/contract/evidence is too thin for a closure claim.

The audit is intentionally conservative. It is a triage aid, not final signoff.


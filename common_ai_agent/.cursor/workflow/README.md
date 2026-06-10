# Workflow Routing

`STAGE_MANIFEST.json` is the canonical routing table for agents and scripts.
Read it before searching the workflow tree when the task is "run this IP to
green", "sign off this IP", or "check harness depth".

Primary entrypoints:

```bash
bash workflow/ssot-gen/scripts/new_ip_emit_chain.sh <ip> --root <ip-parent>
python3 workflow/mutation/scripts/mutation_guard.py <ip> --root <ip-parent>
python3 workflow/signoff/scripts/check_ip_signoff.py <ip> --root <ip-parent>
```

Stage ownership:

- Locked truth lives in SSOT/spec/FL intent and requires human approval before
  semantic changes.
- LLM-editable convergence artifacts live in RTL, TB, sim, coverage, mutation,
  and signoff reports.
- Mutation guard is advisory by default. Use `--enforce-threshold` only after a
  human approves the kill-rate policy for the IP class.

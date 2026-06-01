# Run One Common-Engine Stage

Use the RTL-to-signoff runner as the common Cursor wrapper for individual workflow stages:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute --from-stage <stage> --until <stage>
```

Common stage IDs:

```text
ssot-fl-model
ssot-cycle-model
ssot-equiv-goals
ssot-rtl
lint
ssot-tb-cocotb
sim
coverage
sim-debug
goal-audit
```

For EDA stages:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile eda --execute --from-stage syn --until syn
```

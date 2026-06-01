# Run RTL To Signoff

Run the real delegated ATLAS RTL-to-signoff flow:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile full --execute
```

Common bounded runs:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile eda --execute
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile full --execute --from-stage ssot-rtl
```

The wrapper writes:

```text
<ip>/verify/cursor_rtl_to_signoff_summary.json
```

Do not hand-edit that summary; regenerate it by rerunning the command.

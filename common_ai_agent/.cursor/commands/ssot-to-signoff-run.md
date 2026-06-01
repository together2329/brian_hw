# Run SSOT To Signoff

Run from SSOT generation through signoff:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile ssot-to-signoff --provider fake --execute
```

Use `--provider real` only when live LLM/API cost is expected and credentials are configured.

For an existing SSOT, usually prefer:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute
```

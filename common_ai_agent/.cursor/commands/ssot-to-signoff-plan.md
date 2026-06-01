# Plan SSOT To Signoff

Plan from SSOT generation through DV, EDA, and final goal audit:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile ssot-to-signoff --plan
```

This includes `ssot-gen` through `src/headless_workflow.py`, then common-engine DV stages, EDA command scripts, and final `goal-audit`.

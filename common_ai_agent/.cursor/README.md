# Cursor Project Pack

This `.cursor/` folder makes Cursor operate against the same authority model as `common_ai_agent`:

- Rules: persistent project guardrails in `rules/`.
- Skills: reusable task workflows in `skills/`.
- Agents: project-specific subagents in `agents/`.
- Hooks: deterministic shell/edit/stop guards in `hooks.json` and `hooks/`.
- Commands: lightweight Cursor command recipes in `commands/`.

The canonical implementation stays in the repository source tree. Do not copy workflow validators or test scripts into `.cursor/`; reference and execute:

- `doc/wiki/index.md`
- `workflow/COMMON_ENGINE_FLOW.md`
- `workflow/*/workspace.json`
- `workflow/*/scripts/*`
- `scripts/run_tests.sh`
- `src/main.py`, `src/atlas_ui.py`, `src/textual_main.py`, `src/headless_workflow.py`

Start with `rules/00-project-core.mdc`, then use the skill that matches the task.

For a real RTL-to-signoff run, use `skills/rtl-to-signoff/`:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile full --plan
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile eda --execute
```

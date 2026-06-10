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

## v2 additions (2026-06-10)

- `hooks/stop-todo-loop.py` (stop, loop_limit 20): open todo가 남아 있으면 자동 재투입 — todo-list 기반 작업 루프.
- `hooks/subagent-evidence-check.py` (subagentStop): atlas-* 오너가 증거 없이 "완료"로 멈추면 verdict 라인 인용을 요구.
- `skills/rocev-chain` + `agents/atlas-req-gen`·`atlas-rocev-chain`: req → rtl → tb → sim을 ROCEV(Req→Obligation→Contract→Evidence→Validation)로 구동.
- `skills/atlas-ip-wiki` + `scripts/ip_wiki.py`: IP 폴더 내장 wiki(`<ip>/wiki`)에 개발 히스토리 축적 (init/log/page/check).
- `mcp.json` + `scripts/atlas_mcp_server.py`: RTL DB query MCP (`rtl_db_query`/`rtl_db_wiki` 주 툴 + `ontology_query`/`wiki_search`).
- 검증: `tests/test_cursor_pack.py` + `tests/test_ip_wiki.py` + `tests/test_atlas_mcp_server.py` (팩 무결성 ratchet 포함).

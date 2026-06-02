# External RTL Wiki Computer-Use QA Notepad

## Skill Survey
- `omo:ulw-loop`: used because the user explicitly requested `ulw loop`; durable goal, criteria, ledger, and evidence paths are tracked under this session.
- `computer-use:computer-use`: used because the user explicitly requested Computer Use for the external RTL wiki GUI surface.
- Repo skill `external-db`: used as the actual external RTL DB skill; it requires `wiki_query` and documents `wiki_query(ip="external-db", ...)` recipes.
- Repo skills `verilog-expert` and `testbench-expert`: related only; not used directly because this run does not edit RTL or testbench files.
- Repo skill `code-analysis-expert`: not used beyond ordinary file reads because the target files were already known.
- System skills `omo:programming`, `omo:debugging`, browser/chrome, documents, presentations, spreadsheets, imagegen: not used; no code edits, runtime bug fix, browser-plugin flow, document/deck/sheet, or generated bitmap asset is needed.

## Scope
- Surfaces: `skills/external-db/SKILL.md`, `core.tools.wiki_query`, `/Users/brian/Desktop/andes/wiki`, and a Mac GUI view of the local wiki page.
- Files intentionally created by this run: evidence files under `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/` and this notepad.
- No production code edits intended.

## Criteria
- C001: skill recipe and happy-path `wiki_query` prove external DB lookup returns real RTL facts.
- C002: unavailable DB edge path reports missing config instead of fabricating facts.
- C003: Computer Use opens the external wiki GUI surface and adjacent exact-fact queries still return results.

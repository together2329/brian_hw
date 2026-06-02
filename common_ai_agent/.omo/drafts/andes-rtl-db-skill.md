# Draft: Andes RTL DB Skill

## Requirements (confirmed)
- User wants the generated Andes LLM Wiki to be usable by agents like `pcie-expert`, `nvme-expert`, and `ucie-expert`.
- The skill should tell the agent which tool calls to make, especially `wiki_query(ip="external-db", ...)`.
- Wiki usage should be on/off capable through environment configuration.
- The skill must guide practical RTL fact retrieval: module, submodule, port, parameter, register, memory, FSM, datapath, clock, reset.

## Technical Decisions
- Add a dedicated `skills/andes-rtl-db/SKILL.md` for Andes-specific activation and query recipes.
- Keep `skills/external-db/SKILL.md` as the generic external reference DB skill.
- Cross-link the two skills: `andes-rtl-db` is stricter and exact-fact oriented; `external-db` remains data-source agnostic.
- The dedicated skill will require `wiki_query` and use only the configured wiki/query adapter, never direct assumptions.
- Set `andes-rtl-db` priority to `86` so it outranks protocol skills at `85` and generic `external-db` at `80`.
- Use `wiki_query(ip="external-db", ...)` as the primary recipe because `wiki_query` does not accept `ip="andes-rtl-db"`.
- Validate activation with `config.SKILL_ACTIVATION_THRESHOLD`, not the raw activator default.

## Research Findings
- Existing protocol skills (`pcie-expert`, `nvme-expert`, `ucie-expert`) use high-priority activation metadata and mandatory tool-call recipes.
- Existing `external-db` already requires `wiki_query` and supports `ATLAS_EXTERNAL_DB_*` plus legacy `ATLAS_RTL_DB_*`.
- `wiki_query` aliases include `external-db`, `rtl-db`, and `andes`.
- Andes wiki currently has exact fact-search pages and graph coverage validated against `_rtl_facts`.

## Open Questions
- None blocking. Default: create a dedicated `andes-rtl-db` skill and lightly update `external-db` to refer to it.

## Plan Artifact
- Final plan written to `plans/andes-rtl-db-skill.md`.

## Scope Boundaries
- INCLUDE: skill metadata, tool-call recipes, env on/off guidance, exact-fact query workflow, validation tests for skill loading/activation.
- EXCLUDE: changing `wiki_query` implementation, rebuilding the Andes wiki builder again, altering pcie/nvme/ucie skills.

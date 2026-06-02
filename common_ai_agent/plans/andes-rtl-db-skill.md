# Andes RTL DB Skill Work Plan

## Objective

Create a pcie/nvme-style skill that teaches agents to use the generated Andes RTL DB LLM Wiki through `wiki_query` tool calls. The skill must make the wiki usable as an on/off reference source for Andes peripheral RTL reuse and exact RTL fact lookup.

## Key Decisions

- Add a dedicated skill at `skills/andes-rtl-db/SKILL.md`.
- Keep `skills/external-db/SKILL.md` as the generic external DB skill and add a cross-link to `andes-rtl-db`; do not remove its current Andes examples or activation keywords because that would be a behavior regression.
- Set `andes-rtl-db` priority to `86`, above `pcie-expert`/`nvme-expert`/`ucie-expert` priority `85` and above `external-db` priority `80`.
- Use `requires_tools: [wiki_query]`.
- Recipes must call `wiki_query(ip="external-db", ...)`. `ip="rtl-db"` and `ip="andes"` may be documented as accepted aliases, but never use `ip="andes-rtl-db"` because `wiki_query` does not accept that alias.
- The skill is a prompt/instruction layer, not hard runtime enforcement. Acceptance verifies that loader metadata and injected prompt text tell the agent to call `wiki_query`.
- On/off behavior is env-driven:
  - ON: `ATLAS_EXTERNAL_DB_WIKI=/Users/brian/Desktop/andes/wiki` and `ATLAS_EXTERNAL_DB_NO_REBUILD=1`
  - Legacy ON: `ATLAS_RTL_DB_WIKI=/Users/brian/Desktop/andes/wiki` and `ATLAS_RTL_DB_NO_REBUILD=1`
  - OFF: unset those wiki/query env vars or do not activate/use the skill.
- If `wiki_query` reports missing config or no match, the skill must tell agents to say that plainly and continue from the active SSOT/spec. It must forbid fabricated external DB citations.

## Scope

IN:
- New `skills/andes-rtl-db/SKILL.md`.
- Small update to `skills/external-db/SKILL.md` for `related_skills` and body cross-reference.
- Assertion-based pytest coverage for skill loading, metadata, activation, prompt recipe content, and `external-db` regression.
- Manual QA against the already-built `/Users/brian/Desktop/andes/wiki`.

OUT:
- No changes to `core/tools.py`.
- No new `wiki_query` alias.
- No rebuild of the Andes wiki builder.
- No changes to `pcie-expert`, `nvme-expert`, or `ucie-expert`.
- No new scripts unless test setup proves unavoidable.

## References

- `skills/external-db/SKILL.md`: generic external DB pattern and current `wiki_query` recipe.
- `skills/pcie-expert/SKILL.md`: strict mandatory tool-use style.
- `skills/nvme-expert/SKILL.md`: compact protocol skill structure.
- `skills/ucie-expert/SKILL.md`: compact protocol skill structure.
- `core/skill_system/loader.py`: skill discovery and metadata parsing.
- `core/skill_system/activator.py`: keyword/tool/file activation scoring.
- `tests/test_andes_rtl_db_quality.py`: existing exact-fact wiki query regression coverage.
- `tests/test_wiki_query_tool.py`: external DB `wiki_query` alias and env behavior coverage.

## Implementation Tasks

### Task 1: Add RED Tests For Skill Loading And Activation

Ownership:
- Create `tests/test_andes_rtl_db_skill.py`.

Implement tests first and confirm they fail before creating the skill.

Test cases:
- `test_andes_rtl_db_skill_loads_from_builtin_skills`
  - Given `SkillLoader()`
  - When loading `andes-rtl-db`
  - Then it loads, `skill.name == "andes-rtl-db"`, `priority == 86`, `requires_tools` contains `wiki_query`, and `source_path` points to `skills/andes-rtl-db/SKILL.md`.
- `test_andes_rtl_db_skill_prompt_contains_required_wiki_query_recipes`
  - Given the loaded skill
  - When reading `skill.format_for_prompt()`
  - Then it contains `wiki_query(ip="external-db"` and all exact-fact categories: `module`, `submodule`, `port`, `parameter`, `register`, `memory`, `fsm`, `datapath`, `clock`, `reset`.
  - Then it contains fallback wording for unavailable DB/no match.
- `test_andes_rtl_db_skill_auto_activates_for_andes_rtl_context`
  - Given `SkillActivator`
  - When detecting with `threshold=config.SKILL_ACTIVATION_THRESHOLD` and `allowed_tools={"wiki_query"}`
  - Contexts:
    - `Andes atcuart100 register fsm datapath를 참고해서 RTL 설계해줘`
    - `reuse existing Andes SPI flash bridge ports and parameters`
    - `atcdmac100 dma_req_i signal from rtl db`
  - Then `andes-rtl-db` is in the detected skill list.
- `test_external_db_skill_still_loads_and_links_andes_skill`
  - Given `SkillLoader()`
  - When loading `external-db`
  - Then it still loads, still requires `wiki_query`, and `related_skills` includes `andes-rtl-db`.

Expected RED evidence:
- `python3 -m pytest tests/test_andes_rtl_db_skill.py -q`
- Failure reason should be missing `andes-rtl-db` skill and/or missing cross-link, not import errors.

### Task 2: Create `skills/andes-rtl-db/SKILL.md`

Ownership:
- `skills/andes-rtl-db/SKILL.md`.

Frontmatter:
- `name: andes-rtl-db`
- `description`: mention Andes RTL DB, LLM Wiki, exact RTL facts, `wiki_query`, UART/SPI/I2C/GPIO/DMA/APB/AHB/timer/watchdog/RTC, module/port/parameter/register/memory/FSM/datapath/clock/reset.
- `priority: 86`
- `activation.keywords`: include `andes`, `rtl db`, `llm wiki`, `atcuart100`, `atcspi200`, `atcdmac100`, `atcgpio100`, `atciic100`, `atcpit100`, `atcrtc100`, `atcwdt200`, `atcbmc200`, `apb`, `ahb`, `uart`, `spi`, `i2c`, `gpio`, `dma`, `register`, `fsm`, `datapath`, `submodule`, `port`, `parameter`, `clock`, `reset`.
- `activation.file_patterns`: `["*.sv", "*.v", "*.md", "*.json"]`
- `activation.auto_detect: true`
- `requires_tools: [wiki_query]`
- `related_skills: [external-db, verilog-expert, testbench-expert]`

Body requirements:
- Open with a strict rule mirroring protocol skills: before using or claiming Andes RTL reference facts, call `wiki_query`.
- State that the skill uses the tool; the wiki is the corpus.
- Start broad then drill down:
  - `wiki_query(ip="external-db", topic="<family> <bus> module port parameter", depth=3)`
  - `wiki_query(ip="external-db", topic="<block> submodule hierarchy instance", depth=3)`
  - `wiki_query(ip="external-db", topic="<block> register memory fsm datapath clock reset", depth=3)`
  - `wiki_query(ip="external-db", topic="<block> <exact_fact_name>", depth=3)`
- Exact-fact recipes:
  - module/submodule: `<block> module`, `<block> submodule hierarchy instance`
  - ports/parameters: `<block> port`, `<block> parameter`, `<block> <signal_or_param>`
  - registers/memory: `<block> register`, `<block> memory`, `<block> <reg_or_mem_name>`
  - FSM/datapath: `<block> fsm`, `<block> datapath`, `<block> <state_or_signal>`
  - clock/reset: `<block> clock`, `<block> reset`, `<block> clk rst`
- Source-of-truth hierarchy:
  - `wiki_query` result first for discovery
  - `_rtl_facts/<block>.json` for extracted facts
  - original RTL source under `/Users/brian/Desktop/andes/<block>/hdl` for final confirmation
  - active IP SSOT/spec wins on conflict with reference design
- Env guidance:
  - show ON/OFF commands exactly.
  - say `ATLAS_EXTERNAL_DB_*` preferred, `ATLAS_RTL_DB_*` legacy accepted.
- Failure rules:
  - If no match, say no external DB match and continue.
  - Never invent signal names, register names, or citations.
  - Never claim `_rtl_facts` content without a query/opened source result.

### Task 3: Cross-Link `external-db`

Ownership:
- `skills/external-db/SKILL.md`.

Make a minimal update:
- Add `andes-rtl-db` to `related_skills`.
- Add a short body note:
  - Use `andes-rtl-db` for Andes-specific exact RTL fact workflows.
  - Keep `external-db` for generic previous-project/reference-DB workflows.

Do not remove existing Andes examples or keywords in this pass.

### Task 4: GREEN The Skill Tests

Ownership:
- Same files as Tasks 1-3.

Run:
```sh
python3 -m pytest tests/test_andes_rtl_db_skill.py -q
```

Acceptance:
- All new tests pass.
- The RED failure from Task 1 is specifically fixed by the skill/cross-link files.

### Task 5: Validate Actual Andes Wiki Tool Recipes

Ownership:
- Read-only QA using `/Users/brian/Desktop/andes/wiki`.

Run a small Python or direct tool smoke check with env:
```sh
export ATLAS_EXTERNAL_DB_WIKI=/Users/brian/Desktop/andes/wiki
export ATLAS_EXTERNAL_DB_NO_REBUILD=1
```

Queries to verify:
- `wiki_query(ip="external-db", topic="uart sub module atcuart100 module", depth=2)`
- `wiki_query(ip="external-db", topic="atcuart100 register", depth=2)`
- `wiki_query(ip="external-db", topic="atcuart100 fsm", depth=2)`
- `wiki_query(ip="external-db", topic="atcuart100 oscr_reg", depth=2)`
- `wiki_query(ip="external-db", topic="atcspi200 port spi_clk_out", depth=2)`
- `wiki_query(ip="external-db", topic="atcdmac100 port dma_req_i", depth=2)`

Acceptance:
- Every query returns `scope=rtl-db` and not `matches=0`.
- Exact fact queries return either a `fact-<block>-...` page or the canonical block page.
- Record the first result line for final evidence.

### Task 6: Regression Test Existing Wiki And Skill Behavior

Run:
```sh
python3 -m pytest \
  tests/test_andes_rtl_db_skill.py \
  tests/test_andes_rtl_db_quality.py \
  tests/test_andes_rtl_db_wiki_builder.py \
  tests/test_wiki_query_tool.py \
  tests/test_ip_workflow_scaffold_and_wiki_pointers.py \
  tests/test_wiki_build_graph.py \
  -q
```

Run LSP diagnostics on any edited Python test files:
- `tests/test_andes_rtl_db_skill.py`

Run pure LOC check:
```sh
awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(#|\/\/)/' tests/test_andes_rtl_db_skill.py | wc -l
```

Acceptance:
- Pytest passes.
- LSP error diagnostics are clean.
- New Python test file remains under 250 pure LOC.
- No code or builder files are edited.

## Final Verification Wave

Before final response:
- `git diff --check -- skills/andes-rtl-db/SKILL.md skills/external-db/SKILL.md tests/test_andes_rtl_db_skill.py`
- `git status --porcelain -- skills/andes-rtl-db/SKILL.md skills/external-db/SKILL.md tests/test_andes_rtl_db_skill.py`
- Confirm no changes to `core/tools.py`, `scripts/build_andes_rtl_db_wiki.py`, or `scripts/andes_rtl_db_search.py`.
- Summarize:
  - skill path
  - exact tool-call recipes
  - env on/off
  - tests run
  - actual wiki query smoke evidence

## Defaults Applied

- Dedicated skill instead of only modifying `external-db`, because user asked for pcie/nvme-like behavior and the generic skill should stay generic.
- Co-activation instead of replacement, because `external-db` already works and removing Andes terms would be a regression.
- App config activation threshold for tests, because that reflects runtime activation better than `SkillActivator.detect_skills` default.
- `external-db` alias for all recipes, because it is already accepted by `wiki_query` and matches the generic tool contract.

## Risks And Guardrails

- A skill cannot force runtime tool execution by itself. Guardrail: verify prompt text includes mandatory `wiki_query` recipes and no-guess rules.
- Too many generic keywords could over-activate. Guardrail: keep Andes block names and RTL fact words prominent; rely on priority ordering and existing `external-db` co-activation.
- Env docs can drift from tool behavior. Guardrail: document both preferred `ATLAS_EXTERNAL_DB_*` and legacy `ATLAS_RTL_DB_*`, but do not change tool messages in this plan.
- Existing dirty worktree may contain unrelated files. Guardrail: only touch the three planned files.

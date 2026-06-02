# External RTL Wiki Skill Tool-Call QA Plan

## TL;DR
> Summary:      Test the existing `external-db` skill, `wiki_query` aliases, and the live Andes wiki through evidence-bound ulw-loop QA. No production code changes are planned.
> Deliverables:
> - Static skill/tool contract evidence
> - External wiki graph and exact fact evidence
> - CLI happy, alias, missing-config, and empty-wiki transcripts
> - Computer Use GUI action log and screenshot for `atcuart100.md`
> - ulw-loop evidence records for C001-C003
> Effort:       Short
> Risk:         Medium - live GUI/Computer Use evidence and a dirty worktree can make cleanup/accounting fragile.

## Scope
### Must have
- Use the existing ulw-loop run `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2` as the durable state and evidence root.
- Verify `skills/external-db/SKILL.md` requires `wiki_query` and instructs `wiki_query(ip="external-db", ...)`.
- Verify `core.tools.wiki_query` can read `/Users/brian/Desktop/andes/wiki` through `ATLAS_EXTERNAL_DB_WIKI` and returns `scope=rtl-db`.
- Verify `external-db`, `rtl-db`, and `andes` aliases all use the external RTL DB scope, not an IP directory scope.
- Verify exact live wiki facts: `atcuart100` contains `oscr_reg`, `atcspi200` contains `spi_clk_out`, and `atcdmac100` contains `dma_req` / `dma_mst_req`.
- Verify unavailable and empty external DB behavior is explicit and does not fabricate a citation.
- Drive a local GUI view with Computer Use and capture both an action log and screenshot showing `atcuart100` and `oscr_reg`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Must NOT edit production code, tests, skill files, or the external Andes wiki.
- Must NOT add `skills/andes-rtl-db/SKILL.md`; this plan tests the existing `external-db` skill path.
- Must NOT rebuild or clobber `/Users/brian/Desktop/andes/wiki/_graph.json`; use `ATLAS_EXTERNAL_DB_NO_REBUILD=1`.
- Must NOT mark an ulw-loop criterion passed from tests alone; every pass needs the named evidence artifact and cleanup receipt.
- Must NOT record C003 pass against `dma_req_i` unless the corpus actually contains that exact term. Based on exploration, the current corpus exposes `dma_req` and `dma_mst_req`, not `dma_req_i`.
- Must NOT use Browser-only evidence as a replacement for the requested Computer Use GUI evidence.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + pytest as supporting regression only; primary proof is CLI stdout, parsed corpus dumps, and Computer Use artifacts.
- QA policy: every task has agent-executed scenarios
- Evidence: `evidence/task-<N>-<slug>.<ext>` under `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Initialize evidence/run-state baseline
- Task 2: Verify static skill/tool contract
- Task 3: Verify external wiki corpus and align C003 fact wording if needed

Wave 2 (after Wave 1):
- Task 4: depends [1, 2, 3]
- Task 5: depends [1, 2, 3]
- Task 6: depends [1, 3]

Wave 3 (after Wave 2):
- Task 7: depends [4, 5, 6]

Critical path: Task 1 -> Task 3 -> Task 6 -> Task 7

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 4, 5, 6, 7 | 2, 3 |
| 2    | none       | 4, 5 | 1, 3 |
| 3    | none       | 4, 5, 6 | 1, 2 |
| 4    | 1, 2, 3    | 7 | 5, 6 |
| 5    | 1, 2, 3    | 7 | 4, 6 |
| 6    | 1, 3       | 7 | 4, 5 |
| 7    | 4, 5, 6    | final verification | none |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Initialize evidence/run-state baseline

  What to do: Confirm the existing ulw-loop run files, create the evidence directory if absent, capture pending criteria, and snapshot the dirty worktree without changing unrelated files.
  Must NOT do: Do not edit `goals.json` or `ledger.jsonl` in this task.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5, 6, 7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/brief.md:1` - original brief for this QA run.
  - Pattern:  `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/goals.json:11` - goal id `G001-test-the-external-rtl-wiki-skill-too`.
  - Pattern:  `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/goals.json:15` - C001-C003 success criteria array.
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:45` - ulw-loop artifact locations.
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:137` - per-criterion execution loop.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/brief.md && test -f .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/goals.json && test -f .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/ledger.jsonl`
  - [ ] `test -d .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence`
  - [ ] `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-1-run-state.txt` lists C001, C002, and C003.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: run-state capture
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; mkdir -p "$EVID"; python3 - "$RUN" <<'PY' > "$EVID/task-1-run-state.txt"
              import json, sys
              from pathlib import Path
              run = Path(sys.argv[1])
              goals = json.loads((run / "goals.json").read_text())
              goal = goals["goals"][0]
              print(goal["id"])
              for c in goal["successCriteria"]:
                  print(c["id"], c["status"], c["expectedEvidence"])
              assert goal["id"] == "G001-test-the-external-rtl-wiki-skill-too"
              assert {c["id"] for c in goal["successCriteria"]} == {"C001", "C002", "C003"}
              PY
              git status --short > "$EVID/task-1-git-status.txt"
    Expected: task-1-run-state.txt contains C001, C002, C003 and task-1-git-status.txt exists.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-1-run-state.txt

  Scenario: missing evidence directory recovery
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; mkdir -p "$EVID"; test -d "$EVID"; printf 'cleanup: evidence dir ensured; no runtime resources\n' > "$EVID/task-1-cleanup.txt"
    Expected: test exits 0 and cleanup receipt exists.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-1-cleanup.txt
  ```

  Commit: NO | Message: `test(external-db): capture ulw run baseline` | Files: [.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-1-run-state.txt, .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-1-git-status.txt]

- [ ] 2. Verify static skill/tool contract

  What to do: Prove the repo-local `external-db` skill requires `wiki_query`, documents the `external-db` recipe, accepts `rtl-db`/`andes` aliases, and that the tool schema exposes the same contract.
  Must NOT do: Do not create or edit any skill file.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `skills/external-db/SKILL.md:24` - `requires_tools: [wiki_query]`.
  - Pattern:  `skills/external-db/SKILL.md:51` - "How to query" section.
  - Pattern:  `skills/external-db/SKILL.md:54` - canonical `wiki_query(ip="external-db", ...)` recipe.
  - Pattern:  `skills/external-db/SKILL.md:56` - `rtl-db` / `andes` accepted aliases.
  - Pattern:  `skills/external-db/SKILL.md:83` - no unsupported DB claims without `wiki_query`.
  - API/Type: `core/tool_schema.py:1139` - `wiki_query` schema registration.
  - API/Type: `core/tool_schema.py:1142` - read-only project/IP/RTL DB description.
  - API/Type: `core/tool_schema.py:1151` - `ip` parameter aliases.
  - API/Type: `core/tools.py:8327` - runtime tool table exports `wiki_query`.
  - API/Type: `core/skill_system/loader.py:254` - skill listing discovers `SKILL.md` directories.
  - API/Type: `src/main.py:846` - runtime active skill loading.
  - API/Type: `core/prompt_builder.py:455` - active skill prompt block injection.

  Acceptance criteria (agent-executable only):
  - [ ] `python3 - <<'PY'` command in the happy path exits 0 and prints `skill=external-db requires=wiki_query`.
  - [ ] `test ! -f skills/andes-rtl-db/SKILL.md` exits 0.
  - [ ] `rg -n '"wiki_query": wiki_query' core/tools.py` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: static skill and schema contract
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; python3 - <<'PY' > "$EVID/task-2-skill-contract.txt"
              from pathlib import Path
              from core.skill_system.loader import SkillLoader
              skill_path = Path("skills/external-db/SKILL.md")
              schema_path = Path("core/tool_schema.py")
              tools_path = Path("core/tools.py")
              skill_text = skill_path.read_text()
              schema_text = schema_path.read_text()
              tools_text = tools_path.read_text()
              assert "requires_tools: [wiki_query]" in skill_text
              assert 'wiki_query(ip="external-db"' in skill_text
              assert '"rtl-db"' in skill_text and '"andes"' in skill_text
              assert "Never claim something exists in the external DB without a `wiki_query` result" in skill_text
              assert '"wiki_query": _fn(' in schema_text
              assert 'ip="rtl-db" (or "andes")' in schema_text
              assert '"wiki_query": wiki_query' in tools_text
              assert not Path("skills/andes-rtl-db/SKILL.md").exists()
              loaded = SkillLoader().load_skill("external-db")
              assert loaded is not None
              assert "wiki_query" in loaded.requires_tools
              print("skill=external-db requires=wiki_query aliases=external-db,rtl-db,andes")
              print("cleanup: read-only static checks; no runtime resources")
              PY
    Expected: Output contains `skill=external-db requires=wiki_query aliases=external-db,rtl-db,andes`.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-2-skill-contract.txt

  Scenario: absent Andes-specific skill guardrail
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; test ! -f skills/andes-rtl-db/SKILL.md; printf 'skills/andes-rtl-db/SKILL.md absent; use external-db skill\ncleanup: read-only file existence check\n' > "$EVID/task-2-andes-skill-absent.txt"
    Expected: test exits 0 and evidence says the Andes-specific skill is absent.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-2-andes-skill-absent.txt
  ```

  Commit: NO | Message: `test(external-db): verify skill contract` | Files: [.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-2-skill-contract.txt]

- [ ] 3. Verify external wiki corpus and align C003 fact wording if needed

  What to do: Parse `/Users/brian/Desktop/andes/wiki/_graph.json` and representative pages/sidecars. Prove exact live terms before using them in tool-call and GUI QA. If pending C003 still says `dma_req_i` and the corpus does not contain it, revise the criterion through ulw-loop steering to use `dma_req` / `dma_mst_req`.
  Must NOT do: Do not edit `/Users/brian/Desktop/andes/wiki`, do not rebuild `_graph.json`, and do not hand-edit ulw-loop JSON.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5, 6] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - External: `/Users/brian/Desktop/andes/wiki/_graph.json` - live external graph; current exploration found `node_count=502`.
  - External: `/Users/brian/Desktop/andes/wiki/atcuart100.md:11` - summary includes `oscr_reg`.
  - External: `/Users/brian/Desktop/andes/wiki/_rtl_facts/atcuart100.json:154` - sidecar assignment for `oscr_reg`.
  - External: `/Users/brian/Desktop/andes/wiki/atcspi200.md:11` - summary includes `spi_clk_out`.
  - External: `/Users/brian/Desktop/andes/wiki/atcspi200.md:87` - top-level interface lists `spi_clk_out`.
  - External: `/Users/brian/Desktop/andes/wiki/atcdmac100.md:28` - top-level interface lists `dma_req`.
  - External: `/Users/brian/Desktop/andes/wiki/_rtl_facts/atcdmac100.json:46` - sidecar assignment includes `dma_mst_req`.
  - External: `doc/wiki/andes-rtl-db-wiki-20260527.md:46` - enable/disable env vars for the Andes wiki.
  - External: `doc/wiki/andes-rtl-db-wiki-20260527.md:62` - alias query examples.
  - External: `doc/wiki/external-rtl-db-integration-guide.md:28` - generated content includes block pages, `_rtl_facts`, and `_graph.json`.
  - External: `doc/wiki/external-rtl-db-integration-guide.md:35` - `ATLAS_EXTERNAL_DB_WIKI` / `ATLAS_RTL_DB_WIKI` enablement.
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:183` - structured steering is the supported way to revise criteria.

  Acceptance criteria (agent-executable only):
  - [ ] `task-3-corpus-baseline.txt` contains `node_count=502`, `atcuart100:oscr_reg`, `atcspi200:spi_clk_out`, and `atcdmac100:dma_req`.
  - [ ] If `goals.json` contains `dma_req_i`, then `task-3-c003-steer.json` exists and records a `revise_criterion` command, or the executor records a BLOCKED result explaining the missing CLI.
  - [ ] `_graph.json` mtime before and after this task is identical.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: corpus fact baseline
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; GRAPH=/Users/brian/Desktop/andes/wiki/_graph.json; before=$(stat -f %m "$GRAPH"); python3 - <<'PY' > "$EVID/task-3-corpus-baseline.txt"
              import json
              from pathlib import Path
              root = Path("/Users/brian/Desktop/andes/wiki")
              graph = json.loads((root / "_graph.json").read_text())
              assert graph.get("schema_version") == "wiki_graph.v1"
              assert graph.get("node_count") == 502
              ids = {node.get("id") for node in graph.get("nodes", [])}
              assert {"atcuart100", "atcspi200", "atcdmac100", "coverage"}.issubset(ids)
              uart = (root / "atcuart100.md").read_text()
              spi = (root / "atcspi200.md").read_text()
              dma = (root / "atcdmac100.md").read_text()
              uart_facts = (root / "_rtl_facts" / "atcuart100.json").read_text()
              spi_facts = (root / "_rtl_facts" / "atcspi200.json").read_text()
              dma_facts = (root / "_rtl_facts" / "atcdmac100.json").read_text()
              assert "oscr_reg" in uart and "oscr_reg" in uart_facts
              assert "spi_clk_out" in spi and "spi_clk_out" in spi_facts
              assert "dma_req" in dma and "dma_mst_req" in dma_facts
              assert "dma_req_i" not in dma and "dma_req_i" not in dma_facts
              print("schema=wiki_graph.v1")
              print("node_count=502")
              print("atcuart100:oscr_reg")
              print("atcspi200:spi_clk_out")
              print("atcdmac100:dma_req dma_mst_req")
              print("dma_req_i=absent")
              print("cleanup: read-only corpus parse; no runtime resources")
              PY
              after=$(stat -f %m "$GRAPH"); test "$before" = "$after"; printf 'graph_mtime_before=%s\ngraph_mtime_after=%s\ncleanup: graph not modified\n' "$before" "$after" > "$EVID/task-3-graph-mtime.txt"
    Expected: corpus baseline exits 0 and graph mtime before/after is identical.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-3-corpus-baseline.txt

  Scenario: C003 criterion wording alignment
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; if rg -q 'dma_req_i' "$RUN/goals.json"; then omo ulw-loop steer --kind revise_criterion --goal-id G001-test-the-external-rtl-wiki-skill-too --criterion-id C003 --scenario "Computer Use GUI regression: open file:///Users/brian/Desktop/andes/wiki/atcuart100.md in a local Mac GUI app via Computer Use, find the page title and exact register term oscr_reg on screen; PASS iff Computer Use action log and screenshot show atcuart100 and oscr_reg visible. Also run CLI adjacent exact-fact queries for atcspi200 spi_clk_out and atcdmac100 dma_req dma_mst_req." --expected-evidence ".omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-computer-use-action-log.txt, .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-computer-use-screenshot.png, and .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-adjacent-regression.txt" --evidence "$EVID/task-3-corpus-baseline.txt shows dma_req_i absent and dma_req/dma_mst_req present." --rationale "C003 must name observable facts from the configured external wiki." --json > "$EVID/task-3-c003-steer.json"; else printf 'C003 already aligned; no steer needed\ncleanup: no runtime resources\n' > "$EVID/task-3-c003-steer.json"; fi
    Expected: evidence exists; if steering was needed, C003 no longer requires nonexistent `dma_req_i`.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-3-c003-steer.json
  ```

  Commit: NO | Message: `test(external-db): validate Andes wiki corpus` | Files: [.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-3-corpus-baseline.txt]

- [ ] 4. Execute CLI happy path for `wiki_query(ip="external-db")`

  What to do: Run the actual `wiki_query` function with command-scoped env vars pointing at `/Users/brian/Desktop/andes/wiki`, using the `external-db` alias and `ATLAS_EXTERNAL_DB_NO_REBUILD=1`. Capture stdout as C001 evidence.
  Must NOT do: Do not set persistent shell env vars and do not let an external query/builder override this path.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [7] | Blocked by: [1, 2, 3]

  References (executor has NO interview context - be exhaustive):
  - API/Type: `core/tools.py:7731` - external wiki resolver.
  - API/Type: `core/tools.py:7741` - `ATLAS_EXTERNAL_DB_WIKI` preferred over `ATLAS_RTL_DB_WIKI`.
  - API/Type: `core/tools.py:7750` - `wiki_query` implementation.
  - API/Type: `core/tools.py:7787` - external alias set.
  - API/Type: `core/tools.py:7798` - aliases switch to `scope=rtl-db`.
  - API/Type: `core/tools.py:7969` - depth/max node clamps.
  - API/Type: `core/tools.py:7971` - topic term normalization.
  - API/Type: `core/tools.py:8039` - output header includes scope, depth, matches, shown.
  - Test:     `tests/test_wiki_query_tool.py:94` - external RTL DB wiki without IP scope.
  - Test:     `tests/test_andes_rtl_db_quality.py:78` - `ATLAS_EXTERNAL_DB_WIKI` with `external-db`.

  Acceptance criteria (agent-executable only):
  - [ ] `C001-wiki-query-happy.txt` contains `scope=rtl-db`.
  - [ ] `C001-wiki-query-happy.txt` does not contain `matches=0`.
  - [ ] `C001-wiki-query-happy.txt` contains both `atcuart100` and `oscr_reg`.
  - [ ] `/Users/brian/Desktop/andes/wiki/_graph.json` mtime is unchanged during the task.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: external-db happy path
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; GRAPH=/Users/brian/Desktop/andes/wiki/_graph.json; before=$(stat -f %m "$GRAPH"); env -u ATLAS_EXTERNAL_DB_QUERY -u ATLAS_RTL_DB_QUERY -u ATLAS_EXTERNAL_DB_BUILDER -u ATLAS_RTL_DB_BUILDER ATLAS_PROJECT_ROOT="$PWD" COMMON_AI_AGENT_HOME="$PWD" ATLAS_EXTERNAL_DB_WIKI=/Users/brian/Desktop/andes/wiki ATLAS_EXTERNAL_DB_NO_REBUILD=1 python3 - <<'PY' > "$EVID/C001-wiki-query-happy.txt"
              from core.tools import wiki_query
              out = wiki_query(ip="external-db", topic="atcuart100 register oscr_reg", depth=3, max_nodes=3)
              print(out)
              assert "scope=rtl-db" in out
              assert "matches=0" not in out
              assert "atcuart100" in out.lower()
              assert "oscr_reg" in out
              print("cleanup: command-scoped env only; no runtime resources")
              PY
              after=$(stat -f %m "$GRAPH"); test "$before" = "$after"; printf 'graph_mtime_before=%s\ngraph_mtime_after=%s\ncleanup: graph not modified\n' "$before" "$after" > "$EVID/task-4-graph-mtime.txt"
    Expected: command exits 0; output contains `scope=rtl-db`, `atcuart100`, and `oscr_reg`; graph mtime unchanged.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C001-wiki-query-happy.txt

  Scenario: misleading success guard
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; python3 - "$EVID/C001-wiki-query-happy.txt" <<'PY' > "$EVID/task-4-misleading-success-guard.txt"
              import sys
              text = open(sys.argv[1], encoding="utf-8").read()
              assert "IP directory not found" not in text
              assert "ATLAS_RTL_DB_WIKI is not configured" not in text
              assert "matches=0" not in text
              print("happy-path output is not a misleading empty/error success")
              print("cleanup: read-only transcript check")
              PY
    Expected: guard exits 0.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-4-misleading-success-guard.txt
  ```

  Commit: NO | Message: `test(external-db): capture wiki_query happy path` | Files: [.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C001-wiki-query-happy.txt]

- [ ] 5. Execute alias, missing-config, and empty-wiki edge paths

  What to do: Verify all accepted aliases hit the same `scope=rtl-db` behavior. Then verify missing config and empty external wiki paths return explicit non-fabricated errors.
  Must NOT do: Do not leave temporary directories behind and do not set persistent env vars.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [7] | Blocked by: [1, 2, 3]

  References (executor has NO interview context - be exhaustive):
  - API/Type: `core/tools.py:7787` - accepted external aliases.
  - API/Type: `core/tools.py:7798` - aliases set `scope_kind = "rtl-db"`.
  - API/Type: `core/tools.py:7827` - missing external wiki config.
  - API/Type: `core/tools.py:7864` - empty external wiki with no markdown.
  - API/Type: `core/tools.py:7962` - missing graph behavior.
  - Test:     `tests/test_wiki_query_tool.py:129` - missing external config test.
  - Test:     `tests/test_wiki_query_tool.py:310` - no-rebuild shipped graph behavior.
  - Test:     `tests/test_wiki_query_tool.py:362` - external query adapter override behavior.
  - External: `scripts/example_external_rtl_db_query.py:14` - external query adapter contract.
  - External: `scripts/example_external_rtl_db_builder.py:17` - external builder contract.

  Acceptance criteria (agent-executable only):
  - [ ] `task-5-aliases.txt` contains `alias external-db ok`, `alias rtl-db ok`, and `alias andes ok`.
  - [ ] `C002-missing-config-edge.txt` contains `ATLAS_RTL_DB_WIKI is not configured`.
  - [ ] `task-5-empty-wiki-edge.txt` contains `external RTL DB wiki has no markdown files`.
  - [ ] `task-5-empty-cleanup.txt` proves the temp directory was removed.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: alias parity
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; env -u ATLAS_EXTERNAL_DB_QUERY -u ATLAS_RTL_DB_QUERY -u ATLAS_EXTERNAL_DB_BUILDER -u ATLAS_RTL_DB_BUILDER ATLAS_PROJECT_ROOT="$PWD" COMMON_AI_AGENT_HOME="$PWD" ATLAS_EXTERNAL_DB_WIKI=/Users/brian/Desktop/andes/wiki ATLAS_EXTERNAL_DB_NO_REBUILD=1 python3 - <<'PY' > "$EVID/task-5-aliases.txt"
              from core.tools import wiki_query
              for alias in ("external-db", "rtl-db", "andes"):
                  out = wiki_query(ip=alias, topic="atcuart100 oscr_reg", depth=3, max_nodes=2)
                  assert "scope=rtl-db" in out, alias
                  assert "IP directory not found" not in out, alias
                  assert "atcuart100" in out.lower(), alias
                  assert "oscr_reg" in out, alias
                  print(f"alias {alias} ok")
              print("cleanup: command-scoped env only; no runtime resources")
              PY
    Expected: all three aliases print `ok` and no alias reports an IP directory error.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-5-aliases.txt

  Scenario: unavailable DB does not fabricate
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; env -u ATLAS_EXTERNAL_DB_WIKI -u ATLAS_RTL_DB_WIKI -u ATLAS_EXTERNAL_DB_QUERY -u ATLAS_RTL_DB_QUERY -u ATLAS_EXTERNAL_DB_BUILDER -u ATLAS_RTL_DB_BUILDER python3 - <<'PY' > "$EVID/C002-missing-config-edge.txt"
              from core.tools import wiki_query
              out = wiki_query(ip="external-db", topic="atcuart100 register", depth=3)
              print(out)
              assert "ATLAS_RTL_DB_WIKI is not configured" in out
              assert "atcuart100 RTL reference" not in out
              print("cleanup: command-scoped env only; no runtime resources")
              PY
    Expected: output reports missing config and contains no fabricated `atcuart100 RTL reference`.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C002-missing-config-edge.txt

  Scenario: empty external wiki edge
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; tmp=$(mktemp -d); env -u ATLAS_EXTERNAL_DB_QUERY -u ATLAS_RTL_DB_QUERY -u ATLAS_EXTERNAL_DB_BUILDER -u ATLAS_RTL_DB_BUILDER ATLAS_EXTERNAL_DB_WIKI="$tmp" python3 - <<'PY' > "$EVID/task-5-empty-wiki-edge.txt"; status=$?; rm -rf "$tmp"; test ! -e "$tmp"; printf 'removed_temp=%s\ncleanup: rm -rf temp empty wiki\n' "$tmp" > "$EVID/task-5-empty-cleanup.txt"; exit $status
              from core.tools import wiki_query
              out = wiki_query(ip="external-db", topic="uart", depth=3)
              print(out)
              assert "external RTL DB wiki has no markdown files" in out
              assert "atcuart100 RTL reference" not in out
              PY
    Expected: output reports no markdown files; temp directory is removed.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-5-empty-wiki-edge.txt
  ```

  Commit: NO | Message: `test(external-db): capture alias and edge paths` | Files: [.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-5-aliases.txt, .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C002-missing-config-edge.txt]

- [ ] 6. Capture Computer Use GUI evidence and adjacent exact-fact regression

  What to do: Use Computer Use against the local Mac GUI to open `/Users/brian/Desktop/andes/wiki/atcuart100.md`, find `oscr_reg`, and capture an action log plus screenshot. In parallel, run adjacent CLI exact-fact queries for `atcspi200` and `atcdmac100`.
  Must NOT do: Do not replace this with Browser-only evidence; do not upload the local file or transmit sensitive data.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [7] | Blocked by: [1, 3]

  References (executor has NO interview context - be exhaustive):
  - External: `/Users/brian/.codex/plugins/cache/openai-bundled/computer-use/1.0.799/skills/computer-use/SKILL.md:3` - Computer Use controls local Mac apps.
  - External: `/Users/brian/.codex/plugins/cache/openai-bundled/computer-use/1.0.799/skills/computer-use/SKILL.md:8` - Computer Use reads screen and performs UI actions.
  - External: `/Users/brian/.codex/plugins/cache/openai-bundled/computer-use/1.0.799/skills/computer-use/SKILL.md:16` - policy scope for direct UI actions.
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:24` - Computer Use evidence requires action log and screenshot.
  - External: `/Users/brian/Desktop/andes/wiki/atcuart100.md:9` - page title includes `atcuart100`.
  - External: `/Users/brian/Desktop/andes/wiki/atcuart100.md:11` - visible summary includes `oscr_reg`.
  - External: `/Users/brian/Desktop/andes/wiki/atcspi200.md:87` - adjacent fact `spi_clk_out`.
  - External: `/Users/brian/Desktop/andes/wiki/atcdmac100.md:28` - adjacent fact `dma_req`.
  - API/Type: `core/tools.py:8040` - query output header for adjacent CLI assertions.

  Acceptance criteria (agent-executable only):
  - [ ] `C003-computer-use-action-log.txt` contains the opened path and the search term `oscr_reg`.
  - [ ] `C003-computer-use-screenshot.png` exists and is non-empty.
  - [ ] `C003-adjacent-regression.txt` contains `atcspi200`, `spi_clk_out`, `atcdmac100`, and either `dma_req` or `dma_mst_req`.
  - [ ] If `dma_req_i` remains in `goals.json`, this task must fail and route back to Task 3 steering.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Computer Use GUI page evidence
    Tool:     computer-use
    Steps:    Use OS-level Computer Use actions, not a shell-only shortcut. Open TextEdit or another local Mac GUI text viewer. Open `/Users/brian/Desktop/andes/wiki/atcuart100.md`. Use the GUI find command for `oscr_reg`. Capture a screenshot to `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-computer-use-screenshot.png`. Write the action transcript to `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-computer-use-action-log.txt`, including app name, opened path, find term, and visible text observations `atcuart100` and `oscr_reg`.
    Expected: screenshot file exists and action log contains `atcuart100`, `/Users/brian/Desktop/andes/wiki/atcuart100.md`, and `oscr_reg`.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-computer-use-action-log.txt

  Scenario: adjacent exact-fact regression
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; if rg -q 'dma_req_i' "$RUN/goals.json"; then echo 'C003 still references nonexistent dma_req_i; rerun Task 3 steering first' > "$EVID/C003-adjacent-regression.txt"; exit 1; fi; env -u ATLAS_EXTERNAL_DB_QUERY -u ATLAS_RTL_DB_QUERY -u ATLAS_EXTERNAL_DB_BUILDER -u ATLAS_RTL_DB_BUILDER ATLAS_PROJECT_ROOT="$PWD" COMMON_AI_AGENT_HOME="$PWD" ATLAS_EXTERNAL_DB_WIKI=/Users/brian/Desktop/andes/wiki ATLAS_EXTERNAL_DB_NO_REBUILD=1 python3 - <<'PY' >> "$EVID/C003-adjacent-regression.txt"
              from core.tools import wiki_query
              checks = [
                  ("atcspi200 spi_clk_out", ("atcspi200", "spi_clk_out")),
                  ("atcdmac100 dma_req dma_mst_req", ("atcdmac100", "dma_req")),
              ]
              for topic, required in checks:
                  out = wiki_query(ip="external-db", topic=topic, depth=3, max_nodes=4)
                  print("TOPIC", topic)
                  print(out)
                  assert "scope=rtl-db" in out
                  assert "matches=0" not in out
                  for term in required:
                      assert term in out
              print("cleanup: command-scoped env only; no runtime resources")
              PY
    Expected: both adjacent queries resolve through `scope=rtl-db` with nonzero matches and required terms.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-adjacent-regression.txt
  ```

  Commit: NO | Message: `test(external-db): capture computer-use wiki evidence` | Files: [.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-computer-use-action-log.txt, .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-computer-use-screenshot.png, .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/C003-adjacent-regression.txt]

- [ ] 7. Record ulw-loop evidence and checkpoint readiness

  What to do: Confirm required artifacts exist, record C001-C003 evidence through `omo ulw-loop record-evidence`, and create a checkpoint-readiness summary. Do not mark final completion until F1-F4 approve and the caller explicitly says okay.
  Must NOT do: Do not record pass if any evidence file is missing, any temp dir/process/browser context remains, or C003 screenshot/action log is absent.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [final verification] | Blocked by: [4, 5, 6]

  References (executor has NO interview context - be exhaustive):
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:143` - missing artifact means not done.
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:144` - cleanup receipt required before recording pass.
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:145` - exact `record-evidence` pass/fail/blocked commands.
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:154` - criteria confirmation before checkpoint.
  - External: `/Users/brian/.codex/plugins/cache/sisyphuslabs/omo/0.1.0/skills/ulw-loop/SKILL.md:161` - final quality gate only after criteria pass.
  - Pattern: `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/goals.json:16` - C001 entry.
  - Pattern: `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/goals.json:24` - C002 entry.
  - Pattern: `.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/goals.json:32` - C003 entry.

  Acceptance criteria (agent-executable only):
  - [ ] Required artifacts exist: `C001-wiki-query-happy.txt`, `C002-missing-config-edge.txt`, `C003-computer-use-action-log.txt`, `C003-computer-use-screenshot.png`, and `C003-adjacent-regression.txt`.
  - [ ] `omo ulw-loop criteria --goal-id G001-test-the-external-rtl-wiki-skill-too --json` shows C001, C002, C003 as `pass` after recording.
  - [ ] `task-7-checkpoint-readiness.json` contains all evidence paths and cleanup receipts.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: record criterion evidence
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; test -s "$EVID/C001-wiki-query-happy.txt"; test -s "$EVID/C002-missing-config-edge.txt"; test -s "$EVID/C003-computer-use-action-log.txt"; test -s "$EVID/C003-computer-use-screenshot.png"; test -s "$EVID/C003-adjacent-regression.txt"; omo ulw-loop record-evidence --goal-id G001-test-the-external-rtl-wiki-skill-too --criterion-id C001 --status pass --evidence "$EVID/task-2-skill-contract.txt; $EVID/C001-wiki-query-happy.txt | cleanup: command-scoped env only; graph mtime unchanged; no runtime resources" --json > "$EVID/task-7-record-C001.json"; omo ulw-loop record-evidence --goal-id G001-test-the-external-rtl-wiki-skill-too --criterion-id C002 --status pass --evidence "$EVID/C002-missing-config-edge.txt; $EVID/task-5-empty-wiki-edge.txt | cleanup: command-scoped env only; temp dir removed" --json > "$EVID/task-7-record-C002.json"; omo ulw-loop record-evidence --goal-id G001-test-the-external-rtl-wiki-skill-too --criterion-id C003 --status pass --evidence "$EVID/C003-computer-use-action-log.txt; $EVID/C003-computer-use-screenshot.png; $EVID/C003-adjacent-regression.txt | cleanup: Computer Use app closed or left at non-mutating local file view; no temp dirs; command-scoped env only" --json > "$EVID/task-7-record-C003.json"; omo ulw-loop criteria --goal-id G001-test-the-external-rtl-wiki-skill-too --json > "$EVID/task-7-criteria-after.json"
    Expected: record commands exit 0 and criteria-after shows C001-C003 pass.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-7-criteria-after.json

  Scenario: checkpoint readiness summary
    Tool:     bash
    Steps:    RUN=.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2; EVID="$RUN/evidence"; python3 - <<'PY' > "$EVID/task-7-checkpoint-readiness.json"
              import json
              from pathlib import Path
              evid = Path(".omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence")
              required = [
                  "C001-wiki-query-happy.txt",
                  "C002-missing-config-edge.txt",
                  "C003-computer-use-action-log.txt",
                  "C003-computer-use-screenshot.png",
                  "C003-adjacent-regression.txt",
                  "task-7-criteria-after.json",
              ]
              data = {"required": {}, "cleanup": "all QA env scoped; empty temp dir removed; no production files edited"}
              for name in required:
                  path = evid / name
                  data["required"][name] = {"exists": path.exists(), "size": path.stat().st_size if path.exists() else 0}
                  assert data["required"][name]["exists"]
                  assert data["required"][name]["size"] > 0
              print(json.dumps(data, indent=2))
              PY
    Expected: JSON lists every required artifact with positive size and cleanup summary.
    Evidence: .omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-7-checkpoint-readiness.json
  ```

  Commit: NO | Message: `test(external-db): record ulw evidence` | Files: [.omo/ulw-loop/019e865e-3bba-78d2-9f85-9f52c53a37e2/evidence/task-7-criteria-after.json]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: plans/external-rtl-wiki-skill-tool-call-qa.md`.
- This QA plan expects no production commits. If execution only adds `.omo/ulw-loop/.../evidence` and ledger entries, do not commit unless the caller explicitly asks.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.

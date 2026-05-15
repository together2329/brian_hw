# ATLAS Pipeline Screen

`◫ Pipeline` is a top-level ATLAS screen that turns the 14-stage
common_ai_agent flow into a click-to-run + glance-to-read situation
board. It replaced the mock `◫ Architect` screen on 2026-05-16 (see
[[log]] entry).

Related: [[full-flow-pipeline]] · [[ui-design-references]] ·
[[workflow-ownership-and-boundaries]] ·
[[workflow-feedback-and-scheduling]] · [[deterministic-emit-stages]]

## Why it exists

Before Pipeline, every stage of the flow was dispatched by typing
slash commands into the Workspace chat box (`/to-ssot`,
`/ssot-fl-model arm_m0_min`, `/ssot-rtl arm_m0_min`,
`/ssot-tb arm_m0_min`, `/sim arm_m0_min`, `/lint arm_m0_min`, … ×
14). The user had to remember the slash name, the IP, the workflow,
and the mode every time. There was no at-a-glance status surface for
the whole IP.

Pipeline gives:

- **One-click dispatch** per stage (or a chain of stages).
- **Live DAG map** showing every stage as a colored node, with
  token-flow animation along edges from running stages.
- **Per-stage scoresheet** — 3-5 KPI dots read directly from each
  stage's evidence JSON. Pass / warn / fail / idle at a glance.
- **Owner-aware failure routing** — failed cards offer
  `[ go fix <owner> ]` (never `[ retry ]`), per
  [[workflow-ownership-and-boundaries]].
- **Mode toggle** without typing — `● pipeline / ○ interactive` chip
  in the run-bar.

## Where it lives

| Layer | Location |
|---|---|
| Top-bar button | `frontend/atlas/app.jsx` `◫ Pipeline` |
| Top-level mount | `frontend/atlas/app.jsx` `<window.AtlasPipeline />` |
| Component file | `frontend/atlas/pipeline.jsx` |
| CSS | `frontend/atlas/styles.css` `/* ── Pipeline screen ── */` block |
| Backend state endpoint | `GET /api/pipeline/state?ip=<ip>` in `src/atlas_api_jobs.py` |
| Backend dispatch | `POST /api/pipeline/dispatch` (existing, `src/atlas_api_jobs.py:1146`) |
| Per-stage KPI compute | `compute_kpi_dots(ip, stage)` in `src/workflow_stage_surface.py` |

## Layout

3-column flex on a full-screen canvas:

| Column | Content |
|---|---|
| Left | IP hierarchy + active-IP file tree |
| Center | DAG MAP (top, ~140 px) · STAGE CARDS (2-col grid, 5 phase bands) · DISPATCH RAIL (bottom) |
| Right | `ArchitectChat` (re-used from `soc-architect.jsx:3482`) — the live agent transcript stays one click away |

Phase bands group the 14 stages by domain semantics, not by status:

- **AUTHOR** — `ssot`
- **DETERMINISTIC** — `fl-model`, `cl-model`, `equiv` (visually muted; 0 LLM calls per [[deterministic-emit-stages]])
- **IMPLEMENT** — `rtl`, `lint`, `tb` (the long expensive LLM stages — biggest cards)
- **VERIFY** — `sim`, `coverage`, `sim-debug`, `goal-audit` (truth-check + blame routing)
- **SIGN-OFF** — `syn`, `sta`, `pnr`, `sta-post` (collapsed by default; rarely run for educational IPs)

## Live data contract

`GET /api/pipeline/state?ip=<ip>` returns:

```json
{
  "ip": "arm_m0_min",
  "rtl_version_id": "rtl-v007",
  "mode": "pipeline",
  "stages": {
    "ssot": {
      "state": "passed",
      "glyph": "✓",
      "scoresheet": ["pass","pass","pass","pass","pass"],
      "iter": null, "progress": null, "live_tail": null,
      "top": "yaml/arm_m0_min.ssot.yaml · 72 KB · 34 sect",
      "secondary": "0 TBD · 62 iters · 12m",
      "evidence_paths": ["yaml/arm_m0_min.ssot.yaml"],
      "abortable": false,
      "model": "gpt-5.3-codex", "effort": "high",
      "history": [{"run_id":"…","state":"passed","duration_s":712,"model":"…","cost":0.42}],
      "blame": null
    },
    "rtl": {"state":"running","iter":"12/19","progress":0.65, "…": "…"},
    "…": "…"
  }
}
```

8-state model:

| State | Source |
|---|---|
| `idle` | no `workflow_runs` row AND no on-disk artifact |
| `ready` | upstream all fresh; no running job |
| `running` | `/api/jobs` row with `status=running` |
| `passed` | latest job completed AND artifacts present AND fresh |
| `failed` | latest job error/blocked OR validator JSON shows failure |
| `blocked-by-human-gate` | `<ip>/rtl/rtl_blocked.json` non-empty OR sim_human_gate_doc |
| `evidence-stale` | upstream `rtl_version_id` newer than this stage's |
| `locked` | direct upstream is `idle` or `failed` (per `_PIPELINE_STAGE_DEPS`) |

## Running-state visual cues

A running stage is obvious from any glance angle:

1. **DAG MAP node pulse ring** — `box-shadow` ping expanding outward over 1.4 s.
2. **DAG MAP edge token-flow** — SVG `<animateMotion>` 4 px circle traveling along outgoing edges (1.6 s).
3. **StageCard top-stripe breath** — 1 px top border breathing cyan-strong ↔ cyan-mute over 2 s.
4. **Progress-bar shimmer** — linear-gradient highlight traveling left → right (1.2 s).
5. **Top-bar `▶ N running` chip** — same pulse animation; visible from every screen; click → jumps to the IP.
6. **Browser-tab title** — `▶ ATLAS — <ip> (<stage>)` while any stage runs.

All wrapped in `@media (prefers-reduced-motion: reduce) { animation: none !important; … } .pipe-node[data-state="running"] { outline: 2px solid var(--cyan); }`.

## Per-stage KPI scoresheet (3-5 dots)

| Stage | Dots → source JSON |
|---|---|
| ssot-gen | section_count · qa_resolved · tbd=0 · isa_spec · register_file (`yaml/<ip>.ssot.yaml`) |
| fl-model-gen | emit_passed · self_check.passed · fcov_plan · manifest_ok (`model/fl_model_check.json`, `cov/fcov_plan.json`) |
| cl-model-gen | emit_passed · cl_self_check · cycle_cov_plan (`model/cl_model_check.json`) |
| equiv-goals | parses · goals_resolved · sub_module_refs (`verify/equivalence_goals.json`) |
| rtl-gen | compile_rc=0 · lint_clean · todo_audit=pass · provenance_present (`rtl/rtl_compile.json`, `lint/dut_lint.json`, `rtl/rtl_todo_plan.json`, `rtl/rtl_authoring_provenance.json`) |
| lint | errors=0 · warnings≤waivers · waiver_count (`lint/dut_lint.json`) |
| tb-gen | top_present · scoreboard · tc_count · manifest (`tb/cocotb/*`) |
| sim | results.xml=pass · mismatches=0 · vcd_present · seed_coverage (`sim/results.xml`, `sim/fl_rtl_compare.json`) |
| coverage | bins_hit/total · cycle_cov · func_cov · uncov_count (`cov/coverage.json`) |
| sim-debug | classification_present · owner_routed · feedback_packet (`sim/mismatch_classification.json`) |
| goal-audit | failed_checks=0 · blockers=0 · status=pass (`sim/fl_rtl_goal_audit.json`) |
| syn / sta / pnr / sta-post | tool_rc · area · timing_slack · fanout · power (per-stage report JSON) |

Click a dot → opens the source JSON in the existing `FileViewer` overlay.

## Interactions

| # | Action | Wiring |
|---|---|---|
| a | One-shot run | click card body or `[▶ run]` button → `POST /api/pipeline/dispatch` `{ip,stages:[id],schedule:'serial'}` |
| b | Chained run | Cmd/Ctrl-click stacks cards into DispatchRail; rail sends one call with `stages:[…]` |
| c | Re-run other model | right-click passed card → popover `[model ▾][effort ◐]`; submit dispatches single stage with new model |
| d | Inspect evidence | scoresheet dots and KPI rows visible on the card; click any dot → opens source JSON in `FileViewer` |
| e | Follow blame | failed card shows `! sim blame→rtl-gen`; `[ go fix rtl-gen ]` dispatches rtl-gen with the feedback packet path templated into prompt (per [[workflow-feedback-and-scheduling]]) |
| f | Abort running | running card shows `⏹` (Esc keybind) → `POST /api/job/{id}/cancel` |
| g | Switch mode | run-bar mode chip toggle sends `/mode pipeline` or `/mode normal` through chat input; warn-color when `interactive` |

## Anti-patterns deliberately avoided

| What we avoided | Why |
|---|---|
| Gantt / timeline view | Stage durations span 100× (cl-model 5 s vs rtl-gen 40 min); bars either lie or are invisible |
| Kanban (idle / ready / running / passed columns) | Destroys DAG ordering — the most valuable structural information |
| `[ retry ]` button on failed cards | Per [[workflow-ownership-and-boundaries]] §37-43 the canonical anti-pattern; `[ go fix <owner> ]` only |

## Backend evidence map (load-bearing file:line refs)

- `src/atlas_api_jobs.py:39-55` — `_PIPELINE_STAGES` (15 canonical IDs).
- `src/atlas_api_jobs.py:62-77` — `_PIPELINE_STAGE_DEPS` (DAG edges).
- `src/atlas_api_jobs.py:78-81` — `_RTL_VERSION_DOWNSTREAM_STAGES` (stale rules).
- `src/atlas_api_jobs.py:796-892` — `_job_artifact_recovery` (offline ground truth).
- `src/atlas_api_jobs.py:1146-1211` — `POST /api/pipeline/dispatch` (existing).
- `src/atlas_api_jobs.py:1369-1389` — `POST /api/job/{id}/cancel`.
- `src/workflow_stage_engine.py:1654, 1675, 1687` — `mismatch_classification.json` (blame).
- `src/workflow_stage_surface.py` — `_rtl_authoring_summary`, new `compute_kpi_dots`.

## Frontend evidence map

- `frontend/atlas/app.jsx` — top-bar `◫ Pipeline` button + screen mount.
- `frontend/atlas/pipeline.jsx` — `AtlasPipeline / DagMap / StageCard / MiniScoresheet / DispatchRail` (new).
- `frontend/atlas/soc-architect.jsx:817-893` — `PIPELINE_STAGES`, `PIPELINE_LABEL`, `fullPipeline`, `PipelineStrip` (re-exported, still in use).
- `frontend/atlas/soc-architect.jsx:3482` — `ArchitectChat` (re-mounted as Pipeline's right column).
- `frontend/atlas/data.jsx:42-58` — `DEFAULT_FLOW_STAGES` (glyph + colour tokens).
- `frontend/atlas/styles.css:105-145` — semantic colour tokens.
- `frontend/atlas/index.html` — `pipeline.jsx` script tag.

## Verification

End-to-end smoke after rollout:

1. **Endpoint shape**:
   `curl -s 'http://127.0.0.1:8765/api/pipeline/state?ip=arm_m0_min' | jq '.stages | keys'` → 15 canonical stage IDs.
2. **Screen swap**: open `http://127.0.0.1:8765/`, click `◫ Pipeline`, confirm `localStorage.atlasScreen === 'pipeline'`. Refresh → sticky.
3. **Live state**: dispatch rtl-gen via the RT card `[▶ run]` button; card transitions `idle → running → passed`; chat shows one `dispatched rtl-gen via PIPELINE` line.
4. **Locked semantics**: delete `<ip>/yaml/<ip>.ssot.yaml`; downstream cards dim, DAG nodes dim.
5. **Reduced motion**: enable OS "reduce motion" → animations replaced by `outline` only.

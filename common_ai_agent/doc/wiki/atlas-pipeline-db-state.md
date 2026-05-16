# ATLAS Pipeline — DB-vs-Filesystem State

How the `◫ Pipeline` screen decides what to show, and what is stored
where in `~/.common_ai_agent/atlas.db` vs the filesystem under
`<repo>/<ip>/`.

Related: [[atlas-pipeline-screen]] · [[full-flow-pipeline]] ·
[[golden-todo-evidence]]

## What the DB owns today

| Concern | Table | Columns of interest |
|---|---|---|
| Per-IP run identity | `workflow_runs` | `id`, `workspace_id`, `ip_id`, `workflow`, `status`, `started_at`, `ended_at`, `error_summary`, `model_profile`, `reasoning_effort`, `rtl_version_id` |
| Per-stage attempts | `workflow_stages` | `id`, `run_id`, `stage_name`, `status`, `attempt`, `error_summary`, `started_at`, `ended_at` |
| Event ledger | `workflow_events` | append-only; `event_type` + JSON `payload` |
| Per-stage todos | `workflow_todos` | `status` (open / closed / approved), `evidence` JSON (paths) |
| IP registry | `ip_blocks` | `(workspace_id, ip_name)` exists / `ssot_path` |
| RTL versions | `rtl_versions` | per-IP RTL version tags + manifests |

Index `idx_workflow_runs_context(workspace_id, ip_id, workflow,
started_at)` makes the per-stage state query a single index seek.

## What the filesystem still owns

KPI numerics — the values behind the 3–5 colored dots on each stage
card — live in on-disk JSON written by the per-stage scripts:

| Stage | KPI source file | Read by |
|---|---|---|
| ssot | `<ip>/yaml/<ip>.ssot.yaml` | `_kpi_ssot()` |
| fl-model | `<ip>/model/fl_model_check.json`, `<ip>/cov/fcov_plan.json` | `_kpi_fl_model()` |
| cl-model | `<ip>/model/cl_model_check.json` | `_kpi_cl_model()` |
| equiv | `<ip>/verify/equivalence_goals.json` | `_kpi_equivalence()` |
| rtl | `<ip>/rtl/rtl_compile.json`, `<ip>/lint/dut_lint.json`, `<ip>/rtl/rtl_todo_plan.json`, `<ip>/rtl/rtl_authoring_provenance.json` | `_kpi_rtl()` |
| lint | `<ip>/lint/dut_lint.json` | `_kpi_lint()` |
| tb | `<ip>/tb/cocotb/*.py` (presence) | `_kpi_tb()` |
| sim | `<ip>/sim/results.xml`, `<ip>/sim/fl_rtl_compare.json` | `_kpi_sim()` |
| coverage | `<ip>/cov/coverage.json` | `_kpi_coverage()` |
| sim-debug | `<ip>/sim/mismatch_classification.json` | `_kpi_sim_debug()` |
| goal-audit | `<ip>/sim/fl_rtl_goal_audit.json` | `_kpi_goal_audit()` |
| syn / sta / pnr / sta-post | `<ip>/<stage>/out/*.json` | `_kpi_signoff()` |

These KPI files are not yet mirrored into the DB. The numerics are
small (a single int/float each) but the writers don't currently
upsert them.

## How `/api/pipeline/state` resolves a stage

```
1. /api/jobs has running job for (ip, stage_id)?  → running
2. workflow_runs latest row for (ws, ip, workflow)?
   - status=running    → running
   - status=completed  → passed
   - status=error/...  → failed (+ error_summary)
3. _job_artifact_recovery(ip, stage) sees the artifact?  → passed
   (covers hand-placed evidence with no DB row)
4. all upstream stages passed?  → ready
   else → locked  (locked_reason = "needs <missing-upstream>")
5. <ip>/rtl/rtl_blocked.json non-empty? (rtl stage only)  → blocked
```

Each response stage carries a `source` field: `"db"`, `"fs"`, or
`"none"`, so the UI can label why a verdict was reached.

## Why hybrid, not full DB

The DB at `~/.common_ai_agent/atlas.db` is **per-user-machine**, not
shared across users. Both DB and FS are local; "DB instead of local"
is a category error unless we also deploy a shared service. Within a
single machine, the hybrid buys:

- **Correctness**: state survives FS reorganizations, archive moves,
  and `ATLAS_PROJECT_ROOT` swaps. The DB still knows "this stage
  ran and passed."
- **Speed**: ~30-45 stat()+json.loads ops per request → ~15 indexed
  DB lookups. Per-card KPI dots still cost ~1 file read each.
- **Multi-IP coherence**: a single `SELECT … WHERE workspace_id=?
  AND ip_id IN (...)` can return state for every IP in a workspace
  (future cross-IP Status grid).

A fully centralized service (PostgreSQL or similar) would be a
separate proposal — none of the existing DB consumers assume one.

## Migration to fully DB-driven KPI dots

To remove the remaining filesystem reads in
`compute_kpi_dots_labeled()`, three steps are needed:

1. **Schema** — additive columns on `workflow_stages`, all `NULL`able:
   ```sql
   ALTER TABLE workflow_stages ADD COLUMN kpi_compile_rc INTEGER NULL;
   ALTER TABLE workflow_stages ADD COLUMN kpi_lint_errors INTEGER NULL;
   ALTER TABLE workflow_stages ADD COLUMN kpi_lint_warnings INTEGER NULL;
   ALTER TABLE workflow_stages ADD COLUMN kpi_sim_mismatches INTEGER NULL;
   ALTER TABLE workflow_stages ADD COLUMN kpi_coverage_pct REAL NULL;
   ALTER TABLE workflow_stages ADD COLUMN kpi_payload TEXT NULL;
   ```

2. **Writer upserts** — at the end of each evidence script, call
   `db.finish_workflow_stage(stage_id, status, **kpi_kwargs)`:
   - `workflow/rtl-gen/scripts/rtl_compile_report.py` →
     `kpi_compile_rc`
   - `workflow/lint/scripts/dut_lint_report.py` →
     `kpi_lint_errors`, `kpi_lint_warnings`
   - `workflow/sim_debug/scripts/compare_fl_rtl_results.py` →
     `kpi_sim_mismatches`
   - `workflow/fl-model-gen/scripts/emit_fl_model.py` →
     `kpi_payload` (catch-all JSON for fl_model_check)

3. **Reader rewrite** — `compute_kpi_dots()` reads
   `workflow_stages.kpi_*` first, falls back to filesystem only if
   the DB column is `NULL` (so legacy IPs without DB-mirrored KPIs
   keep working). Each `_kpi_*` helper becomes a thin DB lookup.

The hybrid stays during the migration: stages that have populated
DB columns use the DB; stages that don't fall back to file reads.
Once every workflow upserts its KPIs, the file reads can be deleted.

## Cross-links

- [[atlas-pipeline-screen]] — the user-facing screen.
- [[full-flow-pipeline]] — the 14 canonical stages.
- [[workflow-feedback-and-scheduling]] — `error_summary` semantics.
- [[golden-todo-evidence]] — `workflow_todos.evidence` JSON.
- [[ui-design-references]] — external UI patterns.

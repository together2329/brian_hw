# Artifact Version And Run History

## Current Gap

Today the UI can show workflow, cost, todo, tool, and intervention history, but
it must also show which artifact snapshots a downstream run used. A failed sim
is not trustworthy unless it states the exact `ssot`, `rtl`, and `tb` versions
it consumed. A failed lint/syn/sta/pnr result is stale if a newer RTL version
exists after a repair.

## Required Contract

Every major handoff must create an immutable artifact version record. Downstream
runs must reference those records instead of implicitly reading "whatever files
are in the folder now".

```
ssot-gen -> ssot-v003
rtl-gen  -> rtl-v007 generated_from ssot-v003
tb-gen   -> tb-v004 generated_from ssot-v003, verified_against rtl-v007
sim      -> input set: ssot-v003 + rtl-v007 + tb-v004
```

Do not overwrite old run results. Old results are evidence for the old input
artifact set. New SSOT/RTL/TB gets new downstream workflow runs.

## DB Shape

Use generic artifact version graph tables:

- `artifact_versions`: immutable snapshots such as `ssot`, `rtl`, `tb`,
  `fl_model`, `cl_model`, `netlist`, or `sdc`.
- `artifact_version_edges`: parent-child graph such as `generated_from`,
  `verified_against`, `repaired_from`, or `promoted_from`.
- `run_artifact_versions`: many-to-many mapping from workflow runs to the
  artifact versions they used or produced.

Keep `rtl_versions` as a compatibility wrapper over `artifact_versions` for the
existing RTL Runs UI and APIs. New generic UI should prefer artifact version
sets.

Common version tags:

```text
atlas/<ip>/ssot-v003
atlas/<ip>/rtl-v007
atlas/<ip>/tb-v004
```

The DB remains the run ledger; git tags are reproducible source anchors. Local
pipeline runs without tags must still work, but released or reviewed handoffs
should carry both `git_commit` and `git_tag`.

Implementation default: pipeline registration records the current `git_commit`
when the workspace is a git repo. It records `git_tag` only when the tag already
exists or `ATLAS_RTL_VERSION_CREATE_GIT_TAG=1` allows the local pipeline to
create `atlas/<ip>/<version>` automatically.

## UI Visibility

The UI must show the artifact version set anywhere a downstream result can be
trusted or reused:

- Active workflow banner: `sim uses ssot-v003 / rtl-v007 / tb-v004`.
- Admin dashboard: `Versions` table listing all SSOT/RTL/TB versions.
- Admin dashboard: `Run Sets` table listing which SSOT/RTL/TB each workflow run
  consumed.
- Existing Admin `RTL Runs` remains for RTL-focused lint/sim/syn/sta/pnr view.
- Workflow report tabs: lint, sim, coverage, syn, sta, and pnr report headers
  must include the artifact version set and source artifact links.
- Repair view: when lint/sim fails, show whether a newer required input version
  exists. If newer, mark the old result stale and queue a rerun.

## Repair Loop

When lint or sim finds an issue:

1. Classify owner: RTL, TB, SSOT, tool setup, waiver, or human review.
2. If RTL changes, register a new `rtl_version`.
3. Mark downstream evidence from older versions as stale for signoff purposes.
4. Rerun only the affected workflows against the new RTL version.
5. Keep the old run history for debugging and cost accounting.

## Acceptance Criteria

- A sim run can answer: "Which SSOT, RTL, and TB versions did it use?"
- A TB version can answer: "Which SSOT and RTL versions was it generated or
  verified against?"
- An RTL version can answer: "Which SSOT version generated it?"
- A lint/syn/sta/pnr run cannot be created without a visible RTL version when it
  consumes RTL.
- Admin can answer: "Which RTL version did this run use?"
- Admin can answer: "Which git tag anchors this RTL version?"
- Admin can answer: "Which lint/sim runs are stale after the latest RTL repair?"
- Cost, LLM calls, tool calls, and human interventions can be grouped by
  `ip_id`, `workspace_id`, `workflow`, and `rtl_version_id`.
- Pipeline signoff uses only fresh downstream evidence for the selected RTL
  version.

## Recorded Runs

Concrete reference runs captured in this wiki. Each row anchors a version
set that downstream evidence in this run must name.

| Date | IP | SSOT | RTL | TB | Sim | Lint | Reference |
|---|---|---|---|---|---|---|---|
| 2026-05-15 | `arm_m0_min` | yaml/arm_m0_min.ssot.yaml (31 271 B, 36 sections) | 8 SV files, 22 KB, compile errors=0 | 9 cocotb files, 37 tests | scoreboard 37/37, 0 mismatches, 35/35 fcov bins | pyslang+verilator errors=0 warnings=0 | [[arm-m0-min-pipeline-run]] |


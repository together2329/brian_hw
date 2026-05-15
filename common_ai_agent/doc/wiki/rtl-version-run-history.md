# RTL Version And Run History

## Current Gap

Today the UI can show workflow, cost, todo, tool, and intervention history, but
it does not reliably show which RTL snapshot a lint or sim run used. The admin
usage payload does not expose `rtl_version_id`, `rtl_version`, or
`rtl_sha256_tree` yet. That means a failed lint/sim result can be stale after an
RTL repair, even if it still looks like the latest result in the UI.

## Required Contract

Every RTL handoff must create an immutable RTL version record. Downstream runs
must reference that record instead of implicitly reading "whatever files are in
the folder now".

```
rtl-gen produces RTL -> register rtl_version -> lint/sim/syn/sta/pnr run against rtl_version
RTL repair produces new files -> register new rtl_version -> rerun affected downstream stages
```

Do not overwrite old run results. Old results are evidence for the old RTL
version. New RTL gets new downstream workflow runs.

## DB Shape

Add `rtl_versions` as the version anchor:

- `id`
- `ip_id`
- `workspace_id`
- `source_run_id`
- `source_stage_id`
- `version`
- `label`
- `rtl_root`
- `filelist_path`
- `top_module`
- `artifact_manifest`
- `sha256_tree`
- `git_commit`
- `git_tag`
- `status`
- `created_at`

Add `rtl_version_id` to:

- `workflow_runs`
- `workflow_stages`
- `artifacts`

The DB stores metadata, paths, hashes, manifests, and relationships. Large
artifacts stay in the file/object store.

`git_tag` is optional but recommended for durable review points. A stable tag
scheme should be human-readable and IP-scoped, for example:

```
atlas/<ip>/rtl-v003
```

The DB remains the run ledger; git tags are reproducible source anchors. Local
pipeline runs without tags must still work, but released or reviewed RTL
handoffs should carry both `git_commit` and `git_tag`.

Implementation default: pipeline registration records the current `git_commit`
when the workspace is a git repo. It records `git_tag` only when the tag already
exists or `ATLAS_RTL_VERSION_CREATE_GIT_TAG=1` allows the local pipeline to
create `atlas/<ip>/<version>` automatically.

## UI Visibility

The UI must show the RTL version anywhere a downstream result can be trusted or
reused:

- Active workflow banner: `lint on rtl-v003` or `sim on rtl-v003`.
- Admin dashboard: table grouped by IP, workspace, RTL version, workflow,
  git tag, status, duration, cost, LLM calls, and last error.
- Workflow report tabs: lint, sim, coverage, syn, sta, and pnr report headers
  must include `rtl_version`, `sha256_tree`, and source RTL artifact link.
- Run detail view: show the exact filelist, top module, artifact manifest, and
  parent RTL-gen run.
- Repair view: when lint/sim fails, show whether the latest RTL version is newer
  than the failed run. If newer, mark the old result stale and queue a rerun.

Current UI status: not implemented. This is a required DB/API/frontend follow-up.

## Repair Loop

When lint or sim finds an issue:

1. Classify owner: RTL, TB, SSOT, tool setup, waiver, or human review.
2. If RTL changes, register a new `rtl_version`.
3. Mark downstream evidence from older versions as stale for signoff purposes.
4. Rerun only the affected workflows against the new RTL version.
5. Keep the old run history for debugging and cost accounting.

## Acceptance Criteria

- A lint/sim/syn/sta/pnr run cannot be created without a visible RTL version
  when it consumes RTL.
- Admin can answer: "Which RTL version did this run use?"
- Admin can answer: "Which git tag anchors this RTL version?"
- Admin can answer: "Which lint/sim runs are stale after the latest RTL repair?"
- Cost, LLM calls, tool calls, and human interventions can be grouped by
  `ip_id`, `workspace_id`, `workflow`, and `rtl_version_id`.
- Pipeline signoff uses only fresh downstream evidence for the selected RTL
  version.

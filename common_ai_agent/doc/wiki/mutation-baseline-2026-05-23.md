# Mutation Baseline — 2026-05-23

> **Status: NOT COMPLETED — stats-collection phase exceeded 5-minute cap**
> See "Why it timed out" below. Config and tooling are in place; re-run instructions follow.

---

## Summary

| Item | Value |
|---|---|
| Tool | mutmut 3.3.1 |
| Install | `pip3 install mutmut` → `/Users/brian/Library/Python/3.9/bin/mutmut` |
| Target files | `src/atlas_api_jobs.py` (5860 LOC), `core/atlas_db.py` (4494 LOC) |
| Attempted scope | `_rehydrate_jobs_from_db` function only |
| Mutations generated | 4311 (atlas_db.py only, before kill) |
| Mutations tested | 0 |
| Killed | N/A |
| Survived | N/A |
| Timeout | N/A |
| Wall time before kill | ~9 min (5-min cap exceeded) |

---

## Why it timed out

mutmut 3.x (trampoline architecture) runs a **stats-collection phase** before testing any mutant. During this phase it:

1. Copies the full source tree into `mutants/`
2. Runs the entire test suite once **per source function** with trampoline instrumentation to map which tests cover which functions.

With `src/atlas_api_jobs.py` containing ~200+ top-level functions, and the smoke suite taking ~30 s per run, stats collection alone requires **~100 minutes** before a single mutation is tested. This is independent of the `--max-children` parallelism flag (which only controls concurrent mutation workers, not the stats phase).

The 5-minute cap in the task spec cannot be met with mutmut v3 on files of this size.

---

## Mutants generated (partial)

mutmut did successfully generate mutants for `core/atlas_db.py` before being killed:

- **4311 mutants generated** for `core/atlas_db.py`
- Status for all: `None` (not checked — stats phase never completed)
- `src/atlas_api_jobs.py` meta file was not written before kill

The generated mutants are in `mutants/core/atlas_db.py` and `mutants/src/atlas_api_jobs.py`.

---

## How to run the baseline properly

### Option A — Full mutation run (hours, unattended)

```bash
# Uses setup.cfg [mutmut] config automatically
./scripts/run_tests.sh mutation
```

Expect: 2–4 hours for both files. Run in a tmux/screen session.

### Option B — Scoped to hardened functions only (30–60 min)

```bash
MUTMUT=/Users/brian/Library/Python/3.9/bin/mutmut
$MUTMUT run 'src/atlas_api_jobs.py:_rehydrate_jobs_from_db*'
$MUTMUT run 'src/atlas_api_jobs.py:_lazy_worker_reaper_loop*'
$MUTMUT run 'src/atlas_api_jobs.py:_ensure_lazy_worker*'
$MUTMUT results
```

### Option C — Use mutmut 2.x (supports `--paths-to-mutate` + shell runner)

mutmut 2.x allows `--runner='./scripts/run_tests.sh smoke'` and `--paths-to-mutate`, which is faster because it skips the trampoline stats phase.

```bash
pip3 install 'mutmut<3'
mutmut run \
  --paths-to-mutate=src/atlas_api_jobs.py \
  --runner='./scripts/run_tests.sh smoke' \
  --simple-output
mutmut results
```

---

## Configuration files

- `setup.cfg` — `[mutmut]` section: paths + smoke tests as `tests_dir`
- `mutmut_config.py` — documentation only (v3 ignores Python config files)
- `scripts/run_tests.sh` — `mutation` mode added

---

## What to look for when the run completes

A healthy test suite should kill >60% of mutants. Below 40% killed means tests are mostly checking execution (not results). The newly added safety-net tests gate:

| Function | Tests |
|---|---|
| `_rehydrate_jobs_from_db` | `test_jobs_rehydration.py` (3 cases) |
| `_lazy_worker_reaper_loop` | `test_lazy_worker_reaper.py` (6 cases) |
| `_ensure_lazy_worker` | `test_lazy_worker_cold_start_storm.py`, `test_parallel_todo_dispatcher.py` |
| `_probe_worker_health_cached` | `test_orchestrator_workers_route.py` |
| AtlasDB `_WRITE_LOCK` | `test_atlas_db_concurrent_writers.py` |

Survived mutants in these functions = tests that pass despite wrong behavior = real gaps.

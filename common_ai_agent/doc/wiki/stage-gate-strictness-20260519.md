# Stage Gate Strictness Audit — 2026-05-19

**IP under test:** `cmux_r2_gamma`  
**DB baseline:** `ssot-gen=completed`, `rtl-gen=error` (stale running row also present)  
**Auditor:** d-gate

---

## Method

1. Located IP with a completed ssot-gen run via `workflow_runs` table.
2. Called `_job_artifact_recovery` and `_job_artifact_failure` directly (no live server needed) to simulate what `/api/pipeline/state` computes.
3. Truncated `cmux_r2_gamma/yaml/cmux_r2_gamma.ssot.yaml` to 100 bytes; also emptied `cmux_r2_gamma/rtl/cmux_r2_gamma_cnt.sv` to zero bytes.
4. Re-ran gate functions and traced through the pipeline state priority logic (lines 3181–3204 of `src/atlas_api_jobs.py`).
5. Restored all files from backups.

---

## Pipeline State Priority Logic (summary)

```
if running_job           → state = "running"
elif sid in failed_stages  → state = "failed"   ← fs artifact failure wins
elif db_state == "failed" and sid in passed_stages → state = "passed"
elif db_state is not None  → state = db_state   ← DB is used if no fs failure
elif sid in passed_stages  → state = "passed"   ← fs fallback, no DB row
else                       → idle / ready / locked
```

`failed_stages` is populated by `_job_artifact_failure(fake_job, pr)`.  
`passed_stages` is populated by `_job_artifact_recovery(fake_job, pr)`.

---

## SSOT Stage — Test Result

| Condition | `_job_artifact_recovery` ok | `_job_artifact_failure` bad | Pipeline state (DB=passed) |
|---|---|---|---|
| Intact file (46859 B, 34 sections) | True | False | **passed** |
| Truncated to 100 B | False | **False** | **passed** (BUG) |

**Finding — SSOT gate has no failure branch.**

`_job_artifact_failure` has no case for `stage == "ssot"` — it falls through to `return False, ""` at the bottom. When the DB row is `completed`, the pipeline shows `passed` even if the SSOT yaml has been truncated to garbage.

`_job_artifact_recovery` does run `check_ssot_disk.sh` and correctly returns `ok=False` for the corrupt file, but that only removes the file from `passed_stages`; it does not add it to `failed_stages`. Since `db_state` is `"passed"`, line 3187 wins and the stage stays green.

`check_ssot_disk.sh` itself is strict: it requires ≥3000 B and ≥30 sections in `engineering` mode — the validator works, but its negative result is never promoted to a failure.

---

## RTL Stage — Test Result

| Condition | `_job_artifact_recovery` ok | `_job_artifact_failure` bad | Pipeline state (DB=running/error) |
|---|---|---|---|
| Intact `.sv` (7135 B) | True (via `.f` filelist) | True (gate: open_required_todos=60, static_missing=49) | **failed** |
| Emptied `.sv` (0 B) | True (via `.f` filelist) | True (same gate reason) | **failed** |

**Finding — RTL gate is strict, but for a different reason.**

`_job_artifact_failure` for RTL reads `logs/stage_engine/ssot-rtl.json` and `rtl/rtl_todo_plan.json` via `_rtl_gate_failure_reason`. In this IP the gate file already has 60 open required todos and 49 static_missing items, so RTL correctly shows `failed` regardless of whether the `.sv` is empty or not.

However: `_job_artifact_recovery` returns `ok=True` for RTL as long as `list/<ip>.f` exists — even with an empty `.sv`. That means a hand-placed `.f` file with no actual RTL would be treated as "passed" if the gate doc is absent. The `.f` filelist existence check is too shallow for recovery.

---

## Summary of Findings

| # | Severity | Stage | Issue | Where |
|---|---|---|---|---|
| 1 | **High** | SSOT | `_job_artifact_failure` has no ssot branch — corrupt/truncated SSOT stays "passed" when DB=completed | `src/atlas_api_jobs.py:2182` |
| 2 | Medium | SSOT | `_job_artifact_recovery` correctly rejects corrupt file via `check_ssot_disk.sh`, but the negative result only removes from `passed_stages`, not promotes to `failed_stages` | `src/atlas_api_jobs.py:1997–2022` |
| 3 | Low | RTL | `_job_artifact_recovery` marks RTL as recovered if `list/<ip>.f` exists, even with zero-byte `.sv` files | `src/atlas_api_jobs.py:2039–2042` |

---

## Proposed Tightening (no code changes made)

### Fix 1 — Add ssot failure branch in `_job_artifact_failure` (High priority)

```python
if stage == "ssot" or workflow == "ssot-gen":
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not ssot_path.is_file():
        return True, f"missing artifact: {ip}/yaml/{ip}.ssot.yaml"
    checker = project_root / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
    if not checker.is_file():
        return False, ""   # can't validate, don't block
    try:
        proc = subprocess.run(
            ["bash", str(checker), ip, "--mode", _current_run_mode()],
            cwd=str(project_root), text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30, check=False,
        )
    except Exception as exc:
        return False, ""   # validator crash — don't block, log separately
    if proc.returncode != 0:
        detail = (proc.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else f"rc={proc.returncode}"
        return True, f"SSOT artifact failed validator: {tail}"
    return False, ""
```

This mirrors the existing `_job_artifact_recovery` ssot branch and makes corrupt SSOT override a stale DB "passed" row.

### Fix 2 — RTL recovery should verify sv content (Low priority)

Add a size/content check before accepting `.f` + empty `.sv` as recovered:

```python
rtl_files = [p for p in rtl_dir.glob("*.sv") if p.stat().st_size > 0]
# also check .v files
rtl_files += [p for p in rtl_dir.glob("*.v") if p.stat().st_size > 0]
return bool(filelist.is_file() and rtl_files), ...
```

### Fix 3 — When `_job_artifact_recovery` fails validator, surface as "stale" not just "not passed" (Low priority)

Add a `stale_stages` set populated when recovery returns `ok=False` with a non-empty detail. Pipeline state could then emit `state="stale"` when `db_state="passed"` but artifact is stale/corrupt, giving the UI a distinct visual indicator.

---

## Verdict

- **SSOT gate is permissive when DB=passed**: corruption is detected by `check_ssot_disk.sh` but the negative result is silently discarded. A truncated SSOT yaml will show green in the pipeline UI indefinitely.
- **RTL gate is strict**: the todo/gate document drives a hard failure regardless of DB state.
- **No code changes made** per task instructions. Tightening proposals documented above.

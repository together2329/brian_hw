# fl-model-gen CHANGELOG

## 2026-05-07 — Overnight workflow hardening (OV-001 .. OV-009)

### Goal
Iteratively close gaps in fl-model-gen that block PL330-level RTL generation.
PL330 (92 files / 85488 LoC) is used as the workflow's stress-test SSOT under
`pl330_target/`.

### New emit scripts (sibling files, no edits to existing emit_fl_model.py
behaviour beyond T1 patches below)

| File | Stage / use | Output |
|---|---|---|
| `scripts/emit_model_signature.py` | T2 lock | `<ip>/model/model_signature.json` (4 SHA-256 hashes) |
| `scripts/emit_cycle_model.py` | CL emit | `<ip>/model/cycle_model.py` + `cl_model_check.json` |
| `scripts/emit_dual_fcov.py` | Coverage split | `<ip>/cov/{fl,cl}_fcov_plan.json` + union view |
| `scripts/emit_verification_rtl.py` | cocotb harness | `<ip>/verify/{cocotb_harness.py, Makefile.sim, scoreboard_bindings.sv}` |
| `scripts/emit_golden_todos.py` | TodoTracker | `<ip>/golden/{golden_todos.json, golden_todos_tracker.json}` |
| `scripts/emit_authority_manifest.py` | 9 gates / 9 loops / 6 rules | `<ip>/governance/{authority.json, authority.md}` |
| `scripts/emit_protocol_assertions.py` | L5 SVA | `<ip>/verify/protocol_assertions.sva` |
| `scripts/emit_regression_min.py` | L8 bisect | `<ip>/sim/min_repro.jsonl` |
| `scripts/emit_fail_analysis.py` | L9 root cause | `<ip>/reports/fail_analysis.md` |
| `scripts/emit_loop_map.py` | governance viz | `<ip>/governance/loop_map.{mmd,svg}` |
| `scripts/check_signature_drift.py` | T2 enforcement helper | per-worker entry gate |

### golden-all chain (9 stages — not all are auto-run; some are on-demand)
1. ssot-fl-model
2. ssot-cycle-model
3. ssot-dual-fcov
4. ssot-equiv-goals
5. ssot-verification-rtl
6. ssot-golden-todos
7. ssot-protocol-assertions
8. ssot-authority
9. ssot-loop-map

### On-demand stages (NOT in golden-all)
- `/ssot-regression-min <ip> --seed <jsonl>` — needs an input failing seed
- `/ssot-fail-analysis <ip> --diff <jsonl>` — needs a scoreboard diff
- `check_signature_drift.py` — called by downstream workers, not by golden-all

### T1 / T2 patches applied to existing emit_fl_model.py / emit_equivalence_goals.py
1. **T1 #1** Removed name-heuristic state autoincrement in
   `_apply_primary` template; replaced with `[SSOT QUESTION]` annotation +
   `fabricated_state=False`. Cardinal rule now enforced at FL level.
2. **T1 (extra)** Added `ast.Subscript` support to `_eval_ast` template
   (single-bit + Verilog `[hi:lo]` slice select). Required for IPs that use
   bit-slice expressions in output_rules.
3. **T1 #4** Removed `generated_at` / `timestamp` from 4 payloads
   (decomposition.json, fcov_plan.json, fl_model_check.json,
   equivalence_goals.json). Wall-clock metadata now lives in
   `<ip>/model/manifest.json`. Payloads are byte-stable across runs.
4. **T1 #5** Augmented `run_self_check` template with
   - `invariants_total / invariants_evaluated / invariants_failed / invariants_skipped`
   - `reset_consistency` + `reset_diff`
   - `error_cases_total / error_cases_planned`
   Skipped (unparseable) invariants do NOT count as failed.

### Downstream worker preamble (paste into `system_prompt.md` of each worker)

Workers `rtl-gen`, `tb-gen`, `sim-debug`, `syn`, `dft`, `pnr`, `sta`, etc. should
call `check_signature_drift.py` at entry. Suggested preamble snippet:

```
# Golden signature drift gate — paste at start of worker's runtime
python3 ../fl-model-gen/scripts/check_signature_drift.py "$IP" --root .. --worker "<this-worker-name>" || {
  echo "[SSOT HANDOFF] golden_changed -> human"
  exit 1
}
```

Or in Python:
```python
import subprocess, sys
ret = subprocess.call([
    "python3",
    "../fl-model-gen/scripts/check_signature_drift.py",
    ip,
    "--root", "..",
    "--worker", "rtl-gen",
])
if ret != 0:
    print("[SSOT HANDOFF] golden_changed -> human", file=sys.stderr)
    sys.exit(1)
```

The first time a worker runs, the lock is established silently. Subsequent runs
that detect drift will exit non-zero and emit the handoff message. Human can
approve a change with `--update-lock`.

### Determinism guarantees (now byte-stable across runs)
- `model/model_signature.json`
- `model/decomposition.json`
- `model/fl_model_check.json`
- `model/cycle_model.py`
- `cov/fl_fcov_plan.json`
- `cov/cl_fcov_plan.json`
- `cov/fcov_plan.json` (union view)
- `verify/equivalence_goals.json`
- `verify/protocol_assertions.sva`
- `golden/golden_todos.json`
- `golden/golden_todos_tracker.json`
- `governance/authority.json`
- `governance/authority.md`
- `governance/loop_map.mmd`
- `governance/loop_map.svg` (when mmdc is available)

### Files explicitly NOT changed (preserved invariants)
- `workflow/loader.py` — auto-discovery of `<ip>/<area>/<area>_todo_tracker.json` works without edits.
- `lib/todo_tracker.py` — TodoItem schema strict (lines 115-194).
- Other workflows (rtl-gen, tb-gen, sim-debug, syn, dft, pnr, sta) — their
  signature-drift integration is documented above as a paste-ready snippet, NOT
  applied automatically.

### Pilot results
- **smbus**: 13 todos, FL self-check passed=True, CL emit OK, 5 SVA assertions, 9 governance gates auto-detected.
- **pl330_target** (industrial-grade): 96 equivalence goals, 103 todos, 16
  decomposition units, 88 fcov bins (38 FL + 50 CL), 16 SVA assertions
  (12 handshake + 4 ordering), governance gates 6 approved / 3 pending / 0
  blocked, FL self-check passed=True (9 transactions, 8 with
  `[SSOT QUESTION]`), CL self-check passed=True.

### What remains for next session
- OV-010: emit_submodule_fl.py + emit_module_harness.py (per-module FL
  scoreboards for L2 module-level loop)
- OV-011: final regression sweep + flow_guide.md update + summary
- T2 #7: actually paste the signature-drift preamble into rtl-gen / tb-gen /
  sim-debug system_prompts (this requires modifying other workflows; left for
  human to apply per CHANGELOG snippet above)
- Optional external cycle backend research (deferred; default remains pure Python)

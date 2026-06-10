---
name: rocev-chain
description: Drive one IP through req → rtl → tb → sim with the ROCEV spine (Requirement → Obligation → Contract → Evidence → Validation) closed at every stage. Use when the user asks to take requirements to simulated RTL, or mentions ROCEV / obligation closure / req-to-sim.
---

# ROCEV Chain: req → rtl → tb → sim

Run one IP through four stages, closing the spine at each stage before moving on.
Never claim a stage done without its Validation gate output. The canonical
implementation lives in the repo — execute it, do not reimplement it.

**필독: 같은 폴더의 `KNOWN_TRAPS.md`** — 10-IP 실전에서 수확한 함정 전부
(올바른 게이트 명령, req 번들 수동 저작법, SSOT/TB 생성기 버그 워크어라운드).

## Spine mapping

| Stage | Requirement/Obligation | Contract | Evidence | Validation |
|---|---|---|---|---|
| req | `req/*.json` emitted + locked | locked truth bundle | `req/` bundle + VCM stage todos | `check_locked_truth_bundle.py`, `stage_gate.py` |
| rtl | rtl todo ledger per obligation | `rtl_contract` (SSOT) | `rtl/*.sv`, `rtl/rtl_compile.json` | lint + compile gate + goal-audit `--audit-rtl` |
| tb | scoreboard goals per obligation | equivalence goals (`verify/equivalence_goals.json`) | `tb/cocotb/*`, scoreboard events | tb ledger gate |
| sim | per-obligation sim closure | pass conditions (FL-vs-RTL) | `sim/results.xml`, `sim/sim_report.txt` | `check_sim_disk.py`, `check_truth_coverage.py`, goal-audit |

## Stage 1 — req (Requirement & Obligation 생성)

```bash
python3 .cursor/workflow/req-gen/scripts/emit_requirements_from_ssot.py <ip> --root .
python3 .cursor/workflow/req-gen/scripts/promote_requirement_review.py <ip> --root .
python3 .cursor/workflow/req-gen/scripts/lock_requirement_set.py <ip> --root .
python3 .cursor/workflow/req-gen/scripts/stage_contract_todos.py <ip> --root .   # VCM projector → per-stage todos
python3 .cursor/workflow/req-gen/scripts/check_locked_truth_bundle.py <ip> --root .
python3 .cursor/workflow/req-gen/scripts/stage_gate.py <ip> --root .
```

Gate FAIL → fix the requirement set, do not bypass. `/req-gen` subagent owns this stage.

## Stage 2 — rtl

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute --from-stage ssot-rtl --until lint
```

Evidence: `rtl/rtl_compile.json` fresh, lint gate PASS. `/rtl-gen` owns repairs.

## Stage 3 — tb

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute --from-stage ssot-tb-cocotb --until ssot-tb-cocotb
```

TB must observe every scoreboard observable in the SSOT expected_contract — a
missing observable is a contract violation, not a TB style choice. `/tb-gen` owns.

## Stage 4 — sim (Evidence & Validation 닫기)

```bash
python3 <ip>/tb/cocotb/test_runner.py                       # 안정 폴백 (LLM 불필요)
ATLAS_COV_BLOCK_IS_FAIL=0 python3 .cursor/workflow/req-gen/scripts/stage_gate.py sim <ip> --root .
python3 .cursor/workflow/sim/scripts/check_sim_disk.py <ip>
python3 .cursor/workflow/reqcov/scripts/check_truth_coverage.py <ip> --root .
```

PASS = real artifacts + ≥1 passing scoreboard event + zero failure markers.
A timeout/empty-XML run is NOT evidence. `/sim` owns; escalate DUT bugs
to `/rtl-gen` instead of weakening the TB.

## IP wiki history (every stage)

After each stage's Validation verdict (PASS or final FAIL), append the outcome
to the IP's own wiki so history accumulates next to the artifacts:

```bash
python3 .cursor/scripts/ip_wiki.py log <ip> --stage <req|rtl|tb|sim> --title "<verdict>" --body "<gate output line>"
python3 .cursor/scripts/ip_wiki.py check <ip>
```

See the `ip-wiki` skill for page creation and rules.

## Loop discipline

The `stop-todo-loop` hook re-prompts while stage todos remain open. Work one
todo at a time (`pending → in_progress → completed`), attach validator output
as evidence before completing, and let the loop end itself when the chain is closed.
If the same gate fails 3 consecutive times, stop and report the verbatim gate
output instead of retrying blindly.

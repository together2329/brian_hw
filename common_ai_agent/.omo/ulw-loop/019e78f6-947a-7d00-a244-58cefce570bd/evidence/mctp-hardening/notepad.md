# MCTP verification hardening ULW notepad

Date: 2026-06-02 Asia/Seoul

## Goal
Harden MCTP verification with items 1-6: per-scenario cocotb execution, SRAM payload/no-hole monitor, AXI protocol monitor, APB per-Q readback, survived-mutant classification, and optional safety property/formal artifact.

## Skills
- omo:ulw-loop: required by user; evidence-bound execution with tmux scenario artifacts.
- omo:programming: applies because Python TB/workflow code will be edited; use tests and strict verification.
- omo:debugging: may apply if cocotb/runtime failures appear; use only when needed for runtime failures.
- omo:review-work / codex-ultrawork-reviewer: final audit required because this is multi-file verification work.

## Binding criteria
C001: Directed scenario e2e expansion: 26 scenarios execute as DUT-observed cocotb/scoreboard rows, not only manifest entries. RED proof must show missing per-scenario e2e coverage before change; GREEN proof must show all 26 pass. Manual QA: tmux transcript.
C002: Monitor hardening: SRAM payload/no-hole/no-header monitor plus AXI write/read protocol monitor and APB per-Q register readback checks. RED proof must show monitors/checker detect missing monitor evidence before change; GREEN proof must show monitor evidence present and signoff pass. Manual QA: tmux transcript.
C003: Mutation/formal hardening: classify 16 survived mutants and add optional safety property/formal artifact. RED proof must show missing classification/formal artifact gate before change; GREEN proof must show classification complete and optional formal artifact recorded. Manual QA: tmux transcript.
C004: Final regression/signoff: lint/compile/cocotb/scoreboard/coverage/truth/mutation/signoff all pass, wiki updated, reviewer approval captured. Manual QA: tmux transcript.

## Bootstrap findings
- Prior OMO goal is blocked only by Codex goal mismatch; criteria were pass. This run uses separate evidence under evidence/mctp-hardening/.
- Existing cocotb tests: fl_rtl_equivalence_goals plus two payload datapath tests.
- Existing scenario manifest: 26 directed scenarios.
- `get_goal` still reports a previous completed objective; this run uses the user-visible `# Goal` block as the binding goal and avoids mutating the stale global goal.
- Read-only explorer `mctp_mutation_formal_explorer` mapped mutation/formal support. Read-only explorer `mctp_tb_arch_explorer` targeted `mctp_assembler` instead of `mctp_assembler_scratch`; do not use that result for scratch implementation decisions.
- Plan agent `mctp_hardening_plan` was closed after two wait windows without a result; fallback plan below is the executable ordering.

## Wave plan
- Wave 1 RED gates:
  - Add/execute tests that fail because directed scenario hardening evidence is absent.
  - Add/execute tests that fail because monitor evidence is absent.
  - Add/execute tests that fail because mutation survivor classification/formal artifact is absent.
- Wave 2 implementation:
  - Add reusable monitor artifact generation in `mctp_assembler_scratch/tb/cocotb/test_mctp_payload_datapath.py`.
  - Add scenario execution summary in `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py`.
  - Add survivor classification script/report under `workflow/mutation/scripts/` and `mctp_assembler_scratch/mutation/`.
  - Add safety property/formal optional artifact under `mctp_assembler_scratch/verify/`.
  - Update signoff gate to consume hardening artifacts.
- Wave 3 GREEN + manual QA:
  - Run targeted pytest RED/GREEN evidence.
  - Run cocotb via tmux and capture transcript.
  - Run signoff/lint/compile/scoreboard/coverage/mutation/truth via tmux and capture transcript.
- Wave 4 review:
  - Spawn final reviewer, fix blockers, rerun full scenario list.

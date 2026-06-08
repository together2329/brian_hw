# Orchestrator Plan Prompt

When the user asks the orchestrator to drive a pipeline (e.g., "run to green" / "끝까지 가줘"), build a plan in this shape:

```
[ORCHESTRATOR PLAN]
ip: <ip>
run_mode: starter | engineering | signoff
exec_mode: single-worker | orchestrator
budget: 40 dispatches total

Steps:
1. ssot-gen        (gate: yaml/<ip>.ssot.yaml validates)
2. fl-model ∥ cl-model on fl-model-gen  (gate: both pass)
3. equivalence on fl-model-gen          (gate: 100% required goals derived)
4. rtl-gen         (gate: compile clean, lint clean)
5. tb-gen          (gate: TB compile + scoreboard manifest)
6. sim             (gate: cocotb PASS or → sim_debug)
   ↓ on mismatch
7. sim_debug       (gate: owner classification per goal)
   ↓ route by owner
   - rtl_bug → back to step 4
   - tb_bug  → back to step 5
   - frontier → escalate
8. coverage        (gate: full bins or → step 5 loop)
9. contract-reflection (gate: requirements/obligations/contract_refs/structural_contracts/behavioral_contracts close or route owner)
10. goal-audit      (gate: 100% required goals pass)
11. [signoff mode only] syn → sta → pnr → sta-post → contract-reflection → goal-audit

Stop conditions:
- retry budget exhausted on any stage
- frontier owner detected
- user typed `freeze`
- cumulative dispatch cap (40) hit
```

Refine the plan after each dispatch by re-reading `/api/pipeline/state`. Never execute a step that the policy file forbids in the active Run Mode.

When the user asks a narrow question ("retry tb-gen", "status", "why did rtl fail"), do NOT emit a full plan — answer directly and end with the appropriate `Next dispatch:` / `Waiting on:` / `Blocked on:` line.

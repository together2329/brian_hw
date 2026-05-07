# RTL Authoring Status: pl330_target

## Status

- Top: pl330_target
- Packets: 33
- LLM-actionable tasks: 0
- Human-locked tasks: 5
- Tool-evidence tasks: 4
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 398
- Recommended packet batch limit: 4
- Reference profile: reports/rtl_reference_profile.json
- Reference scale: files=143, modules=210, lines=130568, procedural_blocks=910
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference scale gap: source_files=10/57 (17.5%), modules=10/52 (19.2%), lines=4662/52338 (8.9%), instances=11/472 (2.3%), procedural_blocks=40/561 (7.1%)
- Target scale candidate: present but not SSOT-locked

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=4, next_tool=audit-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_contract_blocked: human_locked=2, json=rtl/authoring_packets/rtl_gate_contract_blocked.json
- rtl_gate_human_closure: human_locked=3, json=rtl/authoring_packets/rtl_gate_human_closure.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.

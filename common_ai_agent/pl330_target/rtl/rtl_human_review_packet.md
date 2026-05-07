# RTL Human Review Packet: pl330_target

Status: pending_human_review

This packet is not approval. It is a review aid for human-locked RTL gates.

## Target Scale

- Blocker: RTL_TARGET_SCALE_POLICY
- Decision: Lock or explicitly waive production RTL target scale before PL330-level PASS claims.
- Suggested minima: `{"basis": "candidate structural scale from rtl_reference_profile; review and lock in SSOT before enforcement", "control_flow_min": 155, "depth_score_min": 4507, "instances_min": 472, "lines_min": 52338, "modules_min": 52, "nonconstant_assigns_min": 1135, "procedural_blocks_min": 561, "source_files_min": 57, "state_updates_min": 295}`

## Connection Contracts

- Blocker: RTL_RESOLVE_CONNECTION_CONTRACTS
- Candidate rows: 398
- Approval target: `integration.connections` or matching `sub_modules[].connections`

| module | instance | port | signal | direction |
| --- | --- | --- | --- | --- |
| pl330_target_engine | u_engine | busy | engine_busy | output |
| pl330_target_engine | u_engine | channel_state | engine_channel_state | output |
| pl330_target_engine | u_engine | clk | clk | input |
| pl330_target_engine | u_engine | cmd_channel | engine_cmd_channel | input |
| pl330_target_engine | u_engine | cmd_dst_addr | engine_cmd_dst_addr | input |
| pl330_target_engine | u_engine | cmd_len | engine_cmd_len | input |
| pl330_target_engine | u_engine | cmd_opcode | engine_cmd_opcode | input |
| pl330_target_engine | u_engine | cmd_privileged | engine_cmd_privileged | input |
| pl330_target_engine | u_engine | cmd_ready | engine_cmd_ready | output |
| pl330_target_engine | u_engine | cmd_secure | engine_cmd_secure | input |
| pl330_target_engine | u_engine | cmd_src_addr | engine_cmd_src_addr | input |
| pl330_target_engine | u_engine | cmd_valid | engine_cmd_valid | input |
| ... | ... | ... | 386 more row(s) in JSON | ... |

## Apply Rule

After human review, copy the edited `draft_rtl_blocker_answers` into an answers JSON as `rtl_blocker_answers`, then run:

```sh
python3 workflow/ssot-gen/scripts/resolve_rtl_blockers.py <ip> --root . --answers-json <approved-answers.json>
```

Then rerun RTL TODO derivation. If the RTL files were already common_ai_agent-authored and only SSOT metadata changed, refresh provenance:

```sh
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py <ip> --root . --audit-rtl
python3 workflow/rtl-gen/scripts/refresh_rtl_provenance.py <ip> --root .
```

Do not treat this packet as SSOT authority by itself.

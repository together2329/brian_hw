Generate canonical SSOT YAML for gpio from gpio/req/gpio_requirements.md.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Valid success schema:
{
  "files": [
    {
      "path": "gpio/yaml/gpio.ssot.yaml",
      "kind": "ssot",
      "content": "<complete YAML document as a JSON string>"
    }
  ]
}

The YAML content must be general IP SSOT, not a fixed template workaround. It must derive semantics from the requirements and include these top-level sections: top_module, sub_modules, parameters, io_list, features, dataflow, function_model, cycle_model, clock_reset_domains, cdc_requirements, rdc_requirements, registers, memory, interrupts, fsm, timing, power, security, error_handling, debug_observability, integration, dft, synthesis, pnr, coding_rules, reuse_modules, custom, dir_structure, filelist, rtl_contract, test_requirements, quality_gates, traceability, workflow_todos, generation_flow. function_model and cycle_model are mandatory and must be substantive enough for FL-vs-RTL equivalence goals, cocotb/pyuvm scoreboard generation, coverage planning, and mismatch ownership.

The generated YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh gpio` without repair. Required validator details:
- function_model.state_variables, function_model.transactions, and function_model.invariants must be non-empty lists.
- Every function_model.transactions[] item must include id, name, preconditions, outputs, and either side_effects or error_cases. If state_updates exist, also summarize them in side_effects.
- cycle_model must include clock, reset, latency, non-empty handshake_rules, non-empty pipeline, and non-empty ordering.
- timing must include target_clocks and latency_budget.
- power must include non-empty domains and power_states.
- security must include classification, non-empty assets, and non-empty threat_model.
- error_handling must include non-empty error_sources plus propagation and recovery.
- debug_observability must include waveform_must_probe and trace_events.
- integration must include bus_attachment and dependencies.
- dft must include scan_required, controllability, and observability.
- synthesis must include dialect, constraints, and required_outputs.
- every test_requirements.scenarios[] item must include id, name, stimulus, expected, checker, and coverage.
- quality_gates must be a mapping with ssot, rtl, dv, coverage, eda, and signoff; each gate must be a mapping with pass and evidence.
- If quality_gates.rtl_gen.profile is production, or the IP is DMA330/PL330-class, quality_gates.rtl_gen must include pass/evidence and every manifest-owned child module must have machine-readable integration.connections or sub_modules[].connections records with module/port/signal fields.
- traceability.yaml_to_output must be a non-empty list.

- workflow_todos.rtl-gen must be a non-empty list of LLM-authored RTL TODOs. Each item must include id, content, detail, criteria, source_refs, priority, required, and owner_module/owner_file when inferable from sub_modules. These TODOs are the downstream rtl-gen work ledger and must be specific to this IP, not fixed boilerplate.

If the requirements leave a semantic decision undefined, return exactly this JSON shape instead of files[]:
{
  "human_gate": {
    "decision_needed": "<specific RTL-engineer decision>",
    "evidence": {"requirement_refs": [], "ssot_refs": [], "tool_logs": [], "goal_ids": []},
    "options": [{"label": "<option>", "effect": "<downstream effect>"}],
    "recommended_default": {"label": "<option>", "why": "<reason>"},
    "downstream_effect": ["function_model", "cycle_model", "rtl_contract", "tb scoreboard"]
  }
}

Requirements:
# gpio IP Requirements

## Intent

Build a small parameterizable bidirectional GPIO peripheral as a smoke
fixture for the common_ai_agent SSOT pipeline. The block is intentionally
narrow: no bus and no interrupt, just direct register-style ports that
exercise SSOT, function-model, cycle-model, equivalence goals, RTL,
lint, TB, sim, coverage, and audit.

## Functional Behavior

- `clk` is the only clock.
- `rst_n` is an active-low asynchronous reset; on assertion all output
  state returns to zero.
- `dir_in[WIDTH-1:0]` is a synchronous control that selects per-pin
  direction. `0` makes the pin an input, `1` makes the pin an output.
- `dout_in[WIDTH-1:0]` is the output data value to drive when the pin
  is configured as output.
- `pad_in[WIDTH-1:0]` is the observed pad value when the pin is an
  input.
- `dir_q[WIDTH-1:0]` is the registered direction state.
- `dout_q[WIDTH-1:0]` is the registered output-data state.
- `oe_o[WIDTH-1:0]` is the combinational output-enable to the pad
  ring; bit `i` is high iff `dir_q[i]` is `1`.
- `pad_o[WIDTH-1:0]` is the combinational output-data to the pad ring;
  bit `i` equals `dout_q[i]` when `dir_q[i]` is `1`, otherwise `0`.
- `din_q[WIDTH-1:0]` is the registered input sample of `pad_in` on the
  rising clock edge for every bit whose `dir_q` is `0`. Bits whose
  `dir_q` is `1` hold their previous `din_q` value.

## Non-Goals

- No APB, AXI, or CSR bus.
- No interrupt or edge-detect logic.
- No clock-domain crossing or asynchronous IO ring metastability
  modeling beyond the simple input sample.
- `WIDTH` is parameterized via SSOT; the smoke fixture default is 8
  bits.

## Verification Hints

- Reset clears `dir_q`, `dout_q`, `din_q`, `oe_o`, and `pad_o`.
- Toggling `dir_in` from 0 to 1 should make `oe_o` follow on the next
  cycle.
- When `dir_q[i]` is 0, `pad_o[i]` must stay at 0 regardless of
  `dout_q[i]`.
- When `dir_q[i]` is 1, `pad_o[i]` must equal `dout_q[i]` and `oe_o[i]`
  must be 1.
- `din_q[i]` only samples `pad_in[i]` for input bits; output bits keep
  their last sampled value.
- Coverage should hit: all-input, all-output, mixed direction, write
  while output, read while input, and a randomized walk that flips
  direction.

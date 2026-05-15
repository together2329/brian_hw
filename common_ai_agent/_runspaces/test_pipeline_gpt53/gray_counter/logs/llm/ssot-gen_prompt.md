Generate canonical SSOT YAML for gray_counter from gray_counter/req/gray_counter_requirements.md.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Valid success schema:
{
  "files": [
    {
      "path": "gray_counter/yaml/gray_counter.ssot.yaml",
      "kind": "ssot",
      "content": "<complete YAML document as a JSON string>"
    }
  ]
}

The YAML content must be general IP SSOT, not a fixed template workaround. It must derive semantics from the requirements and include these top-level sections: top_module, sub_modules, parameters, io_list, features, dataflow, function_model, cycle_model, clock_reset_domains, cdc_requirements, rdc_requirements, registers, memory, interrupts, fsm, timing, power, security, error_handling, debug_observability, integration, dft, synthesis, pnr, coding_rules, reuse_modules, custom, dir_structure, filelist, rtl_contract, test_requirements, quality_gates, traceability, workflow_todos, generation_flow. function_model and cycle_model are mandatory and must be substantive enough for FL-vs-RTL equivalence goals, cocotb/pyuvm scoreboard generation, coverage planning, and mismatch ownership.

The generated YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh gray_counter` without repair. Required validator details:
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
# gray_counter IP Requirements

## Intent

Build a small synchronous Gray-code counter as a smoke fixture for the
common_ai_agent SSOT pipeline. The block is intentionally narrow: no bus,
no memory, no interrupt. It must still exercise SSOT, function-model,
cycle-model, equivalence goals, RTL, lint, TB, sim, coverage, and audit.

## Functional Behavior

- `clk` is the only clock.
- `rst_n` is an active-low asynchronous reset; on assertion the counter
  returns to `gray_value = 0` and `done` deasserts.
- `clear` synchronously forces `gray_value` to 0 and clears `done`.
- `enable` advances the counter by one Gray step on every rising clock
  edge while high.
- `gray_value[WIDTH-1:0]` is the registered Gray-coded output.
- `bin_value[WIDTH-1:0]` is the combinational binary equivalent of
  `gray_value` provided for observers and coverage.
- `done` pulses for exactly one cycle when the counter wraps from the
  maximum Gray code back to zero.

## Non-Goals

- No APB/AXI/CSR bus or register file.
- No clock-domain crossing, asynchronous interface, or reset-domain
  crossing.
- No memory, FIFO, or interrupt generation.
- The counter width is parameterized through SSOT; the default is 4 bits
  for the smoke fixture.

## Verification Hints

- Stimulus uses `enable` pulses with periodic `clear` and `rst_n`
  injection.
- Expected `bin_value` follows the standard `bin = gray ^ (gray >> 1)`
  identity.
- `done` must align with the wrap cycle, not with intermediate counts.
- Coverage should hit reset, clear-after-run, full wrap, hold (enable
  low), and a randomized walk.

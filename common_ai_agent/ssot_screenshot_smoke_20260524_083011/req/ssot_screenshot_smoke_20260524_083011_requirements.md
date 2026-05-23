# ssot_screenshot_smoke_20260524_083011 Requirements Ledger

- Source: ATLAS Web Q&A state plus per-IP wiki/import evidence captured for `ssot_screenshot_smoke_20260524_083011`.
- Evidence index: `ssot_screenshot_smoke_20260524_083011/wiki/index.md`, `ssot_screenshot_smoke_20260524_083011/wiki/import-evidence.md`, `ssot_screenshot_smoke_20260524_083011/req/import_manifest.json`.
- Authority: this file records requirement intent; the YAML SSOT remains the machine-readable source for downstream FL, RTL, DV, lint, simulation, and coverage stages.
- IP kind: Valid-ready byte transform smoke IP for ATLAS SSOT generation screenshot test.
- Generated: 2026-05-24T08:30:12.

## Approved Requirement Decisions
- `bus_interface`: Native valid-ready interface with valid, ready, data_in, command, result, result_valid, accepted_count, busy, and error; no APB or AXI interface.
- `clock_reset`: clk 100MHz, rst_n active-low asynchronous assert and synchronous deassert.
- `interrupt`: No interrupt output in this smoke revision.
- `machine_rules`: sample_condition=valid; output result=data_in ^ command; output result_valid=1; output ready=1; output accepted_count=accepted_count + 1; state accepted_count=accepted_count + 1; state busy=0; state error=0
- `memory_map`: No local RAM or FIFO; only flop state for accepted_count, busy, result_valid, and error.
- `parameters`: DATA_WIDTH=8, COMMAND_WIDTH=8, COUNT_WIDTH=16, ADDR_WIDTH=4
- `purpose`: Accept one byte-oriented valid-ready transaction when valid and ready are high; output result equals data_in XOR command and assert result_valid on the accepted transaction.
- `register_map`: No firmware-visible CSR registers in this smoke revision.
- `submodule_structure`: Single generated top-level module; conceptual units only: input_accept, xor_datapath, result_status.
- `test_expectation`: reset clears busy error result_valid and accepted_count; nominal transaction data_in XOR command produces result and increments accepted_count; valid low holds state; backpressure not applied because ready is always high after reset; malformed unknowns are treated as error in downstream DV if driven

## Behavioral Contract
- Top module `ssot_screenshot_smoke_20260524_083011` must implement the approved function model and cycle model exactly as represented in `ssot_screenshot_smoke_20260524_083011/yaml/ssot_screenshot_smoke_20260524_083011.ssot.yaml`.
- Function model operations: Accept one byte-oriented valid-ready transaction when valid and ready are high; output result equals data_in XOR command and assert result_valid on the accepted transaction..
- Cycle model obligation: latency, sampling, and output timing are defined by the SSOT cycle model.
- Any feature, port, state update, bus behavior, interrupt, memory, or coverage goal absent from the SSOT is outside this revision and requires a new approved requirement entry before implementation.
- RTL generation, test generation, sim-debug, and coverage are expected to read the SSOT and must not infer hidden behavior from chat history.

## Interface And Decomposition

## Decomposition Units
- `ssot_screenshot_smoke_20260524_083011_input_accept` owns Conceptual functional decomposition unit `input_accept` from approved Q&A; implemented inside the single generated top module for this revision..
- `ssot_screenshot_smoke_20260524_083011_xor_datapath` owns Conceptual functional decomposition unit `xor_datapath` from approved Q&A; implemented inside the single generated top module for this revision..
- `ssot_screenshot_smoke_20260524_083011_result_status` owns Conceptual functional decomposition unit `result_status` from approved Q&A; implemented inside the single generated top module for this revision..

## Verification And Coverage Intent
- Verification must prove FL-vs-RTL equivalence for every SSOT goal before final signoff.
- Functional coverage is the primary closure metric for this flow; structural metrics are required only when the SSOT explicitly requests tool evidence for them.
- DUT-only lint must pass before simulation evidence can be used for signoff.
- Scenario 1 `SC_RESET`: Assert and deassert reset using the approved clock/reset scheme.
- Scenario 2 `SC1`: reset clears busy error result_valid and accepted_count
- Scenario 3 `SC2`: nominal transaction data_in XOR command produces result and increments accepted_count
- Scenario 4 `SC3`: valid low holds state
- Scenario 5 `SC4`: backpressure not applied because ready is always high after reset
- Scenario 6 `SC5`: malformed unknowns are treated as error in downstream DV if driven

## Acceptance Criteria
- `ssot_screenshot_smoke_20260524_083011/yaml/ssot_screenshot_smoke_20260524_083011.ssot.yaml` parses and contains the functional model, cycle model, RTL contract, test requirements, quality gates, traceability, and downstream workflow action ledger.
- Generated RTL implements only SSOT-approved behavior and passes DUT-only lint with zero errors.
- Generated cocotb/pyuvm tests execute scoreboard comparisons against the functional model.
- Simulation produces machine-readable pass evidence, FL-vs-RTL comparison evidence, and coverage evidence.
- Final goal audit passes with fresh artifacts for requirements, SSOT, FL model, RTL, lint, DV, simulation, coverage, and equivalence.

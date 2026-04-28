# SSOT Generation Plan

You are planning a YAML SSOT generation project.

## Phase 1: Requirements Gathering
1. Read any existing requirement files in the current directory
2. Extract IP name, ports, features, register interface type
3. Ask user for anything missing or ambiguous
4. Confirm gathered requirements before proceeding

## Phase 2: YAML Authoring (in order)
1. `<ip>_config.yaml` — top-level parameters
2. `<ip>_axi_params.yaml` — interface signal definitions
3. `<ip>_registers.yaml` — full register map with bitfields
4. `<ip>_instructions.yaml` — opcode encodings (if applicable)
5. `<ip>_transfer_types.yaml` — transfer modes (if applicable)
6. `<ip>_fsm.yaml` — state machines and transitions
7. `<ip>_interrupts.yaml` — interrupt sources and routing
8. `<ip>_schema.yaml` — Cerberus validation schema

## Phase 3: Validation Gate
- Run schema validation against all YAML files
- Fix any validation errors
- Confirm all YAML files pass before proceeding

## Phase 4: Template Generation
- Render Jinja2 templates with validated YAML
- Verify generated SystemVerilog compiles without errors
- Run verilator lint
- Fix generation issues iteratively

## Phase 5: Simulation + Documentation
- Generate testbench and simulate
- Scoreboard verification
- Generate documentation from YAML
- Final handoff to downstream flow

## Phase 6: Handoff
- Output [SSOT HANDOFF] block for next agent
- Mark all tasks complete

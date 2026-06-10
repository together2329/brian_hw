# Locked Truth - shift_reg_cx1

## Approval
- status: requirements_locked
- approved_by: cursor_agent
- approved_at_utc: 2026-06-10T14:01:00Z

## Requirements
```json
{
  "ip": "shift_reg_cx1",
  "requirements": [
    {
      "obligation_refs": [
        "OBL_SR8_LINT_001",
        "OBL_SR8_RESET_001",
        "OBL_SR8_SHIFT_001"
      ],
      "required": true,
      "requirement_id": "REQ_SR8_FUNC_001",
      "statement": "The shift register shifts left by 1 on every rising clock edge when rst_n==1 (si enters at bit 0) and clears to 0 synchronously when rst_n==0.",
      "status": "locked",
      "title": "8-bit SIPO shift register with sync reset"
    }
  ],
  "schema_version": 1,
  "type": "requirements_index"
}
```

## Obligations
```json
{
  "ip": "shift_reg_cx1",
  "obligations": [
    {
      "behavioral_contract_refs": [
        "BC_SR8_LINT"
      ],
      "closure_stage": "lint",
      "contract_refs": [
        "C_SR8_LINT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "structural",
      "obligation_id": "OBL_SR8_LINT_001",
      "owned_by_stage": "lint",
      "required_stages": [
        "lint"
      ],
      "requirement_refs": [
        "REQ_SR8_FUNC_001"
      ],
      "statement": "No inferred latches; po is a single-driver registered output.",
      "structural_contract_refs": [
        "SC_SR8_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_SR8_RESET"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_SR8_RESET"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_SR8_RESET_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_SR8_FUNC_001"
      ],
      "statement": "po clears to 0 synchronously when rst_n==0.",
      "structural_contract_refs": [
        "SC_SR8_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_SR8_SHIFT"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_SR8_SHIFT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_SR8_SHIFT_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_SR8_FUNC_001"
      ],
      "statement": "po shifts left each cycle with si entering at bit 0.",
      "structural_contract_refs": [
        "SC_SR8_PORTS"
      ]
    }
  ],
  "schema_version": 1,
  "type": "obligations"
}
```

## Contract Refs
```json
{
  "contract_refs": [
    {
      "contract_ref_id": "C_SR8_LINT",
      "obligation_refs": [
        "OBL_SR8_LINT_001"
      ],
      "ssot_anchor": "coding_rules",
      "stage_contracts": [
        {
          "artifact": "lint/dut_lint.json",
          "stage": "lint"
        }
      ]
    },
    {
      "contract_ref_id": "C_SR8_RESET",
      "obligation_refs": [
        "OBL_SR8_RESET_001"
      ],
      "ssot_anchor": "function_model.transactions.TR_RESET",
      "stage_contracts": [
        {
          "artifact": "rtl/shift_reg_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_shift_reg_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_SR8_SHIFT",
      "obligation_refs": [
        "OBL_SR8_SHIFT_001"
      ],
      "ssot_anchor": "function_model.transactions.TR_SHIFT",
      "stage_contracts": [
        {
          "artifact": "rtl/shift_reg_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_shift_reg_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    }
  ],
  "ip": "shift_reg_cx1",
  "schema_version": 1,
  "type": "contract_refs"
}
```

## Structural Contracts
```json
{
  "contracts": [
    {
      "clock_domains": [
        {
          "clock_signal": "clk",
          "id": "main"
        }
      ],
      "id": "SC_SR8_PORTS",
      "interfaces": [
        {
          "clock_domain": "main",
          "id": "serial_iface",
          "signals": [
            "po",
            "si"
          ]
        }
      ],
      "obligations": [
        "OBL_SR8_LINT_001",
        "OBL_SR8_RESET_001",
        "OBL_SR8_SHIFT_001"
      ],
      "reset_domains": [
        {
          "clock_domain": "main",
          "id": "sync_rst",
          "reset_signal": "rst_n"
        }
      ],
      "signals": [
        {
          "dir": "input",
          "name": "clk",
          "timing": {
            "kind": "clock"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "rst_n",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "si",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "output",
          "name": "po",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 8
        }
      ]
    }
  ],
  "ip": "shift_reg_cx1",
  "schema_version": 1,
  "type": "structural_contracts"
}
```

## Behavioral Contracts
```json
{
  "contracts": [
    {
      "cycle_model_waiver": "lint-only obligation; functional cycle model covered by BC_SR8_SHIFT and BC_SR8_RESET",
      "id": "BC_SR8_LINT",
      "invariants": [
        "No inferred latches in shift_reg_cx1 RTL",
        "po is registered; single driver"
      ],
      "obligations": [
        "OBL_SR8_LINT_001"
      ],
      "ssot_section": "coding_rules",
      "stage_contracts": [
        {
          "artifact": "lint/dut_lint.json",
          "pass_condition": "no latch findings",
          "stage": "lint",
          "timing": "registered output; no async path"
        }
      ],
      "timing": "po is a clocked register; no combinational loop or latch inference"
    },
    {
      "id": "BC_SR8_RESET",
      "latency": {
        "reset_clear": "1 clock cycle: po==0 one rising clk after rst_n asserts"
      },
      "obligations": [
        "OBL_SR8_RESET_001"
      ],
      "reset": "synchronous active-low; po clears to 0 on rising clk when rst_n==0",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/shift_reg_cx1.sv",
          "reset": "synchronous active-low",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_shift_reg_cx1.py",
          "reset": "drive rst_n=0 one cycle, check po==0 next cycle",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "1 cycle reset-to-clear",
          "pass_condition": "po==0 one cycle after rst_n asserts",
          "stage": "sim"
        }
      ],
      "transactions": [
        {
          "id": "TR_RESET",
          "outputs": [
            {
              "expr": "0",
              "name": "po"
            }
          ],
          "preconditions": [
            "rst_n == 0"
          ],
          "state_updates": [
            {
              "expr": "0",
              "name": "shift_reg"
            }
          ]
        }
      ]
    },
    {
      "id": "BC_SR8_SHIFT",
      "latency": {
        "shift_update": "1 clock cycle: po updates one rising clk after si sampled"
      },
      "obligations": [
        "OBL_SR8_SHIFT_001"
      ],
      "ordering": "reset (rst_n==0) takes priority over shift in same cycle",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/shift_reg_cx1.sv",
          "stage": "rtl",
          "timing": "synchronous reset, 1-cycle latency"
        },
        {
          "artifact": "tb/cocotb/test_shift_reg_cx1.py",
          "stage": "tb",
          "timing": "si applied one cycle before expected po update"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "1 clock cycle per shift",
          "pass_condition": "shift sequence matches FL expected",
          "stage": "sim"
        }
      ],
      "timing": "po registered on rising clk edge; si sampled every cycle when rst_n==1",
      "transactions": [
        {
          "id": "TR_SHIFT",
          "outputs": [
            {
              "expr": "((shift_reg << 1) | (si & 1)) & 0xFF",
              "name": "po"
            }
          ],
          "preconditions": [
            "rst_n == 1"
          ],
          "state_updates": [
            {
              "expr": "((shift_reg << 1) | (si & 1)) & 0xFF",
              "name": "shift_reg"
            }
          ]
        }
      ]
    }
  ],
  "ip": "shift_reg_cx1",
  "schema_version": 1,
  "type": "behavioral_contracts"
}
```

## Evidence Plan
```json
{
  "evidence_plan": [
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "BC_SR8_LINT",
      "evidence_id": "E_SR8_BC_LINT",
      "pass_condition": "no latch findings per BC_SR8_LINT",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_SR8_RESET",
      "evidence_id": "E_SR8_BC_RESET",
      "pass_condition": "po==0 one cycle after rst_n asserts per BC_SR8_RESET",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_SR8_SHIFT",
      "evidence_id": "E_SR8_BC_SHIFT",
      "pass_condition": "shift sequence matches BC_SR8_SHIFT TR_SHIFT expected",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "C_SR8_LINT",
      "evidence_id": "E_SR8_LINT",
      "pass_condition": "no latch / no single-driver violations",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_SR8_RESET",
      "evidence_id": "E_SR8_RESET",
      "pass_condition": "po==0 observed one cycle after rst_n asserts",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "rtl/shift_reg_cx1.sv",
      "contract_ref": "SC_SR8_PORTS",
      "evidence_id": "E_SR8_SC_PORTS",
      "pass_condition": "top ports clk rst_n si po present with correct widths",
      "validator": "check_tb_python_compile.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_SR8_SHIFT",
      "evidence_id": "E_SR8_SHIFT",
      "pass_condition": "observed shift sequence matches FL expected",
      "validator": "check_evidence_contract.py"
    }
  ],
  "ip": "shift_reg_cx1",
  "schema_version": 1,
  "type": "evidence_plan"
}
```

## Source Hashes
- req/behavioral_contracts.json: sha256:9d1bec8edf641c556e8faf1e26c011c983b9eb3b78b8bfa3724d8dc4f3397eef
- req/contract_refs.json: sha256:c21e7be085d161a47d0eca1cd1f8b9024c7033a12996f468742303a750cc8383
- req/evidence_plan.json: sha256:190b4c8c8898ee811dac843ab4a76408050b25a94c6a74d47fe935edf605a360
- req/obligations.json: sha256:77e00c6ef5c8ecd5dc259934ae9c25b3d6c2f86633265873e98ccab0febcf825
- req/requirements_index.json: sha256:8a897ae817110542478df836ae82d93c78153ba1ef7fd7275349e4cbc03b2e5f
- req/structural_contracts.json: sha256:3ce8f9f03bd0bfbd663c112f57d27c2b047270f7366b3b919e162f88af835075

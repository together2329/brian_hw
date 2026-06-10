# Locked Truth - counter8_cx1

## Approval
- status: requirements_locked
- approved_by: cursor_agent
- approved_at_utc: 2026-06-10T14:00:08Z

## Requirements
```json
{
  "ip": "counter8_cx1",
  "requirements": [
    {
      "obligation_refs": [
        "OBL_CNT8_COUNT_001",
        "OBL_CNT8_HOLD_001",
        "OBL_CNT8_LINT_001",
        "OBL_CNT8_RESET_001"
      ],
      "required": true,
      "requirement_id": "REQ_CNT8_FUNC_001",
      "statement": "The counter increments by 1 on each rising clock edge when en==1 and rst_n==1, holds when en==0, resets to 0 when rst_n==0, and wraps from 255 to 0.",
      "status": "locked",
      "title": "8-bit up-counter with sync reset and enable"
    }
  ],
  "schema_version": 1,
  "type": "requirements_index"
}
```

## Obligations
```json
{
  "ip": "counter8_cx1",
  "obligations": [
    {
      "behavioral_contract_refs": [
        "BC_CNT8_COUNT"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_CNT8_COUNT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_CNT8_COUNT_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_CNT8_FUNC_001"
      ],
      "statement": "count increments by 1 every enabled cycle and wraps at 255.",
      "structural_contract_refs": [
        "SC_CNT8_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_CNT8_HOLD"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_CNT8_HOLD"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_CNT8_HOLD_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_CNT8_FUNC_001"
      ],
      "statement": "count holds its value when en==0 and rst_n==1.",
      "structural_contract_refs": [
        "SC_CNT8_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_CNT8_LINT"
      ],
      "closure_stage": "lint",
      "contract_refs": [
        "C_CNT8_LINT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "structural",
      "obligation_id": "OBL_CNT8_LINT_001",
      "owned_by_stage": "lint",
      "required_stages": [
        "lint"
      ],
      "requirement_refs": [
        "REQ_CNT8_FUNC_001"
      ],
      "statement": "No inferred latches; count is a single-driver registered output.",
      "structural_contract_refs": [
        "SC_CNT8_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_CNT8_RESET"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_CNT8_RESET"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_CNT8_RESET_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_CNT8_FUNC_001"
      ],
      "statement": "count clears to 0 synchronously when rst_n==0, regardless of en.",
      "structural_contract_refs": [
        "SC_CNT8_PORTS"
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
      "contract_ref_id": "C_CNT8_COUNT",
      "obligation_refs": [
        "OBL_CNT8_COUNT_001"
      ],
      "ssot_anchor": "function_model.transactions.TR_COUNT",
      "stage_contracts": [
        {
          "artifact": "rtl/counter8_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_counter8_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_CNT8_HOLD",
      "obligation_refs": [
        "OBL_CNT8_HOLD_001"
      ],
      "ssot_anchor": "function_model.transactions.TR_HOLD",
      "stage_contracts": [
        {
          "artifact": "rtl/counter8_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_counter8_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_CNT8_LINT",
      "obligation_refs": [
        "OBL_CNT8_LINT_001"
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
      "contract_ref_id": "C_CNT8_RESET",
      "obligation_refs": [
        "OBL_CNT8_RESET_001"
      ],
      "ssot_anchor": "function_model.transactions.TR_RESET",
      "stage_contracts": [
        {
          "artifact": "rtl/counter8_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_counter8_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    }
  ],
  "ip": "counter8_cx1",
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
      "id": "SC_CNT8_PORTS",
      "interfaces": [
        {
          "clock_domain": "main",
          "id": "ctrl_iface",
          "signals": [
            "count",
            "en"
          ]
        }
      ],
      "obligations": [
        "OBL_CNT8_COUNT_001",
        "OBL_CNT8_HOLD_001",
        "OBL_CNT8_LINT_001",
        "OBL_CNT8_RESET_001"
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
          "name": "en",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "output",
          "name": "count",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 8
        }
      ]
    }
  ],
  "ip": "counter8_cx1",
  "schema_version": 1,
  "type": "structural_contracts"
}
```

## Behavioral Contracts
```json
{
  "contracts": [
    {
      "id": "BC_CNT8_COUNT",
      "latency": {
        "count_update": "1 clock cycle: count updates one rising clk after en sampled"
      },
      "obligations": [
        "OBL_CNT8_COUNT_001"
      ],
      "ordering": "reset (rst_n==0) takes priority over enable (en==1) in same cycle",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/counter8_cx1.sv",
          "stage": "rtl",
          "timing": "synchronous reset, 1-cycle latency"
        },
        {
          "artifact": "tb/cocotb/test_counter8_cx1.py",
          "stage": "tb",
          "timing": "stimulus applied one cycle before expected count"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "1 clock cycle per increment",
          "pass_condition": "count increments match FL expected",
          "stage": "sim"
        }
      ],
      "timing": "count registered on rising clk edge; reset synchronous active-low",
      "transactions": [
        {
          "id": "TR_COUNT",
          "outputs": [
            {
              "expr": "(count_reg + 1) & 0xFF",
              "name": "count"
            }
          ],
          "preconditions": [
            "rst_n == 1",
            "en == 1"
          ],
          "state_updates": [
            {
              "expr": "(count_reg + 1) & 0xFF",
              "name": "count_reg"
            }
          ]
        }
      ]
    },
    {
      "id": "BC_CNT8_HOLD",
      "obligations": [
        "OBL_CNT8_HOLD_001"
      ],
      "ordering": "hold is the default state when en==0 and rst_n==1",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/counter8_cx1.sv",
          "stage": "rtl",
          "timing": "no state change when en==0"
        },
        {
          "artifact": "tb/cocotb/test_counter8_cx1.py",
          "stage": "tb",
          "timing": "verify count stable across multiple cycles with en==0"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "0 cycles of change",
          "pass_condition": "count unchanged when en==0",
          "stage": "sim"
        }
      ],
      "timing": "count holds its registered value when en==0; no increment cycle",
      "transactions": [
        {
          "id": "TR_HOLD",
          "outputs": [
            {
              "expr": "count_reg",
              "name": "count"
            }
          ],
          "preconditions": [
            "rst_n == 1",
            "en == 0"
          ],
          "state_updates": [
            {
              "expr": "count_reg",
              "name": "count_reg"
            }
          ]
        }
      ]
    },
    {
      "cycle_model_waiver": "lint-only obligation; functional cycle model covered by BC_CNT8_COUNT and BC_CNT8_RESET",
      "id": "BC_CNT8_LINT",
      "invariants": [
        "No inferred latches in counter8_cx1 RTL",
        "count is registered; single driver"
      ],
      "obligations": [
        "OBL_CNT8_LINT_001"
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
      "timing": "count is a clocked register; no combinational loop or latch inference"
    },
    {
      "id": "BC_CNT8_RESET",
      "latency": {
        "reset_clear": "1 clock cycle: count==0 one rising clk after rst_n asserts"
      },
      "obligations": [
        "OBL_CNT8_RESET_001"
      ],
      "reset": "synchronous active-low; count clears to 0 on rising clk when rst_n==0",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/counter8_cx1.sv",
          "reset": "synchronous active-low",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_counter8_cx1.py",
          "reset": "drive rst_n=0 one cycle, check count==0 next cycle",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "1 cycle reset-to-clear",
          "pass_condition": "count==0 one cycle after rst_n asserts",
          "stage": "sim"
        }
      ],
      "transactions": [
        {
          "id": "TR_RESET",
          "outputs": [
            {
              "expr": "0",
              "name": "count"
            }
          ],
          "preconditions": [
            "rst_n == 0"
          ],
          "state_updates": [
            {
              "expr": "0",
              "name": "count_reg"
            }
          ]
        }
      ]
    }
  ],
  "ip": "counter8_cx1",
  "schema_version": 1,
  "type": "behavioral_contracts"
}
```

## Evidence Plan
```json
{
  "evidence_plan": [
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_CNT8_COUNT",
      "evidence_id": "E_CNT8_BC_COUNT",
      "pass_condition": "count increments match behavioral contract TR_COUNT expected",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_CNT8_HOLD",
      "evidence_id": "E_CNT8_BC_HOLD",
      "pass_condition": "count stable when en==0 per BC_CNT8_HOLD",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "BC_CNT8_LINT",
      "evidence_id": "E_CNT8_BC_LINT",
      "pass_condition": "no latch findings per BC_CNT8_LINT",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_CNT8_RESET",
      "evidence_id": "E_CNT8_BC_RESET",
      "pass_condition": "count==0 one cycle after rst_n asserts per BC_CNT8_RESET",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_CNT8_COUNT",
      "evidence_id": "E_CNT8_COUNT",
      "pass_condition": "observed count sequence matches FL expected increment",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_CNT8_HOLD",
      "evidence_id": "E_CNT8_HOLD",
      "pass_condition": "count unchanged when en==0",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "C_CNT8_LINT",
      "evidence_id": "E_CNT8_LINT",
      "pass_condition": "no latch / no single-driver violations",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_CNT8_RESET",
      "evidence_id": "E_CNT8_RESET",
      "pass_condition": "count==0 observed one cycle after rst_n asserts",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "rtl/counter8_cx1.sv",
      "contract_ref": "SC_CNT8_PORTS",
      "evidence_id": "E_CNT8_SC_PORTS",
      "pass_condition": "top ports clk rst_n en count present with correct widths",
      "validator": "check_tb_python_compile.py"
    }
  ],
  "ip": "counter8_cx1",
  "schema_version": 1,
  "type": "evidence_plan"
}
```

## Source Hashes
- req/behavioral_contracts.json: sha256:3702a8c8e8e635eadf7fa1a811a92e80b1280068300964229541e03288634166
- req/contract_refs.json: sha256:dafa8b3c497442ddc4b32a901643f17f7b4040ec87e1bd9fce73c1c0042bfe07
- req/evidence_plan.json: sha256:4e29820cc8dc4ab88c55458b4842096f28a5597029264e51a26f5d7ac584f4b1
- req/obligations.json: sha256:a816aa83d6919d9a889a8596e88b31f2158e5db1a56e8bbbd6643ccce7eebae9
- req/requirements_index.json: sha256:d267753947e1fd3bc027a56f89e3723b293fbdb8bb6c29b130b253eb48a12a7f
- req/structural_contracts.json: sha256:ac989dcccf1c4c4df0659af33e7ade54e6d8fbb81cecbbf1f8ccf70034e90786

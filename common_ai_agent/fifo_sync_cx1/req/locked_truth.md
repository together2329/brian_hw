# Locked Truth - fifo_sync_cx1

## Approval
- status: requirements_locked
- approved_by: cursor-agent
- approved_at_utc: 2026-06-10T14:36:29Z

## Requirements
```json
{
  "ip": "fifo_sync_cx1",
  "requirements": [
    {
      "obligation_refs": [
        "OBL_FIFO_FLAGS_001",
        "OBL_FIFO_LINT_001",
        "OBL_FIFO_READ_001",
        "OBL_FIFO_RESET_001",
        "OBL_FIFO_WRITE_001"
      ],
      "required": true,
      "requirement_id": "REQ_FIFO_FUNC_001",
      "statement": "The FIFO accepts a write when wr_en is high and full is low; data is stored and count increments. Accepts a read when rd_en is high and empty is low; rd_data presents the head entry and count decrements. full asserts when count==8; empty asserts when count==0. All state clears synchronously when rst_n is low.",
      "status": "locked",
      "title": "8-deep 8-bit synchronous FIFO with full/empty flags"
    }
  ],
  "schema_version": 1,
  "type": "requirements_index"
}
```

## Obligations
```json
{
  "ip": "fifo_sync_cx1",
  "obligations": [
    {
      "behavioral_contract_refs": [
        "BC_FIFO_FLAGS"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_FIFO_FLAGS"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "count",
      "obligation_id": "OBL_FIFO_FLAGS_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_FIFO_FUNC_001"
      ],
      "statement": "full asserts when count reaches 8; empty asserts when count is 0.",
      "structural_contract_refs": [
        "SC_FIFO_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_FIFO_LINT"
      ],
      "closure_stage": "lint",
      "contract_refs": [
        "C_FIFO_LINT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "structural",
      "obligation_id": "OBL_FIFO_LINT_001",
      "owned_by_stage": "lint",
      "required_stages": [
        "lint"
      ],
      "requirement_refs": [
        "REQ_FIFO_FUNC_001"
      ],
      "statement": "No inferred latches; all state is registered.",
      "structural_contract_refs": [
        "SC_FIFO_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_FIFO_READ"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_FIFO_READ"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_FIFO_READ_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_FIFO_FUNC_001"
      ],
      "statement": "When rd_en is high and empty is low, rd_data presents the head entry and count decrements on the rising clock edge.",
      "structural_contract_refs": [
        "SC_FIFO_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_FIFO_RESET"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_FIFO_RESET"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_FIFO_RESET_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_FIFO_FUNC_001"
      ],
      "statement": "All FIFO state clears to reset values synchronously when rst_n is low.",
      "structural_contract_refs": [
        "SC_FIFO_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_FIFO_WRITE"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_FIFO_WRITE"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_FIFO_WRITE_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_FIFO_FUNC_001"
      ],
      "statement": "When wr_en is high and full is low, wr_data is stored and count increments on the rising clock edge.",
      "structural_contract_refs": [
        "SC_FIFO_PORTS"
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
      "contract_ref_id": "C_FIFO_FLAGS",
      "obligation_refs": [
        "OBL_FIFO_FLAGS_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_WRITE",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_fifo_sync_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_FIFO_LINT",
      "obligation_refs": [
        "OBL_FIFO_LINT_001"
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
      "contract_ref_id": "C_FIFO_READ",
      "obligation_refs": [
        "OBL_FIFO_READ_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_READ",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_fifo_sync_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_FIFO_RESET",
      "obligation_refs": [
        "OBL_FIFO_RESET_001"
      ],
      "ssot_anchor": "cycle_model",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_fifo_sync_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_FIFO_WRITE",
      "obligation_refs": [
        "OBL_FIFO_WRITE_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_WRITE",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_fifo_sync_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    }
  ],
  "ip": "fifo_sync_cx1",
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
      "id": "SC_FIFO_PORTS",
      "interfaces": [
        {
          "clock_domain": "main",
          "id": "fifo_io",
          "signals": [
            "empty",
            "full",
            "rd_data",
            "rd_en",
            "wr_data",
            "wr_en"
          ]
        }
      ],
      "obligations": [
        "OBL_FIFO_FLAGS_001",
        "OBL_FIFO_LINT_001",
        "OBL_FIFO_READ_001",
        "OBL_FIFO_RESET_001",
        "OBL_FIFO_WRITE_001"
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
          "name": "wr_en",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "wr_data",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 8
        },
        {
          "dir": "input",
          "name": "rd_en",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "output",
          "name": "rd_data",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 8
        },
        {
          "dir": "output",
          "name": "full",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "output",
          "name": "empty",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        }
      ]
    }
  ],
  "ip": "fifo_sync_cx1",
  "schema_version": 1,
  "type": "structural_contracts"
}
```

## Behavioral Contracts
```json
{
  "contracts": [
    {
      "cycle_model_waiver": "flags are combinational state functions (count==8, count==0); no additional cycle model beyond write/read BCs",
      "id": "BC_FIFO_FLAGS",
      "obligations": [
        "OBL_FIFO_FLAGS_001"
      ],
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "stage": "rtl",
          "timing": "combinational decode of registered count"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "pass_condition": "full asserts at count==8; empty asserts at count==0",
          "stage": "sim"
        }
      ],
      "timing": "full and empty update within the same clock cycle as count; combinational decode of registered count",
      "transactions": [
        {
          "id": "FM_FLAGS",
          "outputs": [
            {
              "expr": "count == 8",
              "name": "full"
            },
            {
              "expr": "count == 0",
              "name": "empty"
            }
          ],
          "preconditions": [
            "rst_n == 1"
          ],
          "state_updates": []
        }
      ]
    },
    {
      "cycle_model_waiver": "lint-only obligation; no cycle model required \u2014 latch-free structure is a static synthesis property",
      "id": "BC_FIFO_LINT",
      "invariants": [
        "No inferred latches in fifo_sync_cx1 RTL",
        "All state (count, wr_ptr, rd_ptr, fifo_memory) is registered"
      ],
      "obligations": [
        "OBL_FIFO_LINT_001"
      ],
      "ssot_section": "coding_rules",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "pass_condition": "RTL compiles and maps declared ports",
          "stage": "rtl"
        },
        {
          "artifact": "lint/dut_lint.json",
          "pass_condition": "no latch findings",
          "stage": "lint"
        }
      ]
    },
    {
      "id": "BC_FIFO_READ",
      "latency": {
        "read_update": "1 clock cycle: count and rd_ptr update one rising clk after rd_en sampled"
      },
      "obligations": [
        "OBL_FIFO_READ_001"
      ],
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_fifo_sync_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "pass_condition": "rd_data matches written data; count decrements",
          "stage": "sim"
        }
      ],
      "transactions": [
        {
          "id": "FM_READ",
          "outputs": [
            {
              "expr": "head_data",
              "name": "rd_data"
            },
            {
              "expr": "(count - 1) == 0",
              "name": "empty"
            }
          ],
          "preconditions": [
            "rst_n == 1",
            "rd_en == 1",
            "empty == 0"
          ],
          "state_updates": [
            {
              "expr": "count - 1",
              "name": "count"
            },
            {
              "expr": "(rd_ptr + 1) % 8",
              "name": "rd_ptr"
            }
          ]
        }
      ]
    },
    {
      "id": "BC_FIFO_RESET",
      "obligations": [
        "OBL_FIFO_RESET_001"
      ],
      "reset": "synchronous active-low; count/ptrs clear to 0 on rising clk when rst_n==0",
      "ssot_section": "cycle_model",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "pass_condition": "empty==1 and full==0 after reset",
          "stage": "sim"
        }
      ],
      "transactions": [
        {
          "id": "TR_RESET",
          "outputs": [
            {
              "expr": "0",
              "name": "full"
            },
            {
              "expr": "1",
              "name": "empty"
            }
          ],
          "preconditions": [
            "rst_n == 0"
          ],
          "state_updates": [
            {
              "expr": "0",
              "name": "count"
            },
            {
              "expr": "0",
              "name": "wr_ptr"
            },
            {
              "expr": "0",
              "name": "rd_ptr"
            }
          ]
        }
      ]
    },
    {
      "id": "BC_FIFO_WRITE",
      "latency": {
        "write_update": "1 clock cycle: count and wr_ptr update one rising clk after wr_en sampled"
      },
      "obligations": [
        "OBL_FIFO_WRITE_001"
      ],
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/fifo_sync_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_fifo_sync_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "pass_condition": "count increments on each accepted write",
          "stage": "sim"
        }
      ],
      "transactions": [
        {
          "id": "FM_WRITE",
          "outputs": [
            {
              "expr": "(count + 1) == 8",
              "name": "full"
            },
            {
              "expr": "0",
              "name": "empty"
            }
          ],
          "preconditions": [
            "rst_n == 1",
            "wr_en == 1",
            "full == 0"
          ],
          "state_updates": [
            {
              "expr": "count + 1",
              "name": "count"
            },
            {
              "expr": "(wr_ptr + 1) % 8",
              "name": "wr_ptr"
            }
          ]
        }
      ]
    }
  ],
  "ip": "fifo_sync_cx1",
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
      "contract_ref": "BC_FIFO_FLAGS",
      "evidence_id": "E_FIFO_BC_FLAGS",
      "pass_condition": "full/empty flags match count==8 and count==0 per BC_FIFO_FLAGS",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "BC_FIFO_LINT",
      "evidence_id": "E_FIFO_BC_LINT",
      "pass_condition": "no latch findings per BC_FIFO_LINT",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_FIFO_READ",
      "evidence_id": "E_FIFO_BC_READ",
      "pass_condition": "read behavior matches BC_FIFO_READ",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_FIFO_RESET",
      "evidence_id": "E_FIFO_BC_RESET",
      "pass_condition": "reset behavior matches BC_FIFO_RESET",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_FIFO_WRITE",
      "evidence_id": "E_FIFO_BC_WRITE",
      "pass_condition": "write behavior matches BC_FIFO_WRITE",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_FIFO_FLAGS",
      "evidence_id": "E_FIFO_FLAGS",
      "pass_condition": "full asserts at depth 8; empty asserts at depth 0",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "C_FIFO_LINT",
      "evidence_id": "E_FIFO_LINT",
      "pass_condition": "no latch violations",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_FIFO_READ",
      "evidence_id": "E_FIFO_READ",
      "pass_condition": "rd_data matches written data; count decrements correctly",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_FIFO_RESET",
      "evidence_id": "E_FIFO_RESET",
      "pass_condition": "empty==1 and full==0 after reset",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "rtl/fifo_sync_cx1.sv",
      "contract_ref": "SC_FIFO_PORTS",
      "evidence_id": "E_FIFO_SC_PORTS",
      "pass_condition": "ports clk rst_n wr_en wr_data rd_en rd_data full empty present with correct widths",
      "validator": "check_tb_python_compile.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_FIFO_WRITE",
      "evidence_id": "E_FIFO_WRITE",
      "pass_condition": "count increments correctly on each accepted write",
      "validator": "check_evidence_contract.py"
    }
  ],
  "ip": "fifo_sync_cx1",
  "schema_version": 1,
  "type": "evidence_plan"
}
```

## Source Hashes
- req/behavioral_contracts.json: sha256:c11a7ef2d41c3d83a66a558d992a93c54857648fee56a4b03b10f1122d74d09d
- req/contract_refs.json: sha256:401b41356c152d3d50871ec4f0e62a3eb81832ce0c67271046fe2cfe22704119
- req/evidence_plan.json: sha256:65dbfa1a52d5ab7776a34b7b121627915bcd4b4a91da2676af3070637c91461b
- req/obligations.json: sha256:a2851529571c34ed538c15892bab9ce2a260dcacabd2054a3f04c009e2cf4690
- req/requirements_index.json: sha256:fa90a860f61b26e1119f6bb3a6e167309367b80f8e48970258e88d8e8a102e70
- req/structural_contracts.json: sha256:0f185db807ce0e1ce5d5e8209974a5a5f29d7ce77982668f0b28693dfd9adb41

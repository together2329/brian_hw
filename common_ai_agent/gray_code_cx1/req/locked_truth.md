# Locked Truth - gray_code_cx1

## Approval
- status: requirements_locked
- approved_by: cursor-agent
- approved_at_utc: 2026-06-10T14:36:29Z

## Requirements
```json
{
  "ip": "gray_code_cx1",
  "requirements": [
    {
      "obligation_refs": [
        "OBL_GC_DECODE_001",
        "OBL_GC_ENCODE_001",
        "OBL_GC_LINT_001",
        "OBL_GC_RESET_001"
      ],
      "required": true,
      "requirement_id": "REQ_GC_FUNC_001",
      "statement": "On each rising clock edge when valid is high, gray_out is registered as bin_in XOR (bin_in>>1) and bin_out is registered as the cascaded XOR reduction of gray_in. Both outputs clear to 0 synchronously when rst_n is low.",
      "status": "locked",
      "title": "4-bit binary-to-Gray and Gray-to-binary converter (registered)"
    }
  ],
  "schema_version": 1,
  "type": "requirements_index"
}
```

## Obligations
```json
{
  "ip": "gray_code_cx1",
  "obligations": [
    {
      "behavioral_contract_refs": [
        "BC_GC_DECODE"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_GC_DECODE"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_GC_DECODE_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_GC_FUNC_001"
      ],
      "statement": "bin_out is registered as cascaded XOR reduction of gray_in one cycle after valid is sampled.",
      "structural_contract_refs": [
        "SC_GC_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_GC_ENCODE"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_GC_ENCODE"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_GC_ENCODE_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_GC_FUNC_001"
      ],
      "statement": "gray_out is registered as bin_in XOR (bin_in>>1) one cycle after valid is sampled.",
      "structural_contract_refs": [
        "SC_GC_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_GC_LINT"
      ],
      "closure_stage": "lint",
      "contract_refs": [
        "C_GC_LINT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "structural",
      "obligation_id": "OBL_GC_LINT_001",
      "owned_by_stage": "lint",
      "required_stages": [
        "lint"
      ],
      "requirement_refs": [
        "REQ_GC_FUNC_001"
      ],
      "statement": "No inferred latches; gray_out and bin_out are registered single-driver outputs.",
      "structural_contract_refs": [
        "SC_GC_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_GC_RESET"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_GC_RESET"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_GC_RESET_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_GC_FUNC_001"
      ],
      "statement": "gray_out and bin_out clear to 0 synchronously when rst_n is low.",
      "structural_contract_refs": [
        "SC_GC_PORTS"
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
      "contract_ref_id": "C_GC_DECODE",
      "obligation_refs": [
        "OBL_GC_DECODE_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_PRIMARY",
      "stage_contracts": [
        {
          "artifact": "rtl/gray_code_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_gray_code_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_GC_ENCODE",
      "obligation_refs": [
        "OBL_GC_ENCODE_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_PRIMARY",
      "stage_contracts": [
        {
          "artifact": "rtl/gray_code_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_gray_code_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_GC_LINT",
      "obligation_refs": [
        "OBL_GC_LINT_001"
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
      "contract_ref_id": "C_GC_RESET",
      "obligation_refs": [
        "OBL_GC_RESET_001"
      ],
      "ssot_anchor": "cycle_model",
      "stage_contracts": [
        {
          "artifact": "rtl/gray_code_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_gray_code_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    }
  ],
  "ip": "gray_code_cx1",
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
      "id": "SC_GC_PORTS",
      "interfaces": [
        {
          "clock_domain": "main",
          "id": "converter_io",
          "signals": [
            "bin_in",
            "bin_out",
            "gray_in",
            "gray_out",
            "mode",
            "valid"
          ]
        }
      ],
      "obligations": [
        "OBL_GC_DECODE_001",
        "OBL_GC_ENCODE_001",
        "OBL_GC_LINT_001",
        "OBL_GC_RESET_001"
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
          "name": "valid",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "mode",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "bin_in",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 4
        },
        {
          "dir": "input",
          "name": "gray_in",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 4
        },
        {
          "dir": "output",
          "name": "gray_out",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 4
        },
        {
          "dir": "output",
          "name": "bin_out",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 4
        }
      ]
    }
  ],
  "ip": "gray_code_cx1",
  "schema_version": 1,
  "type": "structural_contracts"
}
```

## Behavioral Contracts
```json
{
  "contracts": [
    {
      "id": "BC_GC_DECODE",
      "latency": {
        "decode_update": "1 clock cycle: bin_out registered one rising clk after valid sampled"
      },
      "obligations": [
        "OBL_GC_DECODE_001"
      ],
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/gray_code_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_gray_code_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "pass_condition": "bin_out matches cascaded XOR of gray_in",
          "stage": "sim"
        }
      ],
      "transactions": [
        {
          "id": "FM_PRIMARY_DECODE",
          "outputs": [
            {
              "expr": "gray_to_bin(gray_in)",
              "name": "bin_out"
            }
          ],
          "preconditions": [
            "rst_n == 1",
            "valid == 1"
          ],
          "state_updates": []
        }
      ]
    },
    {
      "id": "BC_GC_ENCODE",
      "latency": {
        "encode_update": "1 clock cycle: gray_out registered one rising clk after valid sampled"
      },
      "obligations": [
        "OBL_GC_ENCODE_001"
      ],
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/gray_code_cx1.sv",
          "stage": "rtl",
          "timing": "synchronous reset, 1-cycle latency"
        },
        {
          "artifact": "tb/cocotb/test_gray_code_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "pass_condition": "gray_out matches bin_in XOR (bin_in>>1) for all 16 inputs",
          "stage": "sim"
        }
      ],
      "timing": "gray_out registered on rising clk; valid sampled every cycle when rst_n==1",
      "transactions": [
        {
          "id": "FM_PRIMARY_ENCODE",
          "outputs": [
            {
              "expr": "(bin_in ^ (bin_in >> 1)) & 0xF",
              "name": "gray_out"
            }
          ],
          "preconditions": [
            "rst_n == 1",
            "valid == 1"
          ],
          "state_updates": []
        }
      ]
    },
    {
      "cycle_model_waiver": "lint-only obligation; no cycle model required \u2014 latch-free structure is a static synthesis property",
      "id": "BC_GC_LINT",
      "invariants": [
        "No inferred latches in gray_code_cx1 RTL",
        "gray_out and bin_out are registered; single driver each"
      ],
      "obligations": [
        "OBL_GC_LINT_001"
      ],
      "ssot_section": "coding_rules",
      "stage_contracts": [
        {
          "artifact": "rtl/gray_code_cx1.sv",
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
      "id": "BC_GC_RESET",
      "obligations": [
        "OBL_GC_RESET_001"
      ],
      "reset": "synchronous active-low; outputs clear to 0 on rising clk when rst_n==0",
      "ssot_section": "cycle_model",
      "stage_contracts": [
        {
          "artifact": "rtl/gray_code_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_gray_code_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "pass_condition": "gray_out==0 and bin_out==0 during reset",
          "stage": "sim"
        }
      ],
      "transactions": [
        {
          "id": "TR_RESET",
          "outputs": [
            {
              "expr": "0",
              "name": "gray_out"
            },
            {
              "expr": "0",
              "name": "bin_out"
            }
          ],
          "preconditions": [
            "rst_n == 0"
          ],
          "state_updates": []
        }
      ]
    }
  ],
  "ip": "gray_code_cx1",
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
      "contract_ref": "BC_GC_DECODE",
      "evidence_id": "E_GC_BC_DECODE",
      "pass_condition": "decode sequence matches BC_GC_DECODE expected",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_GC_ENCODE",
      "evidence_id": "E_GC_BC_ENCODE",
      "pass_condition": "encode sequence matches BC_GC_ENCODE expected",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "BC_GC_LINT",
      "evidence_id": "E_GC_BC_LINT",
      "pass_condition": "no latch findings per BC_GC_LINT",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_GC_RESET",
      "evidence_id": "E_GC_BC_RESET",
      "pass_condition": "outputs==0 one cycle after rst_n asserts per BC_GC_RESET",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_GC_DECODE",
      "evidence_id": "E_GC_DECODE",
      "pass_condition": "bin_out matches cascaded XOR of gray_in for all 16 values",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_GC_ENCODE",
      "evidence_id": "E_GC_ENCODE",
      "pass_condition": "gray_out matches XOR formula for all 16 bin_in values",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "C_GC_LINT",
      "evidence_id": "E_GC_LINT",
      "pass_condition": "no latch violations",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_GC_RESET",
      "evidence_id": "E_GC_RESET",
      "pass_condition": "outputs==0 during reset",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "rtl/gray_code_cx1.sv",
      "contract_ref": "SC_GC_PORTS",
      "evidence_id": "E_GC_SC_PORTS",
      "pass_condition": "ports clk rst_n valid mode bin_in gray_in gray_out bin_out present with correct widths",
      "validator": "check_tb_python_compile.py"
    }
  ],
  "ip": "gray_code_cx1",
  "schema_version": 1,
  "type": "evidence_plan"
}
```

## Source Hashes
- req/behavioral_contracts.json: sha256:a56690773d80a1763c77689aa511a8f8416386323e9f1e0d66af381c9f27616f
- req/contract_refs.json: sha256:8242b49110ac3e2f385c75b7abe50f2147767e0b1cf99e655d78adc05329cdd9
- req/evidence_plan.json: sha256:cdaa0d6c9f95fdfa54483730bb54019cd79474d48b30deb8fcb278d86cfeb9a8
- req/obligations.json: sha256:d396f2c11359b1fa08b2299a079ab3fd610383a102fa512e1cd033ca096b4dbb
- req/requirements_index.json: sha256:d799b5a2a604af40abeed8148f3a99541ac8d4131f2a3ecee14eb0387a44a9dd
- req/structural_contracts.json: sha256:79cf313ed560f67f7d72a2c8741d37f7adbd0cf63a3a76bae8bad0aa1940aa0d

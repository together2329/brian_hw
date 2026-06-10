# Locked Truth - uart_tx_lite_cx1

## Approval
- status: requirements_locked
- approved_by: cursor-agent
- approved_at_utc: 2026-06-10T14:04:58Z

## Requirements
```json
{
  "ip": "uart_tx_lite_cx1",
  "requirements": [
    {
      "obligation_refs": [
        "OBL_UART_BUSY_001",
        "OBL_UART_DROP_001",
        "OBL_UART_IDLE_001",
        "OBL_UART_LINT_001",
        "OBL_UART_TX_001"
      ],
      "required": true,
      "requirement_id": "REQ_UART_FUNC_001",
      "statement": "Writing a byte to TX_DATA CSR (offset 0) when not busy begins an 8N1 UART frame on tx_out. The frame: start bit (0), 8 data bits LSB-first, stop bit (1), each for BAUD_DIV PCLK cycles. tx_busy=1 during transmission. Writes while tx_busy are silently dropped.",
      "status": "locked",
      "title": "Minimal UART TX 8N1 byte transmit with fixed baud divisor"
    }
  ],
  "schema_version": 1,
  "type": "requirements_index"
}
```

## Obligations
```json
{
  "ip": "uart_tx_lite_cx1",
  "obligations": [
    {
      "behavioral_contract_refs": [
        "BC_UART_BUSY"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_UART_BUSY"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_UART_BUSY_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_UART_FUNC_001"
      ],
      "statement": "tx_busy=1 from TX_DATA write acceptance until the stop bit completes; tx_busy=0 after stop bit.",
      "structural_contract_refs": [
        "SC_UART_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_UART_DROP"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_UART_DROP"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_UART_DROP_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_UART_FUNC_001"
      ],
      "statement": "APB write to TX_DATA while tx_busy=1 is silently ignored; current frame is unaffected.",
      "structural_contract_refs": [
        "SC_UART_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_UART_IDLE"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_UART_IDLE"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_UART_IDLE_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_UART_FUNC_001"
      ],
      "statement": "When tx_busy=0 and no write, tx_out=1 (idle/mark) and tx_busy=0.",
      "structural_contract_refs": [
        "SC_UART_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_UART_LINT"
      ],
      "closure_stage": "lint",
      "contract_refs": [
        "C_UART_LINT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "structural",
      "obligation_id": "OBL_UART_LINT_001",
      "owned_by_stage": "lint",
      "required_stages": [
        "lint"
      ],
      "requirement_refs": [
        "REQ_UART_FUNC_001"
      ],
      "statement": "No inferred latches; all registered signals are single-driver.",
      "structural_contract_refs": [
        "SC_UART_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_UART_TX"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_UART_TX"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_UART_TX_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_UART_FUNC_001"
      ],
      "statement": "After APB write to TX_DATA when idle, tx_out emits start(0), 8 data bits LSB-first, stop(1), each for BAUD_DIV PCLK cycles.",
      "structural_contract_refs": [
        "SC_UART_PORTS"
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
      "contract_ref_id": "C_UART_BUSY",
      "obligation_refs": [
        "OBL_UART_BUSY_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_TX_BYTE",
      "stage_contracts": [
        {
          "artifact": "rtl/uart_tx_lite_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_uart_tx_lite_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_UART_DROP",
      "obligation_refs": [
        "OBL_UART_DROP_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_TX_BYTE",
      "stage_contracts": [
        {
          "artifact": "rtl/uart_tx_lite_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_uart_tx_lite_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_UART_IDLE",
      "obligation_refs": [
        "OBL_UART_IDLE_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_IDLE",
      "stage_contracts": [
        {
          "artifact": "rtl/uart_tx_lite_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_uart_tx_lite_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_UART_LINT",
      "obligation_refs": [
        "OBL_UART_LINT_001"
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
      "contract_ref_id": "C_UART_TX",
      "obligation_refs": [
        "OBL_UART_TX_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_TX_BYTE",
      "stage_contracts": [
        {
          "artifact": "rtl/uart_tx_lite_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_uart_tx_lite_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    }
  ],
  "ip": "uart_tx_lite_cx1",
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
          "clock_signal": "PCLK",
          "id": "main"
        }
      ],
      "id": "SC_UART_PORTS",
      "interfaces": [
        {
          "clock_domain": "main",
          "id": "apb_iface",
          "signals": [
            "PADDR",
            "PENABLE",
            "PRDATA",
            "PREADY",
            "PSEL",
            "PSLVERR",
            "PWDATA",
            "PWRITE"
          ]
        },
        {
          "clock_domain": "main",
          "id": "uart_iface",
          "signals": [
            "tx_busy",
            "tx_out"
          ]
        }
      ],
      "obligations": [
        "OBL_UART_BUSY_001",
        "OBL_UART_DROP_001",
        "OBL_UART_IDLE_001",
        "OBL_UART_LINT_001",
        "OBL_UART_TX_001"
      ],
      "reset_domains": [
        {
          "clock_domain": "main",
          "id": "async_rst",
          "reset_signal": "PRESETn"
        }
      ],
      "signals": [
        {
          "dir": "input",
          "name": "PCLK",
          "timing": {
            "kind": "clock"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "PRESETn",
          "timing": {
            "kind": "reset"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "PADDR",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 4
        },
        {
          "dir": "input",
          "name": "PSEL",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "PENABLE",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "PWRITE",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "input",
          "name": "PWDATA",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 32
        },
        {
          "dir": "output",
          "name": "PRDATA",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 32
        },
        {
          "dir": "output",
          "name": "PREADY",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "output",
          "name": "PSLVERR",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "output",
          "name": "tx_out",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        },
        {
          "dir": "output",
          "name": "tx_busy",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        }
      ]
    }
  ],
  "ip": "uart_tx_lite_cx1",
  "schema_version": 1,
  "type": "structural_contracts"
}
```

## Behavioral Contracts
```json
{
  "contracts": [
    {
      "id": "BC_UART_BUSY",
      "latency": {
        "busy_duration": "10 * BAUD_DIV PCLK cycles from TX_DATA write to tx_busy deassertion"
      },
      "obligations": [
        "OBL_UART_BUSY_001"
      ],
      "ordering": "tx_busy clears on the cycle after the stop bit baud period ends",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/uart_tx_lite_cx1.sv",
          "stage": "rtl",
          "timing": "tx_busy set on TX_DATA write; cleared after stop bit"
        },
        {
          "artifact": "tb/cocotb/test_uart_tx_lite_cx1.py",
          "stage": "tb",
          "timing": "verify tx_busy high through frame, low after stop"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "10*BAUD_DIV cycles",
          "pass_condition": "tx_busy=1 during frame, tx_busy=0 after stop bit",
          "stage": "sim"
        }
      ],
      "timing": "tx_busy registered on rising PCLK; set on TX_DATA write, cleared after stop bit completes",
      "transactions": [
        {
          "id": "TR_BUSY",
          "outputs": [
            {
              "expr": "1",
              "name": "tx_busy"
            }
          ],
          "preconditions": [
            "PRESETn == 1",
            "tx_busy_q == 1"
          ],
          "state_updates": [
            {
              "expr": "1",
              "name": "tx_busy_q"
            }
          ]
        }
      ]
    },
    {
      "id": "BC_UART_DROP",
      "latency": {
        "drop_response": "1 cycle APB PREADY; no frame effect"
      },
      "obligations": [
        "OBL_UART_DROP_001"
      ],
      "ordering": "busy check occurs before loading shift register; write ignored when tx_busy==1",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/uart_tx_lite_cx1.sv",
          "stage": "rtl",
          "timing": "write while busy completes APB but does not reload shift_reg"
        },
        {
          "artifact": "tb/cocotb/test_uart_tx_lite_cx1.py",
          "stage": "tb",
          "timing": "verify second write mid-frame does not corrupt output"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "1 cycle APB handshake only",
          "pass_condition": "write while busy silently ignored; frame unaffected",
          "stage": "sim"
        }
      ],
      "timing": "ignored write completes APB handshake in 1 cycle but does not change shift register or FSM state",
      "transactions": [
        {
          "id": "TR_DROP",
          "outputs": [
            {
              "expr": "1",
              "name": "tx_busy"
            }
          ],
          "preconditions": [
            "PRESETn == 1",
            "PSEL == 1",
            "PENABLE == 1",
            "PWRITE == 1",
            "PADDR == 0",
            "tx_busy_q == 1"
          ],
          "state_updates": [
            {
              "expr": "1",
              "name": "tx_busy_q"
            }
          ]
        }
      ]
    },
    {
      "cycle_model_waiver": "idle is steady-state; cycle semantics covered by BC_UART_TX and BC_UART_BUSY",
      "id": "BC_UART_IDLE",
      "obligations": [
        "OBL_UART_IDLE_001"
      ],
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/uart_tx_lite_cx1.sv",
          "stage": "rtl",
          "timing": "tx_out=1 static when no frame active"
        },
        {
          "artifact": "tb/cocotb/test_uart_tx_lite_cx1.py",
          "stage": "tb",
          "timing": "verify idle state before and after frames"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "0 cycles of change",
          "pass_condition": "tx_out=1 and tx_busy=0 when idle",
          "stage": "sim"
        }
      ],
      "timing": "tx_out holds 1 (mark/idle) and tx_busy holds 0 when no transmission active",
      "transactions": [
        {
          "id": "TR_IDLE",
          "outputs": [
            {
              "expr": "1",
              "name": "tx_out"
            },
            {
              "expr": "0",
              "name": "tx_busy"
            }
          ],
          "preconditions": [
            "PRESETn == 1",
            "tx_busy_q == 0"
          ],
          "state_updates": [
            {
              "expr": "0",
              "name": "tx_busy_q"
            }
          ]
        }
      ]
    },
    {
      "cycle_model_waiver": "lint-only obligation; functional cycle model covered by BC_UART_TX",
      "id": "BC_UART_LINT",
      "invariants": [
        "No inferred latches in uart_tx_lite_cx1 RTL",
        "All registers are single-driver"
      ],
      "obligations": [
        "OBL_UART_LINT_001"
      ],
      "ssot_section": "coding_rules",
      "stage_contracts": [
        {
          "artifact": "lint/dut_lint.json",
          "pass_condition": "no latch findings",
          "stage": "lint",
          "timing": "registered outputs; no async path"
        }
      ],
      "timing": "all signals are registered; no combinational loop or latch inference"
    },
    {
      "id": "BC_UART_TX",
      "latency": {
        "frame_length": "10 * BAUD_DIV PCLK cycles: 1 start + 8 data + 1 stop"
      },
      "obligations": [
        "OBL_UART_TX_001"
      ],
      "ordering": "start bit begins on cycle after TX_DATA APB write accepted",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/uart_tx_lite_cx1.sv",
          "stage": "rtl",
          "timing": "baud counter gates bit transitions; 8N1 frame"
        },
        {
          "artifact": "tb/cocotb/test_uart_tx_lite_cx1.py",
          "stage": "tb",
          "timing": "observe tx_out for full 10*BAUD_DIV cycles"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "10*BAUD_DIV cycles per frame",
          "pass_condition": "8N1 frame shape matches FL expected",
          "stage": "sim"
        }
      ],
      "timing": "tx_out registered on rising PCLK; each bit state held for BAUD_DIV cycles",
      "transactions": [
        {
          "id": "TR_TX_BYTE",
          "outputs": [
            {
              "expr": "1",
              "name": "tx_busy"
            },
            {
              "expr": "1",
              "name": "tx_out"
            }
          ],
          "preconditions": [
            "PRESETn == 1",
            "PSEL == 1",
            "PENABLE == 1",
            "PWRITE == 1",
            "PADDR == 0",
            "tx_busy_q == 0"
          ],
          "state_updates": [
            {
              "expr": "1",
              "name": "tx_busy_q"
            },
            {
              "expr": "PWDATA & 0xFF",
              "name": "shift_reg"
            },
            {
              "expr": "1",
              "name": "tx_state"
            }
          ]
        }
      ]
    }
  ],
  "ip": "uart_tx_lite_cx1",
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
      "contract_ref": "BC_UART_BUSY",
      "evidence_id": "E_UART_BC_BUSY",
      "pass_condition": "tx_busy=1 during frame, tx_busy=0 after stop bit per BC_UART_BUSY",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_UART_DROP",
      "evidence_id": "E_UART_BC_DROP",
      "pass_condition": "write while busy silently ignored per BC_UART_DROP",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_UART_IDLE",
      "evidence_id": "E_UART_BC_IDLE",
      "pass_condition": "tx_out=1 and tx_busy=0 when idle per BC_UART_IDLE",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "BC_UART_LINT",
      "evidence_id": "E_UART_BC_LINT",
      "pass_condition": "no latch findings per BC_UART_LINT",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_UART_TX",
      "evidence_id": "E_UART_BC_TX",
      "pass_condition": "8N1 frame shape matches behavioral contract TR_TX_BYTE expected",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_UART_BUSY",
      "evidence_id": "E_UART_BUSY",
      "pass_condition": "tx_busy=1 during frame, tx_busy=0 after stop bit",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_UART_DROP",
      "evidence_id": "E_UART_DROP",
      "pass_condition": "write while busy silently ignored; frame unaffected",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_UART_IDLE",
      "evidence_id": "E_UART_IDLE",
      "pass_condition": "tx_out=1 and tx_busy=0 when no transmission active",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "C_UART_LINT",
      "evidence_id": "E_UART_LINT",
      "pass_condition": "no latch / no single-driver violations",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "rtl/uart_tx_lite_cx1.sv",
      "contract_ref": "SC_UART_PORTS",
      "evidence_id": "E_UART_SC_PORTS",
      "pass_condition": "top ports PCLK PRESETn PADDR PSEL PENABLE PWRITE PWDATA PRDATA PREADY PSLVERR tx_out tx_busy present with correct widths",
      "validator": "check_tb_python_compile.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_UART_TX",
      "evidence_id": "E_UART_TX",
      "pass_condition": "8N1 frame shape on tx_out matches FL expected",
      "validator": "check_evidence_contract.py"
    }
  ],
  "ip": "uart_tx_lite_cx1",
  "schema_version": 1,
  "type": "evidence_plan"
}
```

## Source Hashes
- req/behavioral_contracts.json: sha256:96c6c3474d6181ac19538e7ce43f2a249ff73db977cc715039477c64e311831e
- req/contract_refs.json: sha256:62e3224cb77687f974b2fc050187c9b39a5d8601747da28cb68ecf675ef5bc8b
- req/evidence_plan.json: sha256:d338310c85229a453753349f9e9f71ffef358a4170a08f70eba12383ed8032be
- req/obligations.json: sha256:de69cc7eeb104fd89317938fd542dedf3befe852154416ae7afc74e220c8761c
- req/requirements_index.json: sha256:045a97fe71d64e867d2fcb675d1eed216cc51115ca41cdc71c119af2fdb9cf20
- req/structural_contracts.json: sha256:bfef854ad369b7b57d56903f1c9321c359522693673bd9fb2a01858e11512f3d

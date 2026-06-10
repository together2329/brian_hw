# Locked Truth - watchdog_cx1

## Approval
- status: requirements_locked
- approved_by: cursor-agent
- approved_at_utc: 2026-06-10T14:04:53Z

## Requirements
```json
{
  "ip": "watchdog_cx1",
  "requirements": [
    {
      "obligation_refs": [
        "OBL_WDT_IDLE_001",
        "OBL_WDT_KICK_001",
        "OBL_WDT_LINT_001",
        "OBL_WDT_TICK_001",
        "OBL_WDT_TIMEOUT_001"
      ],
      "required": true,
      "requirement_id": "REQ_WDT_FUNC_001",
      "statement": "The watchdog counter decrements by 1 on each rising PCLK edge when CTRL.enable==1. When the counter reaches 1 it emits timeout_pulse=1 for exactly one cycle and auto-reloads from PERIOD.period. When CTRL.enable==0 the counter is frozen and timeout_pulse=0. APB write to KICK reloads the counter.",
      "status": "locked",
      "title": "Watchdog counter decrement and timeout pulse"
    }
  ],
  "schema_version": 1,
  "type": "requirements_index"
}
```

## Obligations
```json
{
  "ip": "watchdog_cx1",
  "obligations": [
    {
      "behavioral_contract_refs": [
        "BC_WDT_IDLE"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_WDT_IDLE"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_WDT_IDLE_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_WDT_FUNC_001"
      ],
      "statement": "When CTRL.enable==0, count_q holds its value and timeout_pulse=0.",
      "structural_contract_refs": [
        "SC_WDT_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_WDT_KICK"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_WDT_KICK"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_WDT_KICK_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_WDT_FUNC_001"
      ],
      "statement": "An APB write to KICK (offset 4) reloads count_q from period_q and clears timeout_pulse.",
      "structural_contract_refs": [
        "SC_WDT_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_WDT_LINT"
      ],
      "closure_stage": "lint",
      "contract_refs": [
        "C_WDT_LINT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "structural",
      "obligation_id": "OBL_WDT_LINT_001",
      "owned_by_stage": "lint",
      "required_stages": [
        "lint"
      ],
      "requirement_refs": [
        "REQ_WDT_FUNC_001"
      ],
      "statement": "No inferred latches; all registered signals are single-driver.",
      "structural_contract_refs": [
        "SC_WDT_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_WDT_TICK"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_WDT_TICK"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_WDT_TICK_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_WDT_FUNC_001"
      ],
      "statement": "count_q decrements by 1 each enabled PCLK cycle when no kick occurs.",
      "structural_contract_refs": [
        "SC_WDT_PORTS"
      ]
    },
    {
      "behavioral_contract_refs": [
        "BC_WDT_TIMEOUT"
      ],
      "closure_stage": "sim",
      "contract_refs": [
        "C_WDT_TIMEOUT"
      ],
      "failure_owner": "rtl-gen",
      "granularity": "temporal",
      "obligation_id": "OBL_WDT_TIMEOUT_001",
      "owned_by_stage": "sim",
      "required_stages": [
        "rtl",
        "tb",
        "sim"
      ],
      "requirement_refs": [
        "REQ_WDT_FUNC_001"
      ],
      "statement": "When count_q reaches 1, timeout_pulse=1 for exactly 1 cycle and count_q auto-reloads from period_q.",
      "structural_contract_refs": [
        "SC_WDT_PORTS"
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
      "contract_ref_id": "C_WDT_IDLE",
      "obligation_refs": [
        "OBL_WDT_IDLE_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_IDLE",
      "stage_contracts": [
        {
          "artifact": "rtl/watchdog_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_watchdog_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_WDT_KICK",
      "obligation_refs": [
        "OBL_WDT_KICK_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_KICK",
      "stage_contracts": [
        {
          "artifact": "rtl/watchdog_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_watchdog_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_WDT_LINT",
      "obligation_refs": [
        "OBL_WDT_LINT_001"
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
      "contract_ref_id": "C_WDT_TICK",
      "obligation_refs": [
        "OBL_WDT_TICK_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_TICK",
      "stage_contracts": [
        {
          "artifact": "rtl/watchdog_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_watchdog_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    },
    {
      "contract_ref_id": "C_WDT_TIMEOUT",
      "obligation_refs": [
        "OBL_WDT_TIMEOUT_001"
      ],
      "ssot_anchor": "function_model.transactions.FM_TICK",
      "stage_contracts": [
        {
          "artifact": "rtl/watchdog_cx1.sv",
          "stage": "rtl"
        },
        {
          "artifact": "tb/cocotb/test_watchdog_cx1.py",
          "stage": "tb"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "stage": "sim"
        }
      ]
    }
  ],
  "ip": "watchdog_cx1",
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
      "id": "SC_WDT_PORTS",
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
          "id": "wdt_iface",
          "signals": [
            "timeout_pulse"
          ]
        }
      ],
      "obligations": [
        "OBL_WDT_IDLE_001",
        "OBL_WDT_KICK_001",
        "OBL_WDT_LINT_001",
        "OBL_WDT_TICK_001",
        "OBL_WDT_TIMEOUT_001"
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
          "name": "timeout_pulse",
          "timing": {
            "clock_domain": "main",
            "kind": "sync"
          },
          "width": 1
        }
      ]
    }
  ],
  "ip": "watchdog_cx1",
  "schema_version": 1,
  "type": "structural_contracts"
}
```

## Behavioral Contracts
```json
{
  "contracts": [
    {
      "cycle_model_waiver": "frozen counter: no state change when enable_q==0; cycle semantics covered by BC_WDT_TICK",
      "id": "BC_WDT_IDLE",
      "obligations": [
        "OBL_WDT_IDLE_001"
      ],
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/watchdog_cx1.sv",
          "stage": "rtl",
          "timing": "no state change when enable_q==0"
        },
        {
          "artifact": "tb/cocotb/test_watchdog_cx1.py",
          "stage": "tb",
          "timing": "verify count_q stable across multiple cycles with enable==0"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "0 cycles of change",
          "pass_condition": "count_q unchanged and timeout_pulse==0 when disabled",
          "stage": "sim"
        }
      ],
      "timing": "count_q holds its registered value when enable_q==0; no decrement cycle",
      "transactions": [
        {
          "id": "TR_IDLE",
          "outputs": [
            {
              "expr": "0",
              "name": "timeout_pulse"
            }
          ],
          "preconditions": [
            "PRESETn == 1",
            "enable_q == 0"
          ],
          "state_updates": [
            {
              "expr": "count_q",
              "name": "count_q"
            }
          ]
        }
      ]
    },
    {
      "id": "BC_WDT_KICK",
      "latency": {
        "kick_to_reload": "1 clock cycle after KICK access-phase write"
      },
      "obligations": [
        "OBL_WDT_KICK_001"
      ],
      "ordering": "KICK write takes priority over tick decrement in the same cycle",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/watchdog_cx1.sv",
          "stage": "rtl",
          "timing": "synchronous PCLK, 1-cycle latency"
        },
        {
          "artifact": "tb/cocotb/test_watchdog_cx1.py",
          "stage": "tb",
          "timing": "stimulus applied one cycle before expected result"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "1 clock cycle",
          "pass_condition": "count_q=period_q after KICK write",
          "stage": "sim"
        }
      ],
      "timing": "count_q reloads from period_q 1 cycle after APB KICK access-phase write",
      "transactions": [
        {
          "id": "TR_KICK",
          "outputs": [
            {
              "expr": "0",
              "name": "timeout_pulse"
            }
          ],
          "preconditions": [
            "PRESETn == 1",
            "PSEL == 1",
            "PENABLE == 1",
            "PWRITE == 1",
            "PADDR == 4"
          ],
          "state_updates": [
            {
              "expr": "period_q",
              "name": "count_q"
            }
          ]
        }
      ]
    },
    {
      "cycle_model_waiver": "lint-only obligation; functional cycle model covered by BC_WDT_TICK and BC_WDT_KICK",
      "id": "BC_WDT_LINT",
      "invariants": [
        "No inferred latches in watchdog_cx1 RTL",
        "All registers are single-driver"
      ],
      "obligations": [
        "OBL_WDT_LINT_001"
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
      "timing": "count_q is a clocked register; no combinational loop or latch inference"
    },
    {
      "id": "BC_WDT_TICK",
      "latency": {
        "count_decrement": "1 clock cycle: count_q updates one rising PCLK after enable sampled"
      },
      "obligations": [
        "OBL_WDT_TICK_001"
      ],
      "ordering": "KICK write has priority over tick in the same cycle",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/watchdog_cx1.sv",
          "stage": "rtl",
          "timing": "synchronous PCLK, 1-cycle latency"
        },
        {
          "artifact": "tb/cocotb/test_watchdog_cx1.py",
          "stage": "tb",
          "timing": "stimulus applied one cycle before expected result"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "1 clock cycle per decrement",
          "pass_condition": "count_q decrements match FL expected",
          "stage": "sim"
        }
      ],
      "timing": "count_q registered on rising PCLK; decrements 1 cycle after sampling enable",
      "transactions": [
        {
          "id": "TR_TICK",
          "outputs": [
            {
              "expr": "1 if count_q == 1 else 0",
              "name": "timeout_pulse"
            }
          ],
          "preconditions": [
            "PRESETn == 1",
            "enable_q == 1",
            "not (PSEL==1 and PENABLE==1 and PWRITE==1 and PADDR==4)"
          ],
          "state_updates": [
            {
              "expr": "period_q if count_q == 1 else (count_q - 1) & 0xFF",
              "name": "count_q"
            }
          ]
        }
      ]
    },
    {
      "id": "BC_WDT_TIMEOUT",
      "latency": {
        "timeout_pulse_width": "exactly 1 clock cycle"
      },
      "obligations": [
        "OBL_WDT_TIMEOUT_001"
      ],
      "ordering": "timeout fires when count_q reaches 1 (one tick before zero)",
      "ssot_section": "function_model",
      "stage_contracts": [
        {
          "artifact": "rtl/watchdog_cx1.sv",
          "stage": "rtl",
          "timing": "timeout_pulse is registered output, 1-cycle wide"
        },
        {
          "artifact": "tb/cocotb/test_watchdog_cx1.py",
          "stage": "tb",
          "timing": "verify pulse width=1 cycle and auto-reload"
        },
        {
          "artifact": "sim/scoreboard_events.jsonl",
          "latency": "1 cycle pulse",
          "pass_condition": "timeout_pulse==1 for exactly 1 cycle when count_q==1",
          "stage": "sim"
        }
      ],
      "timing": "timeout_pulse asserted for exactly 1 PCLK cycle when count_q==1; count_q reloads on same cycle",
      "transactions": [
        {
          "id": "TR_TIMEOUT",
          "outputs": [
            {
              "expr": "1",
              "name": "timeout_pulse"
            }
          ],
          "preconditions": [
            "PRESETn == 1",
            "enable_q == 1",
            "count_q == 1"
          ],
          "state_updates": [
            {
              "expr": "period_q",
              "name": "count_q"
            }
          ]
        }
      ]
    }
  ],
  "ip": "watchdog_cx1",
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
      "contract_ref": "BC_WDT_IDLE",
      "evidence_id": "E_WDT_BC_IDLE",
      "pass_condition": "count_q unchanged and timeout_pulse==0 when disabled per BC_WDT_IDLE",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_WDT_KICK",
      "evidence_id": "E_WDT_BC_KICK",
      "pass_condition": "count_q reloaded to period_q per BC_WDT_KICK",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "BC_WDT_LINT",
      "evidence_id": "E_WDT_BC_LINT",
      "pass_condition": "no latch findings per BC_WDT_LINT",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_WDT_TICK",
      "evidence_id": "E_WDT_BC_TICK",
      "pass_condition": "count_q decrement matches BC_WDT_TICK TR_TICK expected",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "BC_WDT_TIMEOUT",
      "evidence_id": "E_WDT_BC_TIMEOUT",
      "pass_condition": "timeout_pulse==1 for exactly 1 cycle per BC_WDT_TIMEOUT",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_WDT_IDLE",
      "evidence_id": "E_WDT_IDLE",
      "pass_condition": "count_q unchanged and timeout_pulse==0 when enable_q==0",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_WDT_KICK",
      "evidence_id": "E_WDT_KICK",
      "pass_condition": "count_q reloaded to period_q after KICK write",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "lint/dut_lint.json",
      "contract_ref": "C_WDT_LINT",
      "evidence_id": "E_WDT_LINT",
      "pass_condition": "no latch / no single-driver violations",
      "validator": "dut_lint_report.py"
    },
    {
      "artifact": "rtl/watchdog_cx1.sv",
      "contract_ref": "SC_WDT_PORTS",
      "evidence_id": "E_WDT_SC_PORTS",
      "pass_condition": "top ports PCLK PRESETn PADDR PSEL PENABLE PWRITE PWDATA PRDATA PREADY PSLVERR timeout_pulse present with correct widths",
      "validator": "check_tb_python_compile.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_WDT_TICK",
      "evidence_id": "E_WDT_TICK",
      "pass_condition": "observed count_q decrement sequence matches FL expected",
      "validator": "check_evidence_contract.py"
    },
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "contract_ref": "C_WDT_TIMEOUT",
      "evidence_id": "E_WDT_TIMEOUT",
      "pass_condition": "timeout_pulse==1 for exactly 1 cycle when count_q reaches 1",
      "validator": "check_evidence_contract.py"
    }
  ],
  "ip": "watchdog_cx1",
  "schema_version": 1,
  "type": "evidence_plan"
}
```

## Source Hashes
- req/behavioral_contracts.json: sha256:02525a9a9a7d689bf0f9b3150c059f395181915e7b47dfb709adaf714334fbf1
- req/contract_refs.json: sha256:5cf9458cc477fccd563f4569a053fd7db9c580a583af6335cdf6d75cec978dde
- req/evidence_plan.json: sha256:15ffd31cc2cd02ed8f9db41d985f8e80d2e314420263adb5c3d64a5289867cf9
- req/obligations.json: sha256:fca3e31962d366df97eba294976e5df9c02c1b0ef05c071b4c817c37b92d6817
- req/requirements_index.json: sha256:837350e5431f9a4079205265d3bf9650e669b73139c12ab86142a7c8dd5dca00
- req/structural_contracts.json: sha256:934ac0f34645cd5e1575789e634467be3a640f1c075a1842a711f8b0919268fe

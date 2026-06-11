# ROCEV IP Example Catalog

Use these as seminar examples or smoke-test targets.

The point is not that every IP is fully closed. The useful lesson is often the
gap: evidence can exist while validation is still partial.

| IP | Good teaching use | Short ROCEV angle |
|---|---|---|
| `pwm_gen_cx1` | Best small slide example | Sim and scoreboard evidence exist; coverage is blocked, so validation is partial. |
| `fifo_sync_cx1` | FIFO ordering | Requirement is familiar; scoreboard/coverage gaps show why "FIFO passed" is too vague. |
| `counter8_cx1` | Counter behavior | Compile/lint/sim/signoff exist, but coverage is missing in the conservative audit. |
| `debounce_cx1` | Glitch filtering | Coverage passes, but scoreboard failed rows keep validation partial. |
| `edge_det_cx1` | Pulse generation | Useful for one-cycle obligation examples and coverage gap discussion. |
| `gray_code_cx1` | Encoding correctness | Simple expected-model contract; scoreboard/coverage gaps are visible. |
| `parity_gen_cx1` | Combinational checker | Easy requirement, but failed scoreboard rows prevent closure. |
| `shift_reg_cx1` | State movement | Sim and signoff evidence exist; coverage is missing. |
| `uart_tx_lite_cx1` | Protocol serialization | Good for waveform/VCD evidence and missing coverage discussion. |
| `watchdog_cx1` | Timeout behavior | Good for temporal obligation wording; coverage is missing. |
| `mctp_assembler_v3` | Larger protocol example | Rich evidence bundle exists; missing `obligations.json` shows older-flow traceability gap. |

## Recommended Seminar Split

Use `pwm_gen_cx1` on the main slides.

Use `mctp_assembler_v3` as the "why obligations matter" example:

```text
Requirement:
  Legal ingress fragments are accepted, malformed byte-lane patterns are not.

Obligations:
  O1: non-contiguous WSTRB must be rejected or marked malformed.
  O2: accepted fragments write only payload bytes to SRAM.
  O3: interleaved contexts do not mix payload or descriptors.

Contract:
  model/checker + scoreboard + coverage + optional formal property.

Evidence:
  results.xml, scoreboard_events.jsonl, coverage.json, VCD, SVA/formal_status.

Validation:
  close only the obligations with matching evidence.
```


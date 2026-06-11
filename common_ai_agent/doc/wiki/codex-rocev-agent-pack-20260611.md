---
title: Codex ROCEV Agent Pack (2026-06-11)
category: tooling
type: implementation-note
tags: [codex, cursor, skills, hooks, agents, rocev, evidence, seminar]
updated: 2026-06-11
related: [cursor-agent-pack, cursor-rocev-workflow-slim-20260611, req-obligation-contract-evidence-validation, evidence-contract-obligation-traceability, formal-verification-evidence, mctp-assembler-contract-breakdown]
---

# Codex ROCEV Agent Pack

This is the Codex-side version of the seminar pack.

The point is modest:

```text
Cursor/Codex can carry a workflow, not just answer prompts.
```

The workflow spine is still:

```text
Requirement -> Obligation -> Contract -> Evidence -> Validation
```

This spine is not a Skill. It is the work standard. Skills are procedures that
follow the standard.

## Surface Map

| Seminar role | Cursor surface | Codex surface | Why |
|---|---|---|---|
| 기준 | `.cursor/rules/*.mdc` | `AGENTS.md` | Codex reads project guidance from AGENTS files. |
| 절차 | `.cursor/skills/*/SKILL.md` | `.agents/skills/*/SKILL.md` | Codex repo skills live under `.agents/skills`. |
| 역할 | `.cursor/agents/*.md` | `.codex_ref/agents/*.toml` | Codex custom agents are TOML config layers. |
| 안전장치 | `.cursor/hooks.json` | `.codex_ref/hooks.json` | Same idea, different hook output contract. |
| 명령 승인정책 | not used in deck | `.codex_ref/rules/*.rules` | Codex "rules" are command approval policy, not thinking rules. |

## Files Added

```text
AGENTS.md
.agents/skills/ip-rocev-mini-run/SKILL.md
.agents/skills/rocev-evidence-review/SKILL.md
.agents/skills/rocev-ip-audit/SKILL.md
.codex_ref/README.md
.codex_ref/agents/*.toml
.codex_ref/hooks.json
.codex_ref/hooks/*.py
.codex_ref/rules/rocev.rules
.codex_ref/scripts/rocev_ip_audit.py
.codex_ref/reports/rocev-ip-audit-20260611.{json,md}
tests/test_agent_pack_rocev.py
```

## Teaching Example 1: MCTP Shows Why Obligations Matter

MCTP is too large to teach as one requirement like "assemble correctly".

Better:

```text
Requirement:
  The assembler accepts legal ingress fragments and rejects malformed byte-lane
  patterns without corrupting payload assembly.

Obligations:
  O1: non-contiguous WSTRB must be rejected or marked malformed.
  O2: accepted fragments must write only payload bytes to SRAM.
  O3: interleaved contexts must not mix payload or descriptors.

Contract:
  FL/model or checker defines legal WSTRB and expected accept/drop.
  Scoreboard compares RTL observed vs expected.
  Coverage includes non-contiguous WSTRB and interleaving cases.
  Optional formal property proves output stability under backpressure.

Evidence:
  mctp_assembler_v3/sim/results.xml
  mctp_assembler_v3/sim/scoreboard_events.jsonl
  mctp_assembler_v3/cov/coverage.json
  mctp_assembler_v3/sim/mctp_assembler_v3.vcd
  mctp_assembler_v3/verify/protocol_assertions.sva
  mctp_assembler_v3/verify/formal_status.json

Validation:
  Close only the obligations whose scoreboard/coverage/formal evidence exists.
```

This follows [[evidence-contract-obligation-traceability]]: a coverage token is
not enough by itself. The useful layer is obligation -> scenario -> observable
-> pass condition -> exact evidence row.

## Teaching Example 2: PWM Shows Evidence Is Not Validation

`pwm_gen_cx1` is easier for an 8-page seminar because the artifact set is small.

```text
Requirement:
  pwm_out is high when counter_q < duty_reg and low otherwise.

Obligation:
  OBL_PWM_OUT_001: every observed cycle must match the expected PWM compare.

Contract:
  FunctionalModel.apply + equivalence goals + scoreboard compare.

Evidence:
  pwm_gen_cx1/rtl/rtl_compile.json       pass
  pwm_gen_cx1/lint/dut_lint.json         pass
  pwm_gen_cx1/sim/results.xml            pass
  pwm_gen_cx1/sim/scoreboard_events.jsonl 18 rows
  pwm_gen_cx1/sim/pwm_gen_cx1.vcd        exists
  pwm_gen_cx1/cov/coverage.json          blocked

Validation:
  partial. Compile/lint/sim/scoreboard evidence exists, but full closure is not
  claimed because coverage is blocked.
```

This is the cleanest slide example:

```text
sim PASS can be real evidence,
but validation can still be open.
```

## 10+ IP Audit Result

Generated with:

```bash
python3 .codex_ref/scripts/rocev_ip_audit.py \
  pwm_gen_cx1 fifo_sync_cx1 counter8_cx1 debounce_cx1 edge_det_cx1 \
  gray_code_cx1 parity_gen_cx1 shift_reg_cx1 uart_tx_lite_cx1 \
  watchdog_cx1 mctp_assembler_v3 \
  --markdown --output .codex_ref/reports/rocev-ip-audit-20260611.md
```

High-level result:

```text
All 11 IPs have some useful evidence.
All 11 are currently partial by the conservative audit.
Common gaps: blocked/missing coverage, scoreboard failed rows, missing
obligations.json for older MCTP-style flow.
```

This is good for the seminar. It avoids saying the pack magically proves
everything; it shows where the workflow points next.

## Seminar Use

Eight-page flow:

1. Cursor as workflow surface, not just chat.
2. Why workflow matters: MCTP edge case can be missed.
3. Four surfaces: Rules/Skills/Agents/Hooks.
4. Rules: completion language.
5. Skills: repeatable procedure.
6. Agents: role split.
7. Hooks: catch shallow PASS claims.
8. Same pattern in Codex: AGENTS, skills, custom agents, hooks, command rules.

Keep the tone practical. Use one small PWM example on slides, and mention MCTP
as the reason we split requirements into obligations.


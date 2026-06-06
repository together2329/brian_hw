---
title: MCTP Assembler Contract Breakdown
type: proposal
tags: [mctp, contract, obligation, evidence, validation, rx-assembly, tx-disassembly, breakdown-matrix, sva, direction]
updated: 2026-06-06
related: [llm-contract-repair-loop, locked-truth-concept, locked-truth-design-spec-workflow, contract-reflection-workflow, evidence-contract-obligation-traceability, formal-verification-evidence, mctp-assembler-scratch-flow-20260531, mctp-assembler-v3-ingress-fidelity-20260603, truth-coverage-gate]
---

# MCTP Assembler Contract Breakdown

This is the central implementation direction for MCTP assembler work, and the
concrete worked instance of [[locked-truth-concept]],
[[contract-reflection-workflow]], and [[llm-contract-repair-loop]].

```text
Do not verify "the MCTP Assembler" as one thing.
Decompose it into closure-sized contracts first.
The FIRST deliverable is the Contract Breakdown Matrix — RTL/SVA/TB come after.
```

`assemble correctly` is too coarse to lock, generate, or close. Each internal
function locks as its own truth and closes as its own contract.

## Fix RX Vs TX First

By DMTF MCTP Base Spec (DSP0236) terms:

```text
message assembly    = RX: receive multiple MCTP packets, reconstruct one message
message disassembly = TX: split one message into a packet sequence to transmit
```

A module named "MCTP Assembler" must be pinned to **one** of these before any
contract is written — the decomposition axis is different for each (see the TX
section at the end). The rest of this page assumes the **RX message assembler**
(packet stream in → message stream out) unless stated otherwise. Mixing RX/TX is
exactly what makes a spec read as "one coarse MCTP block".

Source: DSP0236 defines assembly as connecting two or more packets of the same
message, and disassembly as generating a packet sequence for a message too large
for one packet (DSP0236 §8, message assembly/disassembly).

## The 12 Contract Units (RX)

```text
MCTP Assembler (RX)
  ├─ ASM-GATE     packet acceptance / drop gate
  ├─ ASM-KEY      message terminus / context key tracking
  ├─ ASM-START    start packet (SOM=1,EOM=0) handling
  ├─ ASM-SINGLE   single packet (SOM=1,EOM=1) handling
  ├─ ASM-CONT     continuation packet handling
  ├─ ASM-SEQ      packet sequence checking (mod-4 + OOS drop)
  ├─ ASM-PAYLOAD  payload accumulation / ordering / length accounting
  ├─ ASM-END      EOM commit behavior
  ├─ ASM-DROP     abort / drop / error handling
  ├─ ASM-OUT      output valid-ready / backpressure
  ├─ ASM-RESET    reset / flush behavior
  └─ ASM-STATUS   status / counter behavior
```

Each unit closes its own `req → obligation → contract → evidence → validation`.
`ASM-CONT` is realized jointly by `ASM-SEQ` (sequence) and `ASM-PAYLOAD`
(append); it is named so continuation-specific scenarios stay visible.

## Per-Unit Matching

### 1. ASM-GATE — packet acceptance / drop gate

Role: decide if an incoming packet is an assembly candidate before it touches
state. DSP0236 treats unexpected middle/end packets, bad header version, and
unsupported transmission unit as drop-before-start/terminate conditions.

```text
REQ:  invalid / non-candidate packets must not corrupt assembly state.
OBIL: OBIL-ASM-GATE-001 only an accepted packet may change context state.
      OBIL-ASM-GATE-002 bad header/version packet must not produce output.
      OBIL-ASM-GATE-003 unexpected middle/end with no active context must drop.
CONTRACT: C-ASM-GATE-DROP, C-ASM-GATE-NO-STATE-CHANGE
EVIDENCE: formal — state stable on invalid packet
          sim    — bad hdr version / unsupported TU / unexpected middle directed
```

Most assembler bugs are "a packet that should have been dropped touched the
buffer/FSM" — this unit is the first line of defense.

### 2. ASM-KEY — message terminus / context key

Role: decide which packets belong to the same message. DSP0236 identifies a
message by `Msg Tag`, `TO`, and `Source Endpoint ID`; only one assembly proceeds
per message terminus at a time.

```text
REQ:  do not mix packets from different message termini.
OBIL: OBIL-ASM-KEY-001 context key = {src_eid, to, msg_tag}.
      OBIL-ASM-KEY-002 a different-key packet must not modify the current buffer.
      OBIL-ASM-KEY-003 a new start on the same key aborts/drops the old assembly.
CONTRACT: C-ASM-KEY-ISOLATION, C-ASM-KEY-NEW-START-ABORT
EVIDENCE: formal — no context write on key mismatch
          sim    — interleaved different-tag packets; same-key new-start collision
```

Do not write "MCTP tag handling" as one item — it splits into key build, key
compare, context isolation, and same-key collision.

### 3. ASM-START — start packet handling

Role: SOM=1, EOM=0 begins a multi-packet assembly.

```text
REQ:  a valid start packet creates a new assembly context.
OBIL: OBIL-ASM-START-001 accepting a start sets active context.
      OBIL-ASM-START-002 start key/seq/size baselines are stored.
      OBIL-ASM-START-003 start payload is stored as the first message payload.
      OBIL-ASM-START-004 start alone must not emit a complete message.
CONTRACT: C-ASM-START-CONTEXT-ALLOC, C-ASM-START-NO-EARLY-COMMIT
EVIDENCE: SVA — context_active the cycle after start accept
          SVA — start-without-EOM must not assert msg_out_valid
          sim — normal multi-packet start
```

### 4. ASM-SINGLE — single packet message

Role: SOM=1, EOM=1 is a complete message with no lingering context.

```text
REQ:  single-packet message commits directly, no long context occupancy.
OBIL: OBIL-ASM-SINGLE-001 SOM&EOM packet is emitted as a complete message.
      OBIL-ASM-SINGLE-002 no partial context remains after single-packet.
      OBIL-ASM-SINGLE-003 single payload length equals output message length.
CONTRACT: C-ASM-SINGLE-COMMIT, C-ASM-SINGLE-NO-STALE-CONTEXT
EVIDENCE: sim — one-packet control message
          formal — context_active == 0 after single accept
```

Keep separate from ASM-START: both have SOM=1 but different state effects.

### 5–6. ASM-CONT / ASM-SEQ — continuation + sequence

Role: continuation packet sequence must follow `Pkt Seq #` modulo 4; `TO` and
`Msg Tag` stay constant from SOM to EOM (DSP0236 transport header).

```text
REQ:  continuation packets follow the expected sequence number.
OBIL: OBIL-ASM-SEQ-001 start accept stores next expected_seq.
      OBIL-ASM-SEQ-002 middle/end seq must equal expected_seq.
      OBIL-ASM-SEQ-003 valid continuation increments expected_seq modulo 4.
      OBIL-ASM-SEQ-004 out-of-sequence packet drops/terminates the assembly.
      OBIL-ASM-SEQ-005 OOS packet must not produce a complete output.
CONTRACT: C-ASM-SEQ-MOD4, C-ASM-SEQ-OOS-DROP
EVIDENCE: formal — accepted continuation implies seq == expected_seq
          formal — accepted continuation implies expected_seq' == (seq+1) mod 4
          sim    — 0→1→2→3 normal; 0→2 out-of-sequence drop
```

```systemverilog
property p_continuation_seq_must_match;
  @(posedge clk) disable iff (!rst_n)
    pkt_accept && context_active && !pkt_som
    |-> (pkt_seq == expected_seq);
endproperty
assert property (p_continuation_seq_must_match);
```

Out-of-sequence is a *separate* contract (error/drop family, not protocol-match):

```systemverilog
property p_oos_drops_current_assembly;
  @(posedge clk) disable iff (!rst_n)
    pkt_accept && context_active && !pkt_som && (pkt_seq != expected_seq)
    |=> !context_active && drop_pulse;
endproperty
assert property (p_oos_drops_current_assembly);
```

### 7. ASM-PAYLOAD — accumulation / ordering / length

Role: append packet payloads into the message body in order. A message body
spans packets; each packet payload is the body slice it carries.

```text
REQ:  accepted payload is order-preserved in the output message.
OBIL: OBIL-ASM-PAYLOAD-001 start payload stored from buffer offset 0.
      OBIL-ASM-PAYLOAD-002 continuation payload appended at current length offset.
      OBIL-ASM-PAYLOAD-003 no duplicate payload bytes.
      OBIL-ASM-PAYLOAD-004 no lost payload bytes absent error/drop.
      OBIL-ASM-PAYLOAD-005 accumulated length == sum of accepted payload lengths.
      OBIL-ASM-PAYLOAD-006 exceeding max body buffer → defined overflow behavior.
CONTRACT: C-ASM-PAYLOAD-LEN, C-ASM-PAYLOAD-WRITE-OFFSET,
          C-ASM-PAYLOAD-SYMBOLIC-BYTE, C-ASM-PAYLOAD-SCOREBOARD
EVIDENCE: formal — length accounting + pointer + no-write-when-drop + symbolic byte
          sim    — full payload ordering, random length, scoreboard compare, overflow
```

Split formal vs sim deliberately: formal owns length/pointer/symbolic-byte; sim
owns full ordering + random length + scoreboard. Do not put whole-payload
ordering into one giant formal property.

### 8. ASM-END — EOM / commit

Role: a valid EOM completes the assembly exactly once. DSP0236: receiving EOM
completes the in-progress assembly into an accepted message, provided no
drop/termination condition fired first.

```text
REQ:  a valid EOM commits exactly one complete message.
OBIL: OBIL-ASM-END-001 valid EOM appends payload then commits.
      OBIL-ASM-END-002 commit length == accumulated length.
      OBIL-ASM-END-003 one completed assembly emits output exactly once.
      OBIL-ASM-END-004 context_active clears after commit.
      OBIL-ASM-END-005 no complete output without EOM.
CONTRACT: C-ASM-END-COMMIT-ONCE, C-ASM-END-CLEAR-CONTEXT, C-ASM-END-NO-PREMATURE-OUTPUT
EVIDENCE: formal — EOM accept implies commit (per design latency); no double commit
          sim    — start-middle-end normal path
```

Keep separate from ASM-PAYLOAD: payload can accumulate correctly while commit
timing is wrong.

### 9. ASM-DROP — abort / drop / error

Role: discard the partial message on any termination condition. DSP0236 lists
same-terminus new start, timeout, out-of-sequence, incorrect transmission unit,
and integrity-check mismatch as assembly-terminating conditions.

```text
REQ:  on an error condition, a partial message must never commit to output.
OBIL: OBIL-ASM-DROP-001 same-key new start drops old partial and starts new.
      OBIL-ASM-DROP-002 timeout drops the partial assembly.
      OBIL-ASM-DROP-003 out-of-sequence drops the partial assembly.
      OBIL-ASM-DROP-004 incorrect transmission unit drops/terminates per policy.
      OBIL-ASM-DROP-005 dropped payload must not bleed into later output.
      OBIL-ASM-DROP-006 a drop event is reflected exactly once in status/counters.
CONTRACT: C-ASM-DROP-NEW-START, C-ASM-DROP-TIMEOUT, C-ASM-DROP-OOS, C-ASM-DROP-NO-STALE-DATA
EVIDENCE: formal — no stale commit after drop
          sim    — timeout; same-key new start; out-of-sequence
```

`C-ASM-DROP-NO-STALE-DATA` is the high-value one: the classic bug is a drop that
fails to clear the buffer, so the previous payload trails the next valid output.

### 10. ASM-OUT — output interface / backpressure

Role: hand the assembled message downstream. This is an RTL interface contract
more than a DSP0236 rule.

```text
REQ:  the output valid-ready interface is stable under backpressure.
OBIL: OBIL-ASM-OUT-001 while msg_out_valid && !msg_out_ready, output fields stable.
      OBIL-ASM-OUT-002 a completed message is not overwritten before handshake.
      OBIL-ASM-OUT-003 the output slot releases only after handshake.
      OBIL-ASM-OUT-004 on output-full, input ready deasserts or buffers per policy.
CONTRACT: C-ASM-OUT-STABLE-WHEN-BACKPRESSURED, C-ASM-OUT-NO-OVERWRITE, C-ASM-OUT-HANDSHAKE-RELEASE
EVIDENCE: formal — output stable; no overwrite under backpressure
          sim    — random ready stall
```

```systemverilog
property p_msg_out_stable_when_backpressured;
  @(posedge clk) disable iff (!rst_n)
    msg_out_valid && !msg_out_ready
    |=> msg_out_valid &&
        $stable({msg_out_src_eid, msg_out_to, msg_out_tag,
                 msg_out_type, msg_out_len, msg_out_data});
endproperty
assert property (p_msg_out_stable_when_backpressured);
```

### 11. ASM-RESET — reset / flush

Role: no partial state survives reset/flush.

```text
REQ:  after reset/flush the assembler is idle and emits no stale message.
OBIL: OBIL-ASM-RESET-001 context_active == 0 while reset asserted.
      OBIL-ASM-RESET-002 no pending output after reset release.
      OBIL-ASM-RESET-003 pre-reset partial payload never outputs after reset.
      OBIL-ASM-FLUSH-001 flush drops the current assembly.
      OBIL-ASM-FLUSH-002 after flush only a new start may begin an assembly.
CONTRACT: C-ASM-RESET-IDLE, C-ASM-RESET-NO-STALE-OUTPUT, C-ASM-FLUSH-DROP-CURRENT
EVIDENCE: formal — reset implies idle; no stale commit after reset
          sim    — reset mid-message; flush mid-message
```

### 12. ASM-STATUS — status / counter

Role: status bits and counters reflect accepted/dropped/committed events
accurately (each event counted exactly once). Pairs with ASM-DROP-006 and
ASM-END-003 so closure/drop events are observable for the repair loop.

## The Trace Matrix Shape

One requirement fans out to several obligations; obligations group into contracts;
each contract is closed by named evidence; validation is the closure of those:

```text
REQ-MCTP-ASM-SEQ-001
  ↓
OBIL-ASM-SEQ-001  start accept stores expected_seq
OBIL-ASM-SEQ-002  continuation seq == expected_seq
OBIL-ASM-SEQ-003  valid continuation → expected_seq mod-4 increment
OBIL-ASM-SEQ-004  out-of-sequence → drop current assembly
  ↓
C-ASM-SEQ-MOD4
C-ASM-SEQ-OOS-DROP
  ↓
E-FORMAL-ASM-SEQ-MATCH
E-FORMAL-ASM-SEQ-UPDATE
E-SIM-ASM-SEQ-NORMAL-0123
E-SIM-ASM-SEQ-OOS-02
  ↓
V-ASM-SEQ-CLOSED
```

## SSOT YAML Shape (sequence unit)

```yaml
requirements:
  - id: REQ-MCTP-ASM-SEQ-001
    block: mctp_rx_assembler
    statement: >
      For a multi-packet message, continuation packets shall follow the expected
      packet sequence number modulo 4.
    source: DSP0236_1.3.3.section_8
obligations:
  - id: OBIL-ASM-SEQ-001
    requirement: REQ-MCTP-ASM-SEQ-001
    statement: "On accepting a start packet, the assembler shall initialize expected_seq."
    condition: "pkt_accept && pkt_som && !pkt_eom"
    observable: [expected_seq, context_active]
  - id: OBIL-ASM-SEQ-002
    requirement: REQ-MCTP-ASM-SEQ-001
    statement: "A continuation packet shall match expected_seq."
    condition: "pkt_accept && context_active && !pkt_som"
    observable: [pkt_seq, expected_seq]
  - id: OBIL-ASM-SEQ-003
    requirement: REQ-MCTP-ASM-SEQ-001
    statement: "After a valid continuation packet, expected_seq shall increment modulo 4."
    condition: "pkt_accept && context_active && !pkt_som && pkt_seq == expected_seq"
    observable: [expected_seq]
  - id: OBIL-ASM-SEQ-004
    requirement: REQ-MCTP-ASM-SEQ-001
    statement: "An out-of-sequence continuation packet shall drop the current assembly."
    condition: "pkt_accept && context_active && !pkt_som && pkt_seq != expected_seq"
    observable: [context_active, drop_pulse, msg_out_valid]
contracts:
  - id: C-ASM-SEQ-MOD4
    obligations: [OBIL-ASM-SEQ-001, OBIL-ASM-SEQ-002, OBIL-ASM-SEQ-003]
    type: protocol_sequence_contract
    proof_targets: [p_continuation_seq_must_match, p_expected_seq_increments_mod4]
  - id: C-ASM-SEQ-OOS-DROP
    obligations: [OBIL-ASM-SEQ-004]
    type: error_drop_contract
    proof_targets: [p_oos_drops_current_assembly, p_oos_never_commits_message]
evidence:
  - id: E-FORMAL-ASM-SEQ-001
    contract: C-ASM-SEQ-MOD4
    type: formal
    properties: [p_continuation_seq_must_match, p_expected_seq_increments_mod4]
    result: proven
  - id: E-SIM-ASM-SEQ-002
    contract: C-ASM-SEQ-OOS-DROP
    type: simulation
    test: [tc_start_seq0_then_seq2_drop]
    result: pass
validation:
  - id: V-ASM-SEQ-001
    requirement: REQ-MCTP-ASM-SEQ-001
    status: closed
    closed_by: [E-FORMAL-ASM-SEQ-001, E-SIM-ASM-SEQ-002]
```

## TX Packet Assembler — Different Axis

If the module is actually a TX packet assembler (message in → MCTP packets out),
the decomposition axis changes to packetization, not reassembly:

```text
TX-MSG-IN    accept input message: length, type, tag, dst/src EID
TX-PKT-SIZE  payload slicing, MTU / baseline transmission-unit handling
TX-HDR       transport header gen: hdr_version, dst_eid, src_eid, SOM, EOM, pkt_seq, TO, msg_tag
TX-SOM-EOM   first packet SOM=1, last EOM=1, middle SOM=0/EOM=0
TX-SEQ       packet sequence number modulo 4
TX-TAG       TO/msg_tag stable across all packets of one split message
TX-PAYLOAD   payload order, no duplicate, no drop, correct offset slicing
TX-OUT       valid-ready stability / backpressure
TX-ERR       illegal length, unsupported MTU, abort/flush
```

```text
REQ-TX-SOM-EOM
  → OBIL-TX-SOM-001 first emitted packet has SOM=1
  → OBIL-TX-EOM-001 last emitted packet has EOM=1
  → OBIL-TX-MID-001 middle packets have SOM=0 / EOM=0
  → C-TX-SOM-EOM-FLAGS
  → E-FORMAL-TX-SOM-EOM + E-SIM-TX-MULTIPACKET
  → V-TX-SOM-EOM-CLOSED

REQ-TX-PAYLOAD-SLICE
  → OBIL-TX-PAYLOAD-001 packet0 carries bytes [0 : mtu-1]
  → OBIL-TX-PAYLOAD-002 packet1 carries bytes [mtu : 2*mtu-1]
  → OBIL-TX-PAYLOAD-003 last packet length equals remaining bytes
  → C-TX-PAYLOAD-SLICING
  → E-SIM-TX-SCOREBOARD + E-FORMAL-TX-LEN-ACCOUNTING
  → V-TX-PAYLOAD-CLOSED
```

For TX the core contracts are packetization / header construction / payload
slicing, not "assembly".

## SSOT Spine Rollup

The 12 units roll up into one per-IP SSOT structure — requirements down to a
closure matrix:

```yaml
mctp_assembler_ssot:
  requirements: [packet construction, header generation, payload segmentation,
                 sequence/tag handling, flow control, error handling]
  obligations:
    - every accepted payload byte is accounted for
    - packet boundary is generated correctly
    - header fields stay stable while valid && !ready
    - no packet is emitted before its required fields are known
    - flush/reset leaves no stale partial packet
  contracts: [input stream contract, output packet contract, MCTP header contract,
              payload ordering contract, backpressure contract, error/drop contract]
  evidence:  [RTL, assertions, testbench, scoreboard, simulation/formal results]
  validation: closure matrix
```

This is the same spine as the 12-unit table, viewed as one rollup. The unit table
closes work item-by-item; this rollup shows the whole IP at once.

RX/TX drift to watch: this rollup (packet construction / header generation /
payload **segmentation**) is **TX/packetization-leaning**, while the 12 units
above describe **RX reassembly**. Same reason as `## Fix RX Vs TX First` — pin the
direction before writing contracts. If the real RTL is the TX packetizer, drive
from the `## TX Packet Assembler` axis; if RX, from the 12 units. Do not carry
both in one contract set.

## Obligation Taxonomy → Unit Map

Every MCTP assembler obligation falls into one of these, each owned by a unit. If
an obligation maps to no unit, the breakdown is incomplete — add a unit rather
than stretching an existing one.

```text
header field correctness        -> ASM-START baseline (RX) / TX-HDR (TX)
SOM / EOM correctness           -> ASM-START / ASM-SINGLE / ASM-END (RX) / TX-SOM-EOM (TX)
packet sequence correctness     -> ASM-SEQ / TX-SEQ
payload ordering                -> ASM-PAYLOAD / TX-PAYLOAD
payload length accounting       -> ASM-PAYLOAD (C-ASM-PAYLOAD-LEN) / TX-PAYLOAD
MTU / max payload boundary      -> ASM-PAYLOAD overflow / TX-PKT-SIZE
valid-ready handshake stability -> ASM-OUT / TX-OUT
backpressure behavior           -> ASM-OUT / TX-OUT
reset / flush behavior          -> ASM-RESET
malformed input handling        -> ASM-GATE
drop / error reporting          -> ASM-DROP + ASM-STATUS / TX-ERR
traceability (spec -> RTL/SVA/test) -> the trace matrix itself
```

## Assume-Guarantee Contract Shape

A contract may be written in assume-guarantee form, which maps directly onto
formal `assume`/`assert` ([[formal-verification-evidence]]). Worked example for
the `ASM-PAYLOAD` ordering concern (alternate representation of `C-ASM-PAYLOAD-*`):

```text
REQ-MCTP-ASM-001: the assembler preserves input payload byte order in output.
  OBIL-...-A: accepted input byte order is preserved at output.
  OBIL-...-B: no accepted byte is lost or duplicated before the packet boundary closes.
  OBIL-...-C: payload over max size triggers a defined split/drop/error.
```

```yaml
contract:
  id: C-MCTP-ASM-PAYLOAD-ORDER          # assume-guarantee view of C-ASM-PAYLOAD-*
  type: data_ordering_contract
  assumptions:                          # -> formal `assume` (MUST be discharged on the driver)
    - "input byte accepted only when in_valid && in_ready"
    - "output byte accepted only when out_valid && out_ready"
  guarantees:                           # -> formal `assert`
    - "accepted input payload bytes appear in the same order at output"
    - "no accepted byte is duplicated"
    - "no accepted byte is dropped unless an explicit error/drop contract fires"
  evidence:
    - SVA-MCTP-ASM-PAYLOAD-ORDER
    - TB-MCTP-ASM-DIRECTED-SINGLE-PACKET
    - TB-MCTP-ASM-MAX-PAYLOAD
    - TB-MCTP-ASM-BACKPRESSURE
    - TB-MCTP-ASM-ERROR-DROP
    - scoreboard pass log
    - coverage report
```

The `assumptions` are real obligations on the *upstream* block — per
[[formal-verification-evidence]] they must be discharged, not merely stated, or
the guarantee is "proven" about an environment that cannot occur.

## Granularity Rules

```text
One OBLIGATION must be pass/fail in a single sentence.
One CONTRACT must be directly expressible as SVA / formal / testbench.
One EVIDENCE must clearly name which contract it closes.
VALIDATION is the sum of small contract closures, not "the assembler works".
```

## Build Order (direction)

This is the order all future MCTP assembler work should follow, tying the
direction pages together:

```text
1. Fix RX vs TX.
2. Produce the Contract Breakdown Matrix (this page) as the FIRST deliverable.
3. Lock each row's truth — [[locked-truth-concept]] + [[locked-truth-design-spec-workflow]].
4. Generate contracts → SVA/TB/RTL per locked truth — [[contract-reflection-workflow]].
5. Close each contract one at a time via the repair loop — [[llm-contract-repair-loop]].
```

## Worked Example (examples/mctp_contract_slice/)

A runnable proof that this breakdown closes end-to-end across three lanes
(iverilog compile + verilator `--assert` random sim + sby/z3 formal), with a
planted bug per contract (mutation kill → non-vacuous):

- `rtl/mctp_rx_assembler.sv` — the 12-contract single-context skeleton. Correct
  PASS on all lanes; all 11 mutants killed (`signoff/validation_closure_12.json`).
- `rtl/mctp_rx_mc.sv` — the multi-context + 3-field key + interleaving deep-dive
  (reflects v3 §9.1/§9.2/§9.3). Cross-context isolation, allocation, duplicate-SOM
  abort, and per-context sequence all closed; a formal `cover` proves two contexts
  are live with different keys at once (`signoff/validation_closure_mc.json`).

Toolchain and the bring-up gotchas it documents are in
[[formal-verification-evidence]] `## Demonstrated With sby + z3`.

## Reflecting The Real v3 Requirements

The example is a teaching skeleton. The production spec is
`mctp_assembler_v3/req/mctp_assembler_v3_requirements.md` (AXI4 256-bit PCIe VDM
assembler). Map of each toy contract to the real spec, and what is not yet
reflected:

| toy contract | real v3 requirement (section) | status |
|---|---|---|
| KEY (tag only) | 3-field key `{source_eid, tag_owner, message_tag}` + dest-EID filter + multi-context isolation (§9.1/§9.3) | done in `mctp_rx_mc` |
| START/SINGLE | `CONTEXT_COUNT` contexts; duplicate-SOM = assembly drop (§9.2) | done in `mctp_rx_mc` |
| SEQ | per-context mod-4 sequence; OOS = assembly drop (§9.2/§10.2 AD_SEQUENCE_MISMATCH) | done |
| PAYLOAD (byte count) | SRAM byte-exact packing + strobes + fragment-no-gap + per-context partial word (§9.4) | done in `mctp_rx_payload` (symbolic-byte) |
| END | descriptor publish (no descriptor before EOM) + first/last TLP header snapshot queue (§9.3/§9.5) | not yet |
| DROP (flat) | packet-drop vs assembly-drop split + 14-step drop priority + reason codes (§10.1/§10.2/§10.3) | done in `mctp_drop_classifier` |
| STATUS | packet/assembly_drop_count + last_drop_class + reason; counter registers (§10/§11.4) | partial |
| *(none)* | header snapshot queue, descriptor queue, timeout/aging, registers (control/status/irq/counter) | not yet |

Caveat found while harvesting v3: its evidence is 102/106 obligations =
`LEGACY_SCOREBOARD_GOAL_CLOSURE` (count-semantic), only 4 truly content-semantic —
so reflect the *requirements* (§7–§14), not v3's thin obligation set. The §14
"Formal Verification Candidates" list maps directly onto this formal approach.
Done so far: KEY/START/SEQ (`mctp_rx_mc`), SRAM byte-exact payload
(`mctp_rx_payload`, symbolic-byte), drop priority + packet/assembly class
(`mctp_drop_classifier`). Remaining deep-dives: descriptor publish +
first/last TLP header-snapshot queue, timeout/aging, and the register file.

The drop-classifier closure also re-confirmed a lane lesson: the `ANY` mutant
(ignoring the timeout reason) only fires when exactly the timeout bit is set
alone — random sim missed it, formal caught it. Run multiple lanes.

한 줄 요약: MCTP Assembler를 하나로 검증하지 말고 gate·key·start·single·cont·
seq·payload·end·drop·out·reset·status로 쪼개, 각 조각마다 req→obil→contract→
evidence→validation을 따로 닫는다. 첫 산출물은 RTL이 아니라 Contract Breakdown
Matrix다.

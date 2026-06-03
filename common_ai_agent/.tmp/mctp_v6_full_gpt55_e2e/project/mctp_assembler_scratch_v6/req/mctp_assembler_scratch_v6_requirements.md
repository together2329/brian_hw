# mctp_assembler_scratch_v6 Requirements

## Scope and Requirement Source

This locked starter requirement defines `mctp_assembler_scratch_v6` as a synthesizable MCTP packet assembler hardware IP. The IP accepts an input byte stream carrying message payload bytes and descriptor sideband information, builds MCTP packet headers, segments long messages into packet-sized fragments, and emits a byte-wide packet stream with ready/valid flow control. The implementation target is a single synthesizable SystemVerilog top at `rtl/mctp_assembler_scratch_v6.sv`.

The design is classified as mixed packet formatter, ready/valid streaming datapath, simple local CSR control/status block, and interrupt source. It is not specified as APB, AXI4-Lite, AXI4-Stream, DMA, or a physical implementation target. A local valid/ready CSR interface is used to avoid inventing an external bus protocol that is not required.

## Functional Requirements

1. The IP shall use `clk` as the rising-edge clock and `rst_n` as an active-low synchronous reset.
2. Reset shall clear the transmit FSM, payload buffering state, output valid state, sticky status, error status, interrupt output, and all control registers to documented reset values.
3. The input payload interface shall be byte-wide with `in_valid`, `in_ready`, `in_data`, `in_sop`, `in_eop`, `in_len`, `in_dst_eid`, `in_src_eid`, `in_msg_tag`, and `in_tag_owner`.
4. An input byte and associated sideband shall be accepted only when `in_valid && in_ready` is true on a rising clock edge.
5. The source shall hold input data and sideband stable while `in_valid && !in_ready`; the RTL and checkers shall preserve this ready/valid contract.
6. The output packet interface shall be byte-wide with `out_valid`, `out_ready`, `out_data`, `out_sop`, `out_eop`, and `out_pkt_seq`.
7. Output bytes shall advance only when `out_valid && out_ready`; all output signals shall remain stable while stalled by `out_valid && !out_ready`.
8. For each accepted message, the assembler shall emit one or more packets containing a four-byte MCTP transport header, a one-byte message type field, and payload bytes in their original order.
9. Header byte 0 shall encode MCTP header version 1 as `8'h10` under the project packet-field assumption.
10. Header byte 1 shall carry the effective destination endpoint ID.
11. Header byte 2 shall carry the effective source endpoint ID.
12. Header byte 3 shall carry start-of-message, end-of-message, two-bit packet sequence, tag-owner, and three-bit message-tag fields.
13. Header byte 4 shall carry the configured message type.
14. Messages longer than the configured packet payload limit shall be segmented. The first segment shall assert SOM, the last segment shall assert EOM, and intermediate segments shall assert neither EOM nor a new SOM.
15. Packet sequence shall start at zero for each message and increment modulo four for each emitted packet segment.
16. Payload ordering shall be lossless and deterministic under arbitrary legal input and output backpressure.
17. The maximum packet payload size shall default to 64 bytes and shall never exceed the `MAX_PAYLOAD_BYTES` parameter.
18. The ingress buffer shall apply backpressure before overflow. If a protocol violation forces an overflow condition, sticky error status shall record it.
19. A simple valid/ready CSR port shall provide control, status, field override, message type, error, and interrupt enable registers.
20. CSR writes shall commit in the accepted request cycle. CSR reads shall return `csr_rvalid` and `csr_rdata` one cycle after an accepted read.
21. The control register shall provide enable, override-fields, and soft-abort controls.
22. When override-fields is clear, EID and tag fields shall be sampled from accepted input SOP sideband. When override-fields is set, CSR-programmed EID and tag fields shall be used.
23. The status register shall expose done, busy, error, and FIFO occupancy indications.
24. Error status shall include FIFO overflow, length mismatch, unexpected SOP, unexpected EOP, disabled start, and unsupported CSR address indications.
25. Done and error indications shall be sticky until cleared by documented write-one-to-clear behavior or reset.
26. `irq` shall be a level-sensitive interrupt that asserts when an enabled sticky done or error source is set and deasserts after all enabled sources are cleared.
27. Soft abort shall terminate the current message, flush pending message state, return the FSM to idle after recovery, and leave appropriate status for software visibility.

## Verification Requirements

The verification environment shall include a reference packet scoreboard, CSR model, ready/valid stability assertions, interrupt checker, reset checker, and error recovery checker. Directed tests shall cover reset defaults, a single-packet message, segmented messages with output stalls, CSR override behavior, interrupt set and clear behavior, and all listed error sources. Functional coverage shall include boundary message lengths of 1, 2, the maximum per-packet payload length, and lengths requiring multiple packet segments. Coverage shall also sample all packet sequence values, stalls on header beats, stalls on payload beats, CSR reads, CSR writes, interrupt assertion, interrupt clearing, and recovery from each error source.

## Quality Requirements

The SSOT shall be schema-repaired and validated in engineering mode. Downstream RTL shall compile without syntax or elaboration errors, avoid inferred latches, drive all outputs, implement reset deterministically, and satisfy ready/valid stability checks. Simulation shall pass all scoreboard and checker requirements before contract-check signoff. Physical implementation stages are outside this run and are not required for completion.

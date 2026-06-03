# AXI4 256-bit PCIe VDM MCTP Assembler Scratch Requirements

## 1. Source Baseline

This requirement is derived from the official DMTF published specifications below.

- DMTF DSP0236, Management Component Transport Protocol (MCTP) Base Specification, version 1.3.3, published 2024-03-25.
- DMTF DSP0238, Management Component Transport Protocol (MCTP) PCIe VDM Transport Binding Specification, version 1.4.0, published 2026-02-28.

Local fetched PDFs:

- `artifacts/local/standards/DSP0236_1.3.3.pdf`
- `artifacts/local/standards/DSP0238_1.4.0.pdf`

The IP implements a bounded hardware receiver/assembler. It is not a full PCIe endpoint, PCIe root complex, MCTP bridge, or DMTF conformance test suite.

## 2. IP Purpose

`mctp_assembler_scratch_v5` receives raw PCIe VDM TLP bytes from an upstream PCIe block through an AXI4 write-slave ingress. One AXI4 write transaction carries exactly one PCIe VDM TLP. The IP validates the TLP as an MCTP-over-PCIe-VDM packet, extracts the MCTP transport header and packet payload, assembles fragmented MCTP messages across multiple interleaved TLP streams, writes only completed MCTP message payload bytes to a 256-bit SRAM write interface, stores first/last TLP header snapshots per assembly queue entry, publishes a completed-message descriptor, records drops/errors, and raises an interrupt.

The functional contract is:

```text
AXI4 write transaction
  -> raw PCIe VDM TLP bytes
  -> MCTP-over-PCIe-VDM packet validation
  -> MCTP transport header decode
  -> packet payload assembly by message key with interleaving
  -> first/last TLP header snapshot stored in the context/descriptor queue
  -> MCTP payload-only 256-bit SRAM writes + descriptor/status
```

## 3. Locked User Assumptions

These assumptions are fixed for the first concrete implementation target.

- Input bus is AXI4 write-side ingress, not AXI-Stream.
- `WDATA` width is 256 bits.
- `WSTRB` width is 32 bits.
- One PCIe VDM TLP maps to one AXI4 write transaction.
- The AXI4 write transaction may contain multiple 256-bit W beats.
- `WLAST` terminates the TLP because one transaction equals one TLP.
- Byte lane 0 of the first accepted `WDATA` beat is TLP byte 0.
- Byte lane N of a beat maps to `WDATA[8*N +: 8]`.
- Multi-byte fields inside the decoded PCIe/MCTP packet follow the DMTF big-endian field ordering unless the PCIe field definition says otherwise.
- The IP has an internal queue/context table for in-progress MCTP assembly.
- Assembly must support interleaving across independent MCTP message keys.
- Each active assembly queue entry stores the first accepted TLP header snapshot and the latest/last accepted TLP header snapshot for that message.
- The external SRAM write interface is 256 bits wide.
- The external SRAM stores only assembled MCTP message payload/body bytes. It does not store PCIe TLP headers, PCIe VDM sideband headers, MCTP transport headers, pad bytes, or optional digest bytes.

## 3.1 Scratch First-Target Locked Defaults

These defaults remove policy ambiguity for the scratch SSOT-to-audit implementation.

- There are no AXI IDs in the first target. The AXI write and AXI read interfaces accept one transaction at a time from a single upstream master.
- There are no multiple outstanding AXI write transactions and no multiple outstanding AXI read transactions.
- AXI read requests to a payload range without a completed descriptor return zero data with `RRESP=SLVERR` unless `raw_sram_debug_read_enable` is set.
- The SRAM payload allocator is a linear bump allocator from `sram_base` to `sram_limit`.
- `descriptor_pop` retires the descriptor entry, but descriptor-pop does not reclaim SRAM payload space in the first target.
- SRAM write traffic required for packet assembly has priority over firmware AXI read traffic.
- formal proof optional: formal verification is a future workflow note and is not required for first local audit closure.

## 4. Out of Scope

- PCIe PHY, data link layer, transaction layer replay, flow control, ordering, and credit management.
- PCIe endpoint configuration space and PCIe enumeration.
- PCIe Flit Mode packet format in the first implementation.
- TLP prefixes and implementation-dependent extra PCIe headers.
- ECRC generation/checking. The upstream PCIe block is responsible for ECRC handling; this IP may strip/ignore a trailing digest only if configured.
- MCTP bridging, routing table management, endpoint discovery, and EID assignment policy.
- Message-type-specific parsing beyond recording the first MCTP message type byte.
- Full DMTF conformance certification.

## 5. Top-Level Parameters

| Parameter | Required default | Meaning |
| --- | ---: | --- |
| `AXI_ADDR_WIDTH` | 16 | AXI write address width for ingress window/debug routing. |
| `AXI_DATA_WIDTH` | 256 | AXI WDATA width. Must remain 256 for this target. |
| `AXI_STRB_WIDTH` | 32 | AXI WSTRB width. Derived from data width. |
| `SRAM_ADDR_WIDTH` | 16 | Byte-addressed SRAM address width. |
| `SRAM_DATA_WIDTH` | 256 | SRAM write data width. Must remain 256 for this target. |
| `CONTEXT_COUNT` | 15 | Maximum active fragmented MCTP assemblies. |
| `TLP_HEADER_SNAPSHOT_BYTES` | 16 | Raw Non-Flit TLP/VDM/MCTP-transport header bytes saved for first and last packet of each assembled message. |
| `MIN_TRANSMISSION_UNIT_BYTES` | 64 | Minimum configured MCTP transmission unit size. |
| `MAX_TRANSMISSION_UNIT_BYTES` | 4096 | Maximum configured MCTP transmission unit size. |
| `TRANSMISSION_UNIT_ALIGN_BYTES` | 4 | Required alignment for configured transmission unit size and non-final packets. |
| `MAX_TLP_BYTES` | 4112 | Maximum stored bytes per incoming AXI transaction/TLP when TLP digest is stripped upstream: 16-byte Non-Flit header plus 4096-byte transmission unit. |
| `MAX_TLP_BEATS` | 129 | Maximum 256-bit AXI W beats needed for `MAX_TLP_BYTES`. |
| `MAX_MESSAGE_BYTES` | 4096 | Maximum assembled message body bytes. |
| `BASELINE_MTU_BYTES` | 64 | Baseline MCTP transmission unit size. |
| `DESCRIPTOR_FIFO_DEPTH` | 8 | Completed-message descriptor/header queue depth. |
| `TIMEOUT_COUNTER_WIDTH` | 24 | Assembly timeout counter width. |

## 6. External Interfaces

### 6.1 Clocks and Reset

- `axi_aclk`, `axi_aresetn`: AXI ingress, parser, assembly, and SRAM write clock/reset.
- `pclk`, `presetn`: APB control/status clock/reset.
- AXI and APB clocks may be asynchronous. All status/control crossings must use explicit CDC logic.

### 6.2 AXI4 Write Ingress

Required signals:

- AW: `s_axi_awaddr`, `s_axi_awlen`, `s_axi_awsize`, `s_axi_awburst`, `s_axi_awvalid`, `s_axi_awready`.
- W: `s_axi_wdata[255:0]`, `s_axi_wstrb[31:0]`, `s_axi_wlast`, `s_axi_wvalid`, `s_axi_wready`.
- B: `s_axi_bresp[1:0]`, `s_axi_bvalid`, `s_axi_bready`.

Initial simplification:

- AXI write ingress and AXI read payload access share the AXI clock domain but serve different functions.
- No multiple outstanding write transactions.
- No write interleaving.
- If AXI IDs are later required, `BID` must echo the accepted `AWID`; the first target can omit ID pins by requiring a single upstream master and one outstanding transaction.

AXI transaction rules:

- `AWSIZE` must be 5, meaning 32 bytes per beat for 256-bit `WDATA`.
- `AWBURST` must be `INCR`.
- Number of expected W beats is `AWLEN + 1`.
- `WLAST` must assert exactly on the final expected W beat.
- `WSTRB` marks valid TLP bytes.
- Full beats before the final beat should use all 32 strobes set.
- The final beat may be partial and must use contiguous valid byte lanes starting at lane 0.
- Non-contiguous `WSTRB`, empty transaction, early `WLAST`, late `WLAST`, unsupported `AWSIZE`, unsupported `AWBURST`, or a byte count greater than `MAX_TLP_BYTES` is a malformed AXI/TLP ingress event.
- A maximum-size 4096-byte MCTP transmission unit requires 4112 raw TLP bytes in Non-Flit mode and therefore 129 AXI W beats on a 256-bit interface.
- `AWADDR` selects the ingress aperture and is captured for debug only; it is not part of the TLP byte stream.

B channel policy:

- `BRESP=OKAY` means the AXI transaction was consumed by this IP.
- Packet/protocol failures after AXI acceptance are reported through drop/error status and counters, not by retrying AXI.
- If a system integration requires AXI error responses for malformed write transactions, that is a configurable integration policy and must be reviewed before changing the base requirement.

### 6.3 AXI4 Read Payload Path

The IP also exposes an AXI4 read path so firmware can read assembled payload bytes from the payload SRAM after consuming a completed-message descriptor.

Required signals:

- AR: `s_axi_araddr`, `s_axi_arlen`, `s_axi_arsize`, `s_axi_arburst`, `s_axi_arvalid`, `s_axi_arready`.
- R: `s_axi_rdata[255:0]`, `s_axi_rresp[1:0]`, `s_axi_rlast`, `s_axi_rvalid`, `s_axi_rready`.

Initial simplification:

- No multiple outstanding read transactions.
- No read IDs in the first target.
- `ARSIZE` must be 5, meaning 32 bytes per beat for 256-bit `RDATA`.
- `ARBURST` must be `INCR`.
- Firmware reads payload only after a descriptor is visible through the control/status register interface.

Read behavior:

- Descriptor metadata gives firmware `payload_base_addr` and `payload_len`.
- Firmware issues AXI read bursts that cover the descriptor range.
- The first target requires firmware read addresses to be 32-byte aligned. If `payload_base_addr` is not 32-byte aligned, firmware reads from `payload_base_addr & ~31` and discards leading bytes using `payload_base_addr[4:0]`.
- Firmware discards trailing bytes past `payload_base_addr + payload_len` on the final read word.
- The AXI read path issues one SRAM read request per AXI read beat and returns the SRAM read data on the AXI R channel.
- `RLAST` must assert on the final beat defined by `ARLEN`.
- Reads outside the configured SRAM read window return `RRESP=SLVERR`.
- Reads to a payload range that has no completed descriptor return zero data with `RRESP=SLVERR` unless `raw_sram_debug_read_enable` is set.
- AXI read backpressure must not corrupt ongoing assembly writes. Read requests may stall behind SRAM writes or behind a read/write arbiter.

### 6.4 APB Control and Status

The APB interface configures and observes the assembler. Required functions:

- Enable/disable ingress.
- Optional drop-while-disabled mode.
- Soft reset.
- Local EID and destination EID filtering policy.
- Accept broadcast EID and null EID policy.
- Configurable MTU, maximum message size, timeout, SRAM base, and SRAM limit.
- Interrupt enable/status and write-one-to-clear.
- Error/drop status.
- Drop counters, accepted packet counters, completed message counters, byte counters.
- Descriptor/header queue status, descriptor words, first/last TLP header snapshot readout, and descriptor pop command.
- AXI read path status and error reporting.

APB must not change the source-of-truth packet interpretation rules. It only configures policy choices that are explicitly listed in this requirement.

### 6.5 SRAM Read/Write Interface

The SRAM interface is a 256-bit payload memory interface in the AXI clock domain. It has a write side for the assembler and a read side for firmware AXI reads.

Required write signals:

- `sram_wr_valid`
- `sram_wr_ready`
- `sram_wr_addr[SRAM_ADDR_WIDTH-1:0]`
- `sram_wr_data[255:0]`
- `sram_wr_strb[31:0]`

Required read signals:

- `sram_rd_req_valid`
- `sram_rd_req_ready`
- `sram_rd_req_addr[SRAM_ADDR_WIDTH-1:0]`
- `sram_rd_rsp_valid`
- `sram_rd_rsp_ready`
- `sram_rd_rsp_data[255:0]`
- `sram_rd_rsp_error`

Rules:

- `sram_wr_addr` is byte addressed.
- Each completed MCTP message payload is written as contiguous bytes from its allocated start address.
- For each completed message, the logical SRAM payload range is exactly `[base_addr, base_addr + payload_len)`. Every byte in that range is an MCTP payload byte and there are no alignment holes inside the range.
- In this requirement, "MCTP payload" means the MCTP message body bytes after removing the PCIe VDM/TLP header and MCTP transport header, with pad/digest bytes stripped. This includes the MCTP message type byte from the first packet.
- Physical SRAM writes are packed into 256-bit words. `sram_wr_addr` for a physical write points to the 32-byte word containing the target byte address, and `sram_wr_strb` marks exactly the valid payload lanes in that word.
- If the next payload byte is not aligned to a 32-byte SRAM word boundary, the writer must continue in the next byte lane of the current SRAM word. It must not skip to the next 32-byte word and leave empty bytes.
- Partial first, middle, and final SRAM words are allowed when the message base or current payload offset is not 32-byte aligned. `sram_wr_strb` marks only payload bytes for those writes.
- The SRAM writer must never write PCIe headers, PCIe VDM sideband header bytes, MCTP transport headers, PCIe pad bytes, or optional TLP digest bytes as payload.
- SRAM read addresses are 32-byte aligned physical word addresses generated from the AXI read path.
- SRAM read data is returned without inserting or removing bytes. Firmware uses descriptor `payload_base_addr` and `payload_len` to trim leading/trailing bytes.
- If SRAM has one shared port, write traffic required for packet assembly has priority over firmware reads unless the integration explicitly chooses a different QoS policy.
- SRAM overflow aborts the affected assembly context and records an assembly drop.

## 7. PCIe VDM Packet Requirements

The first target supports Non-Flit Mode MCTP over PCIe VDM.

### 7.1 Required PCIe VDM Properties

The accepted TLP must match the DMTF PCIe VDM binding:

- PCIe VDM with data.
- Four-DWORD PCIe VDM header in Non-Flit Mode.
- Type indicates PCIe message with supported routing:
  - Route to Root Complex.
  - Route by ID.
  - Broadcast from Root Complex.
- Traffic class is 0.
- Attributes, address type, TH/LN/T8/T9 fields follow DSP0238 values for MCTP over PCIe VDM.
- Message Code is `0x7F`.
- Vendor ID is DMTF `0x1AB4`.
- MCTP VDM Code is `0x0`.
- MCTP header version is `0x1`.
- The MCTP packet payload starts after the 16-byte Non-Flit PCIe VDM/MCTP transport header.

### 7.2 Length and Padding

- The PCIe Length field is the length of the PCIe VDM data in DWORDs.
- The actual AXI-collected valid byte count must be consistent with the PCIe length field plus any accepted trailer policy.
- The configured MCTP transmission unit size is programmable from 64 bytes through 4096 bytes inclusive.
- The configured transmission unit size must be 4-byte aligned.
- Non-final packets in a fragmented message must carry exactly the configured transmission unit size after removing the 16-byte Non-Flit header and excluding pad/digest bytes.
- The final packet of a message may carry fewer payload bytes than the configured transmission unit size.
- A single-packet message is treated as a final packet and may be shorter than the configured transmission unit size.
- Non-final packet payload byte counts must be 4-byte aligned.
- Final packet payload byte counts may be shorter and not naturally 4-byte aligned; PCIe VDM pad bytes are used only to align the transported TLP data and are stripped before assembly.
- Pad length is 0 to 3 bytes.
- Non-EOM packets must have pad length 0.
- EOM packets may use pad bytes to DWORD-align the packet.
- Pad bytes are stripped before assembly.
- If TLP Digest/ECRC is present and the IP is configured for upstream-stripped mode, packets with an unstripped digest are dropped. If configured for digest-present mode, the digest is excluded from MCTP payload bytes and not checked by this IP.

### 7.3 Header Byte Mapping for the First Target

For the first implementation target, the byte stream accepted from AXI is a raw Non-Flit PCIe VDM TLP with byte 0 at `WDATA[7:0]` on the first beat.

Required decoded fields:

- PCIe common header fields from TLP bytes 0 through 3.
- Requester ID from the PCIe VDM header.
- PCIe TAG field bits carrying MCTP VDM Code and Pad Length per DSP0238.
- Message Code from the PCIe VDM header.
- Target ID from the PCIe VDM header.
- Vendor ID from the PCIe VDM header.
- MCTP transport header fields carried in the last four bytes of the Non-Flit PCIe VDM header under the DMTF Vendor ID.

The RTL must not treat bytes 1 through 3 as permanently zero; those bytes include meaningful PCIe header fields such as Length, TD/EP/Attr/AT depending on PCIe version.

For each accepted MCTP packet, the IP captures a raw 16-byte header snapshot from TLP bytes 0 through 15. This snapshot is sideband metadata only; it is never written into payload SRAM.

## 8. MCTP Packet Decode Requirements

The decoded MCTP transport header must expose:

- Header version.
- Destination Endpoint ID.
- Source Endpoint ID.
- SOM.
- EOM.
- 2-bit Packet Sequence Number.
- Tag Owner.
- 3-bit Message Tag.
- IC bit from the first byte of the message body on SOM packets.
- 7-bit Message Type from the first byte of the message body on SOM packets.

Rules:

- Header version must be 1.
- Reserved MCTP header bits are ignored on receive after recording a debug flag; generated test packets should set reserved bits to 0.
- Destination EID is accepted if filtering is disabled, equals configured local EID, equals broadcast EID and broadcast is enabled, or equals null EID and null EID is enabled.
- Packet sequence increments modulo 4 after the SOM packet for each continuation packet in the same message.
- Tag Owner and Message Tag remain constant from SOM through EOM for a fragmented message.
- For fragmented messages, every accepted non-EOM packet must contribute exactly the configured transmission unit byte count to the assembled message.
- The EOM packet may contribute fewer bytes than the configured transmission unit byte count.
- Message Type is recorded from the first message-body byte on a SOM packet.
- The first target records `IC`; it does not calculate or validate a message integrity check.

## 9. Assembly Requirements

### 9.1 Message Key

The assembly key is:

```text
{source_eid, tag_owner, message_tag}
```

This follows the MCTP transport-level message identification fields for a destination endpoint. Destination EID is checked by filter policy but is not part of the active context key in the first target.

### 9.2 Context Allocation

- A packet with `SOM=1,EOM=1` is a complete single-packet message.
- A packet with `SOM=1,EOM=0` starts a fragmented message context.
- A packet with `SOM=0,EOM=0` appends to an existing context.
- A packet with `SOM=0,EOM=1` appends to an existing context and completes it.
- `CONTEXT_COUNT` independent contexts may be active.
- If no context is available for a new fragmented message, drop the packet as packet/context-table-full and do not write payload bytes.
- If a duplicate SOM arrives for an active key, abort the old context, record an assembly drop, and do not publish a successful descriptor for the aborted message.

### 9.3 Interleaving and Header Snapshot Queue

Assembly must support interleaved packet arrival across independent message keys. For example, the following sequence is legal when each packet has a valid sequence number for its own key:

```text
A: SOM
B: SOM
A: middle
B: EOM
A: EOM
```

Each active context/queue entry must hold independent state:

- Active key `{source_eid, tag_owner, message_tag}`.
- Destination EID accepted for the message.
- Expected next packet sequence number.
- Allocated payload SRAM start address.
- Current payload byte count.
- Current SRAM word pack state: aligned word address, 256-bit data buffer, 32-bit strobe mask, and next byte lane.
- First TLP header snapshot.
- Latest TLP header snapshot, which becomes the last TLP header snapshot on EOM.
- Message Type and IC from the first packet payload byte.
- Timeout/age state.
- Drop/error state.

Header snapshot rules:

- On `SOM=1`, allocate or complete a context and store `first_tlp_header = current_tlp_header[0:15]`.
- On every accepted packet for the same active context, update `last_tlp_header = current_tlp_header[0:15]`.
- For a single-packet message, `first_tlp_header` and `last_tlp_header` are both the same accepted TLP header.
- Packet drops do not update any context header snapshot.
- Assembly drops discard the affected context header snapshots unless debug capture is explicitly enabled.
- On successful EOM, push the completed descriptor together with the first/last header snapshots into the completed-message descriptor/header queue.
- The descriptor/header queue must preserve first/last header snapshots until software or downstream logic pops the completed message entry.

### 9.4 Payload Writes

- The assembled message body is the concatenation of MCTP packet payload bytes after removing PCIe/VDM header bytes, MCTP transport header bytes, PCIe pad bytes, and optional digest bytes.
- The first message-body byte of a SOM packet contains `IC` and `Message Type`; it is retained in the assembled message payload unless a later message-type-specific requirement says otherwise.
- Payload bytes are written to SRAM in order.
- Payload byte `i` of a completed message is stored at byte address `base_addr + i`.
- Fragment boundaries do not create SRAM gaps. If a fragment ends at byte offset 68, the next fragment for the same message starts at byte offset 68, which is lane 4 of the 32-byte word whose aligned base is offset 64.
- With interleaving, each active context must preserve its own partial 32-byte SRAM pack state. Switching from context A to context B must not force context A to pad or skip to the next 32-byte word.
- Full 32-byte payload words may be written immediately. Partial words must be retained per context until they become full or the message reaches EOM, unless the SRAM byte-write semantics explicitly allow later non-overlapping byte-enable writes to the same word before descriptor publication.
- The descriptor reports payload start address and payload byte count.
- `MAX_MESSAGE_BYTES` overflow aborts the context and records an assembly drop.
- SRAM write backpressure must stall payload writes without dropping accepted bytes unless timeout/overflow occurs.
- SRAM payload writes for different interleaved contexts must not corrupt each other. Each context owns a separate payload address range or allocation record.
- The final SRAM write for a completed message may be shorter than a 256-bit word and must use `sram_wr_strb` to mark only valid payload bytes.

### 9.5 Descriptor

A completed message descriptor must contain at least:

- Source EID.
- Destination EID.
- Tag Owner.
- Message Tag.
- Message Type.
- Requester ID.
- PCIe routing type.
- SRAM start address.
- Payload byte count.
- First TLP header snapshot readout pointer or inline first header words.
- Last TLP header snapshot readout pointer or inline last header words.
- Final packet sequence.
- Context ID.
- Completion status.

Descriptor/header queue full on message completion is an assembly drop, because the payload and first/last TLP header provenance cannot be published safely.

## 10. Drop and Error Classification

### 10.1 Packet Drop

Packet drop applies before a packet starts, appends, completes, or terminates an assembly context. A packet drop never allocates a new context, never releases an existing context, never writes payload bytes to SRAM, and never publishes a successful descriptor.

Packet drop required effect:

- Discard the current packet only.
- Do not allocate a context.
- Do not update an existing context.
- Do not release an existing context.
- Do not update first/last TLP header snapshots.
- Do not write SRAM.
- Do not publish a successful descriptor.
- Increment `packet_drop_count`.
- Set `last_drop_class=packet_drop` and the matching reason code.

Packet drop reason matrix:

| Reason ID | Conditions that map to this packet drop |
| --- | --- |
| `PD_DISABLED_DROP_MODE` | `CONTROL.enable=0` and `CONTROL.drop_when_disabled=1`. If `drop_when_disabled=0`, the IP backpressures instead of accepting and dropping. |
| `PD_MALFORMED_TLP` | Empty AXI transaction; unsupported `AWSIZE`; unsupported `AWBURST`; unsupported AXI write interleaving; `AWLEN`/W beat count mismatch; early `WLAST`; missing/late `WLAST`; non-contiguous `WSTRB`; valid `WSTRB` holes before the final beat; final `WSTRB` not contiguous from byte lane 0; raw TLP byte count below 16 bytes; raw TLP byte count above `MAX_TLP_BYTES`; raw TLP byte count inconsistent with PCIe Length field; TLP Digest/ECRC present when the selected digest policy says it must be stripped upstream; required header snapshot bytes unavailable. |
| `PD_UNSUPPORTED_VDM` | TLP is not a supported Non-Flit PCIe VDM with data; unsupported Flit Mode packet; unsupported TLP prefix; unsupported routing type; unsupported traffic class; unsupported attribute/address-type/TH/LN/T8/T9 policy; unsupported TD/EP policy; Message Code is not `0x7F`; Vendor ID is not DMTF `0x1AB4`; MCTP VDM Code is not `0x0`; any PCIe VDM binding field required by DSP0238 for this target is not supported. |
| `PD_BAD_MCTP_HEADER` | MCTP transport header is not fully present; header version is not `1`; reserved header bits violate the selected strict policy; SOM/EOM/sequence/tag fields cannot be decoded; SOM packet has no message-body byte from which to record IC/message type; IC policy rejects the packet before assembly state is affected. |
| `PD_BAD_PAD_OR_ALIGNMENT` | Pad length is larger than available payload; `pad_len != 0` on a non-EOM packet; PCIe VDM data length is not DWORD aligned after accounting for pad/digest policy; configured transmission unit size is below 64, above 4096, or not 4-byte aligned; non-EOM packet payload byte count is not exactly the configured transmission unit size; non-EOM packet payload byte count is not 4-byte aligned; EOM packet payload byte count is greater than the configured transmission unit size; EOM pad bytes do not account for the final DWORD alignment. |
| `PD_DEST_EID_REJECT` | Destination EID fails the configured filter: not local EID, not accepted broadcast EID, and not accepted null EID while filtering is enabled. |
| `PD_UNEXPECTED_MIDDLE_END` | `SOM=0,EOM=0` middle packet arrives with no active matching context; `SOM=0,EOM=1` end packet arrives with no active matching context; continuation arrives after the active context was previously timed out, aborted, or completed; EOM arrives for a key that never observed a valid SOM. |
| `PD_BAD_OR_EXPIRED_TAG` | Tag Owner/Message Tag policy rejects the packet before context mutation; context table is full for a new fragmented SOM packet; a tag is reserved, expired, or not currently allowed by integration policy and the packet must not affect assembly state. |

### 10.2 Assembly Drop

Assembly drop applies after a packet has been accepted into, or would update, an active assembly context. An assembly drop aborts the affected context, releases that context slot, suppresses any successful descriptor for that message, and records the reason.

Assembly drop required effect:

- Abort exactly the affected active context.
- Release that context slot.
- Suppress successful descriptor publication for that message.
- Discard or debug-capture the affected first/last TLP header snapshots according to debug policy.
- Do not write any additional payload bytes for the aborted context after the drop condition is detected.
- Increment `assembly_drop_count`.
- Set `last_drop_class=assembly_drop` and the matching reason code.

Assembly drop reason matrix:

| Reason ID | Conditions that map to this assembly drop |
| --- | --- |
| `AD_DUPLICATE_SOM` | `SOM=1` packet arrives for an already active `{source_eid, tag_owner, message_tag}` key; single-packet `SOM=1,EOM=1` arrives for an active key; integration policy says duplicate SOM invalidates the existing active context. |
| `AD_SEQUENCE_MISMATCH` | Continuation packet sequence does not equal the active context's expected modulo-4 packet sequence; sequence repeats unexpectedly; sequence skips a value; sequence is otherwise inconsistent with the active context state; internal consistency check finds an active context with corrupt key, invalid context ID, missing first header snapshot, or other unrecoverable state and no dedicated context-corruption code is approved. |
| `AD_MESSAGE_OVERFLOW` | Appending accepted payload would exceed `MAX_MESSAGE_BYTES`; non-final/full-TU appends would exceed configured message limit; completed single-packet payload exceeds configured message limit; context byte counter overflows; accumulated length cannot be represented by descriptor fields. |
| `AD_SRAM_OVERFLOW` | Allocating payload storage would exceed configured SRAM base/limit; payload write address would wrap; payload write address would exceed `SRAM_ADDR_WIDTH`; SRAM writer reports allocation/write overflow for the active context; partial final write cannot be represented by available `sram_wr_strb` policy. |
| `AD_DESCRIPTOR_FULL` | Message reaches EOM but descriptor/header queue is full; completed payload cannot publish required descriptor metadata; completed payload cannot publish first/last TLP header snapshots; descriptor/header queue write fails. |
| `AD_TIMEOUT` | Active context age exceeds configured assembly timeout; context timeout is detected during periodic aging; continuation arrives for a context that is being timed out in the same service window. |

### 10.3 Drop Priority

If multiple conditions are true for the same accepted AXI transaction, the IP must report the first matching class in this priority order:

1. Disabled/drop-mode packet drop.
2. Malformed AXI/TLP packet drop.
3. Unsupported PCIe VDM packet drop.
4. Bad MCTP transport header packet drop.
5. Bad pad, length, alignment, or transmission-unit packet drop.
6. Destination EID reject packet drop.
7. Unexpected continuation/end packet drop.
8. Tag/context-allocation packet drop.
9. Duplicate SOM assembly drop.
10. Sequence mismatch assembly drop.
11. Message overflow assembly drop.
12. SRAM overflow assembly drop.
13. Descriptor/header queue full assembly drop.
14. Timeout assembly drop.

This priority prevents a later assembly failure from hiding an earlier packet-format failure.

## 11. Register Requirements

The APB register file is divided into Control, Status, Interrupt, Counter, Descriptor, and Debug register blocks. Payload data is read by firmware through AXI read, not by APB data registers.

### 11.1 Control Registers

Control registers configure policy and command side effects.

Required control fields:

- `enable`: enables AXI write ingress.
- `soft_reset`: clears active contexts, descriptor/header queue, parser state, SRAM writer pack state, and AXI read state; it does not rewrite persistent configuration fields.
- `drop_when_disabled`: accepts and packet-drops ingress while disabled instead of backpressuring.
- `dest_filter_enable`.
- `accept_broadcast_eid`.
- `accept_null_eid`.
- `local_eid`.
- `transmission_unit_bytes`: programmable from 64 through 4096 and 4-byte aligned.
- `max_message_bytes`.
- `assembly_timeout_cycles`.
- `sram_base`.
- `sram_limit`.
- `raw_sram_debug_read_enable`: optional debug policy for AXI reads outside completed descriptor ranges.
- `descriptor_pop`: explicit completed-descriptor pop after firmware has consumed the descriptor and, if required by software policy, read the payload.
- `counter_clear`: write-one command to clear counters.
- `debug_context_select`: selects the context/Q slot visible through Debug registers.

### 11.2 Status Registers

Status registers expose current non-destructive state.

Required global status fields:

- `ingress_busy`.
- `axi_read_busy`.
- `sram_write_busy`.
- `sram_read_busy`.
- `descriptor_available`.
- `descriptor_queue_full`.
- `context_active_any`.
- `active_context_count`.
- `context_error_any`.
- `packet_drop_seen`.
- `assembly_drop_seen`.
- `last_drop_class`.
- `last_drop_reason`.
- `last_error_context_id`.

Required per-Q/context status:

Each assembly Q/context slot is an independent assembly FSM. Firmware must be able to read every Q's FSM state and state variables through registers. A selected-debug-context mux may exist as a convenience, but it is not a replacement for per-Q register visibility.

Each context slot exposes a state enum:

  - `0`: `IDLE`.
  - `1`: `ASSEMBLING`.
  - `2`: `ERROR`.
  - `3`: `DONE_WAIT_DESCRIPTOR_POP` or implementation-reserved completed state.

Minimum per-Q register bank, repeated for `context[0]` through `context[CONTEXT_COUNT-1]`:

- `ctx_state`: slot FSM state.
- `ctx_valid`: slot owns an active or completed context.
- `ctx_error`: slot is in error state.
- `ctx_source_eid`.
- `ctx_destination_eid`.
- `ctx_tag_owner`.
- `ctx_message_tag`.
- `ctx_message_type`.
- `ctx_expected_seq`.
- `ctx_last_seq`.
- `ctx_payload_base_addr`: SRAM base address allocated to this Q/message.
- `ctx_payload_next_addr`: next byte address to be written for this Q/message.
- `ctx_payload_byte_count`: assembled payload bytes for this Q/message.
- `ctx_transmission_unit_bytes`: TU size latched when the context was allocated.
- `ctx_timeout_age`.
- `ctx_last_drop_reason`.
- `ctx_first_tlp_header[0:15]`.
- `ctx_last_tlp_header[0:15]`.
- `ctx_partial_word_addr`: aligned 32-byte SRAM word address for the Q's current partial pack buffer.
- `ctx_partial_word_strobe[31:0]`.
- `ctx_partial_word_valid`.
- `ctx_partial_next_lane[4:0]`.

Minimum per-Q FSM behavior:

- `IDLE`: no active message; per-Q payload byte count is zero; Q can allocate on valid SOM.
- `ASSEMBLING`: Q owns a message key and accepts/appends matching fragments; Q preserves independent SRAM base, write offset, expected sequence, first/last headers, timeout age, and partial SRAM word pack state.
- `ERROR`: Q hit an assembly-drop condition; Q holds error state/reason long enough for software/debug visibility, then releases according to clear policy.
- `DONE_WAIT_DESCRIPTOR_POP`: optional state if descriptor/header queue and context storage are tied. If implemented, Q holds completed metadata until descriptor pop. If descriptor queue copies all required metadata, Q may return directly to `IDLE` after successful descriptor push.

The register file may additionally provide compact bitmaps:

- `context_idle_bitmap`.
- `context_assembling_bitmap`.
- `context_error_bitmap`.
- `context_done_bitmap`.

Legacy selected-context debug view:

- `debug_context_select` selects one of the per-Q banks for compact debug readout.
- The selected debug context mirrors the same fields as the corresponding `context[n]` register bank.
- It must not be the only way to observe per-Q SRAM base address, FSM state, or error status.

Removed ambiguity:

- The design must not expose only one selected context while hiding the other Q states.
- The design must not expose only bitmaps while hiding per-Q SRAM base address and per-Q payload counters.
- Each Q has its own FSM, SRAM allocation state, and partial 32-byte SRAM pack state.

Per-Q state encoding summary:

  - `0`: `IDLE`.
  - `1`: `ASSEMBLING`.
  - `2`: `ERROR`.
  - `3`: `DONE_WAIT_DESCRIPTOR_POP` or implementation-reserved completed state.

### 11.3 Interrupt Registers

Interrupt is active-high level style.

Required interrupt registers:

- `intr_raw_status`: raw event state before masking.
- `intr_enable`: interrupt mask.
- `intr_status`: masked interrupt status.
- `intr_clear`: write-one-to-clear interrupt bits.

Required interrupt bits:

- `descriptor_ready`.
- `packet_drop`.
- `assembly_drop`.
- `context_timeout`.
- `sram_overflow`.
- `descriptor_queue_full`.
- `axi_write_malformed`.
- `axi_read_error`.
- `fatal_internal_error`.

Interrupt events crossing from `axi_aclk` to `pclk` must use explicit CDC synchronization.

### 11.4 Counter Registers

Counters are saturating unless a wider software-visible counter policy is specified. `counter_clear` clears all counters unless a counter is documented as sticky.

Required aggregate counters:

- `tlp_seen_count`.
- `tlp_accepted_count`.
- `message_completed_count`.
- `payload_bytes_written_count`.
- `fw_axi_read_beat_count`.
- `fw_axi_read_error_count`.
- `packet_drop_count`.
- `assembly_drop_count`.

Required packet-drop reason counters:

- `pd_disabled_drop_mode_count`.
- `pd_malformed_tlp_count`.
- `pd_unsupported_vdm_count`.
- `pd_bad_mctp_header_count`.
- `pd_bad_pad_or_alignment_count`.
- `pd_dest_eid_reject_count`.
- `pd_unexpected_middle_end_count`.
- `pd_bad_or_expired_tag_count`.

Required assembly-drop reason counters:

- `ad_duplicate_som_count`.
- `ad_sequence_mismatch_count`.
- `ad_message_overflow_count`.
- `ad_sram_overflow_count`.
- `ad_descriptor_full_count`.
- `ad_timeout_count`.

### 11.5 Descriptor Registers

Descriptor registers expose the oldest completed message descriptor/header queue entry.

Required descriptor-visible fields:

- `descriptor_valid`.
- `source_eid`.
- `destination_eid`.
- `tag_owner`.
- `message_tag`.
- `message_type`.
- `requester_id`.
- `pcie_routing_type`.
- `payload_base_addr`.
- `payload_len`.
- `final_packet_sequence`.
- `context_id`.
- `completion_status`.
- `first_tlp_header[0:15]`.
- `last_tlp_header[0:15]`.

Firmware flow:

1. Poll or interrupt on `descriptor_ready`.
2. Read descriptor fields and first/last TLP header snapshots.
3. Read payload bytes through AXI read using `payload_base_addr` and `payload_len`.
4. Write `descriptor_pop` when software is done with the descriptor.

### 11.6 Debug Registers

Debug registers provide low-level observability without changing functional behavior.

Required debug fields:

- `debug_context_select`.
- Selected context mirror of the required per-Q register bank.
- Parser FSM state.
- AXI write ingress FSM state.
- AXI read FSM state.
- SRAM write packer state.
- SRAM read request/response state.
- Last decoded PCIe VDM fields.
- Last decoded MCTP fields.
- Last drop reason and last error context.

## 12. Functional Model Requirements

The FL model must be the golden reference and must implement:

- AXI transaction to byte-stream conversion using 256-bit `WDATA` and `WSTRB`.
- One transaction equals one TLP.
- PCIe VDM Non-Flit header decode.
- MCTP transport header decode.
- Pad/digest stripping policy.
- Configurable transmission unit validation: 64 to 4096 bytes, 4-byte aligned, non-final packets full-sized, final packet may be shorter.
- Destination EID filtering.
- Context allocation and message assembly.
- Interleaved assembly across independent keys.
- First/last TLP header snapshot capture per context.
- Sequence checking.
- MCTP payload-only SRAM byte packing into 256-bit write beats.
- SRAM read request/response behavior for firmware AXI reads.
- AXI read transaction behavior for completed payload access.
- Control, Status, Interrupt, Counter, Descriptor, and Debug register behavior.
- Per-Q FSM and per-Q register bank visibility, including SRAM base address, payload counters, error state, first/last TLP headers, and partial SRAM pack state.
- Aggregate and per-reason packet-drop and assembly-drop counters.
- Descriptor publication.
- Packet-drop versus assembly-drop classification.

The FL model must not be modified by the LLM to make RTL failures pass without human approval.

## 13. Verification Requirements

Minimum directed scenarios:

- Valid single-packet message (`SOM=1,EOM=1`) in one AXI transaction.
- Valid fragmented message across multiple AXI transactions.
- Interleaved fragmented messages with distinct `{source_eid, tag_owner, message_tag}` keys.
- Interleaving where message B completes before message A even though message A started first.
- First TLP header snapshot equals the SOM packet header for each completed message.
- Last TLP header snapshot equals the EOM packet header for each completed message.
- SRAM contains only assembled MCTP payload/body bytes, with no copied TLP or MCTP transport header bytes.
- 256-bit AXI packing with full beats and partial final beat.
- Multi-beat TLP using `AWLEN > 0`.
- Maximum transmission unit packet: 4096-byte MCTP payload plus 16-byte Non-Flit header over 129 AXI W beats.
- Minimum transmission unit packet: 64-byte non-final MCTP payload.
- Final packet shorter than configured transmission unit size.
- Final packet with non-4-byte natural payload length and valid pad stripping.
- Non-final packet shorter than configured transmission unit size is dropped.
- Non-final packet with non-4-byte-aligned payload length is dropped.
- Configured transmission unit not aligned to 32 bytes, for example 68B: next fragment must continue in the same 32-byte SRAM word lane without a gap.
- Interleaved messages where multiple active contexts each hold a partial 32-byte SRAM word; completing one context must not corrupt another context's partial word.
- Descriptor payload range `[base_addr, base_addr + payload_len)` has no unwritten hole bytes.
- Early `WLAST`.
- Late/missing `WLAST`.
- Unsupported `AWSIZE`.
- Unsupported `AWBURST`.
- Non-contiguous `WSTRB`.
- TLP shorter than 16 bytes.
- PCIe length mismatch.
- Wrong message code.
- Wrong Vendor ID.
- Wrong MCTP VDM Code.
- Bad MCTP header version.
- Unsupported destination EID.
- EOM without SOM.
- Middle packet without SOM.
- Duplicate SOM.
- Packet sequence mismatch.
- Context table full.
- Message size overflow.
- SRAM backpressure.
- SRAM overflow.
- Firmware AXI read of a completed payload using descriptor `payload_base_addr` and `payload_len`.
- Firmware AXI read covering an unaligned payload base by reading aligned SRAM words and trimming leading/trailing bytes in software.
- AXI read outside configured SRAM read window returns `SLVERR`.
- AXI read path stalls correctly when SRAM read response is delayed.
- AXI read path does not corrupt or reorder concurrent assembly writes.
- Control register write/read behavior.
- Status register global busy/error/descriptor fields.
- Interrupt enable/status/clear behavior.
- Debug context selection and selected context readout.
- Per-Q FSM state visibility: idle, assembling, error, and completed/waiting when implemented.
- Per-Q register bank visibility for every Q, including SRAM base address and payload next address.
- Aggregate packet drop and assembly drop counters.
- Per-reason packet-drop counters for every `PD_*` reason.
- Per-reason assembly-drop counters for every `AD_*` reason.
- Descriptor/header queue full.
- Assembly timeout.
- Every `PD_*` packet-drop reason in Section 10 has at least one directed test that proves no context/header/SRAM/descriptor side effect.
- Every `AD_*` assembly-drop reason in Section 10 has at least one directed test that proves exactly the affected context is aborted.
- Drop-priority tests where an early packet-format failure and a later possible assembly failure are both present; the earlier packet-drop reason must win.

Minimum reusable monitor obligations:

- AXI4 write transaction monitor reconstructs TLP bytes from AW/W/B.
- AXI4 read transaction monitor reconstructs firmware payload reads from AR/R.
- APB register monitor checks Control, Status, Interrupt, Counter, Descriptor, and Debug register behavior.
- APB register monitor checks every per-Q register bank, not only selected debug context.
- PCIe VDM monitor decodes required header fields and length/pad consistency.
- MCTP packet monitor decodes SOM/EOM/sequence/tag/key/message type.
- SRAM write monitor reconstructs completed payload bytes from 256-bit writes and strobes.
- SRAM write monitor checks byte-accurate packing: payload byte `i` appears at `base_addr + i`, with no alignment gaps across fragment boundaries.
- Descriptor/header monitor correlates descriptor metadata, first/last TLP header snapshots, and SRAM payload bytes.

Minimum mutation categories:

- AXI beat/byte packing and WSTRB handling.
- AXI read address/length/RLAST handling.
- `WLAST`/`AWLEN` boundary handling.
- PCIe VDM constants: message code, vendor ID, MCTP VDM code.
- PCIe length and pad trimming.
- Transmission unit boundary validation.
- MCTP header version.
- SOM/EOM branch handling.
- Sequence modulo-4 update.
- Assembly key fields.
- First/last TLP header snapshot capture/update.
- Context allocation/full handling.
- SRAM byte-to-word packing, unaligned 32-byte word continuation, per-context partial word state, and partial word strobes.
- SRAM read request/response routing into AXI RDATA.
- Control/status/debug/interrupt register decode and counter update paths.
- Per-Q FSM/register update paths.
- Descriptor/header queue full handling.

Mutation is an observation-depth check, not a proof of functional correctness.

## 14. Formal Verification Candidates

Formal is optional for this IP. Good bounded-property candidates:

- AXI ingress never writes beyond `MAX_TLP_BYTES`.
- Non-final accepted packets have payload byte count equal to the configured transmission unit size.
- EOM packets may have payload byte count less than or equal to the configured transmission unit size.
- Accepted transaction eventually produces exactly one parser event or one malformed/drop event.
- No SRAM write occurs before a packet is accepted for assembly.
- AXI read response is not issued before the corresponding SRAM read response.
- AXI read `RLAST` is asserted exactly on the final beat defined by `ARLEN`.
- No descriptor is published before EOM.
- First header snapshot for a context is written only by the accepted SOM packet.
- Last header snapshot for a context equals the most recent accepted packet for that context.
- Sequence mismatch aborts the active context and suppresses success descriptor.
- Context count never exceeds `CONTEXT_COUNT`.
- SRAM write strobes never assert outside valid assembled payload bytes.
- For every published descriptor, every byte address from `base_addr` through `base_addr + payload_len - 1` is written exactly as the corresponding assembled payload byte with no alignment gap.
- Per-context state register encoding is mutually exclusive: a context cannot be idle and assembling or error in the same cycle.
- Per-Q SRAM base and next byte address registers match the payload addresses observed on SRAM writes.

## 15. Deferred Product Review Items

The first scratch target is fully specified by the locked defaults above. The
following are future product changes only. Any item below requires a new
requirement approval before SSOT or RTL is changed:

- Replacing APB with a custom CSR interface.
- Adding AXI ID pins or multiple outstanding AXI transactions.
- Returning AXI `SLVERR` for malformed writes instead of accepting the AXI
  transaction with `OKAY` and reporting protocol failure through status.
- Accepting unstripped TLP Digest/ECRC at this IP input.
- Increasing `MAX_TLP_BYTES`, `MAX_MESSAGE_BYTES`, or allowing a complete
  assembled message to span more than the first-target message limit.
- Adding destination EID to the active context key.
- Adding message-type-specific IC handling.
- Reclaiming SRAM payload space on `descriptor_pop`.
- Supporting unaligned AXI read addresses by shifting `RDATA`.
- Exposing raw SRAM reads outside completed descriptor ranges when
  `raw_sram_debug_read_enable` is not set.
- Changing SRAM read/write arbitration away from assembly-write priority.

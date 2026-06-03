# MCTP Assembler v3 — RTL Integration Contract

Status: DESIGN doc (authored by worker-arch for team mctp-v3-signoff, Task #1).
This file fixes the **module boundaries and inter-module wiring** so that 8 module
`.sv` files can be authored independently with no shared-file conflicts; the team
lead wires the top from this contract.

Authoritative sources (do NOT edit any of them):
- `mctp_assembler_v3/yaml/mctp_assembler_v3.ssot.yaml` (io_list, function_model,
  fsm, registers, interrupts, memory, cdc_requirements, error_handling, integration)
- `mctp_assembler_v3/rtl/rtl_contract.json` (output_map / input_map / output_rules)
- `mctp_assembler_v3/rtl/mctp_assembler_v3_axi_wr_ingress.sv` (PROVEN module +
  its FIXED downstream beat-stream interface)
- `mctp_assembler_v3/rtl/mctp_assembler_v3.sv` (current 51-port top + parameters)
- `mctp_assembler_scratch/rtl/*.sv` (STRUCTURAL reference for decomposition,
  wire widths, FSM topology — referenced, never cloned)

## 0. Global conventions (apply to EVERY module)

- Coding style follows the proven `mctp_assembler_v3_axi_wr_ingress.sv`:
  `` `default_nettype none `` at top, `` `default_nettype wire `` at bottom;
  `input wire` / `output reg`; ANSI port list; no package/interface/modport/
  function/task/`for`/`while` (synthesis.constraints); no inferred latches; all
  flops reset per the clock_reset_domains scheme.
- **Datapath domain clock/reset:** `axi_aclk` / `axi_aresetn` (active-low,
  async-assert / sync-deassert). Modules: ingress, pcie_vdm_parser, mctp_decoder,
  context_table, sram_packer, descriptor_queue, axi_rd_payload.
- **APB domain clock/reset:** `pclk` / `presetn` (active-low). Module: apb_regfile.
- **cdc_sync** straddles both domains (has all four of axi_aclk/axi_aresetn/
  pclk/presetn).
- Reset block clears ALL architectural state and drives all outputs to safe
  inactive defaults (valid=0, resp=OKAY, counters=0), exactly like the ingress.
- All multi-cycle handshakes obey `cycle_model.handshake_rules`: hold
  addr/data/strb stable while `valid && !ready`.
- Parameter names and defaults are the SSOT `parameters` block; pass them down
  from the top by name (see §3 instantiation).

### 0.1 Canonical decoded-packet field set (shared vocabulary)

These names/widths are used identically across parser→decoder→context_table so
the lead can wire them 1:1. Derived from `function_model` state_variables/transactions:

| field | width | meaning / SSOT expr |
|---|---|---|
| `source_eid` | 8 | MCTP source EID |
| `dest_eid` | 8 | MCTP destination EID |
| `tag_owner` | 1 | `mctp_byte0[3]` |
| `message_tag` | 3 | `mctp_byte0[2:0]` |
| `packet_seq` | 2 | `mctp_byte0[5:4]` |
| `som` | 1 | `mctp_byte0[7]` |
| `eom` | 1 | `mctp_byte0[6]` |
| `message_type` | 7 | IC+msg_type low bits from SOM body byte |
| `ic` | 1 | integrity-check bit from SOM body byte |
| `assembly_key` | 12 | `(source_eid<<4)\|(tag_owner<<3)\|message_tag` |
| `payload_bytes` | 13 | decoded MCTP payload byte count this packet |
| `tlp_header_snapshot` | 128 | 16 raw header bytes (`TLP_HEADER_SNAPSHOT_BYTES*8`) |
| `requester_id` | 16 | `(tlp[1]<<8)\|tlp[2]` (VDM) |
| `pcie_routing_type` | 3 | PCIe routing field (VDM) |

---

## 1. Module interfaces (parameters + ordered port lists)

Direction is from the named module's perspective. Clocks/resets first, then the
upstream-facing ports, then the downstream-facing ports, then sideband/debug.

### 1.0 mctp_assembler_v3_axi_wr_ingress — ALREADY AUTHORED (reference; do NOT edit)

The downstream interface below is **FIXED**. The parser is built to consume it.

Parameters: `AXI_ADDR_WIDTH=16, AXI_DATA_WIDTH=256, AXI_STRB_WIDTH=32,
MAX_TLP_BYTES=4112, BRESP_OKAY=2'd0, AXSIZE_32B=3'd5, AXBURST_INCR=2'd1`.

| port | dir | width | meaning |
|---|---|---|---|
| axi_aclk | in | 1 | datapath clock |
| axi_aresetn | in | 1 | datapath reset, active-low |
| s_axi_awaddr | in | 16 | AW address (debug capture) |
| s_axi_awlen | in | 8 | AWLEN (beats-1) |
| s_axi_awsize | in | 3 | AWSIZE (must be 5) |
| s_axi_awburst | in | 2 | AWBURST (must be INCR) |
| s_axi_awvalid | in | 1 | AW valid |
| s_axi_awready | out | 1 | AW ready |
| s_axi_wdata | in | 256 | W data beat |
| s_axi_wstrb | in | 32 | W byte strobes |
| s_axi_wlast | in | 1 | final W beat |
| s_axi_wvalid | in | 1 | W valid |
| s_axi_wready | out | 1 | W ready |
| s_axi_bresp | out | 2 | B response (OKAY) |
| s_axi_bvalid | out | 1 | B valid |
| s_axi_bready | in | 1 | B ready |
| **tlp_beat_valid** | out | 1 | downstream beat valid (1-cycle pulse per accepted W beat) |
| **tlp_beat_data** | out | 256 | beat data (lane N = wdata[8N+:8]) |
| **tlp_beat_strb** | out | 32 | beat byte strobes |
| **tlp_beat_last** | out | 1 | final beat of the TLP |
| **tlp_accept** | out | 1 | 1-cycle pulse: TLP legal & in-bounds (qualified at B) |
| **tlp_byte_count** | out | 13 | total accepted TLP byte count (popcount sum) |

NOTE for the parser author: the ingress streams **raw 256-bit beats**; it does NOT
present the whole TLP as one word. The parser must latch beats into a working
buffer and use `tlp_beat_last` + `tlp_accept`/`tlp_byte_count` to know the TLP is
complete and legal before decoding. The first beat's low 16 bytes
(`tlp_beat_data[127:0]` on the first beat) are the 16B Non-Flit header snapshot.

---

### 1.1 mctp_assembler_v3_pcie_vdm_parser  (FM_DECODE_VDM)

Consumes the FIXED ingress beat stream; decodes/validates the 16B Non-Flit PCIe
VDM header; strips header/pad/digest; emits one validated VDM packet (header +
payload region) or a packet-drop reason. Buffers beats internally.

Parameters: `AXI_DATA_WIDTH=256, AXI_STRB_WIDTH=32,
MIN_TRANSMISSION_UNIT_BYTES=64, MAX_TRANSMISSION_UNIT_BYTES=4096,
TRANSMISSION_UNIT_ALIGN_BYTES=4, TLP_HEADER_SNAPSHOT_BYTES=16`.

| port | dir | width | meaning |
|---|---|---|---|
| axi_aclk | in | 1 | datapath clock |
| axi_aresetn | in | 1 | datapath reset |
| tlp_beat_valid | in | 1 | from ingress |
| tlp_beat_data | in | 256 | from ingress |
| tlp_beat_strb | in | 32 | from ingress |
| tlp_beat_last | in | 1 | from ingress |
| tlp_accept | in | 1 | from ingress: TLP legal at B |
| tlp_byte_count | in | 13 | from ingress |
| cfg_tu_bytes | in | 13 | configured TU (from regfile via cdc) |
| vdm_valid | out | 1 | 1-cycle pulse: validated VDM packet emitted |
| vdm_word | out | 256 | first beat word carrying the 16B header + body byte (for the decoder to slice) |
| vdm_payload_offset | out | 5 | payload byte offset within the TLP (=16) |
| vdm_payload_bytes | out | 13 | VDM-stripped payload byte count |
| vdm_first_header | out | 128 | first 16B header snapshot candidate |
| vdm_last_header | out | 128 | last 16B header snapshot candidate |
| vdm_requester_id | out | 16 | `(tlp[1]<<8)\|tlp[2]` |
| vdm_routing_type | out | 3 | PCIe routing type |
| vdm_payload_word | out | 256 | payload-only data word for downstream pack |
| vdm_payload_strb | out | 32 | payload-only byte strobes |
| packet_drop_valid | out | 1 | 1-cycle pulse: this TLP is dropped |
| packet_drop_reason | out | 6 | PD_* reason code (see §4.2); 0 = none |
| last_decoded_vdm | out | 32 | `(msg_code<<24)\|(vendor_id<<8)\|vdm_code` (DEBUG_CTX mirror) |

Drop reasons it may raise: `PD_UNSUPPORTED_VDM`, `PD_BAD_PAD_OR_ALIGNMENT`
(and pass-through of an upstream `PD_MALFORMED_TLP` when `tlp_accept` is low).

### 1.2 mctp_assembler_v3_mctp_decoder  (FM_DECODE_MCTP)

Decodes the MCTP transport header + IC/message-type on SOM. Produces the canonical
decoded-packet field set (§0.1) and the assembly_key.

Parameters: none required (pure decode; widths fixed by §0.1).

| port | dir | width | meaning |
|---|---|---|---|
| axi_aclk | in | 1 | datapath clock |
| axi_aresetn | in | 1 | datapath reset |
| vdm_valid | in | 1 | from parser |
| vdm_word | in | 256 | from parser (header + SOM body byte) |
| vdm_payload_bytes | in | 13 | from parser |
| vdm_payload_word | in | 256 | from parser (payload-only) |
| vdm_payload_strb | in | 32 | from parser (payload-only) |
| vdm_first_header | in | 128 | from parser |
| vdm_last_header | in | 128 | from parser |
| packet_drop_reason_in | in | 6 | from parser (pass-through priority) |
| cfg_dest_filter_enable | in | 1 | CONTROL.dest_filter_enable (via cdc) |
| cfg_local_eid | in | 8 | CONTROL.local_eid (via cdc) |
| cfg_accept_broadcast_eid | in | 1 | CONTROL.accept_broadcast_eid (via cdc) |
| cfg_accept_null_eid | in | 1 | CONTROL.accept_null_eid (via cdc) |
| frag_valid | out | 1 | 1-cycle pulse: decoded MCTP fragment emitted |
| frag_source_eid | out | 8 | source_eid |
| frag_dest_eid | out | 8 | dest_eid |
| frag_tag_owner | out | 1 | tag_owner |
| frag_message_tag | out | 3 | message_tag |
| frag_packet_seq | out | 2 | packet_seq |
| frag_som | out | 1 | som |
| frag_eom | out | 1 | eom |
| frag_message_type | out | 7 | message_type (SOM) |
| frag_ic | out | 1 | integrity-check bit (SOM) |
| frag_assembly_key | out | 12 | `(source_eid<<4)\|(tag_owner<<3)\|message_tag` |
| frag_payload_word | out | 256 | payload-only data word (forwarded) |
| frag_payload_strb | out | 32 | payload-only strobes (forwarded) |
| frag_payload_bytes | out | 13 | payload_bytes |
| frag_first_header | out | 128 | first 16B header snapshot |
| frag_last_header | out | 128 | last 16B header snapshot |
| packet_drop_valid | out | 1 | 1-cycle pulse: dropped |
| packet_drop_reason | out | 6 | PD_* reason; raises `PD_BAD_MCTP_HEADER`, `PD_DEST_EID_REJECT`; passes through input |
| last_decoded_mctp | out | 32 | DEBUG_CTX mirror of decoded MCTP fields |

### 1.3 mctp_assembler_v3_context_table  (FM_ALLOC_CONTEXT + FM_APPEND + context_fsm)

CONTEXT_COUNT contexts keyed by assembly_key; per-context FSM, expected_seq,
first/last header snapshot, payload base/next addr, partial-word lane, timeout age.
Issues a per-packet payload-write request (to the packer) and a descriptor push
(to the descriptor queue) on EOM. Owns drop classification for the assembly path.

Parameters: `CONTEXT_COUNT=15, TLP_HEADER_SNAPSHOT_BYTES=16, MAX_MESSAGE_BYTES=4096,
SRAM_ADDR_WIDTH=16, AXI_DATA_WIDTH=256, AXI_STRB_WIDTH=32, TIMEOUT_COUNTER_WIDTH=24,
ASSEMBLING=2'd1, DONE_WAIT_DESCRIPTOR_POP=2'd3`.

| port | dir | width | meaning |
|---|---|---|---|
| axi_aclk | in | 1 | datapath clock |
| axi_aresetn | in | 1 | datapath reset |
| frag_valid | in | 1 | from decoder |
| frag_source_eid | in | 8 | from decoder |
| frag_dest_eid | in | 8 | from decoder |
| frag_tag_owner | in | 1 | from decoder |
| frag_message_tag | in | 3 | from decoder |
| frag_packet_seq | in | 2 | from decoder |
| frag_som | in | 1 | from decoder |
| frag_eom | in | 1 | from decoder |
| frag_message_type | in | 7 | from decoder |
| frag_assembly_key | in | 12 | from decoder |
| frag_payload_word | in | 256 | from decoder |
| frag_payload_strb | in | 32 | from decoder |
| frag_payload_bytes | in | 13 | from decoder |
| frag_first_header | in | 128 | from decoder |
| frag_last_header | in | 128 | from decoder |
| packet_drop_reason_in | in | 6 | from decoder (pass-through priority) |
| cfg_enable | in | 1 | CONTROL.enable (via cdc) |
| cfg_drop_when_disabled | in | 1 | CONTROL.drop_when_disabled (via cdc) |
| cfg_sram_base | in | 16 | SRAM_BASE (via cdc) |
| cfg_sram_limit | in | 16 | SRAM_LIMIT (via cdc) |
| cfg_max_message_bytes | in | 13 | CFG_TU.max_message_bytes (via cdc) |
| cfg_timeout_cycles | in | 24 | CFG_TIMEOUT (via cdc) |
| descriptor_full | in | 1 | from descriptor_queue (AD_DESCRIPTOR_FULL at EOM) |
| descriptor_pop | in | 1 | from regfile (via cdc): retire DONE context |
| pack_wr_valid | out | 1 | payload write request to packer (handshaked) |
| pack_wr_ready | in | 1 | from packer: accept payload write |
| pack_wr_data | out | 256 | payload data word |
| pack_wr_strb | out | 32 | payload byte strobes |
| pack_wr_addr | out | 16 | byte start addr for this packet's payload (`base+offset`) |
| pack_wr_bytes | out | 13 | payload bytes contributed by this packet |
| descriptor_push | out | 1 | push completed descriptor (1-cycle) |
| desc_base_addr | out | 16 | payload_base_addr |
| desc_payload_len | out | 13 | ctx_payload_byte_count |
| desc_source_eid | out | 8 | descriptor key |
| desc_dest_eid | out | 8 | descriptor key |
| desc_tag_owner | out | 1 | descriptor key |
| desc_message_tag | out | 3 | descriptor key |
| desc_message_type | out | 7 | message_type |
| desc_final_seq | out | 2 | last accepted seq |
| desc_context_id | out | 4 | context slot id |
| desc_completion_status | out | 3 | completion status code |
| desc_requester_id | out | 16 | from VDM (forwarded) |
| desc_routing_type | out | 3 | from VDM (forwarded) |
| desc_first_header | out | 128 | first 16B header snapshot |
| desc_last_header | out | 128 | last 16B header snapshot |
| packet_drop_pulse | out | 1 | 1-cycle: a PD_* drop classified here |
| assembly_drop_pulse | out | 1 | 1-cycle: an AD_* drop classified here |
| drop_class_o | out | 2 | 0=none,1=packet,2=assembly (top → last_drop_class) |
| drop_reason_o | out | 6 | last drop reason code |
| sram_overflow_pulse | out | 1 | AD_SRAM_OVERFLOW event (→ irq sram_overflow) |
| timeout_pulse | out | 1 | AD_TIMEOUT event (→ irq context_timeout) |
| active_context_count | out | 5 | non-idle context count (STATUS) |
| context_active_any | out | 1 | any context active (STATUS) |
| context_error_any | out | 1 | any context in ERROR (STATUS) |
| last_error_context_id | out | 4 | context id of last error (STATUS) |
| ctx_state_sel | out | 2 | selected-context FSM state (DEBUG_CTX/CTX_STATE) |
| ctx_key_sel | out | 12 | selected-context key (CTX_STATE) |
| ctx_expected_seq_sel | out | 2 | selected-context expected seq (CTX_STATE) |
| ctx_payload_count_sel | out | 13 | selected-context payload byte count |
| debug_context_select | in | 8 | CONTROL.debug_context_select (via cdc) — which slot to mirror |

### 1.4 mctp_assembler_v3_sram_packer  (FM_PACK_SRAM)

Packs payload-only bytes into 256-bit SRAM words. Per-context partial-word state is
held in the context_table; the packer receives `pack_wr_*` requests and drives the
**top SRAM write port** directly (write side owns `sram_wr_*`). Emits 32B-aligned
word writes with `sram_wr_strb` marking only payload lanes.

Parameters: `SRAM_ADDR_WIDTH=16, SRAM_DATA_WIDTH=256, AXI_STRB_WIDTH=32`.

| port | dir | width | meaning |
|---|---|---|---|
| axi_aclk | in | 1 | datapath clock |
| axi_aresetn | in | 1 | datapath reset |
| pack_wr_valid | in | 1 | from context_table |
| pack_wr_ready | out | 1 | accept payload write (backpressure to ctx) |
| pack_wr_data | in | 256 | payload data word |
| pack_wr_strb | in | 32 | payload byte strobes |
| pack_wr_addr | in | 16 | byte start address (`ctx_payload_next_addr`) |
| pack_wr_bytes | in | 13 | payload byte count this request |
| sram_wr_valid_o | out | 1 | top SRAM write valid (→ `sram_wr_valid`) |
| sram_wr_ready | in | 1 | top SRAM write ready |
| sram_wr_addr | out | 16 | 32B-aligned word addr = `ctx_payload_next_addr & ~31` |
| sram_wr_data | out | 256 | SRAM write data word |
| sram_wr_strb | out | 32 | `((1<<payload_bytes)-1) << (addr & 31)` |
| pack_next_lane | out | 5 | next byte lane in the partial word (DEBUG_CTX) |
| sram_write_busy | out | 1 | STATUS.sram_write_busy |

### 1.5 mctp_assembler_v3_descriptor_queue  (FM_PUBLISH_DESCRIPTOR)

DESCRIPTOR_FIFO_DEPTH-deep FIFO of completed descriptors + first/last header
snapshots; holds the oldest descriptor for APB readout until `descriptor_pop`.
Raises `AD_DESCRIPTOR_FULL` (reported by context_table) on overflow at EOM.

Parameters: `DESCRIPTOR_FIFO_DEPTH=8, SRAM_ADDR_WIDTH=16, TLP_HEADER_SNAPSHOT_BYTES=16`.

| port | dir | width | meaning |
|---|---|---|---|
| axi_aclk | in | 1 | datapath clock |
| axi_aresetn | in | 1 | datapath reset |
| descriptor_push | in | 1 | from context_table (push) |
| desc_base_addr | in | 16 | from context_table |
| desc_payload_len | in | 13 | from context_table |
| desc_source_eid | in | 8 | from context_table |
| desc_dest_eid | in | 8 | from context_table |
| desc_tag_owner | in | 1 | from context_table |
| desc_message_tag | in | 3 | from context_table |
| desc_message_type | in | 7 | from context_table |
| desc_final_seq | in | 2 | from context_table |
| desc_context_id | in | 4 | from context_table |
| desc_completion_status | in | 3 | from context_table |
| desc_requester_id | in | 16 | from context_table |
| desc_routing_type | in | 3 | from context_table |
| desc_first_header | in | 128 | from context_table |
| desc_last_header | in | 128 | from context_table |
| descriptor_pop | in | 1 | from regfile (via cdc): retire oldest |
| descriptor_valid | out | 1 | queue non-empty (oldest valid) — to axi_rd_payload + regfile |
| descriptor_full | out | 1 | queue full — to context_table + regfile |
| descriptor_count | out | 4 | occupancy (STATUS / DESC body) |
| descriptor_ready_pulse | out | 1 | 1-cycle on successful push (→ irq descriptor_ready) |
| rd_base_addr | out | 16 | oldest descriptor payload base (→ axi_rd_payload) |
| rd_payload_len | out | 13 | oldest descriptor payload len (→ axi_rd_payload) |
| rd_source_eid | out | 8 | oldest descriptor key (→ regfile DESC) |
| rd_dest_eid | out | 8 | oldest descriptor key (→ regfile DESC) |
| rd_tag_owner | out | 1 | oldest descriptor key (→ regfile DESC) |
| rd_message_tag | out | 3 | oldest descriptor key (→ regfile DESC) |
| rd_message_type | out | 7 | oldest descriptor type (→ regfile DESC) |
| rd_context_id | out | 4 | oldest descriptor context id (→ regfile DESC) |
| rd_completion_status | out | 3 | oldest descriptor status (→ regfile DESC) |
| rd_requester_id | out | 16 | oldest descriptor requester_id (→ regfile DESC body) |
| rd_routing_type | out | 3 | oldest descriptor routing (→ regfile DESC body) |
| rd_first_header | out | 128 | oldest descriptor first header (→ regfile DESC body) |
| rd_last_header | out | 128 | oldest descriptor last header (→ regfile DESC body) |

### 1.6 mctp_assembler_v3_axi_rd_payload  (FM_AXI_READ + axi_read_fsm)

AXI4 read slave for firmware payload access. One SRAM read per R beat; RLAST on
the final ARLEN beat; SLVERR for out-of-window or no-descriptor reads unless
`raw_sram_debug_read_enable`. Drives the **top SRAM read port** directly and the
top `s_axi_r*` outputs.

Parameters: `AXI_ADDR_WIDTH=16, AXI_DATA_WIDTH=256, SRAM_ADDR_WIDTH=16,
RRESP_OKAY=2'd0, RRESP_SLVERR=2'd2, AXSIZE_32B=3'd5, AXBURST_INCR=2'd1`.

| port | dir | width | meaning |
|---|---|---|---|
| axi_aclk | in | 1 | datapath clock |
| axi_aresetn | in | 1 | datapath reset |
| s_axi_araddr | in | 16 | AR address (32B aligned) |
| s_axi_arlen | in | 8 | ARLEN (beats-1) |
| s_axi_arsize | in | 3 | ARSIZE (must be 5) |
| s_axi_arburst | in | 2 | ARBURST (must be INCR) |
| s_axi_arvalid | in | 1 | AR valid |
| s_axi_arready | out | 1 | AR ready |
| s_axi_rdata | out | 256 | R data beat |
| s_axi_rresp | out | 2 | R response (OKAY/SLVERR) |
| s_axi_rlast | out | 1 | final R beat (`beat_index == arlen`) |
| s_axi_rvalid | out | 1 | R valid |
| s_axi_rready | in | 1 | R ready |
| descriptor_valid | in | 1 | from descriptor_queue (descriptor present) |
| rd_base_addr | in | 16 | from descriptor_queue (window base) |
| rd_payload_len | in | 13 | from descriptor_queue (window length) |
| cfg_raw_sram_debug_read_enable | in | 1 | CONTROL bit (via cdc) |
| descriptor_pop_o | out | 1 | retire descriptor after final read beat (→ regfile/queue) |
| sram_rd_req_valid | out | 1 | top SRAM read req valid |
| sram_rd_req_ready | in | 1 | top SRAM read req ready |
| sram_rd_req_addr | out | 16 | 32B-aligned read word address |
| sram_rd_rsp_valid | in | 1 | top SRAM read rsp valid |
| sram_rd_rsp_ready | out | 1 | top SRAM read rsp ready |
| sram_rd_rsp_data | in | 256 | top SRAM read rsp data |
| sram_rd_rsp_error | in | 1 | top SRAM read rsp error |
| axi_read_busy | out | 1 | STATUS.axi_read_busy |
| sram_read_busy | out | 1 | STATUS.sram_read_busy |
| read_error_pulse | out | 1 | 1-cycle SLVERR event (→ irq axi_read_error) |
| axi_rd_state | out | 4 | DEBUG_CTX.axi_rd_state |
| sram_read_state | out | 4 | DEBUG_CTX.sram_read_state |

### 1.7 mctp_assembler_v3_apb_regfile  (registers + interrupts + error_handling)

APB4 control/status/interrupt/counter/descriptor/debug register file in the `pclk`
domain. Owns `prdata/pready/pslverr` and `irq`. Receives config writes (drives the
`cfg_*` to cdc_sync) and observes status/event signals **already synchronized into
pclk by cdc_sync** (regfile itself does no CDC). W1C interrupts; counter_clear;
descriptor_pop / soft_reset / counter_clear command strobes go out via cdc_sync.

Parameters: `CONTEXT_COUNT=15, BASELINE_MTU_BYTES=64` (+ APB addr/data widths 16/32/4).

| port | dir | width | meaning |
|---|---|---|---|
| pclk | in | 1 | APB clock |
| presetn | in | 1 | APB reset, active-low |
| paddr | in | 16 | APB address |
| psel | in | 1 | APB select |
| penable | in | 1 | APB enable |
| pwrite | in | 1 | APB write |
| pwdata | in | 32 | APB write data |
| pstrb | in | 4 | APB byte strobes |
| prdata | out | 32 | APB read data |
| pready | out | 1 | APB ready |
| pslverr | out | 1 | APB error (illegal/unsupported access) |
| irq_o | out | 1 | combined level interrupt (→ top `irq`) |
| cfg_enable | out | 1 | CONTROL.enable → cdc |
| cfg_drop_when_disabled | out | 1 | CONTROL.drop_when_disabled → cdc |
| cfg_dest_filter_enable | out | 1 | CONTROL.dest_filter_enable → cdc |
| cfg_accept_broadcast_eid | out | 1 | CONTROL.accept_broadcast_eid → cdc |
| cfg_accept_null_eid | out | 1 | CONTROL.accept_null_eid → cdc |
| cfg_raw_sram_debug_read_enable | out | 1 | CONTROL.raw_sram_debug_read_enable → cdc |
| cfg_local_eid | out | 8 | CONTROL.local_eid → cdc |
| cfg_debug_context_select | out | 8 | CONTROL.debug_context_select → cdc |
| cfg_tu_bytes | out | 13 | CFG_TU.transmission_unit_bytes → cdc |
| cfg_max_message_bytes | out | 13 | CFG_TU.max_message_bytes → cdc |
| cfg_timeout_cycles | out | 24 | CFG_TIMEOUT → cdc |
| cfg_sram_base | out | 16 | SRAM_BASE → cdc |
| cfg_sram_limit | out | 16 | SRAM_LIMIT → cdc |
| cmd_soft_reset | out | 1 | CONTROL.soft_reset pulse → cdc |
| cmd_descriptor_pop | out | 1 | CONTROL.descriptor_pop pulse → cdc |
| cmd_counter_clear | out | 1 | CONTROL.counter_clear pulse → cdc |
| evt_descriptor_ready | in | 1 | descriptor_ready event (pclk, from cdc) |
| evt_packet_drop | in | 1 | packet_drop event (pclk, from cdc) |
| evt_assembly_drop | in | 1 | assembly_drop event (pclk, from cdc) |
| evt_context_timeout | in | 1 | context_timeout event (pclk, from cdc) |
| evt_sram_overflow | in | 1 | sram_overflow event (pclk, from cdc) |
| evt_descriptor_queue_full | in | 1 | descriptor_queue_full event (pclk, from cdc) |
| evt_axi_write_malformed | in | 1 | malformed-TLP event (pclk, from cdc) |
| evt_axi_read_error | in | 1 | axi_read_error event (pclk, from cdc) |
| evt_fatal_internal_error | in | 1 | fatal event (pclk, from cdc) |
| sts_descriptor_available | in | 1 | STATUS bit (pclk, from cdc) |
| sts_descriptor_queue_full | in | 1 | STATUS bit (pclk, from cdc) |
| sts_active_context_count | in | 6 | STATUS field (pclk, from cdc) |
| sts_context_active_any | in | 1 | STATUS bit (pclk, from cdc) |
| sts_context_error_any | in | 1 | STATUS bit (pclk, from cdc) |
| sts_ingress_busy | in | 1 | STATUS bit (pclk, from cdc) |
| sts_axi_read_busy | in | 1 | STATUS bit (pclk, from cdc) |
| sts_sram_write_busy | in | 1 | STATUS bit (pclk, from cdc) |
| sts_sram_read_busy | in | 1 | STATUS bit (pclk, from cdc) |
| sts_last_drop_class | in | 2 | STATUS.last_drop_class (pclk, from cdc) |
| sts_last_drop_reason | in | 6 | STATUS.last_drop_reason (pclk, from cdc) |
| sts_last_error_context_id | in | 4 | STATUS.last_error_context_id (pclk, from cdc) |
| cnt_block_in | in | 32 | counter read value for the selected counter index (pclk, from cdc) |
| ctx_state_in | in | 32 | selected CTX_STATE word (pclk, from cdc) |
| desc_word_in | in | 32 | selected DESC_VALID/body word (pclk, from cdc) |
| debug_ctx_in | in | 32 | DEBUG_CTX mirror word (pclk, from cdc) |

> Counter/CTX/DESC/DEBUG read banks are wide; cdc_sync presents them to the regfile
> as already-synchronized 32-bit read words selected by the APB address (handshake/
> gray multi-bit crossing inside cdc_sync). The regfile address-decodes and muxes
> these into `prdata` per the `registers.register_list` offsets (CONTROL=0x000,
> CFG_TU=0x004, CFG_TIMEOUT=0x008, SRAM_BASE=0x00C, SRAM_LIMIT=0x010, STATUS=0x020,
> INTR_RAW=0x100, INTR_ENABLE=0x104, INTR_STATUS=0x108, INTR_CLEAR=0x10C,
> CNT base=0x200, DESC base=0x300, DEBUG_CTX=0x380, CTX_STATE base=0x400 stride 0x40).

### 1.8 mctp_assembler_v3_cdc_sync  (cdc_requirements.crossings + synchronizers)

Explicit CDC between `pclk` (APB/config/commands) and `axi_aclk` (datapath
status/events/counters). 2-FF level synchronizers for single-bit flags; pulse
synchronizers for command/event strobes; req/ack (or gray) handshake for multi-bit
counter/descriptor/ctx read words. The regfile is the single owner of register
storage; cdc_sync only moves bits between domains.

Parameters: `SRAM_ADDR_WIDTH=16` (+ widths fixed by signals).

| port | dir | width | meaning |
|---|---|---|---|
| axi_aclk | in | 1 | datapath clock |
| axi_aresetn | in | 1 | datapath reset |
| pclk | in | 1 | APB clock |
| presetn | in | 1 | APB reset |
| **pclk→axi (config, level)** | | | from regfile cfg_* → datapath cfg_* |
| cfg_enable_p | in | 1 | regfile CONTROL.enable |
| cfg_drop_when_disabled_p | in | 1 | regfile |
| cfg_dest_filter_enable_p | in | 1 | regfile |
| cfg_accept_broadcast_eid_p | in | 1 | regfile |
| cfg_accept_null_eid_p | in | 1 | regfile |
| cfg_raw_sram_debug_read_enable_p | in | 1 | regfile |
| cfg_local_eid_p | in | 8 | regfile |
| cfg_debug_context_select_p | in | 8 | regfile |
| cfg_tu_bytes_p | in | 13 | regfile |
| cfg_max_message_bytes_p | in | 13 | regfile |
| cfg_timeout_cycles_p | in | 24 | regfile |
| cfg_sram_base_p | in | 16 | regfile |
| cfg_sram_limit_p | in | 16 | regfile |
| cfg_enable_a … cfg_sram_limit_a | out | (same widths) | synchronized into axi_aclk → datapath consumers |
| **pclk→axi (command pulses)** | | | |
| cmd_soft_reset_p | in | 1 | regfile pulse |
| cmd_descriptor_pop_p | in | 1 | regfile pulse |
| cmd_counter_clear_p | in | 1 | regfile pulse |
| cmd_soft_reset_a | out | 1 | pulse into axi_aclk |
| cmd_descriptor_pop_a | out | 1 | pulse into axi_aclk (→ ctx + descriptor_queue) |
| cmd_counter_clear_a | out | 1 | pulse into axi_aclk |
| **axi→pclk (event pulses)** | | | from datapath → regfile evt_* |
| evt_descriptor_ready_a | in | 1 | descriptor_queue.descriptor_ready_pulse |
| evt_packet_drop_a | in | 1 | context_table.packet_drop_pulse |
| evt_assembly_drop_a | in | 1 | context_table.assembly_drop_pulse |
| evt_context_timeout_a | in | 1 | context_table.timeout_pulse |
| evt_sram_overflow_a | in | 1 | context_table.sram_overflow_pulse |
| evt_descriptor_queue_full_a | in | 1 | descriptor_queue.descriptor_full (edge) |
| evt_axi_write_malformed_a | in | 1 | ingress/parser malformed (from packet_drop_reason) |
| evt_axi_read_error_a | in | 1 | axi_rd_payload.read_error_pulse |
| evt_fatal_internal_error_a | in | 1 | reserved fatal |
| evt_*_p | out | 1 each | synchronized into pclk → regfile |
| **axi→pclk (status, level)** | | | datapath STATUS → regfile sts_* |
| sts_* _a | in | (per §1.7 sts widths) | datapath status levels |
| sts_* _p | out | (same) | synchronized into pclk → regfile |
| **axi→pclk (multi-bit read words)** | | | |
| cnt_block_a | in | 32 | datapath counter value (selected) |
| ctx_state_a | in | 32 | selected CTX_STATE word |
| desc_word_a | in | 32 | selected DESC word |
| debug_ctx_a | in | 32 | DEBUG_CTX word |
| cnt_block_p / ctx_state_p / desc_word_p / debug_ctx_p | out | 32 each | gray/handshake-synced into pclk → regfile |

> The lead may bundle the wide read words behind a small address/select strobe
> driven by the regfile; the contract only requires that every multi-bit value
> crossing domains goes through a handshake/gray synchronizer (no live capture).

---

## 2. Top-level datapath wiring map (every inter-module wire named)

All datapath wires are in the `axi_aclk` domain unless noted. Wire names below are
the canonical top-level net names the lead declares in `mctp_assembler_v3.sv`.

### 2.1 Write/assembly path

```
s_axi_aw*/w*/b*  ─▶ u_ingress
u_ingress  ──(FIXED beat stream)──▶ u_pcie_vdm_parser
    tlp_beat_valid, tlp_beat_data[255:0], tlp_beat_strb[31:0], tlp_beat_last,
    tlp_accept, tlp_byte_count[12:0]
u_pcie_vdm_parser ──▶ u_mctp_decoder
    vdm_valid, vdm_word[255:0], vdm_payload_offset[4:0], vdm_payload_bytes[12:0],
    vdm_first_header[127:0], vdm_last_header[127:0], vdm_requester_id[15:0],
    vdm_routing_type[2:0], vdm_payload_word[255:0], vdm_payload_strb[31:0],
    vdm_drop_valid, vdm_drop_reason[5:0]
u_mctp_decoder ──▶ u_context_table
    frag_valid, frag_source_eid[7:0], frag_dest_eid[7:0], frag_tag_owner,
    frag_message_tag[2:0], frag_packet_seq[1:0], frag_som, frag_eom,
    frag_message_type[6:0], frag_ic, frag_assembly_key[11:0],
    frag_payload_word[255:0], frag_payload_strb[31:0], frag_payload_bytes[12:0],
    frag_first_header[127:0], frag_last_header[127:0],
    mctp_drop_valid, mctp_drop_reason[5:0]
    (requester_id/routing forwarded alongside for the descriptor)
u_context_table ──(payload write req, handshaked)──▶ u_sram_packer
    pack_wr_valid, pack_wr_ready, pack_wr_data[255:0], pack_wr_strb[31:0],
    pack_wr_addr[15:0], pack_wr_bytes[12:0]
u_context_table ──(descriptor push, on EOM)──▶ u_descriptor_queue
    descriptor_push, desc_base_addr[15:0], desc_payload_len[12:0],
    desc_source_eid[7:0], desc_dest_eid[7:0], desc_tag_owner, desc_message_tag[2:0],
    desc_message_type[6:0], desc_final_seq[1:0], desc_context_id[3:0],
    desc_completion_status[2:0], desc_requester_id[15:0], desc_routing_type[2:0],
    desc_first_header[127:0], desc_last_header[127:0]
u_descriptor_queue.descriptor_full ──▶ u_context_table.descriptor_full
u_sram_packer ──▶ TOP SRAM WRITE PORT
    sram_wr_valid (=sram_wr_valid_o), sram_wr_ready, sram_wr_addr[15:0],
    sram_wr_data[255:0], sram_wr_strb[31:0]
```

### 2.2 Read path

```
s_axi_ar*/r*  ─▶ u_axi_rd_payload
u_descriptor_queue ──(oldest descriptor window)──▶ u_axi_rd_payload
    descriptor_valid, rd_base_addr[15:0], rd_payload_len[12:0]
u_axi_rd_payload ──▶ TOP SRAM READ PORT
    sram_rd_req_valid, sram_rd_req_ready, sram_rd_req_addr[15:0],
    sram_rd_rsp_valid, sram_rd_rsp_ready, sram_rd_rsp_data[255:0], sram_rd_rsp_error
u_axi_rd_payload.descriptor_pop_o ──▶ (OR with cdc cmd_descriptor_pop_a) ──▶
    u_descriptor_queue.descriptor_pop
u_axi_rd_payload drives TOP s_axi_rdata/rresp/rlast/rvalid; s_axi_arready
```

> No dedicated SRAM arbiter module: the write port is owned solely by `u_sram_packer`
> and the read port solely by `u_axi_rd_payload` (the SSOT exposes them as two
> independent top ports; single outstanding write + single outstanding read; write
> traffic has logical priority by construction). The scratch `sram_arbiter` is NOT
> reproduced.

### 2.3 Control/status path (APB ↔ datapath via cdc_sync)

```
TOP paddr/psel/penable/pwrite/pwdata/pstrb  ─▶ u_apb_regfile (pclk)
u_apb_regfile drives TOP prdata/pready/pslverr and TOP irq (=irq_o)

u_apb_regfile.cfg_*  ─▶ u_cdc_sync.cfg_*_p ─▶ u_cdc_sync.cfg_*_a ─▶
    cfg_enable/drop_when_disabled/sram_base/sram_limit/max_message_bytes/timeout
      → u_context_table
    cfg_tu_bytes → u_pcie_vdm_parser
    cfg_dest_filter_enable/local_eid/accept_broadcast_eid/accept_null_eid
      → u_mctp_decoder
    cfg_raw_sram_debug_read_enable → u_axi_rd_payload
    cfg_debug_context_select → u_context_table

u_apb_regfile.cmd_soft_reset/descriptor_pop/counter_clear ─▶ u_cdc_sync (pulse) ─▶
    cmd_descriptor_pop_a → u_context_table + u_descriptor_queue (OR with rd pop)
    cmd_soft_reset_a → all datapath modules (soft clear)
    cmd_counter_clear_a → counter logic

datapath event pulses ─▶ u_cdc_sync (axi→pclk pulse) ─▶ u_apb_regfile.evt_*:
    u_context_table.packet_drop_pulse     → evt_packet_drop
    u_context_table.assembly_drop_pulse   → evt_assembly_drop
    u_context_table.timeout_pulse         → evt_context_timeout
    u_context_table.sram_overflow_pulse   → evt_sram_overflow
    u_descriptor_queue.descriptor_ready_pulse → evt_descriptor_ready
    u_descriptor_queue.descriptor_full    → evt_descriptor_queue_full
    u_axi_rd_payload.read_error_pulse     → evt_axi_read_error
    (malformed-TLP)                       → evt_axi_write_malformed

datapath status levels ─▶ u_cdc_sync (axi→pclk level) ─▶ u_apb_regfile.sts_*:
    last_drop_class (= u_context_table.drop_class_o → TOP last_drop_class),
    last_drop_reason, active_context_count, context_active_any, context_error_any,
    descriptor_available(=descriptor_valid), descriptor_queue_full(=descriptor_full),
    ingress_busy, axi_read_busy, sram_write_busy, sram_read_busy,
    last_error_context_id

datapath counter/ctx/desc/debug read words ─▶ u_cdc_sync (handshake/gray) ─▶
    u_apb_regfile.cnt_block_in / ctx_state_in / desc_word_in / debug_ctx_in
```

---

## 3. Module → FL transaction / equivalence-goal mapping

Each module must satisfy the `module_equivalence` goal whose `rtl_observed` are the
ports above and whose `fl_expected` is `FunctionalModel.apply` of the listed
transaction(s).

| module | FL transaction(s) / FSM | equivalence goal source_ref |
|---|---|---|
| axi_wr_ingress (done) | FM_INGEST_TLP + cycle_model.handshake_rules | (already proven) |
| pcie_vdm_parser | **FM_DECODE_VDM**; features.vdm_decode | sub_modules.…_pcie_vdm_parser.module_equivalence |
| mctp_decoder | **FM_DECODE_MCTP**; features.mctp_decode | sub_modules.…_mctp_decoder.module_equivalence |
| context_table | **FM_ALLOC_CONTEXT + FM_APPEND** + the 6 `fsm.context_fsm` transitions (IDLE→ASSEMBLING, IDLE→DONE_WAIT, ASSEMBLING→ASSEMBLING, ASSEMBLING→DONE_WAIT, ASSEMBLING→ERROR, DONE_WAIT→IDLE) + interleave isolation by key | sub_modules.…_context_table.module_equivalence + fsm.context_fsm |
| sram_packer | **FM_PACK_SRAM**; features.payload_pack | sub_modules.…_sram_packer.module_equivalence |
| descriptor_queue | **FM_PUBLISH_DESCRIPTOR**; memory.instances.descriptor_fifo | sub_modules.…_descriptor_queue.module_equivalence |
| axi_rd_payload | **FM_AXI_READ** + fsm.axi_read_fsm | sub_modules.…_axi_rd_payload.module_equivalence + fsm.axi_read_fsm |
| apb_regfile | registers.register_list + interrupts + error_handling (register/interrupt observables, W1C, counters, descriptor readout) | sub_modules.…_apb_regfile.module_equivalence |
| cdc_sync | cdc_requirements.crossings + synchronizers (clock-domain crossing correctness) | sub_modules.…_cdc_sync.module_equivalence |

Cross-module invariants every author must preserve (function_model.invariants):
no SRAM write before accept; never write header/pad/digest as payload; packet
drops mutate nothing; assembly drops abort exactly the affected context; no
descriptor before EOM; earlier packet-drop wins over later assembly-drop
(drop-priority §4).

---

## 4. Scoreboard-observed top outputs (from rtl_contract.json output_map) + which module drives each

The scoreboard observes these TOP ports. Each must be driven by exactly the module
shown, then connected straight to the top output by the lead.

### 4.1 Top output port → driving module

| top output | width | driving module | rtl_contract output_rule / note |
|---|---|---|---|
| s_axi_awready | 1 | axi_wr_ingress | handshake |
| s_axi_wready | 1 | axi_wr_ingress | handshake |
| s_axi_bresp | 2 | axi_wr_ingress | `bresp_next = BRESP_OKAY` |
| s_axi_bvalid | 1 | axi_wr_ingress | handshake |
| s_axi_arready | 1 | axi_rd_payload | handshake |
| s_axi_rdata | 256 | axi_rd_payload | SRAM read data, unmodified |
| s_axi_rresp | 2 | axi_rd_payload | `rresp_next = SLVERR if (out_of_window or (no_descriptor and !raw_sram_debug_read_enable)) else OKAY` |
| s_axi_rlast | 1 | axi_rd_payload | `rlast_next = (beat_index == arlen)` |
| s_axi_rvalid | 1 | axi_rd_payload | handshake |
| prdata | 32 | apb_regfile | register read mux |
| pready | 1 | apb_regfile | APB access-phase complete |
| pslverr | 1 | apb_regfile | illegal/unsupported APB access |
| sram_wr_valid | 1 | sram_packer (`sram_wr_valid_o`) | `sram_wr_valid = (payload_bytes > 0)` |
| sram_wr_addr | 16 | sram_packer | `sram_wr_addr = ctx_payload_next_addr & ~31` |
| sram_wr_data | 256 | sram_packer | packed payload word |
| sram_wr_strb | 32 | sram_packer | `((1<<payload_bytes)-1) << (ctx_payload_next_addr & 31)` |
| sram_rd_req_valid | 1 | axi_rd_payload | one req per R beat |
| sram_rd_req_addr | 16 | axi_rd_payload | 32B-aligned read word |
| sram_rd_rsp_ready | 1 | axi_rd_payload | `special_outputs.ready_output` |
| irq | 1 | apb_regfile (`irq_o`) | `(intr_raw & intr_enable) != 0` after CDC |

`special_outputs.output_valid = sram_wr_valid`; `ready_output = sram_rd_rsp_ready`.
Descriptor observables (`registers.descriptor + descriptor_queue`) are read via
APB DESC_VALID/body words sourced from `u_descriptor_queue` through cdc_sync.

### 4.2 Drop-reason code space (single 6-bit encoding shared by all drop sources)

Use one enum so `last_drop_reason` (STATUS[23:18]) and per-reason counters agree.
Priority order is the SSOT `error_handling.propagation` order; the **first matching
class wins** and is resolved in `u_context_table` (which sees the upstream
`packet_drop_reason_in` and can only add later/lower-priority classes):

1 PD_DISABLED_DROP_MODE · 2 PD_MALFORMED_TLP · 3 PD_UNSUPPORTED_VDM ·
4 PD_BAD_MCTP_HEADER · 5 PD_BAD_PAD_OR_ALIGNMENT · 6 PD_DEST_EID_REJECT ·
7 PD_UNEXPECTED_MIDDLE_END · 8 PD_BAD_OR_EXPIRED_TAG · 9 AD_DUPLICATE_SOM ·
10 AD_SEQUENCE_MISMATCH · 11 AD_MESSAGE_OVERFLOW · 12 AD_SRAM_OVERFLOW ·
13 AD_DESCRIPTOR_FULL · 14 AD_TIMEOUT (0 = none).

Interrupt bit map (INTR_RAW_STATUS[8:0], SSOT interrupts.sources): 0 descriptor_ready,
1 packet_drop, 2 assembly_drop, 3 context_timeout, 4 sram_overflow,
5 descriptor_queue_full, 6 axi_write_malformed, 7 axi_read_error,
8 fatal_internal_error.

---

## 5. Authoring order + no-conflict guarantee

Each of the 8 pending modules is a **separate `.sv` file**; no module edits another
module or the top. The lead owns `mctp_assembler_v3.sv` wiring only. Recommended
authoring order (upstream → downstream so each consumer's input contract is fixed
first; all 8 can also proceed fully in parallel since interfaces are frozen here):

1. `mctp_assembler_v3_pcie_vdm_parser.sv` — consume FIXED ingress beat stream → VDM out.
2. `mctp_assembler_v3_mctp_decoder.sv` — VDM in → decoded fragment (§0.1) out.
3. `mctp_assembler_v3_context_table.sv` — fragment in → pack req + descriptor push + drops/STATUS.
4. `mctp_assembler_v3_sram_packer.sv` — pack req in → TOP sram_wr_* out.
5. `mctp_assembler_v3_descriptor_queue.sv` — descriptor push in → descriptor_valid/window/full + DESC readout.
6. `mctp_assembler_v3_axi_rd_payload.sv` — AR + descriptor window in → TOP s_axi_r* + sram_rd_* out.
7. `mctp_assembler_v3_apb_regfile.sv` — APB in → prdata/pready/pslverr/irq + cfg_*/cmd_* out (consumes pclk-synced sts_/evt_/read words).
8. `mctp_assembler_v3_cdc_sync.sv` — bridges all pclk↔axi_aclk crossings.

Key frozen inter-module wires (the ones with conflict risk):
- ingress→parser: the 6-signal beat stream (FIXED, §1.0).
- parser→decoder: `vdm_*` bundle (§1.1 outputs).
- decoder→context_table: `frag_*` bundle (§0.1 / §1.2 outputs).
- context_table→sram_packer: `pack_wr_*` handshake (§1.3/§1.4).
- context_table→descriptor_queue: `descriptor_push`+`desc_*` bundle (§1.3/§1.5).
- descriptor_queue→axi_rd_payload: `descriptor_valid`+`rd_base_addr`+`rd_payload_len`.
- regfile↔cdc_sync↔datapath: `cfg_*` / `cmd_*` / `evt_*` / `sts_*` / read-word bundles (§1.7/§1.8).

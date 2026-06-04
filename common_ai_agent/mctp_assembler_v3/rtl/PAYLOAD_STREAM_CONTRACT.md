# PAYLOAD_STREAM_CONTRACT.md — multi-beat payload-stream datapath (FROZEN)

Status: FROZEN interface spec. Author NO RTL from this file's prose alone — build
exactly to the port tables and the packing contract below. This ADDS a new
payload-beat-stream path (`pl_beat_*`) alongside the existing
`vdm_*`/`frag_*` metadata path. The proven 104/104 decode/accept/drop/count/
descriptor logic is untouched; the new path only delivers the *real payload
bytes* (up to 4096 B) into SRAM with no holes.

Grounded against the real RTL (read 2026-06-04):
`mctp_assembler_v3_{axi_wr_ingress,pcie_vdm_parser,mctp_decoder,context_table,
sram_packer,axi_rd_payload}.sv`, `mctp_assembler_v3.sv`,
`INTEGRATION_CONTRACT.md`, the SSOT `yaml/mctp_assembler_v3.ssot.yaml`
(io_list + function_model), and the TB SRAM model in `tb/cocotb/mctp_stimulus.py`.

---

## 0. The bug this fixes (evidence)

`mctp_assembler_v3_pcie_vdm_parser.sv:270-271`:

```
vdm_payload_word <= multi_beat ? last_beat_q : first_beat_q;
vdm_payload_strb <= multi_beat ? last_strb_q : first_strb_q;
```

The parser forwards exactly ONE 256-bit beat per accepted TLP. `context_table`
then clamps the byte count written to one 32-byte word
(`alloc_pack_bytes`/`append_pack_bytes`, `context_table.sv:272-282`) so the
sram_packer's "≤32 B per 256-bit word" invariant holds
(`sram_packer.sv:54-73,113-123`). Net effect: at most 32 real payload bytes per
fragment reach SRAM, while `frag_payload_bytes` / `ctx_payload_cnt` /
`desc_payload_len` carry the full *logical* count (64..4096). The descriptor
read window `[rd_base_addr, rd_base_addr+rd_payload_len)`
(`descriptor_queue.sv:217-218`, `axi_rd_payload.sv:96-103`) therefore reads back
mostly-zero SRAM for any payload > 32 B.

The ingress already streams every beat
(`axi_wr_ingress.sv:159-174`: `tlp_beat_valid/data/strb/last` per W beat). Only
the parser drops them. This contract adds a parallel beat-passthrough that the
context_table accumulates into SRAM word-by-word.

---

## 1. Byte/address model (must be internalized before reading the port tables)

- AXI beat = 256 bit = 32 B. Lane N of a beat = `data[8*N +: 8]` (little-endian
  byte N). SSOT/INTEGRATION_CONTRACT `tlp[N]` convention.
- The 16 B Non-Flit PCIe/VDM header occupies TLP bytes 0..15 = beat-0
  `data[127:0]`.
- **Message payload** (what must land in SRAM) starts at TLP byte
  `PAYLOAD_OFFSET = 16` and runs for `payload_bytes = tlp_byte_count - 16 -
  pad_len` bytes. Message byte 0 = the SOM body byte (IC+message_type) at TLP
  byte 16 = beat-0 `data[135:128]` = beat-0 lane 16. (Confirmed by
  `mctp_stimulus.build_vdm_tlp`: body byte at `SOM_BODY_OFFSET=16`, then caller
  payload; `expected_payload_bytes = 16+1+len(payload) - 16 - pad`.)
- SRAM is byte-addressable from the consumer's view; the packer writes 32 B
  words. Message byte i of a context lands at SRAM byte address
  `ctx_payload_base_addr + i` (SSOT: "byte i at base+i; no holes across
  fragments", lines 910,949). This is what makes readback a flat
  `received == driven_payload` compare.
- `pad_len` (0..3) trailing bytes are NOT payload and are NOT written.

### 1.1 Header strip + lane-0 alignment (the one non-trivial transform)

The parser must turn the raw beat stream (whose beat 0 begins with a 16 B
header) into a **lane-0-aligned payload-byte stream** (`pl_beat_data` byte 0 =
message byte 0).

Chosen scheme — **fixed 16-byte down-shift, carry across beats (rolling shift)**.
`PAYLOAD_OFFSET` is a compile-time constant 16, so the realignment is a constant
16-lane (128-bit) right shift, identical every beat. Concretely, maintain a
1-beat carry register `pl_carry[127:0]` (= the high 16 bytes of the previous raw
beat) and emit, per raw beat n:

```
aligned_beat[255:0] = { raw_beat[n][127:0], pl_carry[127:0] }   // 16-byte down-shift
pl_carry            = raw_beat[n][255:128]
```

- Beat 0: the low 16 B of `raw_beat[0]` are the header (discarded); `pl_carry`
  starts at the header-stripped high half, i.e. seed `pl_carry =
  raw_beat[0][255:128]` and emit NOTHING for the raw-beat-0 cycle until beat 1,
  OR (equivalent, preferred) treat the 16 B down-shift as: the FIRST emitted
  aligned beat is available one raw beat later. The simplest correct
  formulation, and the REQUIRED one:

  > For raw beat 0, capture `pl_carry = raw_beat0[255:128]` (payload bytes
  > 0..15, the upper half of beat 0). Do not emit an aligned beat yet. For each
  > subsequent raw beat n≥1, emit `aligned = { raw_beat[n][127:0],
  > pl_carry }` and update `pl_carry = raw_beat[n][255:128]`. On the LAST raw
  > beat, after emitting the combined beat, if there are still carried bytes
  > remaining (payload length not consumed), emit one FINAL aligned beat
  > `{ 128'h0, pl_carry }` carrying the residual high-half bytes.

  This makes every emitted `pl_beat_data` lane-0-aligned with message byte
  `32*k` at lane 0 of emitted beat k. Because the shift constant is the same
  (16) for every beat, there is no per-beat variable shifter — just a fixed
  128-bit splice plus a 128-bit carry register.

- **Single-beat TLP** (≤32 B payload incl. the rarer ≤16 B case): beat 0 is also
  the last beat. `pl_carry = raw_beat0[255:128]` (payload bytes 0..15), and the
  final-residual emit produces ONE aligned beat `{128'h0, pl_carry}`. The
  emitted beat therefore carries up to 16 payload bytes in lanes 0..15. (Payloads
  of 17..32 B in a single-beat TLP would need bytes from lane 16+; but a
  single-beat TLP can hold at most 32-16 = **16 payload bytes**, so one aligned
  residual beat always suffices for the single-beat case. Larger payloads are
  always multi-beat.) This is exactly the count the existing single-beat tests
  drive (SC_SINGLE: `_payload(31)` → 32 payload bytes total... see note below).

  NOTE on SC_SINGLE 32 B: `_payload(31)` + SOM body byte = 32 message bytes, but
  the TLP is 16(hdr)+32 = 48 B = **2 beats** (beat0 = hdr+payload[0:16],
  beat1 = payload[16:32]). So "32 B single-beat" is a 2-beat TLP at the AXI
  level; the down-shift carry handles it as: carry from beat0 = payload[0:16],
  emit on beat1 `{raw_beat1[127:0]=payload[16:32], carry=payload[0:16]}` =
  full 32 payload bytes in lanes 0..31 of ONE aligned beat, then residual
  emit is empty (carry after beat1 = raw_beat1[255:128] = zero/pad, length
  exhausted). Result: a single 32-B `pl_beat` — identical placement to today's
  `vdm_payload_word` upper-half path. Regression-safe (see §6).

### 1.2 `pl_beat_bytes` / strobe per emitted aligned beat

`pl_beat_bytes[5:0]` = number of valid payload bytes in THIS emitted aligned
beat (1..32). `pl_beat_strb[31:0]` = `(1<<pl_beat_bytes)-1` (contiguous LSB run;
always lane-0 aligned because the stream is lane-0 aligned). The parser computes
the remaining payload length from `payload_bytes_raw` (already in the parser,
`pcie_vdm_parser.sv:160`) and decrements by 32 per emitted full beat; the final
emitted beat carries the remainder (`payload_bytes mod 32`, or 32 if exact).
`pl_beat_first` marks emitted beat k==0; `pl_beat_last` marks the final emitted
beat (the one whose running total reaches `payload_bytes`).

---

## 2. Parser (`mctp_assembler_v3_pcie_vdm_parser`) — ADD outputs

The existing `vdm_*`, `packet_drop_*`, `last_decoded_vdm`, `parser_state`
outputs are UNCHANGED. `vdm_payload_word`/`vdm_payload_strb` STAY (the decoder
still forwards them; harmless). ADD a lane-0-aligned payload beat stream, emitted
ONLY for an accepted clean VDM (`vdm_valid` path), never on a drop.

| signal | dir | width | meaning |
|---|---|---|---|
| `pl_beat_valid` | out reg | 1 | 1-cycle pulse per emitted aligned payload beat |
| `pl_beat_data`  | out reg | 256 | lane-0-aligned payload bytes; message byte `32*k` at lane 0 |
| `pl_beat_strb`  | out reg | 32 | `(1<<pl_beat_bytes)-1`, contiguous from lane 0 |
| `pl_beat_bytes` | out reg | 6 | valid payload bytes this beat (1..32) |
| `pl_beat_first` | out reg | 1 | first emitted beat of this packet's payload |
| `pl_beat_last`  | out reg | 1 | final emitted beat of this packet's payload |

Emission rules:
- Drive `pl_beat_valid=0` on a packet drop and when `payload_bytes==0` (a
  legal header-only / zero-payload append: emit NO beats; `frag_payload_bytes=0`
  path in context_table already writes nothing).
- The beat stream for one packet is emitted as a contiguous run aligned to the
  same `tlp_accept`-triggered decode the existing `vdm_valid` uses. Because the
  raw beats were already captured (parser currently only latches first/last; it
  must now retain enough to replay — see §2.1), the aligned stream can be
  produced either (a) by replaying buffered beats after `tlp_accept`, or (b) by
  streaming live during `COLLECT_W` and gating the emit by the post-`tlp_accept`
  accept decision. **Chosen: (a) replay from a beat buffer**, so the emit stays
  perfectly ordered with `vdm_valid`/`frag_valid` and a drop cleanly suppresses
  the whole stream. The downstream context_table consumes ≤1 `pl_beat` per cycle
  and back-pressures via `pl_beat_ready` (see §4), so the replay FSM must honor
  ready.

### 2.1 Parser internal buffer (implementation note, not a port)

Today the parser keeps only `first_beat_q`/`last_beat_q`. To replay the full
payload it must buffer all beats of the current TLP. Max TLP = 4096 payload + 16
hdr + pad ⇒ ≤ 130 beats of 256 bit. Use a small FIFO/array
(`MAX_TLP_BYTES/32 + 1` entries) written during `COLLECT_W`-equivalent capture
(on `tlp_beat_valid`) and read out during the post-accept replay. The header
strip + 16-byte carry shift (§1.1) is applied during replay. (This buffer is
internal; do not expose it.) Reset/replay state on `tlp_accept` like the existing
`first_beat_seen`/`multi_beat` (`pcie_vdm_parser.sv:203-206`).

### 2.2 New parser handshake input

| signal | dir | width | meaning |
|---|---|---|---|
| `pl_beat_ready` | in wire | 1 | downstream (decoder→context_table) accepts this beat |

`pl_beat_valid` is held until `pl_beat_valid & pl_beat_ready` (standard
valid/ready). The replay FSM advances one buffered aligned beat per accepted
handshake.

---

## 3. Decoder (`mctp_assembler_v3_mctp_decoder`) — ADD pass-through

The decoder's `frag_*` metadata path is UNCHANGED. ADD a registered (or wired)
pass-through of the payload beat stream, GATED so that a packet the decoder drops
(`PD_BAD_MCTP_HEADER`/`PD_DEST_EID_REJECT`, or any upstream drop) emits NO
payload beats. Because the decoder asserts `frag_valid` exactly when it accepts
(`mctp_decoder.sv:183-186`), the gate is: forward `pl_beat_*` for a packet only
on the accept path.

Simplest correct realization (avoids a second buffer in the decoder): the
decoder is a 1-cycle stage and the payload stream is multi-cycle, so the decoder
should pass the beat stream through combinationally with a 1-cycle-registered
ACCEPT/DROP qualifier latched at `vdm_valid`:

| signal | dir | width | meaning |
|---|---|---|---|
| `pl_beat_valid_in` | in wire | 1 | from parser `pl_beat_valid` |
| `pl_beat_data_in`  | in wire | 256 | from parser |
| `pl_beat_strb_in`  | in wire | 32 | from parser |
| `pl_beat_bytes_in` | in wire | 6 | from parser |
| `pl_beat_first_in` | in wire | 1 | from parser |
| `pl_beat_last_in`  | in wire | 1 | from parser |
| `pl_beat_ready_out` | out wire | 1 | to parser `pl_beat_ready` |
| `pl_beat_valid` | out wire/reg | 1 | to context_table, = `pl_beat_valid_in & accept_q` |
| `pl_beat_data`  | out wire/reg | 256 | to context_table |
| `pl_beat_strb`  | out wire/reg | 32 | to context_table |
| `pl_beat_bytes` | out wire/reg | 6 | to context_table |
| `pl_beat_first` | out wire/reg | 1 | to context_table |
| `pl_beat_last`  | out wire/reg | 1 | to context_table |
| `pl_beat_ready` | in wire | 1 | from context_table |

`accept_q`: a 1-bit reg set when the decoder asserts `frag_valid` (clean accept)
and cleared on the packet's `pl_beat_last` handshake. While `accept_q==0` (drop
or idle) the decoder asserts `pl_beat_ready_out=1` (drain/discard any stray
parser beats for a dropped packet — the parser will not emit them since the
parser only emits on its own clean `vdm_valid`, but draining keeps the handshake
deadlock-free) and drives `pl_beat_valid=0` downstream. When `accept_q==1`,
forward valid/data/strb/bytes/first/last and connect ready straight through:
`pl_beat_ready_out = pl_beat_ready`.

> Ordering guarantee: the parser emits `vdm_valid` and the payload stream from
> the SAME post-`tlp_accept` decode, and the decoder registers `accept_q` from
> `vdm_valid`→`frag_valid` on the next cycle. The parser's replay FSM (§2.1)
> must not present `pl_beat_first` before the cycle the decoder can latch
> `accept_q`. REQUIRED timing: parser holds the first payload beat valid until
> `pl_beat_ready`, and the decoder raises ready only after `accept_q` is set
> (1 cycle after `vdm_valid`). This naturally serializes metadata-before-payload
> and prevents a payload beat from racing ahead of its accept decision. Workers
> MUST implement this 1-cycle gate; it is the only cross-stage timing subtlety.

---

## 4. context_table (`mctp_assembler_v3_context_table`) — ADD payload-beat consumer

This is the heart of the change. The existing fragment-metadata FSM
(alloc/append/drop/descriptor) is UNCHANGED. We REPLACE the single-beat
`pack_wr_*` emission (today driven once per fragment from
`frag_payload_word`/`alloc_pack_bytes`/`append_pack_bytes`,
`context_table.sv:533-539,619-625`) with a **multi-beat pack engine** fed by the
new `pl_beat_*` stream, while keeping `pack_wr_*` to the sram_packer BYTE-FOR-BYTE
contract-identical (`§1.4`: `sram_wr_addr = addr & ~31`, `strb =
((1<<bytes)-1)<<(addr&31)`).

### 4.1 New inputs

| signal | dir | width | meaning |
|---|---|---|---|
| `pl_beat_valid` | in wire | 1 | aligned payload beat valid (from decoder) |
| `pl_beat_data`  | in wire | 256 | lane-0-aligned payload bytes |
| `pl_beat_strb`  | in wire | 32 | contiguous LSB run, `pl_beat_bytes` lanes |
| `pl_beat_bytes` | in wire | 6 | valid bytes this beat (1..32) |
| `pl_beat_first` | in wire | 1 | first beat of a packet's payload |
| `pl_beat_last`  | in wire | 1 | final beat of a packet's payload |
| `pl_beat_ready` | out reg/wire | 1 | back-pressure to decoder/parser |

### 4.2 Per-context partial-word pointer (REUSE existing state)

The context already holds, per slot:
- `ctx_payload_next[idx]` (16b) = `ctx_payload_next_addr`, the running BYTE write
  pointer (SSOT `ctx_payload_next_addr += payload_bytes`).
- `ctx_partial_lane[idx]` (5b) = `ctx_partial_next_lane` (SSOT `(lane + bytes)
  % 32`).

These are exactly the no-hole accumulation state. Today they advance once per
fragment by `frag_payload_bytes`; in the new design they advance per ACCEPTED
PACK WORD (≤32 B) as the beats stream in. The byte pointer is the single source
of truth for the SRAM address: **message byte i ⇒ SRAM address
`ctx_payload_base + i`**, computed incrementally as `ctx_payload_next`.

### 4.3 The pack engine (no-hole, ≤32 B/word, across beats AND fragments)

For each accepted `pl_beat` (when `pl_beat_valid & pl_beat_ready`), the engine
must split it into pack-writes that never cross a 32 B word boundary and never
exceed 32 B (the sram_packer invariant). Because the stream is lane-0 aligned but
the SRAM write pointer `ctx_payload_next` may sit at an arbitrary lane
`L = ctx_payload_next[4:0]` (carried over from the previous fragment's partial
tail), one 32-B `pl_beat` can straddle TWO physical SRAM words:

```
L          = ctx_payload_next[4:0]            // current partial-word start lane (0..31)
room       = 32 - L                           // bytes left in the current word (1..32)
chunk0     = min(pl_beat_bytes, room)         // bytes that go into the current word
chunk1     = pl_beat_bytes - chunk0           // remainder into the NEXT word (0..)
```

Emit:
1. **pack-write A** at byte address `ctx_payload_next`, `pack_wr_bytes = chunk0`,
   `pack_wr_data = pl_beat_data << (8*L)` (shift the lane-0 bytes up to lane L),
   `pack_wr_strb = ((1<<chunk0)-1) << L`. The sram_packer then computes
   `word_addr = (ctx_payload_next) & ~31` and `lane_mask = ((1<<chunk0)-1) << L`
   — exactly its frozen rule. Advance `ctx_payload_next += chunk0`.
2. If `chunk1 > 0`: **pack-write B** at the new `ctx_payload_next` (now 32-B
   aligned, lane 0), `pack_wr_bytes = chunk1`,
   `pack_wr_data = pl_beat_data >> (8*chunk0)` (the bytes that didn't fit),
   `pack_wr_strb = (1<<chunk1)-1`. Advance `ctx_payload_next += chunk1`.

Update `ctx_partial_lane[idx] = ctx_payload_next[4:0]` after the beat.

**No holes**: byte i always writes to `ctx_payload_base + i`; consecutive beats
and consecutive fragments share the byte counter, so a fragment whose payload
ends mid-word (lane L≠0) is continued by the next fragment's first beat at the
SAME word/lane — the sram_packer's strobe-masked write commits only the new
lanes, and the TB SRAM model (and real SRAM with byte-enables) merges them
(`mctp_stimulus.py:503-506` commits per strobed lane; no read-modify-write
needed because each lane is written exactly once across the whole message).

**≤32 B invariant**: `chunk0 ≤ room ≤ 32` and `chunk1 ≤ 32`; the sram_packer's
`pack_bytes_over` guard (`sram_packer.sv:123`) therefore never fires.

### 4.4 Two pack-writes per beat vs one outstanding sram_packer beat

The sram_packer accepts ONE outstanding write and back-pressures via
`pack_wr_ready` (`sram_packer.sv:138`). A straddling `pl_beat` needs up to TWO
sequential pack-writes (A then B). So the pack engine is a small per-beat FSM:

```
S_BEAT_IDLE : pl_beat_ready = (pack engine idle) ; on accepted pl_beat, compute
              chunk0/chunk1, issue pack-write A (if chunk0>0), go S_WRA.
S_WRA       : hold pack_wr_valid until pack_wr_ready; on accept, if chunk1>0
              issue pack-write B and go S_WRB else go S_BEAT_IDLE.
S_WRB       : hold pack_wr_valid until pack_wr_ready; on accept go S_BEAT_IDLE.
```

`pl_beat_ready` is asserted only in `S_BEAT_IDLE` (engine ready for a new beat).
This serializes A/B behind `pack_wr_ready` and keeps the ≤1-outstanding packer
contract intact. Because `chunk0` is almost always 32 (lane 0 fragments) or the
fragment tail, the common case is a single pack-write per beat.

### 4.5 Which context does a beat belong to?

The metadata fragment (`frag_valid`) for a packet is accepted (alloc on SOM /
append on match) the cycle BEFORE its payload beats stream in (decoder registers
metadata, then payload replays). Capture the resolved context index for the
in-flight payload stream into a small `stream_ctx_id` reg latched at the
fragment-accept decision (`free_idx` on alloc, `match_idx` on append). The pack
engine uses `stream_ctx_id` to index `ctx_payload_next`/`ctx_partial_lane`. A
beat with `pl_beat_first` re-latches nothing (it was already latched at accept);
`pl_beat_last` marks the stream end. (Only ONE payload stream is in flight at a
time because the parser emits one packet's payload contiguously and the decoder
gates one packet at a time — no interleave at the beat level.)

### 4.6 Descriptor / count interaction (UNCHANGED semantics)

`ctx_payload_cnt` (logical byte count) and `desc_payload_len` keep accumulating
`frag_payload_bytes` exactly as today (`context_table.sv:519,606-607,645-646`).
The descriptor is still pushed at the metadata boundary (single-packet SOM+EOM,
or append EOM). The ONLY change is that by the time the descriptor is read back,
the real bytes are actually in SRAM. Backpressure note: the descriptor push on
EOM must not race ahead of the last pack-write. Because the EOM fragment's
metadata is accepted before its payload streams, but the descriptor is consumed
only by a later AXI read, the pack engine will have drained all beats long before
readback in practice. For strictness, gate `descriptor_push` on EOM behind the
pack engine being idle (`S_BEAT_IDLE` and `pl_beat_last` consumed) — RECOMMENDED
but the existing many-cycle settle (tests use 80..400 cycles) makes it
non-blocking. Workers SHOULD add this gate to be water-tight.

---

## 5. Top wiring (`mctp_assembler_v3.sv`) — ADD nets, no module reorg

Add nets and connect parser→decoder→context_table:

```
wire         pl_beat_valid_pd;   // parser → decoder
wire [255:0] pl_beat_data_pd;
wire [31:0]  pl_beat_strb_pd;
wire [5:0]   pl_beat_bytes_pd;
wire         pl_beat_first_pd;
wire         pl_beat_last_pd;
wire         pl_beat_ready_pd;   // decoder → parser

wire         pl_beat_valid_dc;   // decoder → context_table
wire [255:0] pl_beat_data_dc;
wire [31:0]  pl_beat_strb_dc;
wire [5:0]   pl_beat_bytes_dc;
wire         pl_beat_first_dc;
wire         pl_beat_last_dc;
wire         pl_beat_ready_dc;   // context_table → decoder
```

- parser `.pl_beat_*(... _pd)`, `.pl_beat_ready(pl_beat_ready_pd)`.
- decoder `.pl_beat_*_in(... _pd)`, `.pl_beat_ready_out(pl_beat_ready_pd)`,
  `.pl_beat_*(... _dc)`, `.pl_beat_ready(pl_beat_ready_dc)`.
- context_table `.pl_beat_*(... _dc)`, `.pl_beat_ready(pl_beat_ready_dc)`.

No change to the `pack_wr_*`/`sram_wr_*`/`sram_rd_*`/descriptor wiring.

### 5.1 Modules that need NO change (confirmed)

- **`axi_wr_ingress`**: already streams every beat
  (`tlp_beat_valid/data/strb/last`, lines 159-174). No change.
- **`sram_packer`**: already does one strobe-masked 32-B word write per
  `pack_wr_*` request with the exact `addr & ~31` / `((1<<bytes)-1)<<(addr&31)`
  rule and per-lane data gating (lines 54-138). It needs NO change: the new pack
  engine simply issues MORE `pack_wr_*` requests (one or two per payload beat)
  to the SAME interface. Its ≤32 B guard stays satisfied (§4.3). No change.
- **`axi_rd_payload`**: reads SRAM word-by-word over the descriptor window
  `[rd_base_addr, rd_base_addr+rd_payload_len)` (lines 82-110, 184-212). Since
  the bytes are now actually present at `base+i`, readback is correct with NO
  change.
- **`descriptor_queue`**: carries `desc_base_addr (=ctx_payload_base)` /
  `desc_payload_len (=ctx_payload_cnt)` unchanged (lines 116-117, 217-218). No
  change.

---

## 6. Regression safety (104/104 must stay green)

- `vdm_*`/`frag_*` metadata path, drop classification, alloc/append/seq/overflow/
  timeout/descriptor logic: byte-for-byte unchanged. The new path only ADDS the
  `pl_beat_*` engine and REPLACES the per-fragment single `pack_wr_*` emission
  with the multi-beat engine that produces IDENTICAL writes for the ≤32-B case.
- **SC_SINGLE / single-beat equivalence**: for a packet whose payload ≤32 B, the
  pack engine emits exactly one pack-write at `ctx_payload_next` with
  `pack_wr_bytes = payload_bytes`, `pack_wr_strb = ((1<<payload_bytes)-1) << L`,
  `pack_wr_data = payload << 8*L`. With `L=0` (fresh alloc) this is identical to
  today's `alloc_pack_bytes` path. The SRAM contents and `sram_wr_*` waveform
  match the current behavior for all existing ≤32-B rows. (§1.1 shows the
  32-B "single" case resolves to one aligned 32-B beat ⇒ one pack-write.)
- The `pack_bytes_over` sticky guard in sram_packer must remain UNSET in all
  rows (chunks are ≤32 by construction) — a built-in regression sentinel.
- Existing readback rows (SC_FW_READ n_beats=1, SC_READ_FSM n_beats=2,
  SC_MAX_TU) keep their current pass criteria; the NEW full-content assertions
  (§7) are added, not substituted.

---

## 7. Verification plan — write→readback full-content compare

The TB already has everything needed: a flat byte `sram_mem` serviced by the
SRAM write BFM (`DatapathMonitor.run`, `mctp_stimulus.py:491-506`, commits
per strobed lane), the SRAM read BFM + `axi_read(...)` which returns the full
reconstructed payload as `result["data"]` (`mctp_stimulus.py:600-636`), and the
descriptor read window already equals `[ctx_payload_base, +payload_len)`.

### 7.1 Address mapping for the readback (so bytes line up)

- Configure `sram_base = 0`, `sram_limit = 0xFFFF`, `max_message_bytes = 4096`,
  `tu = 4096` (or 64 for the small case), `timeout_cycles` large (disabled is
  fine: 0xFFFFFF).
- A fresh context allocates `ctx_payload_base = sram_alloc_ptr` (= `sram_base`
  for the first context after reset). So message byte i ⇒ `sram_mem[base + i]`.
- After assembly, `descriptor_valid=1`, `rd_base_addr = base`, `rd_payload_len =
  payload_byte_count`.
- Read `n_beats = ceil(payload_byte_count / 32)` starting at `araddr = base`.
  `axi_read` returns `data` of length `n_beats*32`; compare `data[:payload_len]`
  to the driven message-payload bytes.

### 7.2 Driven-vs-readback reference bytes

The driven message payload = the SOM body byte ++ caller payload bytes, i.e. the
TLP bytes `[16 : 16+payload_len)` of the SOM packet, then for each appended
fragment its `[16 : 16+frag_payload_len)`, concatenated in arrival order. Build
the golden vector in the test as:

```
golden = bytearray()
for pkt in packets_in_order:
    tlp = build_vdm_tlp(pkt)
    plen = expected_payload_bytes(pkt)      # = tlp_byte_count-16-pad
    golden += tlp[16 : 16+plen]
# readback:
rd = await axi_read(dut, araddr=base, n_beats=ceil(len(golden)/32), sram_mem=sram)
assert rd["data"][:len(golden)] == bytes(golden)
```

### 7.3 Concrete test cases (add to `test_mctp_datapath.py`)

1. **SC_RB_64 (single packet, 64 B, 2 payload-bearing beats)**:
   `Packet(som=1,eom=1, payload=_payload(63))` ⇒ payload_len = 1+63 = 64.
   TLP = 16+64 = 80 B = 3 AXI beats (hdr+pl[0:16], pl[16:48], pl[48:64]).
   Expect: `sram_wr_count >= 2` (today it is 1 → this FAILS pre-fix, PASSES
   post-fix), `descriptor_valid=1`, and `axi_read(base,2).data[:64] == golden`.
   Pre-fix this readback compare FAILS (bytes 32..63 are zero) — it is the
   direct exposure of the bug and the acceptance gate for the fix.

2. **SC_RB_FRAG (two fragments, no-hole across fragment boundary)**: a SOM
   fragment contributing a non-32-aligned tail then an EOM fragment, e.g.
   `Packet(som=1,eom=0,seq=0, payload=_payload(40))` (payload_len=41, ends at
   lane 41%32 = 9) then `Packet(som=0,eom=1,seq=1, payload=_payload(22,seed=5))`
   (payload_len=23). Total = 64 B. The second fragment's first byte MUST land at
   `base+41` (lane 9 of word 1), proving no-hole packing across fragments.
   `axi_read(base, ceil(64/32)=2).data[:64] == golden`.

3. **SC_RB_4096 (max payload)**: reuse `pmax` (`_payload(4095)` ⇒ 4096 B). Read
   `n_beats = 128` from `base=0`; assert `data[:4096] == golden`. This is the
   real "assembles up to 4096 B with no holes" proof (today SC_MAX_TU only
   checks `ctx_payload_count_sel>=4096`, never the bytes).

4. **SC_RB_SINGLE_REGRESSION (≤32 B equivalence)**: `Packet(payload=_payload(31))`
   ⇒ 32 B. `axi_read(base,1).data[:32] == golden` AND the `sram_wr_*` waveform /
   count equals the pre-fix single-write behavior (one 32-B word write). Guards
   the regression in §6.

All four use the EXISTING `axi_read`, `DatapathMonitor(sram_mem=...)`,
`build_vdm_tlp`, `expected_payload_bytes`, `_payload` helpers — no TB
infrastructure change required, only new test bodies + a `golden` compare.

### 7.4 Pass criteria summary

- SC_RB_64 / SC_RB_FRAG / SC_RB_4096: `rd["data"][:plen] == golden` AND
  `rresp == 0 (OKAY)` AND `rlast_count == 1`.
- SC_RB_SINGLE_REGRESSION: byte compare passes AND single-write behavior
  unchanged.
- The full 104/104 suite stays green (metadata path untouched).
- sram_packer `pack_bytes_overflow` sticky flag stays 0 in every row.

---

## 8. Frozen port-addition summary (for the 3 RTL workers)

| module | ADD ports |
|---|---|
| `pcie_vdm_parser` | out `pl_beat_valid`, out `pl_beat_data[255:0]`, out `pl_beat_strb[31:0]`, out `pl_beat_bytes[5:0]`, out `pl_beat_first`, out `pl_beat_last`; in `pl_beat_ready` |
| `mctp_decoder` | in `pl_beat_valid_in`, `pl_beat_data_in[255:0]`, `pl_beat_strb_in[31:0]`, `pl_beat_bytes_in[5:0]`, `pl_beat_first_in`, `pl_beat_last_in`; out `pl_beat_ready_out`; out `pl_beat_valid`, `pl_beat_data[255:0]`, `pl_beat_strb[31:0]`, `pl_beat_bytes[5:0]`, `pl_beat_first`, `pl_beat_last`; in `pl_beat_ready` |
| `context_table` | in `pl_beat_valid`, `pl_beat_data[255:0]`, `pl_beat_strb[31:0]`, `pl_beat_bytes[5:0]`, `pl_beat_first`, `pl_beat_last`; out `pl_beat_ready` |
| `axi_wr_ingress` | NONE (no change) |
| `sram_packer` | NONE (no change) |
| `axi_rd_payload` | NONE (no change) |
| `descriptor_queue` | NONE (no change) |
| `mctp_assembler_v3` (top) | ADD the `pl_beat_*_pd` and `pl_beat_*_dc` wire bundles (§5) |

Work split that avoids conflict:
- Worker P: parser beat buffer + header-strip/carry-shift + `pl_beat_*` emit FSM.
- Worker D: decoder `pl_beat_*` accept-gated pass-through + `accept_q`.
- Worker C: context_table pack engine (§4.3/§4.4/§4.5) replacing the single
  `pack_wr_*` emit, REUSING `ctx_payload_next`/`ctx_partial_lane`.
- Top wiring (§5) is a 3-line-per-bundle add; assign to Worker C or the integrator.

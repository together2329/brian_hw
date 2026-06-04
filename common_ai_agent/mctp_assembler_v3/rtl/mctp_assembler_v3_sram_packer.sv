// mctp_assembler_v3_sram_packer.sv
// 256-bit SRAM payload packer for the MCTP assembler.
// Implements function_model.FM_PACK_SRAM (payload_pack_write):
//   - consumes the per-context payload write request handshake (pack_wr_*)
//     produced by mctp_assembler_v3_context_table, which already holds the
//     per-context partial-word pack buffer / next-byte-lane state
//   - drives the TOP SRAM write port directly (this module owns sram_wr_*),
//     emitting 32B-aligned 256-bit word writes whose strobe marks only the
//     payload byte lanes with NO-HOLE contiguous packing into the word
//   - registers a single outstanding write beat so it is held across
//     sram_wr_ready backpressure, and back-pressures the context_table via
//     pack_wr_ready while a beat is in flight
//
// FROZEN interface per rtl/INTEGRATION_CONTRACT.md §1.4. The combinational
// output rules use payload_bytes := pack_wr_bytes and
// ctx_payload_next_addr := pack_wr_addr (the byte start address the
// context_table supplies for this request):
//   sram_wr_valid = (payload_bytes > 0)
//   sram_wr_addr  = ctx_payload_next_addr & ~31
//   sram_wr_strb  = ((1<<payload_bytes)-1) << (ctx_payload_next_addr & 31)
`default_nettype none
module mctp_assembler_v3_sram_packer #(
    parameter integer SRAM_ADDR_WIDTH = 16,
    parameter integer SRAM_DATA_WIDTH = 256,
    parameter integer AXI_STRB_WIDTH  = 32
) (
    input  wire                        axi_aclk,
    input  wire                        axi_aresetn,
    // payload write request from context_table (handshaked)
    input  wire                        pack_wr_valid,
    output wire                        pack_wr_ready,
    input  wire [SRAM_DATA_WIDTH-1:0]  pack_wr_data,
    input  wire [AXI_STRB_WIDTH-1:0]   pack_wr_strb,
    input  wire [SRAM_ADDR_WIDTH-1:0]  pack_wr_addr,   // ctx_payload_next_addr
    input  wire [12:0]                 pack_wr_bytes,  // payload_bytes this request
    // TOP SRAM write port (write side owns sram_wr_*)
    output reg                         sram_wr_valid_o,
    input  wire                        sram_wr_ready,
    output reg  [SRAM_ADDR_WIDTH-1:0]  sram_wr_addr,
    output reg  [SRAM_DATA_WIDTH-1:0]  sram_wr_data,
    output reg  [AXI_STRB_WIDTH-1:0]   sram_wr_strb,
    // observable partial-word lane (DEBUG_CTX) and STATUS busy
    output wire [4:0]                  pack_next_lane,
    output wire                        sram_write_busy
);

    // ------------------------------------------------------------------
    // Combinational FM_PACK_SRAM output rules over the incoming request.
    // payload_bytes := pack_wr_bytes ; ctx_payload_next_addr := pack_wr_addr.
    // The byte lane within the 256-bit word is the low 5 bits of the byte
    // start address; the contiguous (no-hole) payload lane mask is the
    // payload_bytes-wide run shifted up to that lane.
    // ------------------------------------------------------------------
    wire [12:0]                payload_bytes = pack_wr_bytes;
    wire [4:0]                 lane_offset   = pack_wr_addr[4:0];      // addr & 31
    wire [SRAM_ADDR_WIDTH-1:0] word_addr     = pack_wr_addr & ~{{(SRAM_ADDR_WIDTH-5){1'b0}}, 5'd31};

    // contiguous (no-hole) byte-lane mask, exactly the FM output rule:
    //   ((1<<payload_bytes)-1) << (ctx_payload_next_addr & 31)
    // One 256-bit SRAM word holds at most AXI_STRB_WIDTH (=32) byte lanes, so a
    // single request's run is bounded to 0..32. The mask is built robustly over
    // that full range, comparing the WHOLE 13-bit payload_bytes (never [5:0],
    // which would alias e.g. 33->1) so an out-of-contract pack_wr_bytes>32 can
    // never silently collapse to a wrong short run:
    //   payload_bytes == 0          -> empty mask (avoids the prior `>> 32` UB)
    //   payload_bytes >= STRB_WIDTH  -> all lanes set (saturate, not wrap)
    //   else                        -> (1<<payload_bytes)-1  (here pb<32 so the
    //                                  [5:0] shift amount equals pb exactly)
    wire [AXI_STRB_WIDTH-1:0]  lane_run  =
        (payload_bytes == 13'd0)              ? {AXI_STRB_WIDTH{1'b0}} :
        (payload_bytes >= AXI_STRB_WIDTH[12:0]) ? {AXI_STRB_WIDTH{1'b1}} :
        (({{(AXI_STRB_WIDTH-1){1'b0}}, 1'b1} << payload_bytes[5:0]) - {{(AXI_STRB_WIDTH-1){1'b0}}, 1'b1});
    wire [AXI_STRB_WIDTH-1:0]  lane_mask = lane_run << lane_offset;

    // Per-lane byte gate on the write data: keep only the payload bytes the
    // context_table marks valid in pack_wr_strb (the partial-word lanes for
    // this request) and zero the untouched lanes of the 256-bit word.
    // Explicit unroll — AXI_STRB_WIDTH is fixed at 32 (policy: no for loops).
    wire [SRAM_DATA_WIDTH-1:0] data_gated;
    assign data_gated[  7:  0] = pack_wr_strb[ 0] ? pack_wr_data[  7:  0] : 8'h00;
    assign data_gated[ 15:  8] = pack_wr_strb[ 1] ? pack_wr_data[ 15:  8] : 8'h00;
    assign data_gated[ 23: 16] = pack_wr_strb[ 2] ? pack_wr_data[ 23: 16] : 8'h00;
    assign data_gated[ 31: 24] = pack_wr_strb[ 3] ? pack_wr_data[ 31: 24] : 8'h00;
    assign data_gated[ 39: 32] = pack_wr_strb[ 4] ? pack_wr_data[ 39: 32] : 8'h00;
    assign data_gated[ 47: 40] = pack_wr_strb[ 5] ? pack_wr_data[ 47: 40] : 8'h00;
    assign data_gated[ 55: 48] = pack_wr_strb[ 6] ? pack_wr_data[ 55: 48] : 8'h00;
    assign data_gated[ 63: 56] = pack_wr_strb[ 7] ? pack_wr_data[ 63: 56] : 8'h00;
    assign data_gated[ 71: 64] = pack_wr_strb[ 8] ? pack_wr_data[ 71: 64] : 8'h00;
    assign data_gated[ 79: 72] = pack_wr_strb[ 9] ? pack_wr_data[ 79: 72] : 8'h00;
    assign data_gated[ 87: 80] = pack_wr_strb[10] ? pack_wr_data[ 87: 80] : 8'h00;
    assign data_gated[ 95: 88] = pack_wr_strb[11] ? pack_wr_data[ 95: 88] : 8'h00;
    assign data_gated[103: 96] = pack_wr_strb[12] ? pack_wr_data[103: 96] : 8'h00;
    assign data_gated[111:104] = pack_wr_strb[13] ? pack_wr_data[111:104] : 8'h00;
    assign data_gated[119:112] = pack_wr_strb[14] ? pack_wr_data[119:112] : 8'h00;
    assign data_gated[127:120] = pack_wr_strb[15] ? pack_wr_data[127:120] : 8'h00;
    assign data_gated[135:128] = pack_wr_strb[16] ? pack_wr_data[135:128] : 8'h00;
    assign data_gated[143:136] = pack_wr_strb[17] ? pack_wr_data[143:136] : 8'h00;
    assign data_gated[151:144] = pack_wr_strb[18] ? pack_wr_data[151:144] : 8'h00;
    assign data_gated[159:152] = pack_wr_strb[19] ? pack_wr_data[159:152] : 8'h00;
    assign data_gated[167:160] = pack_wr_strb[20] ? pack_wr_data[167:160] : 8'h00;
    assign data_gated[175:168] = pack_wr_strb[21] ? pack_wr_data[175:168] : 8'h00;
    assign data_gated[183:176] = pack_wr_strb[22] ? pack_wr_data[183:176] : 8'h00;
    assign data_gated[191:184] = pack_wr_strb[23] ? pack_wr_data[191:184] : 8'h00;
    assign data_gated[199:192] = pack_wr_strb[24] ? pack_wr_data[199:192] : 8'h00;
    assign data_gated[207:200] = pack_wr_strb[25] ? pack_wr_data[207:200] : 8'h00;
    assign data_gated[215:208] = pack_wr_strb[26] ? pack_wr_data[215:208] : 8'h00;
    assign data_gated[223:216] = pack_wr_strb[27] ? pack_wr_data[223:216] : 8'h00;
    assign data_gated[231:224] = pack_wr_strb[28] ? pack_wr_data[231:224] : 8'h00;
    assign data_gated[239:232] = pack_wr_strb[29] ? pack_wr_data[239:232] : 8'h00;
    assign data_gated[247:240] = pack_wr_strb[30] ? pack_wr_data[247:240] : 8'h00;
    assign data_gated[255:248] = pack_wr_strb[31] ? pack_wr_data[255:248] : 8'h00;

    wire has_bytes = (payload_bytes != 13'd0);          // payload_bytes > 0
    wire req_fire  = pack_wr_valid & pack_wr_ready;     // accepted this cycle

    // Boundary invariant guard (NON-silent): a single 256-bit word write can
    // carry at most AXI_STRB_WIDTH (=32) payload bytes, so the context_table
    // must never present pack_wr_bytes > 32 on an accepted request. lane_run
    // now saturates instead of wrapping, but a violation still means a packing
    // contract break upstream — surface it via a sticky registered debug flag
    // (observable in waves) plus a simulation assertion, rather than letting it
    // pass unnoticed. This is debug-only and does not affect packing behavior.
    wire pack_bytes_over = req_fire & (payload_bytes > AXI_STRB_WIDTH[12:0]);
    reg  pack_bytes_overflow;                            // sticky overflow flag

    // next byte lane in the partial word after this request (mod 32):
    // (ctx_partial_next_lane + payload_bytes) % 32, observed via lane_offset.
    assign pack_next_lane = lane_offset + payload_bytes[4:0];

    // ------------------------------------------------------------------
    // Single-outstanding registered SRAM write beat. The context_table is
    // back-pressured (pack_wr_ready low) while a beat is in flight; a new
    // request is accepted only when the port is idle or completing.
    // ------------------------------------------------------------------
    wire wr_done = sram_wr_valid_o & sram_wr_ready;     // current beat retires

    assign sram_write_busy = sram_wr_valid_o;
    assign pack_wr_ready    = (~sram_wr_valid_o) | sram_wr_ready;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            sram_wr_valid_o    <= 1'b0;
            sram_wr_addr       <= {SRAM_ADDR_WIDTH{1'b0}};
            sram_wr_data       <= {SRAM_DATA_WIDTH{1'b0}};
            sram_wr_strb       <= {AXI_STRB_WIDTH{1'b0}};
            pack_bytes_overflow <= 1'b0;
        end else begin
            if (req_fire & has_bytes) begin
                // launch a 32B-aligned word write for this payload request
                sram_wr_valid_o <= 1'b1;
                sram_wr_addr    <= word_addr;
                sram_wr_data    <= data_gated;
                sram_wr_strb    <= lane_mask;
            end else if (wr_done) begin
                // beat retired and no new request taking its place
                sram_wr_valid_o <= 1'b0;
            end
            // sticky once set: latch any ≤32B-invariant violation for debug
            if (pack_bytes_over) begin
                pack_bytes_overflow <= 1'b1;
            end
        end
    end

`ifndef SYNTHESIS
    // Simulation-only contract check: keeps the boundary invariant from being
    // silent. pack_bytes_over already requires an accepted request (req_fire),
    // so it cannot assert during reset; it intentionally does NOT read
    // axi_aresetn here (that would make the reset a mixed sync/async net).
    // Reads pack_bytes_overflow so the flag is never an unused reg.
    always @(posedge axi_aclk) begin
        if (pack_bytes_over) begin
            $display("[%0t] %m WARNING: pack_wr_bytes=%0d exceeds AXI_STRB_WIDTH=%0d (single-word <=32B invariant violated); lane_run saturated. sticky pack_bytes_overflow=%0b",
                     $time, payload_bytes, AXI_STRB_WIDTH, pack_bytes_overflow);
        end
    end
`endif

endmodule
`default_nettype wire

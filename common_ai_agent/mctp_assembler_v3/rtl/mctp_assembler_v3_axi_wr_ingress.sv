// mctp_assembler_v3_axi_wr_ingress.sv
// AXI4 256-bit write-slave ingress for the MCTP assembler.
// Implements function_model.FM_INGEST_TLP (axi_write_to_tlp_bytes):
//   - AXI4 write handshake (AW / W / B channels) in the axi_aclk domain
//   - legality check: AWSIZE == 5 (32B beats) and AWBURST == INCR
//   - accumulates the TLP byte count from per-beat WSTRB popcount
//   - streams accepted WDATA/WSTRB beats downstream to the PCIe VDM parser
//   - drives BRESP = OKAY and pulses tlp_accept on a legal, in-bounds TLP
`default_nettype none
module mctp_assembler_v3_axi_wr_ingress #(
    parameter integer AXI_ADDR_WIDTH = 16,
    parameter integer AXI_DATA_WIDTH = 256,
    parameter integer AXI_STRB_WIDTH = 32,
    parameter integer MAX_TLP_BYTES  = 4112,
    parameter [1:0]   BRESP_OKAY     = 2'd0,
    parameter [2:0]   AXSIZE_32B     = 3'd5,
    parameter [1:0]   AXBURST_INCR   = 2'd1
) (
    input  wire                        axi_aclk,
    input  wire                        axi_aresetn,
    // AXI4 write address channel
    input  wire [AXI_ADDR_WIDTH-1:0]   s_axi_awaddr,
    input  wire [7:0]                  s_axi_awlen,
    input  wire [2:0]                  s_axi_awsize,
    input  wire [1:0]                  s_axi_awburst,
    input  wire                        s_axi_awvalid,
    output reg                         s_axi_awready,
    // AXI4 write data channel
    input  wire [AXI_DATA_WIDTH-1:0]   s_axi_wdata,
    input  wire [AXI_STRB_WIDTH-1:0]   s_axi_wstrb,
    input  wire                        s_axi_wlast,
    input  wire                        s_axi_wvalid,
    output reg                         s_axi_wready,
    // AXI4 write response channel
    output reg  [1:0]                  s_axi_bresp,
    output reg                         s_axi_bvalid,
    input  wire                        s_axi_bready,
    // downstream TLP beat stream to the PCIe VDM parser
    output reg                         tlp_beat_valid,
    output reg  [AXI_DATA_WIDTH-1:0]   tlp_beat_data,
    output reg  [AXI_STRB_WIDTH-1:0]   tlp_beat_strb,
    output reg                         tlp_beat_last,
    // downstream accept + metadata (qualified by the B handshake)
    output reg                         tlp_accept,
    output reg  [12:0]                 tlp_byte_count,
    output reg                         malformed_tlp_valid,
    output reg  [5:0]                  malformed_tlp_reason
);

    // Ingress write FSM — state names follow SSOT fsm.ingress_fsm exactly so
    // the assembled byte stream is traceable to the specification:
    //   IDLE        : awready high, waiting for an AW beat
    //   ACCEPT_AW   : AW accepted; latch AWSIZE/AWBURST legality, open W channel
    //   COLLECT_W   : accept W beats, accumulate byte count, stream beats out
    //   CHECK_LEGAL : WLAST seen; evaluate beat-count/WSTRB/length legality
    //   EMIT_TLP    : legal TLP — pulse tlp_accept with the assembled byte count
    //   RESP_B      : drive BRESP=OKAY and complete the B handshake
    localparam [2:0] IDLE        = 3'd0;
    localparam [2:0] ACCEPT_AW   = 3'd1;
    localparam [2:0] COLLECT_W   = 3'd2;
    localparam [2:0] CHECK_LEGAL = 3'd3;
    localparam [2:0] EMIT_TLP    = 3'd4;
    localparam [2:0] RESP_B      = 3'd5;

    // AXI4 address/length fields are accepted on the port but not used for
    // legality checks in this ingress (only AWSIZE/AWBURST are checked).
    // The wire below reads them so Verilator does not emit UNUSEDSIGNAL.
    wire _unused_aw = &{s_axi_awaddr, s_axi_awlen};

    reg  [2:0]  state;
    reg         aw_legal;     // latched AWSIZE/AWBURST legality for the burst
    reg         wlast_seen;   // a WLAST beat was observed in this burst
    reg  [12:0] byte_acc;     // running TLP byte count (popcount of WSTRB)
    reg         strb_contig;  // all beats so far satisfy WSTRB contiguity
    reg         tlp_legal;    // CHECK_LEGAL verdict latched for EMIT_TLP

    wire        aw_fire    = s_axi_awvalid & s_axi_awready;
    wire        beat_fire  = s_axi_wvalid  & s_axi_wready;
    // $countones returns a 32-bit signed int; the explicit unsigned'() cast clears
    // the signedness warning and 6'() narrows to 6 bits without truncation warning
    // (pyslang L60: implicit-signedness + truncation 32->6 fixed by explicit casts).
    wire [5:0]  beat_bytes = 6'(unsigned'($countones(s_axi_wstrb))); // 0..32 bytes/beat
    wire        size_ok    = (s_axi_awsize  == AXSIZE_32B);
    wire        burst_ok   = (s_axi_awburst == AXBURST_INCR);
    // WSTRB contiguity (req:128) — earlier beats must be fully strobed; the
    // final beat must be a contiguous run of valid lanes starting at lane 0.
    // A 32-bit value is an LSB-aligned contiguous run iff it is non-zero and
    // (w & (w + 1)) == 0.
    wire        wstrb_all_ones = (s_axi_wstrb == {AXI_STRB_WIDTH{1'b1}});
    wire        wstrb_lsb_run  = (s_axi_wstrb != {AXI_STRB_WIDTH{1'b0}}) &&
                                 ((s_axi_wstrb & (s_axi_wstrb + 32'd1)) == {AXI_STRB_WIDTH{1'b0}});
    wire        beat_contig    = s_axi_wlast ? wstrb_lsb_run : wstrb_all_ones;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            state          <= IDLE;
            s_axi_awready  <= 1'b0;
            s_axi_wready   <= 1'b0;
            s_axi_bvalid   <= 1'b0;
            s_axi_bresp    <= BRESP_OKAY;
            aw_legal       <= 1'b0;
            wlast_seen     <= 1'b0;
            byte_acc       <= 13'd0;
            strb_contig    <= 1'b1;
            tlp_legal      <= 1'b0;
            tlp_beat_valid <= 1'b0;
            tlp_beat_data  <= {AXI_DATA_WIDTH{1'b0}};
            tlp_beat_strb  <= {AXI_STRB_WIDTH{1'b0}};
            tlp_beat_last  <= 1'b0;
            tlp_accept     <= 1'b0;
            tlp_byte_count <= 13'd0;
            malformed_tlp_valid  <= 1'b0;
            malformed_tlp_reason <= 6'd0;
        end else begin
            // single-cycle downstream pulses default low
            tlp_beat_valid <= 1'b0;
            tlp_beat_last  <= 1'b0;
            tlp_accept     <= 1'b0;
            malformed_tlp_valid  <= 1'b0;
            malformed_tlp_reason <= 6'd0;

            case (state)
                // IDLE: hold AWREADY high until an AW beat is accepted.
                IDLE: begin
                    s_axi_awready <= 1'b1;
                    s_axi_bvalid  <= 1'b0;
                    if (aw_fire) begin
                        // IDLE -> ACCEPT_AW : awvalid && awready
                        s_axi_awready <= 1'b0;
                        aw_legal      <= size_ok & burst_ok;
                        wlast_seen    <= 1'b0;
                        byte_acc      <= 13'd0;
                        strb_contig   <= 1'b1;
                        tlp_legal     <= 1'b0;
                        state         <= ACCEPT_AW;
                    end
                end

                // ACCEPT_AW: AWSIZE==5 && AWBURST==INCR opens the W channel;
                // an illegal AW (PD_MALFORMED_TLP) skips straight to RESP_B.
                ACCEPT_AW: begin
                    if (aw_legal) begin
                        // ACCEPT_AW -> COLLECT_W : AWSIZE==5 && AWBURST==INCR
                        s_axi_wready <= 1'b1;
                        state        <= COLLECT_W;
                    end else begin
                        // ACCEPT_AW -> RESP_B : illegal AWSIZE/AWBURST
                        s_axi_bvalid <= 1'b1;
                        s_axi_bresp  <= BRESP_OKAY;
                        tlp_legal    <= 1'b0;
                        malformed_tlp_valid  <= 1'b1;
                        malformed_tlp_reason <= 6'd2;
                        state        <= RESP_B;
                    end
                end

                // COLLECT_W: accept W beats, accumulate byte count, stream each
                // beat downstream; WLAST ends collection.
                COLLECT_W: begin
                    if (beat_fire) begin
                        tlp_beat_valid <= 1'b1;
                        tlp_beat_data  <= s_axi_wdata;
                        tlp_beat_strb  <= s_axi_wstrb;
                        tlp_beat_last  <= s_axi_wlast;
                        byte_acc       <= byte_acc + {7'd0, beat_bytes};
                        strb_contig    <= strb_contig & beat_contig;
                        if (s_axi_wlast) begin
                            // COLLECT_W -> CHECK_LEGAL : wlast && wvalid && wready
                            wlast_seen   <= 1'b1;
                            s_axi_wready <= 1'b0;
                            state        <= CHECK_LEGAL;
                        end
                    end
                end

                // CHECK_LEGAL: evaluate beat-count/WSTRB-contiguity/length legality
                // for the assembled TLP and latch the verdict for EMIT_TLP.
                CHECK_LEGAL: begin
                    tlp_legal    <= aw_legal & wlast_seen & strb_contig &
                                    (byte_acc >= 13'd16) &
                                    (byte_acc <= MAX_TLP_BYTES[12:0]);
                    // both legal and malformed verdicts converge on the B response;
                    // EMIT_TLP performs the downstream accept pulse on the legal path.
                    state        <= EMIT_TLP;
                end

                // EMIT_TLP: raise the B response with the legality verdict latched;
                // the downstream tlp_accept pulse is issued on the B handshake in
                // RESP_B so its timing matches the original ingress contract that
                // the PCIe VDM parser decodes against.
                EMIT_TLP: begin
                    // EMIT_TLP -> RESP_B : TLP bytes emitted to parser
                    s_axi_bvalid   <= 1'b1;
                    s_axi_bresp    <= BRESP_OKAY;
                    malformed_tlp_valid  <= ~tlp_legal;
                    malformed_tlp_reason <= tlp_legal ? 6'd0 : 6'd2;
                    state          <= RESP_B;
                end

                // RESP_B: complete the B handshake, pulse the downstream accept for
                // a legal TLP, and return to IDLE.
                RESP_B: begin
                    if (s_axi_bready) begin
                        // RESP_B -> IDLE : bvalid && bready (OKAY)
                        s_axi_bvalid   <= 1'b0;
                        tlp_accept     <= tlp_legal;
                        tlp_byte_count <= tlp_legal ? byte_acc : 13'd0;
                        tlp_legal      <= 1'b0;
                        s_axi_awready  <= 1'b1;
                        state          <= IDLE;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
`default_nettype wire

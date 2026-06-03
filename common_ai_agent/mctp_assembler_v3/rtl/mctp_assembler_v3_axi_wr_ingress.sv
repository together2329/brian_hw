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
    output reg  [12:0]                 tlp_byte_count
);

    localparam [1:0] S_IDLE = 2'd0;
    localparam [1:0] S_DATA = 2'd1;
    localparam [1:0] S_RESP = 2'd2;

    reg  [1:0]  state;
    reg         aw_legal;     // latched AWSIZE/AWBURST legality for the burst
    reg         wlast_seen;   // a WLAST beat was observed in this burst
    reg  [12:0] byte_acc;     // running TLP byte count (popcount of WSTRB)
    reg         strb_contig;  // all beats so far satisfy WSTRB contiguity

    wire        aw_fire    = s_axi_awvalid & s_axi_awready;
    wire        beat_fire  = s_axi_wvalid  & s_axi_wready;
    wire [5:0]  beat_bytes = $countones(s_axi_wstrb);          // 0..32 bytes/beat
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
            state          <= S_IDLE;
            s_axi_awready  <= 1'b0;
            s_axi_wready   <= 1'b0;
            s_axi_bvalid   <= 1'b0;
            s_axi_bresp    <= BRESP_OKAY;
            aw_legal       <= 1'b0;
            wlast_seen     <= 1'b0;
            byte_acc       <= 13'd0;
            strb_contig    <= 1'b1;
            tlp_beat_valid <= 1'b0;
            tlp_beat_data  <= {AXI_DATA_WIDTH{1'b0}};
            tlp_beat_strb  <= {AXI_STRB_WIDTH{1'b0}};
            tlp_beat_last  <= 1'b0;
            tlp_accept     <= 1'b0;
            tlp_byte_count <= 13'd0;
        end else begin
            // single-cycle downstream pulses default low
            tlp_beat_valid <= 1'b0;
            tlp_beat_last  <= 1'b0;
            tlp_accept     <= 1'b0;

            case (state)
                S_IDLE: begin
                    s_axi_awready <= 1'b1;
                    s_axi_bvalid  <= 1'b0;
                    if (aw_fire) begin
                        s_axi_awready <= 1'b0;
                        s_axi_wready  <= 1'b1;
                        aw_legal      <= size_ok & burst_ok;
                        wlast_seen    <= 1'b0;
                        byte_acc      <= 13'd0;
                        strb_contig   <= 1'b1;
                        state         <= S_DATA;
                    end
                end

                S_DATA: begin
                    if (beat_fire) begin
                        tlp_beat_valid <= 1'b1;
                        tlp_beat_data  <= s_axi_wdata;
                        tlp_beat_strb  <= s_axi_wstrb;
                        tlp_beat_last  <= s_axi_wlast;
                        byte_acc       <= byte_acc + {7'd0, beat_bytes};
                        strb_contig    <= strb_contig & beat_contig;
                        if (s_axi_wlast) begin
                            wlast_seen   <= 1'b1;
                            s_axi_wready <= 1'b0;
                            s_axi_bvalid <= 1'b1;
                            s_axi_bresp  <= BRESP_OKAY;
                            state        <= S_RESP;
                        end
                    end
                end

                S_RESP: begin
                    if (s_axi_bready) begin
                        s_axi_bvalid   <= 1'b0;
                        // accept the TLP downstream only when the burst was legal
                        // and the assembled byte count is within [16, MAX_TLP_BYTES]
                        tlp_accept     <= aw_legal & wlast_seen & strb_contig &
                                          (byte_acc >= 13'd16) &
                                          (byte_acc <= MAX_TLP_BYTES[12:0]);
                        tlp_byte_count <= byte_acc;
                        s_axi_awready  <= 1'b1;
                        state          <= S_IDLE;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
`default_nettype wire

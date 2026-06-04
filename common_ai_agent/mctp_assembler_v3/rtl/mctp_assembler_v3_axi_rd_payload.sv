// mctp_assembler_v3_axi_rd_payload.sv
// AXI4 256-bit read-slave egress for firmware payload access.
// Implements function_model.FM_AXI_READ (firmware_payload_read) and the
// fsm.axi_read_fsm (IDLE -> ACCEPT_AR -> {ISSUE_SRAM_RD,DRIVE_R} -> WAIT_SRAM_RSP
// -> DRIVE_R -> DONE -> IDLE):
//   - AXI4 read handshake (AR / R channels) in the axi_aclk domain
//   - legality / window check: ARSIZE == 5 (32B beats), ARBURST == INCR, and the
//     requested [araddr, araddr+(arlen+1)*32) range fits the descriptor read
//     window [rd_base_addr, rd_base_addr+rd_payload_len) unless debug read enable
//   - one SRAM read request per R beat; rdata returned unmodified to s_axi_rdata
//   - RLAST asserts on the final ARLEN beat (beat_index == arlen)
//   - RRESP = SLVERR for out-of-window or no-descriptor reads unless
//     raw_sram_debug_read_enable; OKAY otherwise
//   - retires the consumed descriptor (descriptor_pop_o) after the final beat
`default_nettype none
module mctp_assembler_v3_axi_rd_payload #(
    parameter integer AXI_ADDR_WIDTH  = 16,
    parameter integer AXI_DATA_WIDTH  = 256,
    parameter integer SRAM_ADDR_WIDTH = 16,
    parameter [1:0]   RRESP_OKAY      = 2'd0,
    parameter [1:0]   RRESP_SLVERR    = 2'd2,
    parameter [2:0]   AXSIZE_32B      = 3'd5,
    parameter [1:0]   AXBURST_INCR    = 2'd1
) (
    input  wire                        axi_aclk,
    input  wire                        axi_aresetn,
    // AXI4 read address channel
    input  wire [AXI_ADDR_WIDTH-1:0]   s_axi_araddr,
    input  wire [7:0]                  s_axi_arlen,
    input  wire [2:0]                  s_axi_arsize,
    input  wire [1:0]                  s_axi_arburst,
    input  wire                        s_axi_arvalid,
    output reg                         s_axi_arready,
    // AXI4 read data channel
    output reg  [AXI_DATA_WIDTH-1:0]   s_axi_rdata,
    output reg  [1:0]                  s_axi_rresp,
    output reg                         s_axi_rlast,
    output reg                         s_axi_rvalid,
    input  wire                        s_axi_rready,
    // descriptor read window (from descriptor_queue: oldest descriptor)
    input  wire                        descriptor_valid,
    input  wire [SRAM_ADDR_WIDTH-1:0]  rd_base_addr,
    input  wire [12:0]                 rd_payload_len,
    // config (from regfile via cdc_sync)
    input  wire                        cfg_raw_sram_debug_read_enable,
    // descriptor retire (to descriptor_queue / regfile)
    output reg                         descriptor_pop_o,
    // top SRAM read port
    output reg                         sram_rd_req_valid,
    input  wire                        sram_rd_req_ready,
    output reg  [SRAM_ADDR_WIDTH-1:0]  sram_rd_req_addr,
    input  wire                        sram_rd_rsp_valid,
    output reg                         sram_rd_rsp_ready,
    input  wire [AXI_DATA_WIDTH-1:0]   sram_rd_rsp_data,
    input  wire                        sram_rd_rsp_error,
    // status / debug
    output reg                         axi_read_busy,
    output reg                         sram_read_busy,
    output reg                         read_error_pulse,
    output reg  [3:0]                  axi_rd_state,
    output reg  [3:0]                  sram_read_state
);

    // axi_read_fsm state encoding (one register, conventional FSM style)
    localparam [3:0] S_IDLE          = 4'd0;
    localparam [3:0] S_ACCEPT_AR     = 4'd1;
    localparam [3:0] S_ISSUE_SRAM_RD = 4'd2;
    localparam [3:0] S_WAIT_SRAM_RSP = 4'd3;
    localparam [3:0] S_DRIVE_R       = 4'd4;
    localparam [3:0] S_DONE          = 4'd5;

    reg [3:0]                  state;
    reg [AXI_ADDR_WIDTH-1:0]   araddr_q;     // latched AR base address
    reg [7:0]                  arlen_q;      // latched ARLEN (beats-1)
    reg                        ar_legal;     // ARSIZE==5 && ARBURST==INCR
    reg [7:0]                  beat_index;   // current R beat index (0..arlen)
    reg                        slverr_q;     // latched SLVERR decision for the burst
    reg [31:0]                 fw_axi_read_beat_count;   // FM state: completed R beats
    reg [31:0]                 fw_axi_read_error_count;  // FM state: SLVERR responses

    // 32B-aligned word address for the current beat: base + beat_index*32.
    wire [AXI_ADDR_WIDTH-1:0]  beat_addr = araddr_q +
        ({{(AXI_ADDR_WIDTH-8){1'b0}}, beat_index} << 5);

    // FM_AXI_READ preconditions evaluated on the accepted AR (ACCEPT_AR state).
    // precondition_0: ARSIZE==5, precondition_1: ARBURST==INCR (latched ar_legal).
    // precondition_2: descriptor visible for the range or raw_sram_debug_read_enable.
    // Window arithmetic uses the full SRAM byte address space so every address
    // bit participates. araddr/rd_base_addr are AXI_ADDR_WIDTH/SRAM_ADDR_WIDTH
    // wide; widen to AXI_ADDR_WIDTH+1 to hold the exclusive end byte without wrap.
    wire [8:0]                 ar_beats   = {1'b0, s_axi_arlen} + 9'd1;        // arlen+1
    wire [13:0]                ar_bytes   = {ar_beats, 5'd0};                  // beats*32
    wire [AXI_ADDR_WIDTH:0]    ar_addr_ext= {1'b0, s_axi_araddr};
    wire [AXI_ADDR_WIDTH:0]    ar_end     = ar_addr_ext +
                                            {{(AXI_ADDR_WIDTH+1-14){1'b0}}, ar_bytes}; // exclusive end byte
    wire [AXI_ADDR_WIDTH:0]    win_base   = {{(AXI_ADDR_WIDTH+1-SRAM_ADDR_WIDTH){1'b0}}, rd_base_addr};
    wire [AXI_ADDR_WIDTH:0]    win_end    = win_base +
                                            {{(AXI_ADDR_WIDTH+1-13){1'b0}}, rd_payload_len};
    wire                       no_descriptor   = ~descriptor_valid;
    // out_of_window: requested byte range escapes the descriptor read window.
    wire                       out_of_window   = (ar_addr_ext < win_base) ||
                                                 (ar_end > win_end) ||
                                                 (rd_payload_len == 13'd0);
    // rresp_next decode: SLVERR if (out_of_window or (no_descriptor and not
    // raw_sram_debug_read_enable)) else OKAY.
    wire                       rresp_slverr_cond = out_of_window |
                                 (no_descriptor & ~cfg_raw_sram_debug_read_enable);
    wire [1:0]                 rresp_next = rresp_slverr_cond ? RRESP_SLVERR : RRESP_OKAY;
    // rlast_next: this beat is the final ARLEN beat.
    wire                       rlast_next = (beat_index == arlen_q);
    // read_error qualifies the SLVERR side effect / error counter for this burst.
    wire                       read_error = slverr_q;

    wire                       ar_fire   = s_axi_arvalid & s_axi_arready;
    wire                       r_fire    = s_axi_rvalid  & s_axi_rready;
    wire                       size_ok   = (s_axi_arsize  == AXSIZE_32B);
    wire                       burst_ok  = (s_axi_arburst == AXBURST_INCR);

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            state                  <= S_IDLE;
            s_axi_arready          <= 1'b0;
            s_axi_rdata            <= {AXI_DATA_WIDTH{1'b0}};
            s_axi_rresp            <= RRESP_OKAY;
            s_axi_rlast            <= 1'b0;
            s_axi_rvalid           <= 1'b0;
            descriptor_pop_o       <= 1'b0;
            sram_rd_req_valid      <= 1'b0;
            sram_rd_req_addr       <= {SRAM_ADDR_WIDTH{1'b0}};
            sram_rd_rsp_ready      <= 1'b0;
            axi_read_busy          <= 1'b0;
            sram_read_busy         <= 1'b0;
            read_error_pulse       <= 1'b0;
            axi_rd_state           <= S_IDLE;
            sram_read_state        <= S_IDLE;
            araddr_q               <= {AXI_ADDR_WIDTH{1'b0}};
            arlen_q                <= 8'd0;
            ar_legal               <= 1'b0;
            beat_index             <= 8'd0;
            slverr_q               <= 1'b0;
            fw_axi_read_beat_count <= 32'd0;
            fw_axi_read_error_count<= 32'd0;
        end else begin
            // single-cycle pulses default low
            descriptor_pop_o <= 1'b0;
            read_error_pulse <= 1'b0;

            case (state)
                // IDLE: wait for an AR; arready high.
                S_IDLE: begin
                    s_axi_arready  <= 1'b1;
                    s_axi_rvalid   <= 1'b0;
                    s_axi_rlast    <= 1'b0;
                    axi_read_busy  <= 1'b0;
                    sram_read_busy <= 1'b0;
                    // transition_0: IDLE -> ACCEPT_AR on arvalid && arready
                    if (ar_fire) begin
                        s_axi_arready <= 1'b0;
                        araddr_q      <= s_axi_araddr;
                        arlen_q       <= s_axi_arlen;
                        ar_legal      <= size_ok & burst_ok;
                        beat_index    <= 8'd0;
                        axi_read_busy <= 1'b1;
                        state         <= S_ACCEPT_AR;
                    end
                end

                // ACCEPT_AR: evaluate window/descriptor preconditions and choose
                // the SRAM-read path or the SLVERR path.
                S_ACCEPT_AR: begin
                    slverr_q <= rresp_slverr_cond | ~ar_legal;
                    // transition_1: ACCEPT_AR -> ISSUE_SRAM_RD when in window and a
                    // descriptor is present (or raw_sram_debug_read_enable).
                    // transition_2: ACCEPT_AR -> DRIVE_R on out-of-window/no-descriptor
                    // (-> SLVERR), bypassing the SRAM read.
                    if (ar_legal & ~rresp_slverr_cond) begin
                        state <= S_ISSUE_SRAM_RD;
                    end else begin
                        state <= S_DRIVE_R;
                    end
                end

                // ISSUE_SRAM_RD: drive one SRAM read request for this beat.
                S_ISSUE_SRAM_RD: begin
                    sram_read_busy    <= 1'b1;
                    sram_rd_req_valid <= 1'b1;
                    sram_rd_req_addr  <= beat_addr;
                    // transition_3: ISSUE_SRAM_RD -> WAIT_SRAM_RSP when req accepted
                    if (sram_rd_req_valid & sram_rd_req_ready) begin
                        sram_rd_req_valid <= 1'b0;
                        sram_rd_rsp_ready <= 1'b1;
                        state             <= S_WAIT_SRAM_RSP;
                    end
                end

                // WAIT_SRAM_RSP: capture the SRAM read response into rdata.
                S_WAIT_SRAM_RSP: begin
                    // transition_4: WAIT_SRAM_RSP -> DRIVE_R on sram_rd_rsp_valid
                    if (sram_rd_rsp_valid & sram_rd_rsp_ready) begin
                        sram_rd_rsp_ready <= 1'b0;
                        sram_read_busy    <= 1'b0;
                        s_axi_rdata       <= sram_rd_rsp_data;   // rdata returned unmodified
                        // a late SRAM error also forces SLVERR for this burst
                        if (sram_rd_rsp_error) begin
                            slverr_q <= 1'b1;
                        end
                        s_axi_rresp  <= (slverr_q | sram_rd_rsp_error) ? RRESP_SLVERR : rresp_next;
                        s_axi_rlast  <= rlast_next;
                        s_axi_rvalid <= 1'b1;
                        state        <= S_DRIVE_R;
                    end
                end

                // DRIVE_R: present the R beat. For the SLVERR path no SRAM read
                // happened, so drive zero data with SLVERR directly.
                S_DRIVE_R: begin
                    if (!s_axi_rvalid) begin
                        // SLVERR-path entry from ACCEPT_AR: no SRAM data this beat.
                        s_axi_rdata  <= {AXI_DATA_WIDTH{1'b0}};
                        s_axi_rresp  <= RRESP_SLVERR;
                        s_axi_rlast  <= rlast_next;
                        s_axi_rvalid <= 1'b1;
                    end else if (r_fire) begin
                        // R beat accepted: count it and advance.
                        s_axi_rvalid           <= 1'b0;
                        fw_axi_read_beat_count <= fw_axi_read_beat_count + 32'd1;
                        if (s_axi_rlast) begin
                            // transition_6: DRIVE_R -> DONE on rvalid && rready && rlast
                            // fw_axi_read_error_count += (1 if read_error else 0)
                            if (read_error) begin
                                fw_axi_read_error_count <= fw_axi_read_error_count + 32'd1;
                                read_error_pulse        <= 1'b1;
                            end
                            s_axi_rlast <= 1'b0;
                            state       <= S_DONE;
                        end else begin
                            // transition_5: DRIVE_R -> ISSUE_SRAM_RD on
                            // rvalid && rready && !rlast (next beat)
                            beat_index <= beat_index + 8'd1;
                            if (slverr_q) begin
                                state <= S_DRIVE_R;   // SLVERR path keeps streaming
                            end else begin
                                state <= S_ISSUE_SRAM_RD;
                            end
                        end
                    end
                end

                // DONE: retire the consumed descriptor (non-debug, non-error) and
                // return to IDLE.
                S_DONE: begin
                    axi_read_busy <= 1'b0;
                    // Pop the descriptor only when it was actually consumed: a valid
                    // descriptor existed and this was not a raw debug-window read.
                    if (descriptor_valid & ~cfg_raw_sram_debug_read_enable & ~slverr_q) begin
                        descriptor_pop_o <= 1'b1;
                    end
                    // transition_7: DONE -> IDLE
                    s_axi_arready <= 1'b1;
                    state         <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase

            // DEBUG_CTX state mirrors track the FSM each cycle.
            axi_rd_state    <= state;
            sram_read_state <= state;
        end
    end

endmodule
`default_nettype wire

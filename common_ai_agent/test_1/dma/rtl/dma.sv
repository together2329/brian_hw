// ============================================================================
// DMA Controller - Direct Memory Access
// Based on Module Architecture Specification v1.0
// States: IDLE -> SETUP -> READ -> WRITE -> DONE
// ============================================================================

module dma #(
    parameter int NUM_CHANNELS      = 4,
    parameter int DATA_WIDTH        = 32,
    parameter int ADDR_WIDTH        = 32,
    parameter int MAX_TRANSFER_SIZE = 1024,
    parameter int FIFO_DEPTH        = 8
)(
    // Clock and reset
    input  logic                          clk,
    input  logic                          rst_n,

    // APB Slave Interface
    input  logic                          psel,
    input  logic                          penable,
    input  logic                          pwrite,
    input  logic [11:0]                   paddr,
    input  logic [DATA_WIDTH-1:0]         pwdata,
    output logic [DATA_WIDTH-1:0]         prdata,
    output logic                          pready,
    output logic                          pslverr,

    // AHB Master Interface
    output logic                          hbusreq,
    input  logic                          hgrant,
    output logic [ADDR_WIDTH-1:0]         haddr,
    output logic [1:0]                    htrans,
    output logic                          hwrite,
    output logic [2:0]                    hsize,
    output logic [2:0]                    hburst,
    output logic [3:0]                    hprot,
    output logic [DATA_WIDTH-1:0]         hwdata,
    input  logic [DATA_WIDTH-1:0]         hrdata,
    input  logic                          hready,
    input  logic                          hresp,

    // Interrupts
    output logic [NUM_CHANNELS-1:0]       irq
);

    // =========================================================================
    // Types and Constants
    // =========================================================================

    typedef enum logic [2:0] {
        CH_IDLE   = 3'd0,
        CH_SETUP  = 3'd1,
        CH_READ   = 3'd2,
        CH_WRITE  = 3'd3,
        CH_DONE   = 3'd4
    } ch_state_t;

    localparam logic [1:0] AHB_IDLE   = 2'b00;
    localparam logic [1:0] AHB_BUSY   = 2'b01;
    localparam logic [1:0] AHB_NONSEQ = 2'b10;
    localparam logic [1:0] AHB_SEQ    = 2'b11;

    localparam logic [2:0] AHB_SINGLE = 3'b000;
    localparam logic [2:0] AHB_INCR   = 3'b001;
    localparam logic [2:0] AHB_INCR4  = 3'b011;
    localparam logic [2:0] AHB_INCR8  = 3'b101;
    localparam logic [2:0] AHB_INCR16 = 3'b111;

    localparam logic       AHB_OKAY   = 1'b0;
    localparam logic       AHB_ERROR  = 1'b1;

    // =========================================================================
    // Internal Signals - Global Registers
    // =========================================================================

    logic                          dma_en_reg;
    logic [NUM_CHANNELS-1:0]       int_status_reg;
    logic [NUM_CHANNELS-1:0]       int_raw_reg;
    logic [NUM_CHANNELS-1:0]       int_mask_reg;
    logic [NUM_CHANNELS-1:0]       err_status_reg;
    logic [NUM_CHANNELS-1:0]       sw_req_pulse;

    // =========================================================================
    // Internal Signals - Per-Channel
    // =========================================================================

    logic [NUM_CHANNELS-1:0]                         ch_en;
    logic [NUM_CHANNELS-1:0][ADDR_WIDTH-1:0]         ch_src_addr;
    logic [NUM_CHANNELS-1:0][ADDR_WIDTH-1:0]         ch_dst_addr;
    logic [NUM_CHANNELS-1:0][15:0]                   ch_xfer_size;
    logic [NUM_CHANNELS-1:0][31:0]                   ch_ctrl;
    logic [NUM_CHANNELS-1:0][31:0]                   ch_cfg;

    logic [NUM_CHANNELS-1:0][31:0]                   ch_status;
    logic [NUM_CHANNELS-1:0][15:0]                   ch_remain;

    ch_state_t [NUM_CHANNELS-1:0]                    ch_state;

    logic [NUM_CHANNELS-1:0][ADDR_WIDTH-1:0]         ch_cur_src_addr;
    logic [NUM_CHANNELS-1:0][ADDR_WIDTH-1:0]         ch_cur_dst_addr;
    logic [NUM_CHANNELS-1:0][15:0]                   ch_xfer_count;

    logic [NUM_CHANNELS-1:0][4:0]                    ch_burst_count;
    logic [NUM_CHANNELS-1:0][4:0]                    ch_burst_total;

    logic [NUM_CHANNELS-1:0]                         ch_bus_request;
    logic [NUM_CHANNELS-1:0]                         ch_bus_grant;

    logic [NUM_CHANNELS-1:0]                         ch_err_flag;
    logic [NUM_CHANNELS-1:0]                         ch_irq_pulse;
    logic [NUM_CHANNELS-1:0]                         ch_half_irq;

    logic [NUM_CHANNELS-1:0][ADDR_WIDTH-1:0]         ch_saved_src_addr;
    logic [NUM_CHANNELS-1:0][ADDR_WIDTH-1:0]         ch_saved_dst_addr;
    logic [NUM_CHANNELS-1:0][15:0]                   ch_saved_xfer_size;

    // Per-channel decoded control fields (visible outside generate)
    logic [NUM_CHANNELS-1:0][2:0]                    ch_src_width;
    logic [NUM_CHANNELS-1:0][2:0]                    ch_dst_width;
    logic [NUM_CHANNELS-1:0][1:0]                    ch_src_burst;
    logic [NUM_CHANNELS-1:0][1:0]                    ch_dst_burst;
    logic [NUM_CHANNELS-1:0]                         ch_src_inc;
    logic [NUM_CHANNELS-1:0]                         ch_dst_inc;
    logic [NUM_CHANNELS-1:0]                         ch_int_en;
    logic [NUM_CHANNELS-1:0]                         ch_int_err_en;
    logic [NUM_CHANNELS-1:0]                         ch_circular;
    logic [NUM_CHANNELS-1:0]                         ch_half_irq_en;
    logic [NUM_CHANNELS-1:0][3:0]                    ch_src_per;
    logic [NUM_CHANNELS-1:0][3:0]                    ch_dst_per;
    logic [NUM_CHANNELS-1:0][1:0]                    ch_priority;

    // =========================================================================
    // FIFO Signals
    // =========================================================================

    logic [NUM_CHANNELS-1:0][DATA_WIDTH-1:0]         fifo_wr_data;
    logic [NUM_CHANNELS-1:0]                         fifo_wr_en;
    logic [NUM_CHANNELS-1:0]                         fifo_rd_en;
    logic [NUM_CHANNELS-1:0][DATA_WIDTH-1:0]         fifo_rd_data;
    logic [NUM_CHANNELS-1:0]                         fifo_full;
    logic [NUM_CHANNELS-1:0]                         fifo_empty;
    logic [NUM_CHANNELS-1:0]                         fifo_almost_full;
    logic [NUM_CHANNELS-1:0]                         fifo_almost_empty;
    logic [NUM_CHANNELS-1:0][$clog2(FIFO_DEPTH+1)-1:0] fifo_count;

    // =========================================================================
    // Arbiter Signals
    // =========================================================================

    logic [NUM_CHANNELS-1:0]                         arb_grant;
    logic [$clog2(NUM_CHANNELS)-1:0]                 active_ch;
    logic                                            arb_any_active;

    // =========================================================================
    // Helper Functions
    // =========================================================================

    function automatic logic [2:0] width_to_hsize(input logic [2:0] width_sel);
        case (width_sel)
            3'd0: return 3'b000; // 8-bit  = BYTE
            3'd1: return 3'b001; // 16-bit = HALFWORD
            3'd2: return 3'b010; // 32-bit = WORD
            default: return 3'b010;
        endcase
    endfunction

    function automatic logic [2:0] burst_to_hburst(input logic [1:0] burst_sel);
        case (burst_sel)
            2'd0: return AHB_SINGLE;
            2'd1: return AHB_INCR4;
            2'd2: return AHB_INCR8;
            2'd3: return AHB_INCR16;
            default: return AHB_SINGLE;
        endcase
    endfunction

    function automatic logic [4:0] burst_beat_count(input logic [1:0] burst_sel);
        case (burst_sel)
            2'd0: return 5'd1;
            2'd1: return 5'd4;
            2'd2: return 5'd8;
            2'd3: return 5'd16;
            default: return 5'd1;
        endcase
    endfunction

    function automatic logic [ADDR_WIDTH-1:0] size_bytes(input logic [2:0] width_sel);
        case (width_sel)
            3'd0: return {{(ADDR_WIDTH-1){1'b0}}, 1'b1}; // 1 byte
            3'd1: return {{(ADDR_WIDTH-2){1'b0}}, 2'b10}; // 2 bytes
            3'd2: return {{(ADDR_WIDTH-3){1'b0}}, 3'b100}; // 4 bytes
            default: return {{(ADDR_WIDTH-3){1'b0}}, 3'b100};
        endcase
    endfunction

    // =========================================================================
    // APB Register File (Section 5.1: FR-01)
    // =========================================================================

    logic [DATA_WIDTH-1:0] reg_rdata;
    logic                  reg_error;
    logic                  apb_write_active;

    assign pready  = 1'b1;  // Zero wait states (FR-01)
    assign apb_write_active = psel & penable & pwrite;

    // Write decode
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dma_en_reg     <= 1'b0;
            int_mask_reg   <= {NUM_CHANNELS{1'b1}};  // All masked at reset
            err_status_reg <= {NUM_CHANNELS{1'b0}};
            int_status_reg <= {NUM_CHANNELS{1'b0}};
            int_raw_reg    <= {NUM_CHANNELS{1'b0}};
            sw_req_pulse   <= {NUM_CHANNELS{1'b0}};

            for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                ch_en[ch]        <= 1'b0;
                ch_src_addr[ch]  <= {ADDR_WIDTH{1'b0}};
                ch_dst_addr[ch]  <= {ADDR_WIDTH{1'b0}};
                ch_xfer_size[ch] <= 16'd0;
                ch_ctrl[ch]      <= 32'd0;
                ch_cfg[ch]       <= 32'd0;
            end
        end else begin
            // Default: clear SW request pulse every cycle
            sw_req_pulse <= {NUM_CHANNELS{1'b0}};

            if (apb_write_active) begin
                case (paddr[11:0])
                    12'h000: dma_en_reg <= pwdata[0];

                    12'h00C: begin // INT_CLEAR - write-1-to-clear
                        int_raw_reg    <= int_raw_reg    & ~pwdata[NUM_CHANNELS-1:0];
                        int_status_reg <= int_status_reg & ~pwdata[NUM_CHANNELS-1:0];
                    end

                    12'h010: int_mask_reg <= pwdata[NUM_CHANNELS-1:0];

                    12'h018: begin // ERR_CLEAR - write-1-to-clear
                        err_status_reg <= err_status_reg & ~pwdata[NUM_CHANNELS-1:0];
                    end

                    12'h01C: begin // SW_REQ
                        sw_req_pulse <= pwdata[NUM_CHANNELS-1:0];
                    end

                    default: begin
                        // Per-channel register decode
                        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                            if (paddr[11:8] == ch[3:0]) begin
                                case (paddr[7:0])
                                    8'h00: ch_en[ch]        <= pwdata[0];
                                    8'h04: ch_src_addr[ch]  <= pwdata[ADDR_WIDTH-1:0];
                                    8'h08: ch_dst_addr[ch]  <= pwdata[ADDR_WIDTH-1:0];
                                    8'h0C: ch_xfer_size[ch] <= pwdata[15:0];
                                    8'h10: ch_ctrl[ch]      <= pwdata;
                                    8'h14: ch_cfg[ch]       <= pwdata;
                                    default: ;
                                endcase
                            end
                        end
                    end
                endcase
            end

            // Auto-clear channel enable on error (FR-09)
            for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                if (ch_err_flag[ch])
                    ch_en[ch] <= 1'b0;
            end
        end
    end

    // Read decode (combinational)
    always_comb begin
        reg_rdata = {DATA_WIDTH{1'b0}};
        reg_error = 1'b0;

        case (paddr[11:0])
            12'h000: reg_rdata = {31'd0, dma_en_reg};
            12'h004: reg_rdata = {{(32-NUM_CHANNELS){1'b0}}, int_status_reg};
            12'h008: reg_rdata = {{(32-NUM_CHANNELS){1'b0}}, int_raw_reg};
            12'h00C: reg_rdata = {DATA_WIDTH{1'b0}}; // Write-only
            12'h010: reg_rdata = {{(32-NUM_CHANNELS){1'b0}}, int_mask_reg};
            12'h014: reg_rdata = {{(32-NUM_CHANNELS){1'b0}}, err_status_reg};
            12'h018: reg_rdata = {DATA_WIDTH{1'b0}}; // Write-only
            12'h01C: reg_rdata = {DATA_WIDTH{1'b0}}; // Write-only

            default: begin
                // Per-channel registers
                logic addr_matched;
                addr_matched = 1'b0;
                for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                    if (paddr[11:8] == ch[3:0]) begin
                        addr_matched = 1'b1;
                        case (paddr[7:0])
                            8'h00: reg_rdata = {31'd0, ch_en[ch]};
                            8'h04: reg_rdata = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch_src_addr[ch]};
                            8'h08: reg_rdata = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch_dst_addr[ch]};
                            8'h0C: reg_rdata = {16'd0, ch_xfer_size[ch]};
                            8'h10: reg_rdata = ch_ctrl[ch];
                            8'h14: reg_rdata = ch_cfg[ch];
                            8'h18: reg_rdata = ch_status[ch];
                            8'h1C: reg_rdata = {16'd0, ch_remain[ch]};
                            default: reg_error = 1'b1;
                        endcase
                    end
                end
                if (!addr_matched)
                    reg_error = 1'b1;
            end
        endcase
    end

    assign prdata  = reg_rdata;
    assign pslverr = reg_error & psel & penable;

    // =========================================================================
    // Per-Channel Decode Control Fields
    // =========================================================================

    genvar ch;
    generate
        for (ch = 0; ch < NUM_CHANNELS; ch++) begin : gen_ch_decode
            assign ch_src_width[ch]  = ch_ctrl[ch][2:0];
            assign ch_dst_width[ch]  = ch_ctrl[ch][5:3];
            assign ch_src_burst[ch]  = ch_ctrl[ch][7:6];
            assign ch_dst_burst[ch]  = ch_ctrl[ch][9:8];
            assign ch_src_inc[ch]    = ch_ctrl[ch][10];
            assign ch_dst_inc[ch]    = ch_ctrl[ch][11];
            assign ch_int_en[ch]     = ch_ctrl[ch][16];
            assign ch_int_err_en[ch] = ch_ctrl[ch][17];
            assign ch_src_per[ch]    = ch_cfg[ch][3:0];
            assign ch_dst_per[ch]    = ch_cfg[ch][7:4];
            assign ch_priority[ch]   = ch_cfg[ch][9:8];
            assign ch_circular[ch]   = ch_cfg[ch][10];
            assign ch_half_irq_en[ch]= ch_cfg[ch][11];
        end
    endgenerate

    // =========================================================================
    // Per-Channel FIFOs
    // =========================================================================

    generate
        for (ch = 0; ch < NUM_CHANNELS; ch++) begin : gen_fifo

            dma_fifo #(
                .WIDTH (DATA_WIDTH),
                .DEPTH (FIFO_DEPTH)
            ) u_fifo (
                .clk         (clk),
                .rst_n       (rst_n),
                .wr_en       (fifo_wr_en[ch]),
                .wr_data     (fifo_wr_data[ch]),
                .rd_en       (fifo_rd_en[ch]),
                .rd_data     (fifo_rd_data[ch]),
                .full        (fifo_full[ch]),
                .empty       (fifo_empty[ch]),
                .almost_full (fifo_almost_full[ch]),
                .almost_empty(fifo_almost_empty[ch]),
                .count       (fifo_count[ch])
            );

        end
    endgenerate

    // =========================================================================
    // Per-Channel FSM (Section 4.3)
    // =========================================================================

    generate
        for (ch = 0; ch < NUM_CHANNELS; ch++) begin : gen_channel_fsm

            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    ch_state[ch]          <= CH_IDLE;
                    ch_cur_src_addr[ch]   <= {ADDR_WIDTH{1'b0}};
                    ch_cur_dst_addr[ch]   <= {ADDR_WIDTH{1'b0}};
                    ch_xfer_count[ch]     <= 16'd0;
                    ch_burst_count[ch]    <= 5'd0;
                                         ch_burst_total[ch]    <= 5'd0;
                    ch_bus_request[ch]    <= 1'b0;
                    ch_err_flag[ch]       <= 1'b0;
                    ch_irq_pulse[ch]      <= 1'b0;
                    ch_half_irq[ch]       <= 1'b0;
                    ch_saved_src_addr[ch] <= {ADDR_WIDTH{1'b0}};
                    ch_saved_dst_addr[ch] <= {ADDR_WIDTH{1'b0}};
                    ch_saved_xfer_size[ch]<= 16'd0;
                    fifo_wr_en[ch]        <= 1'b0;
                    fifo_rd_en[ch]        <= 1'b0;
                    fifo_wr_data[ch]      <= {DATA_WIDTH{1'b0}};
                end else begin
                    // Default: clear pulses
                    ch_irq_pulse[ch] <= 1'b0;
                    ch_half_irq[ch]  <= 1'b0;
                    fifo_wr_en[ch]   <= 1'b0;
                    fifo_rd_en[ch]   <= 1'b0;

                    case (ch_state[ch])

                        // -------------------------------------------------
                        // IDLE: Wait for enable + software request
                        // -------------------------------------------------
                        CH_IDLE: begin
                            ch_bus_request[ch] <= 1'b0;
                            if (dma_en_reg && ch_en[ch] && sw_req_pulse[ch] &&
                                (ch_xfer_size[ch] > 16'd0)) begin
                                ch_state[ch]          <= CH_SETUP;
                                ch_cur_src_addr[ch]   <= ch_src_addr[ch];
                                ch_cur_dst_addr[ch]   <= ch_dst_addr[ch];
                                ch_xfer_count[ch]     <= ch_xfer_size[ch];
                                ch_saved_src_addr[ch] <= ch_src_addr[ch];
                                ch_saved_dst_addr[ch] <= ch_dst_addr[ch];
                                ch_saved_xfer_size[ch]<= ch_xfer_size[ch];
                                ch_err_flag[ch]       <= 1'b0;
                            end
                        end

                        // -------------------------------------------------
                        // SETUP: Request bus arbitration
                        // -------------------------------------------------
                        CH_SETUP: begin
                            ch_bus_request[ch] <= 1'b1;
                            if (ch_bus_grant[ch]) begin
                                ch_state[ch]       <= CH_READ;
                                ch_burst_total[ch] <= burst_beat_count(ch_src_burst[ch]);
                                ch_burst_count[ch] <= 5'd0;
                            end
                        end

                        // -------------------------------------------------
                        // READ: AHB read burst from source
                        // -------------------------------------------------
                        CH_READ: begin
                            if (ch_bus_grant[ch] && hready) begin
                                if (hresp == AHB_ERROR) begin
                                    // FR-09: Error handling
                                    ch_err_flag[ch] <= 1'b1;
                                    ch_state[ch]    <= CH_DONE;
                                end else begin
                                    // Store read data in FIFO
                                    fifo_wr_en[ch]   <= 1'b1;
                                    fifo_wr_data[ch] <= hrdata;

                                    // Increment source address (FR-07)
                                    if (ch_src_inc[ch]) begin
                                        ch_cur_src_addr[ch] <= ch_cur_src_addr[ch] +
                                            size_bytes(ch_src_width[ch]);
                                    end

                                    ch_burst_count[ch] <= ch_burst_count[ch] + 5'd1;
                                    ch_xfer_count[ch]  <= ch_xfer_count[ch] - 16'd1;

                                    // Burst complete or FIFO pressure or last beat
                                    if ((ch_burst_count[ch] + 5'd1 >= ch_burst_total[ch]) ||
                                        fifo_almost_full[ch] ||
                                        (ch_xfer_count[ch] <= 16'd1)) begin
                                        ch_state[ch]       <= CH_WRITE;
                                        ch_burst_count[ch] <= 5'd0;
                                        ch_burst_total[ch] <= burst_beat_count(ch_dst_burst[ch]);
                                    end
                                end
                            end
                        end

                        // -------------------------------------------------
                        // WRITE: AHB write burst to destination
                        // -------------------------------------------------
                        CH_WRITE: begin
                            if (ch_bus_grant[ch] && !fifo_empty[ch] && hready) begin
                                if (hresp == AHB_ERROR) begin
                                    // FR-09: Error handling
                                    ch_err_flag[ch] <= 1'b1;
                                    fifo_rd_en[ch]  <= 1'b1;
                                    ch_state[ch]    <= CH_DONE;
                                end else begin
                                    fifo_rd_en[ch] <= 1'b1;

                                    // Increment destination address (FR-07)
                                    if (ch_dst_inc[ch]) begin
                                        ch_cur_dst_addr[ch] <= ch_cur_dst_addr[ch] +
                                            size_bytes(ch_dst_width[ch]);
                                    end

                                    ch_burst_count[ch] <= ch_burst_count[ch] + 5'd1;

                                    // Burst complete or FIFO draining
                                    if ((ch_burst_count[ch] + 5'd1 >= ch_burst_total[ch]) ||
                                        (fifo_count[ch] <= 1)) begin
                                        if (ch_xfer_count[ch] == 16'd0) begin
                                            ch_state[ch]       <= CH_DONE;
                                        end else begin
                                            // Go back to READ for more data
                                            ch_state[ch]       <= CH_READ;
                                            ch_burst_count[ch] <= 5'd0;
                                            ch_burst_total[ch] <= burst_beat_count(ch_src_burst[ch]);
                                        end
                                    end
                                end
                            end
                        end

                        // -------------------------------------------------
                        // DONE: Transfer complete (FR-08, FR-10)
                        // -------------------------------------------------
                        CH_DONE: begin
                            ch_bus_request[ch] <= 1'b0;
                            ch_irq_pulse[ch]   <= 1'b1;

                            if (ch_circular[ch] && !ch_err_flag[ch]) begin
                                // FR-10: Circular mode - reload and continue
                                ch_cur_src_addr[ch]    <= ch_saved_src_addr[ch];
                                ch_cur_dst_addr[ch]    <= ch_saved_dst_addr[ch];
                                ch_xfer_count[ch]      <= ch_saved_xfer_size[ch];
                                ch_err_flag[ch]        <= 1'b0;
                                ch_state[ch]           <= CH_SETUP;
                            end else begin
                                ch_state[ch] <= CH_IDLE;
                            end
                        end

                        default: ch_state[ch] <= CH_IDLE;
                    endcase

                    // FR-11: Global enable off -> abort all to IDLE
                    if (!dma_en_reg && ch_state[ch] != CH_IDLE) begin
                        ch_state[ch]       <= CH_IDLE;
                        ch_bus_request[ch] <= 1'b0;
                    end
                end
            end

            // Channel status register (FR-12)
            always_comb begin
                ch_status[ch] = {32{1'b0}};
                case (ch_state[ch])
                    CH_IDLE:  ch_status[ch][1:0] = 2'd0;
                    CH_SETUP: ch_status[ch][1:0] = 2'd1;
                    CH_READ:  ch_status[ch][1:0] = 2'd2;
                    CH_WRITE: ch_status[ch][1:0] = 2'd3;
                    CH_DONE:  ch_status[ch][1:0] = 2'd0;
                    default:  ch_status[ch][1:0] = 2'd0;
                endcase
                ch_status[ch][2] = ch_err_flag[ch];
                ch_status[ch][3] = (ch_state[ch] == CH_DONE) ? 1'b1 : 1'b0;
            end

            // Remaining count
            assign ch_remain[ch] = ch_xfer_count[ch];

        end
    endgenerate

    // =========================================================================
    // Priority Arbiter (Section 4.4)
    // =========================================================================

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            arb_grant     <= {NUM_CHANNELS{1'b0}};
            arb_any_active <= 1'b0;
        end else begin
            arb_grant <= {NUM_CHANNELS{1'b0}};

            // Priority-based arbitration: lower number = higher priority
            // Round-robin within same priority level (priority 0 first)
            for (int pri = 0; pri < 4; pri++) begin
                for (int c = 0; c < NUM_CHANNELS; c++) begin
                    if (ch_priority[c] == pri[1:0] &&
                        ch_bus_request[c] &&
                        arb_grant == {NUM_CHANNELS{1'b0}}) begin
                        arb_grant[c] <= 1'b1;
                    end
                end
            end

            arb_any_active <= |arb_grant;
        end
    end

    // Assign bus grant to channels
    always_comb begin
        for (int c = 0; c < NUM_CHANNELS; c++) begin
            ch_bus_grant[c] = arb_grant[c];
        end
    end

    // Determine which channel is active (for AHB mux)
    always_comb begin
        active_ch = {$clog2(NUM_CHANNELS){1'b0}};
        for (int c = 0; c < NUM_CHANNELS; c++) begin
            if (arb_grant[c])
                active_ch = c[$clog2(NUM_CHANNELS)-1:0];
        end
    end

    // =========================================================================
    // AHB Master Interface (Section 9.5)
    // =========================================================================

    // Mux active channel to AHB
    logic [ADDR_WIDTH-1:0]   ahb_addr_next;
    logic [1:0]              ahb_trans_next;
    logic                    ahb_write_next;
    logic [2:0]              ahb_size_next;
    logic [2:0]              ahb_burst_next;
    logic [3:0]              ahb_prot_next;
    logic [DATA_WIDTH-1:0]   ahb_wdata_next;

    always_comb begin
        ahb_addr_next  = {ADDR_WIDTH{1'b0}};
        ahb_trans_next = AHB_IDLE;
        ahb_write_next = 1'b0;
        ahb_size_next  = 3'b000;
        ahb_burst_next = AHB_SINGLE;
        ahb_prot_next  = 4'b0011;  // Non-privileged, non-cacheable, data access
        ahb_wdata_next = {DATA_WIDTH{1'b0}};

        for (int c = 0; c < NUM_CHANNELS; c++) begin
            if (arb_grant[c]) begin
                case (ch_state[c])
                    CH_READ: begin
                        ahb_addr_next  = ch_cur_src_addr[c];
                        ahb_write_next = 1'b0;
                        ahb_size_next  = width_to_hsize(ch_src_width[c]);
                        ahb_burst_next = burst_to_hburst(ch_src_burst[c]);
                        ahb_trans_next = (ch_burst_count[c] == 5'd0) ? AHB_NONSEQ : AHB_SEQ;
                    end

                    CH_WRITE: begin
                        ahb_addr_next  = ch_cur_dst_addr[c];
                        ahb_write_next = 1'b1;
                        ahb_size_next  = width_to_hsize(ch_dst_width[c]);
                        ahb_burst_next = burst_to_hburst(ch_dst_burst[c]);
                        ahb_trans_next = (ch_burst_count[c] == 5'd0) ? AHB_NONSEQ : AHB_SEQ;
                        ahb_wdata_next = fifo_rd_data[c];
                    end

                    default: begin
                        ahb_trans_next = AHB_IDLE;
                    end
                endcase
            end
        end
    end

    // Register AHB outputs
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            hbusreq <= 1'b0;
            haddr   <= {ADDR_WIDTH{1'b0}};
            htrans  <= AHB_IDLE;
            hwrite  <= 1'b0;
            hsize   <= 3'b000;
            hburst  <= AHB_SINGLE;
            hprot   <= 4'b0011;
            hwdata  <= {DATA_WIDTH{1'b0}};
        end else begin
            // Bus request when any channel needs bus
            hbusreq <= |ch_bus_request;

            if (hgrant) begin
                haddr  <= ahb_addr_next;
                htrans <= ahb_trans_next;
                hwrite <= ahb_write_next;
                hsize  <= ahb_size_next;
                hburst <= ahb_burst_next;
                hprot  <= ahb_prot_next;
            end else begin
                htrans <= AHB_IDLE;
            end

            // AHB write data is driven in data phase (one cycle after address)
            if (hwrite && hready)
                hwdata <= ahb_wdata_next;
        end
    end

    // =========================================================================
    // Interrupt Controller (Section 9.6, FR-08)
    // =========================================================================

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int c = 0; c < NUM_CHANNELS; c++) begin
                int_raw_reg[c]     <= 1'b0;
                int_status_reg[c]  <= 1'b0;
                irq[c]             <= 1'b0;
            end
        end else begin
            for (int c = 0; c < NUM_CHANNELS; c++) begin
                // Set raw interrupt on channel events
                if (ch_irq_pulse[c])
                    int_raw_reg[c] <= 1'b1;

                // Half-transfer interrupt
                if (ch_half_irq[c])
                    int_raw_reg[c] <= 1'b1;

                // Error interrupt
                if (ch_err_flag[c])
                    int_raw_reg[c] <= 1'b1;

                // Masked interrupt status
                int_status_reg[c] <= int_raw_reg[c] & ~int_mask_reg[c];

                // Level-sensitive output
                irq[c] <= int_status_reg[c];
            end
        end
    end

endmodule


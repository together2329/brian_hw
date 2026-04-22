`default_nettype none
module dma_channel #(
    parameter int DATA_WIDTH    = 32,
    parameter int ADDR_WIDTH    = 32,
    parameter int ID_WIDTH      = 4,
    parameter int FIFO_DEPTH    = 16,
    parameter int MAX_BURST_LEN = 16,
    parameter int CH_INDEX      = 0
)(
    input  logic                      clk,
    input  logic                      rst_n,

    // Global control
    input  logic                      dma_enable,
    input  logic                      endian_swap,
    input  logic                      clk_gated,

    // Channel registers (from reg_block)
    input  logic [31:0]               ch_sar_i,
    input  logic [31:0]               ch_dar_i,
    input  logic [31:0]               ch_len_i,
    input  logic [31:0]               ch_cr_i,
    input  logic [31:0]               ch_sr_w1c_i,
    input  logic [31:0]               ch_llp_i,
    input  logic [31:0]               ch_cfg_i,

    // Channel status outputs (to reg_block)
    output logic [2:0]                ch_state_o,
    output logic                      ch_fifo_empty_o,
    output logic                      ch_fifo_full_o,
    output logic [2:0]                ch_fifo_count_o,
    output logic [15:0]               ch_bcr_bytes_o,
    output logic                      ch_active_o,
    output logic                      ch_idle_o,
    output logic                      ch_bus_error_o,
    output logic                      ch_align_error_o,
    output logic                      ch_desc_error_o,
    output logic                      ch_xfer_complete_o,

    // Peripheral interface
    input  logic                      dma_req_i,
    output logic                      dma_ack_o,
    input  logic                      dma_eop_i,

    // Channel request to arbiter
    output logic                      ch_req_o,
    output logic [1:0]                ch_priority_o,

    // AXI read interface request
    output logic                      axi_rd_req_o,
    output logic [ID_WIDTH-1:0]       axi_rd_id_o,
    output logic [ADDR_WIDTH-1:0]     axi_rd_addr_o,
    output logic [7:0]                axi_rd_len_o,
    output logic [2:0]                axi_rd_size_o,
    output logic [1:0]                axi_rd_burst_o,
    output logic [2:0]                axi_rd_prot_o,
    output logic [3:0]                axi_rd_cache_o,

    // AXI write interface request
    output logic                      axi_wr_req_o,
    output logic [ID_WIDTH-1:0]       axi_wr_id_o,
    output logic [ADDR_WIDTH-1:0]     axi_wr_addr_o,
    output logic [7:0]                axi_wr_len_o,
    output logic [2:0]                axi_wr_size_o,
    output logic [1:0]                axi_wr_burst_o,
    output logic [2:0]                axi_wr_prot_o,
    output logic [3:0]                axi_wr_cache_o,
    output logic [DATA_WIDTH-1:0]     axi_wr_data_o,
    output logic [DATA_WIDTH/8-1:0]   axi_wr_strb_o,
    output logic                      axi_wr_last_o,

    // AXI read response
    input  logic                      axi_rd_data_valid_i,
    input  logic [DATA_WIDTH-1:0]     axi_rd_data_i,
    input  logic [1:0]                axi_rd_resp_i,
    input  logic                      axi_rd_last_i,
    input  logic [ID_WIDTH-1:0]       axi_rd_data_id_i,

    // AXI write response
    input  logic                      axi_wr_resp_valid_i,
    input  logic [ID_WIDTH-1:0]       axi_wr_resp_id_i,
    input  logic [1:0]                axi_wr_resp_i,

    // AXI write data handshake feedback
    input  logic                      axi_wr_ready_i,

    // Arbiter grant
    input  logic [ID_WIDTH-1:0]       arb_grant_id_i,
    input  logic                      arb_grant_valid_i,

    // Interrupt outputs
    output logic                      ch_irq_done_o,
    output logic                      ch_irq_err_o
);

    // ========================================================================
    // FSM State Encoding
    // ========================================================================
    typedef enum logic [3:0] {
        ST_IDLE       = 4'd0,
        ST_DESC_FETCH = 4'd1,
        ST_WAIT_REQ   = 4'd2,
        ST_READ_ADDR  = 4'd3,
        ST_READ_DATA  = 4'd4,
        ST_WRITE_ADDR = 4'd5,
        ST_WRITE_DATA = 4'd6,
        ST_WRITE_RESP = 4'd7,
        ST_COMPLETE   = 4'd8,
        ST_ERROR      = 4'd9
    } state_t;

    state_t state_q, state_d;

    // ========================================================================
    // Channel Control Register fields (latched copy)
    // ========================================================================
    logic        ch_enable;
    logic        ch_done;
    logic        ch_pause;
    logic        ch_abort;
    logic [1:0]  src_mode;
    logic [1:0]  dst_mode;
    logic        src_per;
    logic        dst_per;
    logic [1:0]  src_burst;
    logic [1:0]  dst_burst;
    logic [1:0]  src_width;
    logic [1:0]  dst_width;
    logic [1:0]  ch_pri_v;
    logic        int_en;
    logic        int_err_en;
    logic        sg_en;
    logic        cyclic_en;

    // Latched control on enable
    logic [1:0]  src_mode_q, dst_mode_q;
    logic        src_per_q, dst_per_q;
    logic [1:0]  src_burst_q, dst_burst_q;
    logic [1:0]  src_width_q, dst_width_q;
    logic        sg_en_q, cyclic_en_q;
    logic        int_en_q, int_err_en_q;

    // ========================================================================
    // Internal Registers
    // ========================================================================
    logic [ADDR_WIDTH-1:0] src_addr_q, dst_addr_q;
    logic [15:0]           bytes_total_q;
    logic [15:0]           bytes_left_q;
    logic [ADDR_WIDTH-1:0] llp_q;

    // Error/status flags
    logic bus_error_q, align_error_q, desc_error_q, xfer_complete_q;
    logic bus_error_set, align_error_set, desc_error_set, xfer_complete_set;

    // ========================================================================
    // FIFO (16 entries, DATA_WIDTH wide)
    // ========================================================================
    localparam int FIFO_ADDR_W = (FIFO_DEPTH == 1) ? 1 : $clog2(FIFO_DEPTH);
    localparam int FIFO_COUNT_W = FIFO_ADDR_W + 1;

    logic [DATA_WIDTH-1:0] fifo_mem [0:FIFO_DEPTH-1];
    logic [FIFO_COUNT_W-1:0] fifo_wr_ptr, fifo_rd_ptr;
    logic                  fifo_wr_en, fifo_rd_en;
    logic [DATA_WIDTH-1:0] fifo_rd_data;
    logic [FIFO_COUNT_W-1:0]  fifo_count;
    logic                  fifo_empty, fifo_full;
    logic                  fifo_threshold_met;

    // FIFO write/read
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fifo_wr_ptr <= '0;
            fifo_rd_ptr <= '0;
        end else begin
            if (fifo_wr_en && !fifo_full)
                fifo_wr_ptr <= fifo_wr_ptr + 1'b1;
            if (fifo_rd_en && !fifo_empty)
                fifo_rd_ptr <= fifo_rd_ptr + 1'b1;
        end
    end

    always_ff @(posedge clk) begin
        if (fifo_wr_en && !fifo_full)
            fifo_mem[fifo_wr_ptr[FIFO_ADDR_W-1:0]] <= axi_rd_data_i;
    end

    assign fifo_rd_data = fifo_mem[fifo_rd_ptr[FIFO_ADDR_W-1:0]];
    assign fifo_count   = fifo_wr_ptr - fifo_rd_ptr;
    assign fifo_empty   = (fifo_count == '0);
    assign fifo_full    = (fifo_count == FIFO_DEPTH[FIFO_COUNT_W-1:0]);

    // FIFO threshold: half-full (8) or quarter-full (4)
    logic [FIFO_COUNT_W-1:0] threshold;
    always_comb begin
        if (ch_cfg_i[7]) // fifo_threshold bit
            threshold = FIFO_DEPTH / 4;
        else
            threshold = FIFO_DEPTH / 2;
    end
    assign fifo_threshold_met = (fifo_count >= threshold);

    // ========================================================================
    // Extract control register fields
    // ========================================================================
    assign ch_enable  = ch_cr_i[0];
    assign ch_done    = ch_cr_i[1];
    assign ch_pause   = ch_cr_i[2];
    assign ch_abort   = ch_cr_i[3];
    assign src_mode   = ch_cr_i[5:4];
    assign dst_mode   = ch_cr_i[7:6];
    assign src_per    = ch_cr_i[8];
    assign dst_per    = ch_cr_i[9];
    assign src_burst  = ch_cr_i[11:10];
    assign dst_burst  = ch_cr_i[13:12];
    assign src_width  = ch_cr_i[15:14];
    assign dst_width  = ch_cr_i[17:16];
    assign ch_pri_v   = ch_cr_i[19:18];
    assign int_en     = ch_cr_i[20];
    assign int_err_en = ch_cr_i[21];
    assign sg_en      = ch_cr_i[22];
    assign cyclic_en  = ch_cr_i[23];

    // ========================================================================
    // Transfer width to bytes conversion
    // ========================================================================
    logic [2:0] src_size_bytes;
    logic [2:0] dst_size_bytes;
    always_comb begin
        case (src_width_q)
            2'd0: src_size_bytes = 3'd1;
            2'd1: src_size_bytes = 3'd2;
            2'd2: src_size_bytes = 3'd4;
            2'd3: src_size_bytes = 3'd8;
            default: src_size_bytes = 3'd4;
        endcase
        case (dst_width_q)
            2'd0: dst_size_bytes = 3'd1;
            2'd1: dst_size_bytes = 3'd2;
            2'd2: dst_size_bytes = 3'd4;
            2'd3: dst_size_bytes = 3'd8;
            default: dst_size_bytes = 3'd4;
        endcase
    end

    // AXI size encoding
    logic [2:0] src_axi_size, dst_axi_size;
    always_comb begin
        case (src_width_q)
            2'd0: src_axi_size = 3'd0; // 1 byte
            2'd1: src_axi_size = 3'd1; // 2 bytes
            2'd2: src_axi_size = 3'd2; // 4 bytes
            2'd3: src_axi_size = 3'd3; // 8 bytes
            default: src_axi_size = 3'd2;
        endcase
        case (dst_width_q)
            2'd0: dst_axi_size = 3'd0;
            2'd1: dst_axi_size = 3'd1;
            2'd2: dst_axi_size = 3'd2;
            2'd3: dst_axi_size = 3'd3;
            default: dst_axi_size = 3'd2;
        endcase
    end

    // Burst length encoding
    logic [7:0] src_burst_len, dst_burst_len;
    always_comb begin
        case (src_burst_q)
            2'd0: src_burst_len = 8'd0; // 1 beat
            2'd1: src_burst_len = 8'd3; // 4 beats
            2'd2: src_burst_len = 8'd7; // 8 beats
            2'd3: src_burst_len = 8'd15; // 16 beats
            default: src_burst_len = 8'd0;
        endcase
        case (dst_burst_q)
            2'd0: dst_burst_len = 8'd0;
            2'd1: dst_burst_len = 8'd3;
            2'd2: dst_burst_len = 8'd7;
            2'd3: dst_burst_len = 8'd15;
            default: dst_burst_len = 8'd0;
        endcase
    end

    // ========================================================================
    // Burst type: INCR=01 for incrementing, FIXED=00 for fixed
    // ========================================================================
    logic [1:0] src_burst_type, dst_burst_type;
    assign src_burst_type = (src_mode_q == 2'd01) ? 2'b00 : 2'b01; // FIXED : INCR
    assign dst_burst_type = (dst_mode_q == 2'd01) ? 2'b00 : 2'b01;

    // Cache: 0x0 for peripheral, CH_CFG.cache for memory
    logic [3:0] src_cache, dst_cache;
    assign src_cache = (src_per_q) ? 4'd0 : ch_cfg_i[6:4];
    assign dst_cache = (dst_per_q) ? 4'd0 : ch_cfg_i[6:4];

    // Protection
    logic [2:0] axi_prot;
    always_comb begin
        axi_prot = ch_cfg_i[3:1]; // prot field
        if (!ch_cfg_i[0]) // non-secure
            axi_prot[1] = 1'b1;
    end

    // ========================================================================
    // Granted flag
    // ========================================================================
    logic granted;
    assign granted = arb_grant_valid_i && (arb_grant_id_i == ID_WIDTH'(CH_INDEX));

    // ========================================================================
    // ID match for filtering AXI responses
    // ========================================================================
    logic id_match;
    assign id_match = (axi_rd_data_id_i == ID_WIDTH'(CH_INDEX));

    // ========================================================================
    // DMA acknowledge
    // ========================================================================
    logic dma_ack_q;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            dma_ack_q <= 1'b0;
        else
            dma_ack_q <= (state_q == ST_WAIT_REQ) && dma_req_i && granted;
    end
    assign dma_ack_o = dma_ack_q;

    // ========================================================================
    // Address update logic
    // ========================================================================
    logic [ADDR_WIDTH-1:0] next_src_addr, next_dst_addr;

    always_comb begin
        // Source address
        if (src_mode_q == 2'd01)
            next_src_addr = src_addr_q; // Fixed
        else
            next_src_addr = src_addr_q + src_size_bytes; // Incrementing

        // Destination address
        if (dst_mode_q == 2'd01)
            next_dst_addr = dst_addr_q; // Fixed
        else
            next_dst_addr = dst_addr_q + dst_size_bytes; // Incrementing
    end

    // ========================================================================
    // Write burst tracking
    // ========================================================================
    logic [FIFO_COUNT_W-1:0] wr_beat_cnt;
    logic [FIFO_COUNT_W-1:0] wr_total_beats;
    logic                     wr_burst_active_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_beat_cnt       <= '0;
            wr_total_beats    <= '0;
            wr_burst_active_q <= 1'b0;
        end else begin
            if (state_q == ST_WRITE_ADDR && state_d == ST_WRITE_DATA) begin
                // Capture how many FIFO entries to drain
                wr_total_beats    <= fifo_count;
                wr_beat_cnt       <= '0;
                wr_burst_active_q <= 1'b1;
            end else if (state_q == ST_WRITE_DATA) begin
                if (fifo_rd_en && !fifo_empty) begin
                    wr_beat_cnt <= wr_beat_cnt + 1'b1;
                end
                if (wr_beat_cnt + 1'b1 >= wr_total_beats && fifo_count > '0) begin
                    wr_burst_active_q <= 1'b0;
                end
            end else begin
                wr_burst_active_q <= 1'b0;
            end
        end
    end

    // ========================================================================
    // Scatter-Gather descriptor parsing
    // ========================================================================
    logic [1:0]  desc_word_cnt;
    logic [31:0] desc_sar, desc_dar, desc_ctrl, desc_next;
    logic        desc_valid_q;
    logic        desc_loaded;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            desc_word_cnt <= '0;
            desc_sar  <= '0;
            desc_dar  <= '0;
            desc_ctrl <= '0;
            desc_next <= '0;
            desc_valid_q <= 1'b0;
            desc_loaded  <= 1'b0;
        end else begin
            desc_valid_q <= 1'b0;
            if (state_q == ST_DESC_FETCH && axi_rd_data_valid_i && id_match) begin
                case (desc_word_cnt)
                    2'd0: desc_sar  <= axi_rd_data_i;
                    2'd1: desc_dar  <= axi_rd_data_i;
                    2'd2: desc_ctrl <= axi_rd_data_i;
                    2'd3: begin
                        desc_next <= axi_rd_data_i;
                        desc_valid_q <= 1'b1;
                    end
                endcase
                desc_word_cnt <= desc_word_cnt + 1'b1;
            end else if (state_q == ST_IDLE) begin
                desc_word_cnt <= '0;
                desc_loaded   <= 1'b0;
            end
        end
    end

    // ========================================================================
    // Enable: use ch_enable directly. Use a started flag to prevent re-trigger.
    // The flag is set when the channel leaves IDLE and cleared when it returns.
    // ========================================================================
    logic ch_started;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            ch_started <= 1'b0;
        else if (state_q != ST_IDLE)
            ch_started <= 1'b1;
        else
            ch_started <= 1'b0;
    end
    wire ch_enable_latch = ch_enable && !ch_started;

    // ========================================================================
    // FSM: Next State Logic
    // ========================================================================
    logic rd_data_done;
    logic wr_burst_done;

    assign rd_data_done = axi_rd_data_valid_i && axi_rd_last_i && id_match;
    assign wr_burst_done = (wr_beat_cnt + 1'b1 >= wr_total_beats) && !fifo_empty && granted && axi_wr_ready_i;

    always_comb begin
        state_d = state_q;
        fifo_wr_en = 1'b0;
        fifo_rd_en = 1'b0;
        bus_error_set = 1'b0;
        align_error_set = 1'b0;
        desc_error_set = 1'b0;
        xfer_complete_set = 1'b0;
        ch_irq_done_o = 1'b0;
        ch_irq_err_o = 1'b0;

        // Abort overrides everything (including pause)
        if (ch_abort && state_q != ST_IDLE && state_q != ST_ERROR) begin
            state_d = ST_ERROR;
        end
        else begin
            case (state_q)
                ST_IDLE: begin
                    if (ch_enable_latch && dma_enable && !clk_gated) begin
                        if (sg_en)
                            state_d = ST_DESC_FETCH;
                        else if (src_per)
                            state_d = ST_WAIT_REQ;
                        else
                            state_d = ST_READ_ADDR;
                    end
                end

                ST_DESC_FETCH: begin
                    // Wait for descriptor data to arrive
                    if (axi_rd_data_valid_i && id_match) begin
                        // desc_word_cnt is managed in the registered block above.
                        // When desc_valid_q fires (word 3 received), we check LLP.
                        // But desc_valid_q is registered, so we check it next cycle.
                    end
                    // Check if descriptor is fully loaded (one cycle after word 3)
                    if (desc_valid_q) begin
                        if (llp_q == '0) begin
                            state_d = ST_ERROR;
                            desc_error_set = 1'b1;
                        end else begin
                            // Load addresses from descriptor
                            state_d = ST_READ_ADDR;
                        end
                    end
                end

                ST_WAIT_REQ: begin
                    // Wait for peripheral dma_req before proceeding
                    if (dma_req_i && granted) begin
                        if (src_per_q && !dst_per_q)
                            state_d = ST_READ_ADDR;
                        else
                            state_d = ST_WRITE_ADDR;
                    end
                end

                ST_READ_ADDR: begin
                    // Wait for first read data beat with matching ID.
                    if (axi_rd_data_valid_i && id_match) begin
                        fifo_wr_en = 1'b1;
                        // Check bus error
                        if (axi_rd_resp_i != 2'b00) begin
                            state_d = ST_ERROR;
                            bus_error_set = 1'b1;
                        end
                        else if (axi_rd_last_i) begin
                            // Single-beat burst or last beat arrived immediately
                            if (dst_per_q)
                                state_d = ST_WAIT_REQ;
                            else
                                state_d = ST_WRITE_ADDR;
                        end
                        else begin
                            // Multi-beat burst: continue to READ_DATA
                            state_d = ST_READ_DATA;
                        end
                    end
                end

                ST_READ_DATA: begin
                    // Continue receiving read data beats (multi-beat bursts)
                    if (axi_rd_data_valid_i && id_match) begin
                        fifo_wr_en = 1'b1;
                        // Check bus error
                        if (axi_rd_resp_i != 2'b00) begin
                            state_d = ST_ERROR;
                            bus_error_set = 1'b1;
                        end
                    end
                    // Transition only on last beat (burst complete)
                    if (rd_data_done) begin
                        if (dst_per_q)
                            state_d = ST_WAIT_REQ;
                        else
                            state_d = ST_WRITE_ADDR;
                    end
                end

                ST_WRITE_ADDR: begin
                    if (granted) begin
                        state_d = ST_WRITE_DATA;
                    end
                end

                ST_WRITE_DATA: begin
                    if (!fifo_empty && granted && axi_wr_ready_i) begin
                        fifo_rd_en = 1'b1;
                    end
                    if (wr_burst_done) begin
                        state_d = ST_WRITE_RESP;
                    end
                end

                ST_WRITE_RESP: begin
                    if (axi_wr_resp_valid_i) begin
                        if (axi_wr_resp_i != 2'b00) begin
                            state_d = ST_ERROR;
                            bus_error_set = 1'b1;
                        end else if (bytes_left_q == '0) begin
                            state_d = ST_COMPLETE;
                        end else begin
                            // More data: back to read or wait for peripheral
                            if (src_per_q)
                                state_d = ST_WAIT_REQ;
                            else
                                state_d = ST_READ_ADDR;
                        end
                    end
                end

                ST_COMPLETE: begin
                    xfer_complete_set = 1'b1;
                    // Scatter-gather: chain to next descriptor if available
                    if (sg_en_q && !cyclic_en_q) begin
                        if (llp_q != '0) begin
                            state_d = ST_DESC_FETCH;
                            // Don't fire interrupt for intermediate completions
                        end else begin
                            state_d = ST_IDLE; // End of chain
                            if (int_en_q)
                                ch_irq_done_o = 1'b1;
                        end
                    end else begin
                        state_d = ST_IDLE;
                        if (int_en_q)
                            ch_irq_done_o = 1'b1;
                    end
                end

                ST_ERROR: begin
                    if (int_err_en_q)
                        ch_irq_err_o = 1'b1;
                    // Stay in ERROR until software clears errors and re-enables
                    if (!ch_enable) begin
                        state_d = ST_IDLE;
                    end else begin
                        state_d = ST_ERROR;
                    end
                end

                default: state_d = ST_IDLE;
            endcase
        end

        // Pause: gate new operations but allow in-flight AXI data to drain.
        if (ch_pause && state_q != ST_IDLE && state_q != ST_ERROR) begin
            state_d    = state_q; // Hold FSM state
            fifo_wr_en = 1'b0;    // Discard in-flight data
            fifo_rd_en = 1'b0;    // Don't drain FIFO
        end
    end

    // ========================================================================
    // FSM: State Register
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q <= ST_IDLE;
        end else begin
            state_q <= state_d;
        end
    end

    // ========================================================================
    // Latch control fields on channel enable
    // Also handles address/byte-count init and increment in one always_ff
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            src_mode_q   <= 2'd0;
            dst_mode_q   <= 2'd0;
            src_per_q    <= 1'b0;
            dst_per_q    <= 1'b0;
            src_burst_q  <= 2'd0;
            dst_burst_q  <= 2'd0;
            src_width_q  <= 2'd0;
            dst_width_q  <= 2'd0;
            sg_en_q      <= 1'b0;
            cyclic_en_q  <= 1'b0;
            int_en_q     <= 1'b0;
            int_err_en_q <= 1'b0;
            src_addr_q   <= '0;
            dst_addr_q   <= '0;
            bytes_total_q <= '0;
            bytes_left_q  <= '0;
            llp_q        <= '0;
        end else if (state_q == ST_IDLE && ch_enable_latch && dma_enable) begin
            // Latch control fields from CR
            src_mode_q   <= src_mode;
            dst_mode_q   <= dst_mode;
            src_per_q    <= src_per;
            dst_per_q    <= dst_per;
            src_burst_q  <= src_burst;
            dst_burst_q  <= dst_burst;
            src_width_q  <= src_width;
            dst_width_q  <= dst_width;
            sg_en_q      <= sg_en;
            cyclic_en_q  <= cyclic_en;
            int_en_q     <= int_en;
            int_err_en_q <= int_err_en;
            src_addr_q   <= ch_sar_i;
            dst_addr_q   <= ch_dar_i;
            llp_q        <= ch_llp_i;
            bytes_total_q <= (ch_len_i[15:0] == '0) ? 16'hFFFF : ch_len_i[15:0];
            bytes_left_q  <= (ch_len_i[15:0] == '0) ? 16'hFFFF : ch_len_i[15:0];
        end else if (desc_valid_q) begin
            // Descriptor loaded - update addresses and byte count
            src_addr_q    <= desc_sar;
            dst_addr_q    <= desc_dar;
            bytes_left_q  <= desc_ctrl[15:0];
            bytes_total_q <= desc_ctrl[15:0];
            llp_q         <= desc_next;
        end else if (state_q != ST_IDLE && state_q != ST_ERROR && !ch_pause) begin
            if (axi_rd_data_valid_i && id_match && axi_rd_resp_i == 2'b00) begin
                if (src_mode_q != 2'd01)
                    src_addr_q <= next_src_addr;
                bytes_left_q <= bytes_left_q - src_size_bytes;
            end
            if (fifo_rd_en && !fifo_empty) begin
                if (dst_mode_q != 2'd01)
                    dst_addr_q <= next_dst_addr;
            end
        end
    end

    // ========================================================================
    // Error/Status flags
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bus_error_q    <= 1'b0;
            align_error_q  <= 1'b0;
            desc_error_q   <= 1'b0;
            xfer_complete_q <= 1'b0;
        end else begin
            // W1C clear from register block
            if (ch_sr_w1c_i[8])  bus_error_q     <= 1'b0;
            if (ch_sr_w1c_i[9])  align_error_q   <= 1'b0;
            if (ch_sr_w1c_i[10]) desc_error_q    <= 1'b0;
            if (ch_sr_w1c_i[11]) xfer_complete_q <= 1'b0;

            // Set on events (takes priority over clear)
            if (bus_error_set)     bus_error_q     <= 1'b1;
            if (align_error_set)   align_error_q   <= 1'b1;
            if (desc_error_set)    desc_error_q    <= 1'b1;
            if (xfer_complete_set) xfer_complete_q <= 1'b1;
        end
    end

    // ========================================================================
    // Output assignments
    // ========================================================================
    assign ch_state_o         = state_q[2:0];
    assign ch_fifo_empty_o    = fifo_empty;
    assign ch_fifo_full_o     = fifo_full;
    assign ch_fifo_count_o    = fifo_count[2:0];
    assign ch_bcr_bytes_o     = bytes_left_q;
    assign ch_active_o        = (state_q != ST_IDLE) && (state_q != ST_ERROR);
    assign ch_idle_o          = (state_q == ST_IDLE);
    assign ch_bus_error_o     = bus_error_q;
    assign ch_align_error_o   = align_error_q;
    assign ch_desc_error_o    = desc_error_q;
    assign ch_xfer_complete_o = xfer_complete_q;

    // Channel request to arbiter — include all active states
    assign ch_req_o     = (state_q == ST_READ_ADDR) || (state_q == ST_READ_DATA) ||
                          (state_q == ST_WRITE_ADDR) || (state_q == ST_DESC_FETCH) ||
                          (state_q == ST_WRITE_DATA) || (state_q == ST_WRITE_RESP) ||
                          (state_q == ST_WAIT_REQ);
    assign ch_priority_o = ch_pri_v;

    // AXI read request
    assign axi_rd_req_o   = (state_q == ST_READ_ADDR) || (state_q == ST_DESC_FETCH);
    assign axi_rd_id_o    = ID_WIDTH'(CH_INDEX);
    assign axi_rd_addr_o  = (state_q == ST_DESC_FETCH) ? llp_q : src_addr_q;
    assign axi_rd_len_o   = (state_q == ST_DESC_FETCH) ? 8'd3 : src_burst_len;
    assign axi_rd_size_o  = (state_q == ST_DESC_FETCH) ? 3'd2 : src_axi_size;
    assign axi_rd_burst_o = (state_q == ST_DESC_FETCH) ? 2'b01 : src_burst_type;
    assign axi_rd_prot_o  = axi_prot;
    assign axi_rd_cache_o = (state_q == ST_DESC_FETCH) ? 4'h3 : src_cache;

    // AXI write request
    assign axi_wr_req_o   = (state_q == ST_WRITE_ADDR) || (state_q == ST_WRITE_DATA);
    assign axi_wr_id_o    = ID_WIDTH'(CH_INDEX);
    assign axi_wr_addr_o  = dst_addr_q;
    assign axi_wr_len_o   = dst_burst_len;
    assign axi_wr_size_o  = dst_axi_size;
    assign axi_wr_burst_o = dst_burst_type;
    assign axi_wr_prot_o  = axi_prot;
    assign axi_wr_cache_o = dst_cache;
    assign axi_wr_data_o  = fifo_rd_data;
    assign axi_wr_strb_o  = {(DATA_WIDTH/8){1'b1}};
    assign axi_wr_last_o  = (wr_beat_cnt + 1'b1 >= wr_total_beats) && !fifo_empty;

endmodule

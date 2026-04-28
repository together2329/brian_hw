`timescale 1ns / 1ps

module ai_engine (
    input  wire         S_AXI_ACLK,
    input  wire         S_AXI_ARESETn,

    input  wire         S_AXI_AWVALID,
    output reg          S_AXI_AWREADY,
    input  wire [31:0]  S_AXI_AWADDR,
    input  wire [2:0]   S_AXI_AWPROT,

    input  wire         S_AXI_WVALID,
    output reg          S_AXI_WREADY,
    input  wire [31:0]  S_AXI_WDATA,
    input  wire [3:0]   S_AXI_WSTRB,

    output reg          S_AXI_BVALID,
    input  wire         S_AXI_BREADY,
    output reg  [1:0]   S_AXI_BRESP,

    input  wire         S_AXI_ARVALID,
    output reg          S_AXI_ARREADY,
    input  wire [31:0]  S_AXI_ARADDR,
    input  wire [2:0]   S_AXI_ARPROT,

    output reg          S_AXI_RVALID,
    input  wire         S_AXI_RREADY,
    output reg  [31:0]  S_AXI_RDATA,
    output reg  [1:0]   S_AXI_RRESP,

    output reg          ai_irq
);

    localparam MAX_DIM = 16;
    localparam SRAM_SIZE = 256;
    localparam [2:0] OP_MATMUL=0, OP_RELU=1, OP_SIGMOID=2, OP_ADD_VEC=3, OP_LAYERNORM=4;

    // AXI states
    localparam [1:0] W_IDLE = 2'd0, W_PROC = 2'd1, W_RESP = 2'd2;
    localparam [1:0] R_IDLE = 2'd0, R_PROC = 2'd1, R_RESP = 2'd2;

    // Write channel
    reg [1:0]  w_state;
    reg        aw_latched;
    reg        w_latched;
    reg [31:0] awaddr_cap;
    reg [31:0] wdata_cap;

    // Read channel
    reg [1:0]  r_state;
    reg [31:0] araddr_cap;

    // Registers
    reg        reg_enable, reg_start, reg_irq_en;
    reg [2:0]  reg_op;
    reg [7:0]  reg_dim, reg_input_addr, reg_weight_addr, reg_result_addr;
    reg        reg_busy, reg_done;
    reg        done_clear;   // pulse from AXI read FSM to clear reg_done

    // SRAM
    reg [7:0] sram [0:SRAM_SIZE-1];

    // Engine
    reg [7:0]  input_buf [0:MAX_DIM-1];
    reg [7:0]  weight_buf [0:7];
    reg [7:0]  eng_row, eng_col, eng_load_cnt;
    reg [15:0] eng_accum;
    reg [15:0] eng_sum;
    reg [23:0] eng_sqsum;
    reg [7:0]  eng_mean, eng_variance;
    reg [3:0]  eng_state;

    localparam [3:0] E_IDLE=0, E_LOAD_A=1, E_LOAD_WEIGHTS=2, E_COMPUTE_DOT=3;
    localparam [3:0] E_STORE_ROW=4, E_ACTIVATE=5, E_LN_MEAN=6, E_LN_VAR=7;
    localparam [3:0] E_LN_NORM=8, E_DONE=9;

    function [7:0] sigmoid8;
        input [7:0] x;
        begin
            if (x <= 64) sigmoid8 = 0;
            else if (x <= 96) sigmoid8 = (x - 64) * 4;
            else if (x <= 160) sigmoid8 = 128 + (x - 96) * 2;
            else sigmoid8 = 255;
        end
    endfunction

    //==========================================================================
    // AXI WRITE CHANNEL FSM
    //==========================================================================
    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETn) begin
            w_state    <= W_IDLE;
            aw_latched <= 1'b0;
            w_latched  <= 1'b0;
            awaddr_cap <= 32'd0;
            wdata_cap  <= 32'd0;
            reg_start  <= 1'b0;
            // Config registers — single driver in this block
            reg_enable      <= 1'b0;
            reg_irq_en      <= 1'b0;
            reg_op          <= 3'd0;
            reg_dim         <= 8'd0;
            reg_input_addr  <= 8'd0;
            reg_weight_addr <= 8'd0;
            reg_result_addr <= 8'd0;
            S_AXI_AWREADY <= 1'b1;
            S_AXI_WREADY  <= 1'b1;
            S_AXI_BVALID  <= 1'b0;
            S_AXI_BRESP   <= 2'b00;
        end else begin
            case (w_state)
                W_IDLE: begin
                    S_AXI_BVALID <= 1'b0;
                    // Latch AW independently
                    if (S_AXI_AWVALID && S_AXI_AWREADY && !aw_latched) begin
                        awaddr_cap <= S_AXI_AWADDR;
                        aw_latched <= 1'b1;
                    end
                    // Latch W independently
                    if (S_AXI_WVALID && S_AXI_WREADY && !w_latched) begin
                        wdata_cap <= S_AXI_WDATA;
                        w_latched <= 1'b1;
                    end
                    // Both ready -> process
                    if (aw_latched && w_latched) begin
                        w_state <= W_PROC;
                        S_AXI_AWREADY <= 1'b0;
                        S_AXI_WREADY  <= 1'b0;
                    end
                end

                W_PROC: begin
                    // Execute write (1 cycle)
                    if (awaddr_cap[11:5] == 7'd0) begin
                        case (awaddr_cap[5:2])
                            4'd0: begin
                                reg_enable <= wdata_cap[0];
                                reg_start  <= wdata_cap[1];
                                reg_op     <= wdata_cap[4:2];
                                reg_irq_en <= wdata_cap[5];
                            end
                            4'd1: ;
                            4'd2: reg_dim         <= wdata_cap[7:0];
                            4'd3: reg_input_addr  <= wdata_cap[7:0];
                            4'd4: reg_weight_addr <= wdata_cap[7:0];
                            4'd5: reg_result_addr <= wdata_cap[7:0];
                            default: ;
                        endcase
                    end else begin
                        if ((awaddr_cap[11:0] - 12'h020 + 3) < SRAM_SIZE) begin
                            sram[awaddr_cap[11:0] - 12'h020 + 0] <= wdata_cap[7:0];
                            sram[awaddr_cap[11:0] - 12'h020 + 1] <= wdata_cap[15:8];
                            sram[awaddr_cap[11:0] - 12'h020 + 2] <= wdata_cap[23:16];
                            sram[awaddr_cap[11:0] - 12'h020 + 3] <= wdata_cap[31:24];
                        end
                    end
                    S_AXI_BVALID <= 1'b1;
                    S_AXI_BRESP  <= 2'b00;
                    aw_latched <= 1'b0;
                    w_latched  <= 1'b0;
                    // Re-assert ready for next transaction
                    S_AXI_AWREADY <= 1'b1;
                    S_AXI_WREADY  <= 1'b1;
                    w_state <= W_RESP;
                end

                W_RESP: begin
                    if (S_AXI_BVALID && S_AXI_BREADY) begin
                        S_AXI_BVALID <= 1'b0;
                        w_state <= W_IDLE;
                    end
                end

                default: w_state <= W_IDLE;
            endcase
        end
    end

    //==========================================================================
    // AXI READ CHANNEL FSM
    //==========================================================================
    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETn) begin
            r_state     <= R_IDLE;
            araddr_cap  <= 32'd0;
            S_AXI_ARREADY <= 1'b1;
            S_AXI_RVALID  <= 1'b0;
            S_AXI_RDATA   <= 32'd0;
            S_AXI_RRESP   <= 2'b00;
            done_clear    <= 1'b0;
        end else begin
            case (r_state)
                R_IDLE: begin
                    S_AXI_RVALID <= 1'b0;
                    done_clear   <= 1'b0;
                    if (S_AXI_ARVALID && S_AXI_ARREADY) begin
                        araddr_cap <= S_AXI_ARADDR;
                        S_AXI_ARREADY <= 1'b0;
                        r_state <= R_PROC;
                    end
                end

                R_PROC: begin
                    // Prepare data
                    if (araddr_cap[11:5] == 7'd0) begin
                        case (araddr_cap[5:2])
                            4'd0: S_AXI_RDATA <= {26'd0, reg_irq_en, reg_op, reg_start, reg_enable};
                            4'd1: begin
                                S_AXI_RDATA <= {30'd0, reg_done, reg_busy};
                                done_clear <= 1'b1;
                            end
                            4'd2: S_AXI_RDATA <= {24'd0, reg_dim};
                            4'd3: S_AXI_RDATA <= {24'd0, reg_input_addr};
                            4'd4: S_AXI_RDATA <= {24'd0, reg_weight_addr};
                            4'd5: S_AXI_RDATA <= {24'd0, reg_result_addr};
                            default: S_AXI_RDATA <= 32'd0;
                        endcase
                    end else begin
                        if ((araddr_cap[11:0] - 12'h020 + 3) < SRAM_SIZE)
                            S_AXI_RDATA <= { sram[araddr_cap[11:0] - 12'h020 + 3],
                                             sram[araddr_cap[11:0] - 12'h020 + 2],
                                             sram[araddr_cap[11:0] - 12'h020 + 1],
                                             sram[araddr_cap[11:0] - 12'h020 + 0] };
                        else
                            S_AXI_RDATA <= 32'd0;
                    end
                    S_AXI_RVALID  <= 1'b1;
                    S_AXI_RRESP   <= 2'b00;
                    S_AXI_ARREADY <= 1'b1;
                    r_state <= R_RESP;
                end

                R_RESP: begin
                    if (S_AXI_RVALID && S_AXI_RREADY) begin
                        S_AXI_RVALID <= 1'b0;
                        S_AXI_RDATA  <= 32'd0;
                        r_state <= R_IDLE;
                    end
                end

                default: r_state <= R_IDLE;
            endcase
        end
    end

    //==========================================================================
    // COMPUTE ENGINE
    //==========================================================================
    reg        reg_start_d1;  // edge detector for start

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETn) begin
            eng_state     <= E_IDLE;
            reg_busy      <= 1'b0;
            reg_done      <= 1'b0;
            ai_irq        <= 1'b0;
            eng_row       <= 8'd0;
            eng_col       <= 8'd0;
            eng_load_cnt  <= 8'd0;
            eng_accum     <= 16'd0;
            eng_sum       <= 16'd0;
            eng_sqsum     <= 24'd0;
            eng_mean      <= 8'd0;
            eng_variance  <= 8'd0;
            reg_start_d1  <= 1'b0;
        end else begin
            reg_start_d1 <= reg_start;

            // Rising-edge detection of reg_start (set by AXI write FSM)
            // This avoids multi-driver issues since reg_start is only
            // assigned in the AXI write FSM.
            if (reg_start && !reg_start_d1 && reg_enable && reg_dim > 0 && reg_dim <= MAX_DIM && eng_state == E_IDLE) begin
                reg_busy      <= 1'b1;
                reg_done      <= 1'b0;
                eng_row       <= 8'd0;
                eng_col       <= 8'd0;
                eng_load_cnt  <= 8'd0;
                eng_accum     <= 16'd0;
                eng_state     <= E_LOAD_A;
            end

            // Handle done_clear pulse from AXI read FSM (single-driver for reg_done)
            if (done_clear) begin
                reg_done   <= 1'b0;
            end

            ai_irq <= reg_done && reg_irq_en;

            case (eng_state)
                E_IDLE: begin
                    // Start is handled by the edge-detector block above.
                    // No level-triggered re-start here to avoid re-triggering
                    // after E_DONE while reg_start is still high.
                end

                E_LOAD_A: begin
                    if (eng_load_cnt < reg_dim) begin
                        input_buf[eng_load_cnt] <= sram[reg_input_addr + eng_load_cnt];
                        eng_load_cnt <= eng_load_cnt + 8'd1;
                    end else begin
                        eng_load_cnt <= 8'd0;
                        case (reg_op)
                            OP_MATMUL:   eng_state <= E_LOAD_WEIGHTS;
                            OP_RELU, OP_SIGMOID:  eng_state <= E_ACTIVATE;
                            OP_ADD_VEC:  eng_state <= E_LOAD_WEIGHTS;
                            OP_LAYERNORM: begin
                                eng_sum   <= 16'd0;
                                eng_row   <= 8'd0;
                                eng_state <= E_LN_MEAN;
                            end
                            default:     eng_state <= E_DONE;
                        endcase
                    end
                end

                E_LOAD_WEIGHTS: begin
                    if (eng_load_cnt < 8 && (eng_col + eng_load_cnt) < reg_dim) begin
                        if (reg_op == OP_ADD_VEC)
                            weight_buf[eng_load_cnt] <= sram[reg_weight_addr + eng_load_cnt];
                        else
                            weight_buf[eng_load_cnt] <= sram[reg_weight_addr + eng_row * reg_dim + eng_col + eng_load_cnt];
                        eng_load_cnt <= eng_load_cnt + 8'd1;
                    end else begin
                        eng_load_cnt <= 8'd0;
                        if (reg_op == OP_ADD_VEC)
                            eng_state <= E_ACTIVATE;
                        else
                            eng_state <= E_COMPUTE_DOT;
                    end
                end

                E_COMPUTE_DOT: begin
                    // One MAC per cycle — only iterate over valid entries
                    if (eng_load_cnt < 8 && (eng_col + eng_load_cnt) < reg_dim) begin
                        eng_accum <= eng_accum +
                            input_buf[eng_col + eng_load_cnt] * weight_buf[eng_load_cnt];
                        eng_load_cnt <= eng_load_cnt + 8'd1;
                    end else begin
                        eng_load_cnt <= 8'd0;
                        if ((eng_col + 8'd8) >= reg_dim)
                            eng_state <= E_STORE_ROW;
                        else begin
                            eng_col <= eng_col + 8'd8;
                            eng_state <= E_LOAD_WEIGHTS;
                        end
                    end
                end

                E_STORE_ROW: begin
                    sram[reg_result_addr + eng_row] <= (eng_accum > 255) ? 8'd255 : eng_accum[7:0];
                    eng_row   <= eng_row + 8'd1;
                    eng_col   <= 8'd0;
                    eng_accum <= 16'd0;
                    if ((eng_row + 8'd1) >= reg_dim)
                        eng_state <= E_DONE;
                    else
                        eng_state <= E_LOAD_WEIGHTS;
                end

                E_ACTIVATE: begin
                    if (eng_load_cnt < reg_dim) begin
                        case (reg_op)
                            OP_RELU:
                                sram[reg_result_addr + eng_load_cnt] <= (input_buf[eng_load_cnt] > 127) ? input_buf[eng_load_cnt] : 8'd0;
                            OP_SIGMOID:
                                sram[reg_result_addr + eng_load_cnt] <= sigmoid8(input_buf[eng_load_cnt]);
                            OP_ADD_VEC:
                                sram[reg_result_addr + eng_load_cnt] <= ((input_buf[eng_load_cnt] + weight_buf[eng_load_cnt]) > 255) ? 8'd255 : input_buf[eng_load_cnt] + weight_buf[eng_load_cnt];
                            default: ;
                        endcase
                        eng_load_cnt <= eng_load_cnt + 8'd1;
                    end else begin
                        eng_load_cnt <= 8'd0;
                        eng_state <= E_DONE;
                    end
                end

                E_LN_MEAN: begin
                    if (eng_row < reg_dim) begin
                        eng_sum <= eng_sum + input_buf[eng_row];
                        eng_row <= eng_row + 8'd1;
                    end else begin
                        eng_mean  <= eng_sum / reg_dim;
                        eng_row   <= 8'd0;
                        eng_sqsum <= 24'd0;
                        eng_state <= E_LN_VAR;
                    end
                end

                E_LN_VAR: begin
                    if (eng_row < reg_dim) begin
                        eng_sqsum <= eng_sqsum +
                            ($signed({1'b0, input_buf[eng_row]}) - $signed({1'b0, eng_mean})) *
                            ($signed({1'b0, input_buf[eng_row]}) - $signed({1'b0, eng_mean}));
                        eng_row <= eng_row + 8'd1;
                    end else begin
                        eng_variance <= (eng_sqsum >= reg_dim) ? eng_sqsum / reg_dim : 8'd1;
                        if (eng_variance == 0) eng_variance <= 8'd1;
                        eng_row <= 8'd0;
                        eng_state <= E_LN_NORM;
                    end
                end

                E_LN_NORM: begin
                    if (eng_row < reg_dim) begin
                        integer diff_signed, norm_val;
                        diff_signed = $signed({1'b0, input_buf[eng_row]}) - $signed({1'b0, eng_mean});
                        norm_val = (diff_signed * 128) / $signed({1'b0, eng_variance});
                        if (norm_val < -128) norm_val = -128;
                        else if (norm_val > 127) norm_val = 127;
                        sram[reg_result_addr + eng_row] <= norm_val + 128;
                        eng_row <= eng_row + 8'd1;
                    end else begin
                        eng_state <= E_DONE;
                    end
                end

                E_DONE: begin
                    reg_busy <= 1'b0;
                    reg_done <= 1'b1;
                    eng_state <= E_IDLE;
                end

                default: eng_state <= E_IDLE;
            endcase
        end
    end

endmodule

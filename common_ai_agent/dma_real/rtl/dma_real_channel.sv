// dma_real_channel.sv — Per-channel FSM, address counters, remaining counter, burst control
//
// SSOT refs: fsm.per_channel, function_model.transactions.FM_DMA_START/STEP/COMPLETE/ERROR,
//   error_handling, registers.register_list.CHx_STATUS
//
// FIX: Dual-phase FSM (read burst → write burst) with write_phase_q register.
//   done/error outputs are 1-cycle pulses to IRQ module (which latches them sticky).
//   Removed auto-clear of done/error latches; IRQ module owns the sticky state.

module dma_real_channel #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer BURST_MAX  = 16,
    parameter integer FIFO_DEPTH = 8,
    parameter integer CH_ID      = 0
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // Configuration (from apb_cfg)
    input  logic                  ch_en,
    input  logic                  ch_start,
    input  logic                  dma_en,
    input  logic [ADDR_WIDTH-1:0] cfg_src_addr,
    input  logic [ADDR_WIDTH-1:0] cfg_dst_addr,
    input  logic [15:0]           cfg_len,
    // Arbiter interface
    output logic                  ch_request,
    input  logic                  ch_grant,
    // AHB master interface
    output logic                  ahb_start,
    output logic                  ahb_write,
    output logic [ADDR_WIDTH-1:0] ahb_addr,
    output logic [15:0]           ahb_len,
    input  logic                  ahb_done,
    input  logic                  ahb_error,
    input  logic [DATA_WIDTH-1:0] ahb_rdata,
    output logic [DATA_WIDTH-1:0] ahb_wdata,
    // Status outputs (1-cycle pulses to IRQ module)
    output logic                  status_busy,
    output logic                  status_done,
    output logic                  status_error,
    output logic [1:0]            status_err_code,
    // FIFO data
    output logic [DATA_WIDTH-1:0] fifo_wdata,
    output logic                  fifo_wen,
    input  logic [DATA_WIDTH-1:0] fifo_rdata,
    output logic                  fifo_ren,
    input  logic                  fifo_empty,
    input  logic                  fifo_full
);

    // FSM states from SSOT
    localparam [3:0] IDLE     = 4'd0;
    localparam [3:0] CFG      = 4'd1;
    localparam [3:0] REQUEST  = 4'd2;
    localparam [3:0] READ_ST  = 4'd3;
    localparam [3:0] WRITE_ST = 4'd4;
    localparam [3:0] UPDATE   = 4'd5;
    localparam [3:0] DONE_ST  = 4'd6;
    localparam [3:0] ERROR_ST = 4'd7;

    logic [3:0] state_q, next_state;

    // Read/write phase tracker
    logic write_phase_q;

    // Internal counters
    logic [ADDR_WIDTH-1:0] src_addr_q;
    logic [ADDR_WIDTH-1:0] dst_addr_q;
    logic [15:0]           remaining_q;
    logic [1:0]            err_code_q;

    // 1-cycle pulse registers for done/error (fed to IRQ module which latches sticky)
    logic done_pulse_q;
    logic error_pulse_q;

    // Status outputs
    assign status_busy     = (state_q != IDLE);
    assign status_done     = done_pulse_q;
    assign status_error    = error_pulse_q;
    assign status_err_code = err_code_q;

    // Validation from SSOT function_model
    wire src_aligned  = (cfg_src_addr[1:0] == 2'b00);
    wire dst_aligned  = (cfg_dst_addr[1:0] == 2'b00);
    wire len_nonzero  = (cfg_len != 16'd0);
    wire valid_cfg    = len_nonzero && src_aligned && dst_aligned;

    // Accept conditions
    wire accept_start = ch_start && ch_en && dma_en;
    wire accept_valid = accept_start && valid_cfg;
    wire accept_error = accept_start && !valid_cfg;

    // Burst calculation
    wire [15:0] burst_len = (remaining_q < BURST_MAX[15:0]) ? remaining_q : BURST_MAX[15:0];
    wire remaining_done = (remaining_q <= burst_len) && (remaining_q > 16'd0);

    // AHB control — ahb_write depends on phase, not just state
    assign ch_request = (state_q == REQUEST) || (state_q == READ_ST) || (state_q == WRITE_ST);
    assign ahb_start  = (state_q == REQUEST) && ch_grant;
    assign ahb_write  = write_phase_q;
    assign ahb_addr   = write_phase_q ? dst_addr_q : src_addr_q;
    assign ahb_len    = burst_len;

    // FIFO interface
    assign fifo_wdata = ahb_rdata;
    assign fifo_wen   = (state_q == READ_ST) && ahb_done && !fifo_full;
    assign fifo_ren   = (state_q == WRITE_ST) && !fifo_empty;
    assign ahb_wdata  = fifo_rdata;

    // State register
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            state_q        <= IDLE;
            write_phase_q  <= 1'b0;
            src_addr_q     <= {ADDR_WIDTH{1'b0}};
            dst_addr_q     <= {ADDR_WIDTH{1'b0}};
            remaining_q    <= 16'd0;
            err_code_q     <= 2'd0;
            done_pulse_q   <= 1'b0;
            error_pulse_q  <= 1'b0;
        end else begin
            // Default: clear 1-cycle pulses
            done_pulse_q  <= 1'b0;
            error_pulse_q <= 1'b0;

            state_q <= next_state;

            case (state_q)
                IDLE: begin
                    write_phase_q <= 1'b0;
                    if (accept_valid) begin
                        src_addr_q  <= cfg_src_addr;
                        dst_addr_q  <= cfg_dst_addr;
                        remaining_q <= cfg_len;
                        err_code_q  <= 2'd0;
                    end else if (accept_error) begin
                        if (!len_nonzero)
                            err_code_q <= 2'd2;
                        else
                            err_code_q <= 2'd1;
                    end
                end
                READ_ST: begin
                    if (ahb_done && !ahb_error) begin
                        src_addr_q  <= src_addr_q + (burst_len << 2);
                        write_phase_q <= 1'b1;
                    end
                    if (ahb_error) begin
                        err_code_q <= 2'd3;
                    end
                end
                WRITE_ST: begin
                    if (ahb_done && !ahb_error) begin
                        dst_addr_q <= dst_addr_q + (burst_len << 2);
                    end
                    if (ahb_error) begin
                        err_code_q <= 2'd3;
                    end
                end
                UPDATE: begin
                    write_phase_q <= 1'b0;
                    if (remaining_q > burst_len)
                        remaining_q <= remaining_q - burst_len;
                    else
                        remaining_q <= 16'd0;
                end
                DONE_ST: begin
                    done_pulse_q <= 1'b1;
                end
                ERROR_ST: begin
                    error_pulse_q <= 1'b1;
                end
                default: begin
                    // CFG, REQUEST: no counter updates
                end
            endcase
        end
    end

    // Next-state logic
    always @(*) begin
        next_state = state_q;
        case (state_q)
            IDLE: begin
                if (accept_valid)
                    next_state = CFG;
                else if (accept_error)
                    next_state = ERROR_ST;
            end
            CFG: begin
                next_state = REQUEST;
            end
            REQUEST: begin
                if (ch_grant)
                    next_state = write_phase_q ? WRITE_ST : READ_ST;
            end
            READ_ST: begin
                if (ahb_error)
                    next_state = ERROR_ST;
                else if (ahb_done)
                    next_state = REQUEST;  // FIX: go back to REQUEST for write phase
            end
            WRITE_ST: begin
                if (ahb_error)
                    next_state = ERROR_ST;
                else if (ahb_done)
                    next_state = UPDATE;
            end
            UPDATE: begin
                if (remaining_q > burst_len)
                    next_state = REQUEST;
                else
                    next_state = DONE_ST;
            end
            DONE_ST: begin
                next_state = IDLE;
            end
            ERROR_ST: begin
                next_state = IDLE;
            end
            default: begin
                next_state = IDLE;
            end
        endcase
    end

endmodule

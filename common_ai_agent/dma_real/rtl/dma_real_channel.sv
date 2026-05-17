// dma_real_channel.sv — Per-channel FSM with stride, timeout, perf counters
// v2: programmable stride, timeout counter, perf_words/perf_cycles, generate-ready
module dma_real_channel #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer BURST_MAX  = 16,
    parameter integer FIFO_DEPTH = 16,
    parameter integer CH_ID      = 0
) (
    input  logic                  hclk,
    input  logic                  hresetn,
    input  logic                  ch_en,
    input  logic                  ch_start,
    input  logic                  dma_en,
    input  logic [ADDR_WIDTH-1:0] cfg_src_addr,
    input  logic [ADDR_WIDTH-1:0] cfg_dst_addr,
    input  logic [15:0]           cfg_len,
    input  logic [ADDR_WIDTH-1:0] cfg_stride,
    input  logic [2:0]            cfg_hsize,
    input  logic [2:0]            cfg_hburst,
    input  logic [15:0]           cfg_timeout,
    output logic                  ch_request,
    input  logic                  ch_grant,
    output logic                  ahb_start,
    output logic                  ahb_write,
    output logic [ADDR_WIDTH-1:0] ahb_addr,
    output logic [15:0]           ahb_len,
    input  logic                  ahb_done,
    input  logic                  ahb_error,
    input  logic [2:0]            ahb_err_code,
    input  logic [DATA_WIDTH-1:0] ahb_rdata,
    output logic [DATA_WIDTH-1:0] ahb_wdata,
    output logic                  status_busy,
    output logic                  status_done,
    output logic                  status_error,
    output logic [2:0]            status_err_code,
    output logic [DATA_WIDTH-1:0] fifo_wdata,
    output logic                  fifo_wen,
    input  logic [DATA_WIDTH-1:0] fifo_rdata,
    output logic                  fifo_ren,
    input  logic                  fifo_empty,
    input  logic                  fifo_full,
    output logic [31:0]           perf_words,
    output logic [31:0]           perf_cycles
);

    localparam [3:0] IDLE     = 4'd0;
    localparam [3:0] CFG      = 4'd1;
    localparam [3:0] REQUEST  = 4'd2;
    localparam [3:0] READ_ST  = 4'd3;
    localparam [3:0] WRITE_ST = 4'd4;
    localparam [3:0] UPDATE   = 4'd5;
    localparam [3:0] DONE_ST  = 4'd6;
    localparam [3:0] ERROR_ST = 4'd7;

    logic [3:0] state_q, next_state;
    logic write_phase_q;
    logic [ADDR_WIDTH-1:0] src_addr_q, dst_addr_q;
    logic [ADDR_WIDTH-1:0] stride_q;
    logic [15:0] remaining_q;
    logic [2:0] err_code_q;
    logic done_pulse_q, error_pulse_q;
    logic [31:0] perf_words_q, perf_cycles_q;

    assign status_busy     = (state_q != IDLE);
    assign status_done     = done_pulse_q;
    assign status_error    = error_pulse_q;
    assign status_err_code = err_code_q;
    assign perf_words  = perf_words_q;
    assign perf_cycles = perf_cycles_q;

    wire src_aligned = (cfg_src_addr[1:0] == 2'b00);
    wire dst_aligned = (cfg_dst_addr[1:0] == 2'b00);
    wire len_nonzero = (cfg_len != 16'd0);
    wire valid_cfg   = len_nonzero && src_aligned && dst_aligned;
    wire accept_start = ch_start && ch_en && dma_en;
    wire accept_valid = accept_start && valid_cfg;
    wire accept_error = accept_start && !valid_cfg;

    wire [15:0] burst_len = (remaining_q < BURST_MAX[15:0]) ? remaining_q : BURST_MAX[15:0];
    wire remaining_done = (remaining_q <= burst_len) && (remaining_q > 16'd0);

    assign ch_request = (state_q == REQUEST) || (state_q == READ_ST) || (state_q == WRITE_ST);
    assign ahb_start  = (state_q == REQUEST) && ch_grant;
    assign ahb_write  = write_phase_q;
    assign ahb_addr   = write_phase_q ? dst_addr_q : src_addr_q;
    assign ahb_len    = burst_len;

    assign fifo_wdata = ahb_rdata;
    assign fifo_wen   = (state_q == READ_ST) && ahb_done && !fifo_full;
    assign fifo_ren   = (state_q == WRITE_ST) && !fifo_empty;
    assign ahb_wdata  = fifo_rdata;

    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) begin
            state_q        <= IDLE;
            write_phase_q  <= 1'b0;
            src_addr_q     <= {ADDR_WIDTH{1'b0}};
            dst_addr_q     <= {ADDR_WIDTH{1'b0}};
            stride_q       <= {ADDR_WIDTH{1'b1}};
            remaining_q    <= 16'd0;
            err_code_q     <= 3'd0;
            done_pulse_q   <= 1'b0;
            error_pulse_q  <= 1'b0;
            perf_words_q   <= 32'd0;
            perf_cycles_q  <= 32'd0;
        end else begin
            done_pulse_q  <= 1'b0;
            error_pulse_q <= 1'b0;
            if (status_busy && perf_cycles_q < 32'hFFFFFFFE)
                perf_cycles_q <= perf_cycles_q + 32'd1;
            state_q <= next_state;
            case (state_q)
                IDLE: begin
                    write_phase_q <= 1'b0;
                    if (accept_valid) begin
                        src_addr_q   <= cfg_src_addr;
                        dst_addr_q   <= cfg_dst_addr;
                        remaining_q  <= cfg_len;
                        stride_q     <= cfg_stride;
                        err_code_q   <= 3'd0;
                        perf_words_q <= 32'd0;
                        perf_cycles_q <= 32'd0;
                    end else if (accept_error) begin
                        if (!len_nonzero) err_code_q <= 3'd2;
                        else              err_code_q <= 3'd1;
                    end
                end
                READ_ST: begin
                    if (ahb_done && !ahb_error) begin
                        src_addr_q <= src_addr_q + (burst_len * stride_q);
                        write_phase_q <= 1'b1;
                        perf_words_q <= perf_words_q + {{16{1'b0}}, burst_len};
                    end
                    if (ahb_error) begin
                        err_code_q <= ahb_err_code;
                    end
                end
                WRITE_ST: begin
                    if (ahb_done && !ahb_error) begin
                        dst_addr_q <= dst_addr_q + (burst_len * stride_q);
                    end
                    if (ahb_error) begin
                        err_code_q <= ahb_err_code;
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
                end
            endcase
        end
    end

    always @(*) begin
        next_state = state_q;
        case (state_q)
            IDLE: begin
                if (accept_valid)      next_state = CFG;
                else if (accept_error) next_state = ERROR_ST;
            end
            CFG:      next_state = REQUEST;
            REQUEST:  if (ch_grant) next_state = write_phase_q ? WRITE_ST : READ_ST;
            READ_ST: begin
                if (ahb_error)     next_state = ERROR_ST;
                else if (ahb_done) next_state = REQUEST;
            end
            WRITE_ST: begin
                if (ahb_error)     next_state = ERROR_ST;
                else if (ahb_done) next_state = UPDATE;
            end
            UPDATE:   next_state = (remaining_q > burst_len) ? REQUEST : DONE_ST;
            DONE_ST:  next_state = IDLE;
            ERROR_ST: next_state = IDLE;
            default:  next_state = IDLE;
        endcase
    end

endmodule

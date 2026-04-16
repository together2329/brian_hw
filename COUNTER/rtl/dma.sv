`timescale 1ns/1ps

module dma #(
    parameter int ADDR_WIDTH = 32,
    parameter int DATA_WIDTH = 512,
    parameter int LEN_WIDTH  = 16
) (
    input  logic                      clk,
    input  logic                      rst_n,

    // Control interface
    input  logic                      start,
    input  logic [ADDR_WIDTH-1:0]     src_addr,
    input  logic [ADDR_WIDTH-1:0]     dst_addr,
    input  logic [LEN_WIDTH-1:0]      length,      // number of DATA_WIDTH words
    output logic                      busy,
    output logic                      done,

    // Simple memory interface (shared for src and dst)
    output logic                      mem_req,
    output logic [ADDR_WIDTH-1:0]     mem_addr,
    output logic                      mem_write,   // 0 = read, 1 = write
    output logic [DATA_WIDTH-1:0]     mem_wdata,
    input  logic [DATA_WIDTH-1:0]     mem_rdata,
    input  logic                      mem_ready
);

    typedef enum logic [2:0] {
        IDLE,
        READ_REQ,
        READ_WAIT,
        WRITE_REQ,
        WRITE_WAIT
    } state_t;

    state_t                 state, state_n;
    logic [ADDR_WIDTH-1:0]  src_addr_q, src_addr_n;
    logic [ADDR_WIDTH-1:0]  dst_addr_q, dst_addr_n;
    logic [LEN_WIDTH-1:0]   remaining_q, remaining_n;
    logic [DATA_WIDTH-1:0]  data_buf_q, data_buf_n;

    // Busy/done
    assign busy = (state != IDLE);

    localparam int WORD_BYTES = DATA_WIDTH / 8;

    // Sequential logic — state and data registers only
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state       <= IDLE;
            src_addr_q  <= '0;
            dst_addr_q  <= '0;
            remaining_q <= '0;
            data_buf_q  <= '0;
            done        <= 1'b0;
        end else begin
            state       <= state_n;
            src_addr_q  <= src_addr_n;
            dst_addr_q  <= dst_addr_n;
            remaining_q <= remaining_n;
            data_buf_q  <= data_buf_n;
            done        <= ((state == WRITE_REQ || state == WRITE_WAIT) &&
                            mem_ready && (remaining_q == 1));
        end
    end

    // Combinational next-state and output logic
    // mem_req / mem_write / mem_addr / mem_wdata are driven combinationally
    always_comb begin
        // defaults — hold addresses, clear request
        state_n       = state;
        src_addr_n    = src_addr_q;
        dst_addr_n    = dst_addr_q;
        remaining_n   = remaining_q;
        data_buf_n    = data_buf_q;

        mem_req    = 1'b0;
        mem_write  = 1'b0;
        mem_addr   = src_addr_q;
        mem_wdata  = '0;

        case (state)
            IDLE: begin
                if (start && (length != 0)) begin
                    src_addr_n  = src_addr;
                    dst_addr_n  = dst_addr;
                    remaining_n = length;
                    state_n     = READ_REQ;
                end
            end

            READ_REQ: begin
                // Issue read request
                mem_req   = 1'b1;
                mem_write = 1'b0;
                mem_addr  = src_addr_q;
                if (mem_ready) begin
                    data_buf_n = mem_rdata;
                    state_n    = WRITE_REQ;
                end else begin
                    state_n    = READ_WAIT;
                end
            end

            READ_WAIT: begin
                mem_req   = 1'b1;
                mem_write = 1'b0;
                mem_addr  = src_addr_q;
                if (mem_ready) begin
                    data_buf_n = mem_rdata;
                    state_n    = WRITE_REQ;
                end
            end

            WRITE_REQ: begin
                // Issue write request with buffered data
                mem_req   = 1'b1;
                mem_write = 1'b1;
                mem_addr  = dst_addr_q;
                mem_wdata = data_buf_q;
                if (mem_ready) begin
                    // Word completed
                    src_addr_n  = src_addr_q + (WORD_BYTES);
                    dst_addr_n  = dst_addr_q + (WORD_BYTES);
                    remaining_n = remaining_q - 1'b1;
                    if (remaining_q == 1) begin
                        state_n = IDLE;
                    end else begin
                        state_n = READ_REQ;
                    end
                end else begin
                    state_n = WRITE_WAIT;
                end
            end

            WRITE_WAIT: begin
                mem_req   = 1'b1;
                mem_write = 1'b1;
                mem_addr  = dst_addr_q;
                mem_wdata = data_buf_q;
                if (mem_ready) begin
                    src_addr_n  = src_addr_q + (WORD_BYTES);
                    dst_addr_n  = dst_addr_q + (WORD_BYTES);
                    remaining_n = remaining_q - 1'b1;
                    if (remaining_q == 1) begin
                        state_n = IDLE;
                    end else begin
                        state_n = READ_REQ;
                    end
                end
            end

            default: state_n = IDLE;
        endcase
    end

endmodule

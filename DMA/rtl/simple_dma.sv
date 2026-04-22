`timescale 1ns/1ps

module simple_dma #(
    parameter int unsigned ADDR_WIDTH = 32,
    parameter int unsigned DATA_WIDTH = 32,
    parameter int unsigned LEN_WIDTH  = 16
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    start,
    input  logic [ADDR_WIDTH-1:0]   src_addr,
    input  logic [ADDR_WIDTH-1:0]   dst_addr,
    input  logic [LEN_WIDTH-1:0]    len,
    output logic                    busy,
    output logic                    done,
    output logic                    error,
    output logic                    rd_req_valid,
    output logic [ADDR_WIDTH-1:0]   rd_req_addr,
    input  logic                    rd_req_ready,
    input  logic                    rd_data_valid,
    input  logic [DATA_WIDTH-1:0]   rd_data,
    output logic                    rd_data_ready,
    output logic                    wr_req_valid,
    output logic [ADDR_WIDTH-1:0]   wr_req_addr,
    output logic [DATA_WIDTH-1:0]   wr_req_data,
    input  logic                    wr_req_ready
);

    typedef enum logic [2:0] {
        ST_IDLE,
        ST_READ_REQ,
        ST_READ_WAIT,
        ST_WRITE_REQ,
        ST_DONE
    } state_t;

    localparam logic [LEN_WIDTH-1:0]  LEN_ZERO    = '0;
    localparam logic [LEN_WIDTH-1:0]  LEN_ONE     = {{(LEN_WIDTH-1){1'b0}}, 1'b1};
    localparam logic [ADDR_WIDTH-1:0] ADDR_STRIDE = DATA_WIDTH / 8;

    state_t                 state_q;
    logic [ADDR_WIDTH-1:0]  src_addr_q;
    logic [ADDR_WIDTH-1:0]  dst_addr_q;
    logic [LEN_WIDTH-1:0]   remaining_q;
    logic [DATA_WIDTH-1:0]  data_buf_q;

    assign busy = (state_q != ST_IDLE);

    assign rd_req_valid  = (state_q == ST_READ_REQ);
    assign rd_req_addr   = src_addr_q;
    assign rd_data_ready = (state_q == ST_READ_WAIT);

    assign wr_req_valid = (state_q == ST_WRITE_REQ);
    assign wr_req_addr  = dst_addr_q;
    assign wr_req_data  = data_buf_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q     <= ST_IDLE;
            src_addr_q  <= '0;
            dst_addr_q  <= '0;
            remaining_q <= '0;
            data_buf_q  <= '0;
            done        <= 1'b0;
            error       <= 1'b0;
        end else begin
            done <= 1'b0;

            if ((state_q != ST_IDLE) && start) begin
                error <= 1'b1;
            end

            case (state_q)
                ST_IDLE: begin
                    error <= 1'b0;

                    if (start) begin
                        src_addr_q  <= src_addr;
                        dst_addr_q  <= dst_addr;
                        remaining_q <= len;

                        if (len == LEN_ZERO) begin
                            state_q <= ST_DONE;
                        end else begin
                            state_q <= ST_READ_REQ;
                        end
                    end
                end

                ST_READ_REQ: begin
                    if (rd_req_valid && rd_req_ready) begin
                        state_q <= ST_READ_WAIT;
                    end
                end

                ST_READ_WAIT: begin
                    if (rd_data_valid && rd_data_ready) begin
                        data_buf_q <= rd_data;
                        state_q    <= ST_WRITE_REQ;
                    end
                end

                ST_WRITE_REQ: begin
                    if (wr_req_valid && wr_req_ready) begin
                        if (remaining_q == LEN_ONE) begin
                            remaining_q <= '0;
                            state_q     <= ST_DONE;
                        end else begin
                            src_addr_q  <= src_addr_q + ADDR_STRIDE;
                            dst_addr_q  <= dst_addr_q + ADDR_STRIDE;
                            remaining_q <= remaining_q - LEN_ONE;
                            state_q     <= ST_READ_REQ;
                        end
                    end
                end

                ST_DONE: begin
                    done    <= 1'b1;
                    state_q <= ST_IDLE;
                end

                default: begin
                    state_q <= ST_IDLE;
                end
            endcase
        end
    end

endmodule

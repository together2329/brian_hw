`timescale 1ns/1ps

module dma (
    input  logic        clk,
    input  logic        rst_n,

    // Control/config interface
    input  logic [31:0] src_addr,
    input  logic [31:0] dst_addr,
    input  logic [31:0] len,
    input  logic        start,
    input  logic        clear_done,
    input  logic        clear_error,
    output logic        busy,
    output logic        done,
    output logic        error,

    // Read request/response channel
    output logic        rd_req_valid,
    input  logic        rd_req_ready,
    output logic [31:0] rd_req_addr,
    input  logic        rd_rsp_valid,
    output logic        rd_rsp_ready,
    input  logic [31:0] rd_rsp_data,

    // Write request/response channel
    output logic        wr_req_valid,
    input  logic        wr_req_ready,
    output logic [31:0] wr_req_addr,
    output logic [31:0] wr_req_data,
    input  logic        wr_rsp_valid,
    output logic        wr_rsp_ready
);

    typedef enum logic [2:0] {
        S_IDLE    = 3'd0,
        S_RD_REQ  = 3'd1,
        S_RD_WAIT = 3'd2,
        S_WR_REQ  = 3'd3,
        S_WR_WAIT = 3'd4
    } dma_state_t;

    dma_state_t   state;
    logic [31:0]  cur_src;
    logic [31:0]  cur_dst;
    logic [31:0]  beats_rem;
    logic [31:0]  rd_data_q;

    logic align_err;
    assign align_err = (src_addr[1:0] != 2'b00) ||
                       (dst_addr[1:0] != 2'b00) ||
                       (len[1:0]      != 2'b00);

    // Simple 1-beat-at-a-time handshake outputs derived from state.
    assign rd_req_valid = (state == S_RD_REQ);
    assign rd_req_addr  = cur_src;
    assign rd_rsp_ready = (state == S_RD_WAIT);

    assign wr_req_valid = (state == S_WR_REQ);
    assign wr_req_addr  = cur_dst;
    assign wr_req_data  = rd_data_q;
    assign wr_rsp_ready = (state == S_WR_WAIT);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= S_IDLE;
            cur_src    <= 32'h0;
            cur_dst    <= 32'h0;
            beats_rem  <= 32'h0;
            rd_data_q  <= 32'h0;
            busy       <= 1'b0;
            done       <= 1'b0;
            error      <= 1'b0;
        end else begin
            if (clear_done) begin
                done <= 1'b0;
            end
            if (clear_error) begin
                error <= 1'b0;
            end

            // Illegal request while transfer active.
            if (start && busy) begin
                error <= 1'b1;
            end

            unique case (state)
                S_IDLE: begin
                    if (start) begin
                        if (align_err) begin
                            error <= 1'b1;
                        end else if (len == 32'd0) begin
                            // Successful no-op completion.
                            done  <= 1'b1;
                            busy  <= 1'b0;
                            state <= S_IDLE;
                        end else begin
                            cur_src   <= src_addr;
                            cur_dst   <= dst_addr;
                            beats_rem <= {2'b00, len[31:2]};
                            busy      <= 1'b1;
                            state     <= S_RD_REQ;
                        end
                    end
                end

                S_RD_REQ: begin
                    if (rd_req_ready) begin
                        state <= S_RD_WAIT;
                    end
                end

                S_RD_WAIT: begin
                    if (rd_rsp_valid) begin
                        rd_data_q <= rd_rsp_data;
                        state     <= S_WR_REQ;
                    end
                end

                S_WR_REQ: begin
                    if (wr_req_ready) begin
                        state <= S_WR_WAIT;
                    end
                end

                S_WR_WAIT: begin
                    if (wr_rsp_valid) begin
                        cur_src <= cur_src + 32'd4;
                        cur_dst <= cur_dst + 32'd4;

                        if (beats_rem == 32'd1) begin
                            beats_rem <= 32'd0;
                            busy      <= 1'b0;
                            done      <= 1'b1;
                            state     <= S_IDLE;
                        end else begin
                            beats_rem <= beats_rem - 32'd1;
                            state     <= S_RD_REQ;
                        end
                    end
                end

                default: begin
                    state <= S_IDLE;
                    busy  <= 1'b0;
                end
            endcase
        end
    end

endmodule

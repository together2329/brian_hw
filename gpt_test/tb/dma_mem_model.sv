`timescale 1ns/1ps

module dma_mem_model #(
    parameter int MEM_BYTES         = 4096,
    parameter int RD_LATENCY_CYCLES = 1,
    parameter int WR_LATENCY_CYCLES = 1,
    parameter bit USE_STALLS        = 0,
    parameter int STALL_DIVISOR     = 3
) (
    input  logic        clk,
    input  logic        rst_n,

    // Read request/response channel
    input  logic        rd_req_valid,
    output logic        rd_req_ready,
    input  logic [31:0] rd_req_addr,
    output logic        rd_rsp_valid,
    input  logic        rd_rsp_ready,
    output logic [31:0] rd_rsp_data,

    // Write request/response channel
    input  logic        wr_req_valid,
    output logic        wr_req_ready,
    input  logic [31:0] wr_req_addr,
    input  logic [31:0] wr_req_data,
    output logic        wr_rsp_valid,
    input  logic        wr_rsp_ready
);

    localparam int MEM_WORDS = MEM_BYTES/4;

    logic [31:0] mem [0:MEM_WORDS-1];

    logic [31:0] rd_addr_q;
    logic [31:0] wr_addr_q;
    logic [31:0] wr_data_q;

    int rd_countdown;
    int wr_countdown;

    logic rd_pending;
    logic wr_pending;

    int stall_counter;

    // ------------------------------
    // Public helper tasks/functions
    // ------------------------------
    task automatic init_pattern(input logic [31:0] seed);
        int i;
        begin
            for (i = 0; i < MEM_WORDS; i++) begin
                mem[i] = seed ^ (32'h9E37_79B9 * i);
            end
        end
    endtask

    task automatic clear_mem();
        int i;
        begin
            for (i = 0; i < MEM_WORDS; i++) begin
                mem[i] = 32'h0;
            end
        end
    endtask

    task automatic poke_word(input logic [31:0] byte_addr, input logic [31:0] data);
        int idx;
        begin
            idx = byte_addr[31:2];
            if ((byte_addr[1:0] != 2'b00) || (idx < 0) || (idx >= MEM_WORDS)) begin
                $fatal(1, "dma_mem_model poke_word invalid addr 0x%08x", byte_addr);
            end
            mem[idx] = data;
        end
    endtask

    task automatic peek_word(input logic [31:0] byte_addr, output logic [31:0] data);
        int idx;
        begin
            idx = byte_addr[31:2];
            if ((byte_addr[1:0] != 2'b00) || (idx < 0) || (idx >= MEM_WORDS)) begin
                $fatal(1, "dma_mem_model peek_word invalid addr 0x%08x", byte_addr);
            end
            data = mem[idx];
        end
    endtask

    function automatic logic [31:0] get_word(input logic [31:0] byte_addr);
        int idx;
        begin
            idx = byte_addr[31:2];
            if ((byte_addr[1:0] != 2'b00) || (idx < 0) || (idx >= MEM_WORDS)) begin
                $fatal(1, "dma_mem_model get_word invalid addr 0x%08x", byte_addr);
                get_word = 32'hX;
            end else begin
                get_word = mem[idx];
            end
        end
    endfunction

    task automatic check_copy_region(
        input logic [31:0] src_base,
        input logic [31:0] dst_base,
        input logic [31:0] len_bytes,
        output int errors
    );
        logic [31:0] s;
        logic [31:0] d;
        logic [31:0] ofs;
        begin
            errors = 0;
            if (len_bytes[1:0] != 2'b00) begin
                $fatal(1, "check_copy_region len_bytes not aligned: %0d", len_bytes);
            end
            for (ofs = 0; ofs < len_bytes; ofs += 4) begin
                s = get_word(src_base + ofs);
                d = get_word(dst_base + ofs);
                if (s !== d) begin
                    errors++;
                    $display("[MEMCHK] MISMATCH ofs=0x%08x src=0x%08x dst=0x%08x", ofs, s, d);
                end
            end
        end
    endtask

    // ------------------------------
    // Deterministic ready generation
    // ------------------------------
    always_comb begin
        if (!USE_STALLS) begin
            rd_req_ready = 1'b1;
            wr_req_ready = 1'b1;
        end else begin
            // Deterministic periodic stalls based on a counter.
            rd_req_ready = (stall_counter % STALL_DIVISOR) != 0;
            wr_req_ready = (stall_counter % (STALL_DIVISOR + 1)) != 0;
        end
    end

    // ------------------------------
    // Request capture + timed response
    // ------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_addr_q     <= 32'h0;
            wr_addr_q     <= 32'h0;
            wr_data_q     <= 32'h0;
            rd_rsp_valid  <= 1'b0;
            wr_rsp_valid  <= 1'b0;
            rd_rsp_data   <= 32'h0;
            rd_countdown  <= 0;
            wr_countdown  <= 0;
            rd_pending    <= 1'b0;
            wr_pending    <= 1'b0;
            stall_counter <= 0;
        end else begin
            stall_counter <= stall_counter + 1;

            // Accept read request if possible
            if (rd_req_valid && rd_req_ready && !rd_pending && !rd_rsp_valid) begin
                rd_addr_q    <= rd_req_addr;
                rd_countdown <= (RD_LATENCY_CYCLES > 0) ? RD_LATENCY_CYCLES : 1;
                rd_pending   <= 1'b1;
            end

            // Accept write request if possible
            if (wr_req_valid && wr_req_ready && !wr_pending && !wr_rsp_valid) begin
                wr_addr_q    <= wr_req_addr;
                wr_data_q    <= wr_req_data;
                wr_countdown <= (WR_LATENCY_CYCLES > 0) ? WR_LATENCY_CYCLES : 1;
                wr_pending   <= 1'b1;
            end

            // Progress read timing pipeline
            if (rd_pending) begin
                if (rd_countdown > 1) begin
                    rd_countdown <= rd_countdown - 1;
                end else begin
                    if (rd_addr_q[1:0] != 2'b00 || rd_addr_q[31:2] >= MEM_WORDS) begin
                        $fatal(1, "dma_mem_model read addr out of range/alignment: 0x%08x", rd_addr_q);
                    end
                    rd_rsp_data  <= mem[rd_addr_q[31:2]];
                    rd_rsp_valid <= 1'b1;
                    rd_pending   <= 1'b0;
                end
            end

            // Hold read response until consumed
            if (rd_rsp_valid && rd_rsp_ready) begin
                rd_rsp_valid <= 1'b0;
            end

            // Progress write timing pipeline
            if (wr_pending) begin
                if (wr_countdown > 1) begin
                    wr_countdown <= wr_countdown - 1;
                end else begin
                    if (wr_addr_q[1:0] != 2'b00 || wr_addr_q[31:2] >= MEM_WORDS) begin
                        $fatal(1, "dma_mem_model write addr out of range/alignment: 0x%08x", wr_addr_q);
                    end
                    mem[wr_addr_q[31:2]] <= wr_data_q;
                    wr_rsp_valid         <= 1'b1;
                    wr_pending           <= 1'b0;
                end
            end

            // Hold write response until consumed
            if (wr_rsp_valid && wr_rsp_ready) begin
                wr_rsp_valid <= 1'b0;
            end
        end
    end

endmodule

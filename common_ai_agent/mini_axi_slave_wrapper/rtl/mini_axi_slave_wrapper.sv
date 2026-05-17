// mini_axi_slave_wrapper.sv
//
// Minimal AXI4 slave wrapper with a 32-bit memory aperture and four
// outstanding single-beat read/write transactions. The wrapper intentionally
// keeps the backend simple: accepted writes update an internal word array and
// accepted reads return one word from that array. AXI bursts are consumed as
// single-beat transactions and reported with SLVERR.

`timescale 1ns/1ps

module mini_axi_slave_wrapper #(
    parameter integer ADDR_WIDTH  = 8,
    parameter integer DATA_WIDTH  = 32,
    parameter integer ID_WIDTH    = 4,
    parameter integer OUTSTANDING = 4,
    parameter integer MEM_WORDS   = 64
) (
    input  logic                     ACLK,
    input  logic                     ARESETn,

    // AXI write address channel
    input  logic [ID_WIDTH-1:0]      S_AXI_AWID,
    input  logic [ADDR_WIDTH-1:0]    S_AXI_AWADDR,
    input  logic [7:0]               S_AXI_AWLEN,
    input  logic [2:0]               S_AXI_AWSIZE,
    input  logic [1:0]               S_AXI_AWBURST,
    input  logic                     S_AXI_AWVALID,
    output logic                     S_AXI_AWREADY,

    // AXI write data channel
    input  logic [DATA_WIDTH-1:0]    S_AXI_WDATA,
    input  logic [(DATA_WIDTH/8)-1:0] S_AXI_WSTRB,
    input  logic                     S_AXI_WLAST,
    input  logic                     S_AXI_WVALID,
    output logic                     S_AXI_WREADY,

    // AXI write response channel
    output logic [ID_WIDTH-1:0]      S_AXI_BID,
    output logic [1:0]               S_AXI_BRESP,
    output logic                     S_AXI_BVALID,
    input  logic                     S_AXI_BREADY,

    // AXI read address channel
    input  logic [ID_WIDTH-1:0]      S_AXI_ARID,
    input  logic [ADDR_WIDTH-1:0]    S_AXI_ARADDR,
    input  logic [7:0]               S_AXI_ARLEN,
    input  logic [2:0]               S_AXI_ARSIZE,
    input  logic [1:0]               S_AXI_ARBURST,
    input  logic                     S_AXI_ARVALID,
    output logic                     S_AXI_ARREADY,

    // AXI read data channel
    output logic [ID_WIDTH-1:0]      S_AXI_RID,
    output logic [DATA_WIDTH-1:0]    S_AXI_RDATA,
    output logic [1:0]               S_AXI_RRESP,
    output logic                     S_AXI_RLAST,
    output logic                     S_AXI_RVALID,
    input  logic                     S_AXI_RREADY,

    // Debug/status counters exposed for verification and integration.
    output logic [2:0]               write_outstanding_o,
    output logic [2:0]               read_outstanding_o
);

    localparam integer STRB_WIDTH = DATA_WIDTH / 8;
    localparam integer ADDR_LSB   = (STRB_WIDTH <= 1) ? 0 : $clog2(STRB_WIDTH);
    localparam integer INDEX_W    = (MEM_WORDS <= 2) ? 1 : $clog2(MEM_WORDS);
    localparam integer PTR_W      = (OUTSTANDING <= 2) ? 1 : $clog2(OUTSTANDING);
    localparam integer AXI_SIZE   = (STRB_WIDTH <= 1) ? 0 : $clog2(STRB_WIDTH);
    localparam integer WORD_ADDR_W = INDEX_W + 1;

    localparam logic [1:0] RESP_OKAY  = 2'b00;
    localparam logic [1:0] RESP_SLVERR = 2'b10;
    localparam logic [2:0] OUTSTANDING_COUNT = 3'd4;
    localparam logic [PTR_W-1:0] OUTSTANDING_LAST = PTR_W'(OUTSTANDING - 1);
    localparam logic [WORD_ADDR_W-1:0] MEM_WORDS_LIMIT = WORD_ADDR_W'(MEM_WORDS);
    localparam logic [2:0] AXI_SIZE_BITS = 3'(AXI_SIZE);

    logic [DATA_WIDTH-1:0] mem [0:MEM_WORDS-1];

    logic [ID_WIDTH-1:0]   aw_id_q    [0:OUTSTANDING-1];
    logic [ADDR_WIDTH-1:0] aw_addr_q  [0:OUTSTANDING-1];
    logic [7:0]            aw_len_q   [0:OUTSTANDING-1];
    logic [2:0]            aw_size_q  [0:OUTSTANDING-1];
    logic [1:0]            aw_burst_q [0:OUTSTANDING-1];
    logic [PTR_W-1:0]      aw_wr_ptr;
    logic [PTR_W-1:0]      aw_rd_ptr;
    logic [2:0]            aw_count;

    logic [ID_WIDTH-1:0]   b_id_q     [0:OUTSTANDING-1];
    logic [1:0]            b_resp_q   [0:OUTSTANDING-1];
    logic [PTR_W-1:0]      b_wr_ptr;
    logic [PTR_W-1:0]      b_rd_ptr;
    logic [2:0]            b_count;

    logic [ID_WIDTH-1:0]   r_id_q     [0:OUTSTANDING-1];
    logic [DATA_WIDTH-1:0] r_data_q   [0:OUTSTANDING-1];
    logic [1:0]            r_resp_q   [0:OUTSTANDING-1];
    logic [PTR_W-1:0]      r_wr_ptr;
    logic [PTR_W-1:0]      r_rd_ptr;
    logic [2:0]            r_count;

    function automatic [PTR_W-1:0] bump_ptr(input [PTR_W-1:0] ptr);
        begin
            bump_ptr = (ptr == OUTSTANDING_LAST) ? '0 : ptr + {{(PTR_W-1){1'b0}}, 1'b1};
        end
    endfunction

    wire aw_push = S_AXI_AWVALID && S_AXI_AWREADY;
    wire w_pop   = S_AXI_WVALID  && S_AXI_WREADY;
    wire b_pop   = S_AXI_BVALID  && S_AXI_BREADY;
    wire ar_push = S_AXI_ARVALID && S_AXI_ARREADY;
    wire r_pop   = S_AXI_RVALID  && S_AXI_RREADY;

    wire [INDEX_W-1:0]    aw_head_index     = aw_addr_q[aw_rd_ptr][ADDR_LSB +: INDEX_W];
    wire [WORD_ADDR_W-1:0] aw_head_word_addr = {1'b0, aw_head_index};
    wire                  aw_head_addr_ok  = (aw_head_word_addr < MEM_WORDS_LIMIT)
                                           && (aw_addr_q[aw_rd_ptr][ADDR_LSB-1:0] == '0);
    wire aw_head_size_ok = (aw_size_q[aw_rd_ptr] == AXI_SIZE_BITS);
    wire aw_head_len_ok  = (aw_len_q[aw_rd_ptr] == 8'd0) && S_AXI_WLAST;
    wire aw_head_burst_ok = (aw_burst_q[aw_rd_ptr] == 2'b00)
                         || (aw_burst_q[aw_rd_ptr] == 2'b01);
    wire write_ok = aw_head_addr_ok && aw_head_size_ok && aw_head_len_ok && aw_head_burst_ok;
    wire [INDEX_W-1:0] write_idx = aw_head_index;

    wire [INDEX_W-1:0]    ar_index     = S_AXI_ARADDR[ADDR_LSB +: INDEX_W];
    wire [WORD_ADDR_W-1:0] ar_word_addr = {1'b0, ar_index};
    wire ar_addr_ok  = (ar_word_addr < MEM_WORDS_LIMIT) && (S_AXI_ARADDR[ADDR_LSB-1:0] == '0);
    wire ar_size_ok  = (S_AXI_ARSIZE == AXI_SIZE_BITS);
    wire ar_len_ok   = (S_AXI_ARLEN == 8'd0);
    wire ar_burst_ok = (S_AXI_ARBURST == 2'b00) || (S_AXI_ARBURST == 2'b01);
    wire read_ok     = ar_addr_ok && ar_size_ok && ar_len_ok && ar_burst_ok;
    wire [INDEX_W-1:0] read_idx = ar_index;

    assign write_outstanding_o = aw_count + b_count;
    assign read_outstanding_o  = r_count;

    assign S_AXI_AWREADY = (write_outstanding_o < OUTSTANDING_COUNT);
    assign S_AXI_WREADY  = (aw_count != 3'd0) && (b_count < OUTSTANDING_COUNT);

    assign S_AXI_BVALID  = (b_count != 3'd0);
    assign S_AXI_BID     = b_id_q[b_rd_ptr];
    assign S_AXI_BRESP   = b_resp_q[b_rd_ptr];

    assign S_AXI_ARREADY = (r_count < OUTSTANDING_COUNT);

    assign S_AXI_RVALID  = (r_count != 3'd0);
    assign S_AXI_RID     = r_id_q[r_rd_ptr];
    assign S_AXI_RDATA   = r_data_q[r_rd_ptr];
    assign S_AXI_RRESP   = r_resp_q[r_rd_ptr];
    assign S_AXI_RLAST   = 1'b1;

    integer i;
    integer byte_i;

    initial begin
        if (DATA_WIDTH % 8 != 0) begin
            $fatal(1, "DATA_WIDTH must be byte-addressable");
        end
        if (OUTSTANDING != 4) begin
            $fatal(1, "mini_axi_slave_wrapper is fixed to OUTSTANDING=4");
        end
        if (MEM_WORDS < OUTSTANDING) begin
            $fatal(1, "MEM_WORDS must be at least OUTSTANDING");
        end
    end

    always_ff @(posedge ACLK or negedge ARESETn) begin
        if (!ARESETn) begin
            aw_wr_ptr <= '0;
            aw_rd_ptr <= '0;
            aw_count  <= 3'd0;
            b_wr_ptr  <= '0;
            b_rd_ptr  <= '0;
            b_count   <= 3'd0;
            r_wr_ptr  <= '0;
            r_rd_ptr  <= '0;
            r_count   <= 3'd0;

            for (i = 0; i < MEM_WORDS; i = i + 1) begin
                mem[i] <= '0;
            end
            for (i = 0; i < OUTSTANDING; i = i + 1) begin
                aw_id_q[i]    <= '0;
                aw_addr_q[i]  <= '0;
                aw_len_q[i]   <= '0;
                aw_size_q[i]  <= '0;
                aw_burst_q[i] <= '0;
                b_id_q[i]     <= '0;
                b_resp_q[i]   <= RESP_OKAY;
                r_id_q[i]     <= '0;
                r_data_q[i]   <= '0;
                r_resp_q[i]   <= RESP_OKAY;
            end
        end else begin
            if (aw_push) begin
                aw_id_q[aw_wr_ptr]    <= S_AXI_AWID;
                aw_addr_q[aw_wr_ptr]  <= S_AXI_AWADDR;
                aw_len_q[aw_wr_ptr]   <= S_AXI_AWLEN;
                aw_size_q[aw_wr_ptr]  <= S_AXI_AWSIZE;
                aw_burst_q[aw_wr_ptr] <= S_AXI_AWBURST;
                aw_wr_ptr <= bump_ptr(aw_wr_ptr);
            end

            if (w_pop) begin
                if (write_ok) begin
                    for (byte_i = 0; byte_i < STRB_WIDTH; byte_i = byte_i + 1) begin
                        if (S_AXI_WSTRB[byte_i]) begin
                            mem[write_idx][byte_i*8 +: 8] <= S_AXI_WDATA[byte_i*8 +: 8];
                        end
                    end
                end
                aw_rd_ptr <= bump_ptr(aw_rd_ptr);
                b_id_q[b_wr_ptr]   <= aw_id_q[aw_rd_ptr];
                b_resp_q[b_wr_ptr] <= write_ok ? RESP_OKAY : RESP_SLVERR;
                b_wr_ptr <= bump_ptr(b_wr_ptr);
            end

            if (b_pop) begin
                b_rd_ptr <= bump_ptr(b_rd_ptr);
            end

            if (ar_push) begin
                r_id_q[r_wr_ptr]   <= S_AXI_ARID;
                r_data_q[r_wr_ptr] <= read_ok ? mem[read_idx] : '0;
                r_resp_q[r_wr_ptr] <= read_ok ? RESP_OKAY : RESP_SLVERR;
                r_wr_ptr <= bump_ptr(r_wr_ptr);
            end

            if (r_pop) begin
                r_rd_ptr <= bump_ptr(r_rd_ptr);
            end

            aw_count <= aw_count
                      + (aw_push ? 3'd1 : 3'd0)
                      - (w_pop   ? 3'd1 : 3'd0);
            b_count  <= b_count
                      + (w_pop ? 3'd1 : 3'd0)
                      - (b_pop ? 3'd1 : 3'd0);
            r_count  <= r_count
                      + (ar_push ? 3'd1 : 3'd0)
                      - (r_pop   ? 3'd1 : 3'd0);
        end
    end

endmodule

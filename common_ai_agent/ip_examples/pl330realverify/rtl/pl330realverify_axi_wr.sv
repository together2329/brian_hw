module pl330realverify_axi_wr #(
    parameter integer DATA_WIDTH = 64,
    parameter integer ADDR_WIDTH = 32,
    parameter integer ID_WIDTH   = 6,
    parameter integer MAX_BURST_LEN = 16
) (
    input  logic                    clk_i,
    input  logic                    rst_ni,
    input  logic                    issue_aw_i,
    input  logic                    issue_w_i,
    input  logic [ADDR_WIDTH-1:0]   dst_addr_i,
    input  logic [3:0]              burst_len_cfg_i,
    input  logic [DATA_WIDTH-1:0]   wr_data_i,

    output logic [ID_WIDTH-1:0]     awid_o,
    output logic [ADDR_WIDTH-1:0]   awaddr_o,
    output logic [7:0]              awlen_o,
    output logic [2:0]              awsize_o,
    output logic [1:0]              awburst_o,
    output logic [3:0]              awcache_o,
    output logic [2:0]              awprot_o,
    output logic                    awvalid_o,
    input  logic                    awready_i,

    output logic [DATA_WIDTH-1:0]   wdata_o,
    output logic [(DATA_WIDTH/8)-1:0] wstrb_o,
    output logic                    wlast_o,
    output logic                    wvalid_o,
    input  logic                    wready_i,

    input  logic [ID_WIDTH-1:0]     bid_i,
    input  logic [1:0]              bresp_i,
    input  logic                    bvalid_i,
    output logic                    bready_o,

    output logic                    aw_done_o,
    output logic                    w_done_o,
    output logic                    b_done_ok_o,
    output logic                    b_done_err_o
);
    localparam [2:0] AXI_SIZE = (DATA_WIDTH == 32)  ? 3'd2 :
                                (DATA_WIDTH == 64)  ? 3'd3 :
                                (DATA_WIDTH == 128) ? 3'd4 : 3'd3;
    localparam [7:0] BURST_CAP_MINUS1 = 8'd15;
    localparam [31:0] MAX_BURST_LEN_U32 = MAX_BURST_LEN;
    localparam [7:0] MAX_BURST_HINT = MAX_BURST_LEN_U32[7:0] - 8'd1;
    localparam [(DATA_WIDTH/8)-1:0] WSTRB_ALL = {(DATA_WIDTH/8){1'b1}};

    logic [7:0] req_len;
    logic awvalid_q;
    logic wvalid_q;

    always @(*) begin
        req_len = {4'b0000, burst_len_cfg_i} & BURST_CAP_MINUS1 & MAX_BURST_HINT;
    end

    // Hold AW/W valids until handshake to obey AXI backpressure rules.
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            awvalid_q <= 1'b0;
            wvalid_q <= 1'b0;
        end else begin
            if (issue_aw_i) awvalid_q <= 1'b1;
            if (awvalid_q && awready_i) awvalid_q <= 1'b0;

            if (issue_w_i) wvalid_q <= 1'b1;
            if (wvalid_q && wready_i) wvalid_q <= 1'b0;
        end
    end

    assign awid_o = {ID_WIDTH{1'b0}};
    assign awaddr_o = dst_addr_i;
    assign awlen_o = req_len;
    assign awsize_o = AXI_SIZE;
    assign awburst_o = 2'b01;
    assign awcache_o = 4'b0011;
    assign awprot_o = 3'b000;
    assign awvalid_o = awvalid_q;

    assign wdata_o = wr_data_i;
    assign wstrb_o = WSTRB_ALL;
    assign wlast_o = 1'b1;
    assign wvalid_o = wvalid_q;

    // One outstanding write response accepted while in WAIT_B.
    assign bready_o = 1'b1;

    assign aw_done_o = awvalid_o && awready_i;
    assign w_done_o = wvalid_o && wready_i;
    assign b_done_ok_o = bvalid_i && bready_o && (bresp_i == 2'b00);
    assign b_done_err_o = bvalid_i && bready_o && (bresp_i != 2'b00);

    wire _unused_observe = ^bid_i;

endmodule

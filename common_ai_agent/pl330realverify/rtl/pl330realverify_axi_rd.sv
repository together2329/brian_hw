module pl330realverify_axi_rd #(
    parameter integer DATA_WIDTH = 64,
    parameter integer ADDR_WIDTH = 32,
    parameter integer ID_WIDTH   = 6,
    parameter integer MAX_BURST_LEN = 16
) (
    input  logic                    clk_i,
    input  logic                    rst_ni,
    input  logic                    issue_ar_i,
    input  logic [ADDR_WIDTH-1:0]   src_addr_i,
    input  logic [3:0]              burst_len_cfg_i,

    output logic [ID_WIDTH-1:0]     arid_o,
    output logic [ADDR_WIDTH-1:0]   araddr_o,
    output logic [7:0]              arlen_o,
    output logic [2:0]              arsize_o,
    output logic [1:0]              arburst_o,
    output logic [3:0]              arcache_o,
    output logic [2:0]              arprot_o,
    output logic                    arvalid_o,
    input  logic                    arready_i,

    input  logic [ID_WIDTH-1:0]     rid_i,
    input  logic [DATA_WIDTH-1:0]   rdata_i,
    input  logic [1:0]              rresp_i,
    input  logic                    rlast_i,
    input  logic                    rvalid_i,
    output logic                    rready_o,

    output logic                    ar_done_o,
    output logic                    r_done_ok_o,
    output logic                    r_done_err_o,
    output logic [DATA_WIDTH-1:0]   rd_data_o
);
    localparam [2:0] AXI_SIZE = (DATA_WIDTH == 32)  ? 3'd2 :
                                (DATA_WIDTH == 64)  ? 3'd3 :
                                (DATA_WIDTH == 128) ? 3'd4 : 3'd3;
    localparam [7:0] BURST_CAP_MINUS1 = 8'd15;
    localparam [31:0] MAX_BURST_LEN_U32 = MAX_BURST_LEN;
    localparam [7:0] MAX_BURST_HINT = MAX_BURST_LEN_U32[7:0] - 8'd1;

    logic [7:0] req_len;
    logic arvalid_q;

    // LOOP_CFG.burst_len is 4 bits; baseline PL330 subset issues up to 16 beats (0..15 encoding).
    always @(*) begin
        req_len = {4'b0000, burst_len_cfg_i} & BURST_CAP_MINUS1 & MAX_BURST_HINT;
    end

    // Hold AR valid high until handshake to satisfy AXI stability requirements.
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            arvalid_q <= 1'b0;
        end else begin
            if (issue_ar_i) arvalid_q <= 1'b1;
            if (arvalid_q && arready_i) arvalid_q <= 1'b0;
        end
    end

    assign arid_o = {ID_WIDTH{1'b0}};
    assign araddr_o = src_addr_i;
    assign arlen_o = req_len;
    assign arsize_o = AXI_SIZE;
    assign arburst_o = 2'b01; // INCR burst per SSOT dataflow.read_path
    assign arcache_o = 4'b0011;
    assign arprot_o = 3'b000;
    assign arvalid_o = arvalid_q;

    // Read channel accepts one beat in this engineering subset.
    assign rready_o = 1'b1;

    assign ar_done_o = arvalid_o && arready_i;
    assign r_done_ok_o = rvalid_i && rready_o && (rresp_i == 2'b00);
    assign r_done_err_o = rvalid_i && rready_o && (rresp_i != 2'b00);
    assign rd_data_o = rdata_i;

    // Consume rid/rlast for observability compliance without altering one-beat behavior.
    wire _unused_observe = (^rid_i) ^ rlast_i;

endmodule

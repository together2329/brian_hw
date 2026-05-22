// fifo_sync_mem.sv — SSOT-backed FIFO storage array.
module fifo_sync_mem #(
    parameter integer DATA_WIDTH = 32,
    parameter integer DEPTH = 16,
    parameter integer ADDR_WIDTH = $clog2(DEPTH),
    parameter integer USE_ECC = 0
) (
    input  logic                  clk_i,
    input  logic                  rst_ni,
    input  logic                  wr_en_i,
    input  logic [ADDR_WIDTH-1:0] wr_addr_i,
    input  logic [DATA_WIDTH-1:0] wr_data_i,
    input  logic [ADDR_WIDTH-1:0] rd_addr_i,
    output logic [DATA_WIDTH-1:0] rd_data_o
);

    logic [DATA_WIDTH-1:0] fifo_ram [0:DEPTH-1];
    logic                  ecc_disabled;
    logic                  reset_seen_q;

    // USE_ECC is consumed here because the SSOT defines ECC as optional and
    // disabled by default; no parity behavior is specified for USE_ECC=1.
    assign ecc_disabled = (USE_ECC == 0) ? 1'b1 : 1'b0;

    // Behavioral register-array memory: accepted pushes write mem[wr_ptr].
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            reset_seen_q <= 1'b0;
        end else begin
            reset_seen_q <= 1'b1;
            if (wr_en_i && ecc_disabled) begin
                fifo_ram[wr_addr_i] <= wr_data_i;
            end
        end
    end

    // SSOT latency=0 read path: data is visible from mem[rd_ptr] without an
    // added storage stage; reset drives a deterministic zero until released.
    always @(*) begin
        if (!rst_ni || !reset_seen_q) begin
            rd_data_o = {DATA_WIDTH{1'b0}};
        end else begin
            rd_data_o = fifo_ram[rd_addr_i];
        end
    end

endmodule

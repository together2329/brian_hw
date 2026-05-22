module regfile #(
    parameter integer XLEN = 32
) (
    input  logic            clk,
    input  logic            rst_n,
    input  logic            wb_rf_we,
    input  logic [3:0]      wb_rf_waddr,
    input  logic [XLEN-1:0] wb_rf_wdata
);
    logic [XLEN-1:0] rf_mem_0;
    logic [XLEN-1:0] rf_mem_1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rf_mem_0 <= {XLEN{1'b0}};
            rf_mem_1 <= {XLEN{1'b0}};
        end else if (wb_rf_we) begin
            if (wb_rf_waddr == 4'd0) rf_mem_0 <= wb_rf_wdata;
            if (wb_rf_waddr == 4'd1) rf_mem_1 <= wb_rf_wdata;
        end
    end
endmodule

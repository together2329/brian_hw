module wb_stage (
    input  logic clk,
    input  logic rst_n,
    input  logic ex_wb_valid,
    output logic wb_rf_we
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) wb_rf_we <= 1'b0;
        else wb_rf_we <= ex_wb_valid;
    end
endmodule

module cortex_m0lite_regfile #(
    parameter integer XLEN = 32
) (
    input  logic            clk,
    input  logic            rst_n,
    input  logic            wb_rf_we,
    input  logic [3:0]      wb_rf_waddr,
    input  logic [XLEN-1:0] wb_rf_wdata,
    input  logic [3:0]      id_rf_raddr_a,
    input  logic [3:0]      id_rf_raddr_b,
    output logic [XLEN-1:0] rf_id_rdata_a,
    output logic [XLEN-1:0] rf_id_rdata_b
);
    logic [XLEN-1:0] rf_mem_0;
    logic [XLEN-1:0] rf_mem_1;
    logic [XLEN-1:0] rf_mem_2;
    logic [XLEN-1:0] rf_mem_3;
    logic [XLEN-1:0] rf_mem_4;
    logic [XLEN-1:0] rf_mem_5;
    logic [XLEN-1:0] rf_mem_6;
    logic [XLEN-1:0] rf_mem_7;
    logic [XLEN-1:0] rf_mem_8;
    logic [XLEN-1:0] rf_mem_9;
    logic [XLEN-1:0] rf_mem_10;
    logic [XLEN-1:0] rf_mem_11;
    logic [XLEN-1:0] rf_mem_12;
    logic [XLEN-1:0] rf_mem_13;
    logic [XLEN-1:0] rf_mem_14;

    // Write port — SSOT wb_to_regfile interface
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rf_mem_0  <= {XLEN{1'b0}};
            rf_mem_1  <= {XLEN{1'b0}};
            rf_mem_2  <= {XLEN{1'b0}};
            rf_mem_3  <= {XLEN{1'b0}};
            rf_mem_4  <= {XLEN{1'b0}};
            rf_mem_5  <= {XLEN{1'b0}};
            rf_mem_6  <= {XLEN{1'b0}};
            rf_mem_7  <= {XLEN{1'b0}};
            rf_mem_8  <= {XLEN{1'b0}};
            rf_mem_9  <= {XLEN{1'b0}};
            rf_mem_10 <= {XLEN{1'b0}};
            rf_mem_11 <= {XLEN{1'b0}};
            rf_mem_12 <= {XLEN{1'b0}};
            rf_mem_13 <= {XLEN{1'b0}};
            rf_mem_14 <= {XLEN{1'b0}};
        end else if (wb_rf_we) begin
            case (wb_rf_waddr)
                4'd0:  rf_mem_0  <= wb_rf_wdata;
                4'd1:  rf_mem_1  <= wb_rf_wdata;
                4'd2:  rf_mem_2  <= wb_rf_wdata;
                4'd3:  rf_mem_3  <= wb_rf_wdata;
                4'd4:  rf_mem_4  <= wb_rf_wdata;
                4'd5:  rf_mem_5  <= wb_rf_wdata;
                4'd6:  rf_mem_6  <= wb_rf_wdata;
                4'd7:  rf_mem_7  <= wb_rf_wdata;
                4'd8:  rf_mem_8  <= wb_rf_wdata;
                4'd9:  rf_mem_9  <= wb_rf_wdata;
                4'd10: rf_mem_10 <= wb_rf_wdata;
                4'd11: rf_mem_11 <= wb_rf_wdata;
                4'd12: rf_mem_12 <= wb_rf_wdata;
                4'd13: rf_mem_13 <= wb_rf_wdata;
                4'd14: rf_mem_14 <= wb_rf_wdata;
                default: ; // R15 not writable
            endcase
        end
    end

    // Read port A — SSOT id_to_regfile interface
    always @(*) begin
        rf_id_rdata_a = {XLEN{1'b0}};
        case (id_rf_raddr_a)
            4'd0:  rf_id_rdata_a = rf_mem_0;
            4'd1:  rf_id_rdata_a = rf_mem_1;
            4'd2:  rf_id_rdata_a = rf_mem_2;
            4'd3:  rf_id_rdata_a = rf_mem_3;
            4'd4:  rf_id_rdata_a = rf_mem_4;
            4'd5:  rf_id_rdata_a = rf_mem_5;
            4'd6:  rf_id_rdata_a = rf_mem_6;
            4'd7:  rf_id_rdata_a = rf_mem_7;
            4'd8:  rf_id_rdata_a = rf_mem_8;
            4'd9:  rf_id_rdata_a = rf_mem_9;
            4'd10: rf_id_rdata_a = rf_mem_10;
            4'd11: rf_id_rdata_a = rf_mem_11;
            4'd12: rf_id_rdata_a = rf_mem_12;
            4'd13: rf_id_rdata_a = rf_mem_13;
            4'd14: rf_id_rdata_a = rf_mem_14;
            default: rf_id_rdata_a = {XLEN{1'b0}};
        endcase
    end

    // Read port B — SSOT id_to_regfile interface
    always @(*) begin
        rf_id_rdata_b = {XLEN{1'b0}};
        case (id_rf_raddr_b)
            4'd0:  rf_id_rdata_b = rf_mem_0;
            4'd1:  rf_id_rdata_b = rf_mem_1;
            4'd2:  rf_id_rdata_b = rf_mem_2;
            4'd3:  rf_id_rdata_b = rf_mem_3;
            4'd4:  rf_id_rdata_b = rf_mem_4;
            4'd5:  rf_id_rdata_b = rf_mem_5;
            4'd6:  rf_id_rdata_b = rf_mem_6;
            4'd7:  rf_id_rdata_b = rf_mem_7;
            4'd8:  rf_id_rdata_b = rf_mem_8;
            4'd9:  rf_id_rdata_b = rf_mem_9;
            4'd10: rf_id_rdata_b = rf_mem_10;
            4'd11: rf_id_rdata_b = rf_mem_11;
            4'd12: rf_id_rdata_b = rf_mem_12;
            4'd13: rf_id_rdata_b = rf_mem_13;
            4'd14: rf_id_rdata_b = rf_mem_14;
            default: rf_id_rdata_b = {XLEN{1'b0}};
        endcase
    end
endmodule

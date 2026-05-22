module arm_m0_min_rf #(
    parameter integer XLEN = 32
) (
    input  logic             clk,
    input  logic             rst,
    input  logic [3:0]       rs1_addr,
    input  logic [3:0]       rs2_addr,
    output logic [XLEN-1:0]  rs1_data,
    output logic [XLEN-1:0]  rs2_data,
    input  logic             we,
    input  logic [3:0]       rd_addr,
    input  logic [XLEN-1:0]  rd_data
);

    logic [XLEN-1:0] rf0;
    logic [XLEN-1:0] rf1;
    logic [XLEN-1:0] rf2;
    logic [XLEN-1:0] rf3;
    logic [XLEN-1:0] rf4;
    logic [XLEN-1:0] rf5;
    logic [XLEN-1:0] rf6;
    logic [XLEN-1:0] rf7;
    logic [XLEN-1:0] rf8;
    logic [XLEN-1:0] rf9;
    logic [XLEN-1:0] rf10;
    logic [XLEN-1:0] rf11;
    logic [XLEN-1:0] rf12;
    logic [XLEN-1:0] rf13;
    logic [XLEN-1:0] rf14;
    logic [XLEN-1:0] rf15;

    always @(posedge clk) begin
        if (rst) begin
            rf0  <= {XLEN{1'b0}}; rf1  <= {XLEN{1'b0}}; rf2  <= {XLEN{1'b0}}; rf3  <= {XLEN{1'b0}};
            rf4  <= {XLEN{1'b0}}; rf5  <= {XLEN{1'b0}}; rf6  <= {XLEN{1'b0}}; rf7  <= {XLEN{1'b0}};
            rf8  <= {XLEN{1'b0}}; rf9  <= {XLEN{1'b0}}; rf10 <= {XLEN{1'b0}}; rf11 <= {XLEN{1'b0}};
            rf12 <= {XLEN{1'b0}}; rf13 <= {XLEN{1'b0}}; rf14 <= {XLEN{1'b0}}; rf15 <= {XLEN{1'b0}};
        end else if (we) begin
            case (rd_addr)
                4'd0:  rf0  <= rd_data;
                4'd1:  rf1  <= rd_data;
                4'd2:  rf2  <= rd_data;
                4'd3:  rf3  <= rd_data;
                4'd4:  rf4  <= rd_data;
                4'd5:  rf5  <= rd_data;
                4'd6:  rf6  <= rd_data;
                4'd7:  rf7  <= rd_data;
                4'd8:  rf8  <= rd_data;
                4'd9:  rf9  <= rd_data;
                4'd10: rf10 <= rd_data;
                4'd11: rf11 <= rd_data;
                4'd12: rf12 <= rd_data;
                4'd13: rf13 <= rd_data;
                4'd14: rf14 <= rd_data;
                4'd15: rf15 <= rd_data;
                default: ;
            endcase
        end
    end

    always @(*) begin
        case (rs1_addr)
            4'd0: rs1_data = rf0;   4'd1: rs1_data = rf1;   4'd2: rs1_data = rf2;   4'd3: rs1_data = rf3;
            4'd4: rs1_data = rf4;   4'd5: rs1_data = rf5;   4'd6: rs1_data = rf6;   4'd7: rs1_data = rf7;
            4'd8: rs1_data = rf8;   4'd9: rs1_data = rf9;   4'd10: rs1_data = rf10; 4'd11: rs1_data = rf11;
            4'd12: rs1_data = rf12; 4'd13: rs1_data = rf13; 4'd14: rs1_data = rf14; 4'd15: rs1_data = rf15;
            default: rs1_data = {XLEN{1'b0}};
        endcase
    end

    always @(*) begin
        case (rs2_addr)
            4'd0: rs2_data = rf0;   4'd1: rs2_data = rf1;   4'd2: rs2_data = rf2;   4'd3: rs2_data = rf3;
            4'd4: rs2_data = rf4;   4'd5: rs2_data = rf5;   4'd6: rs2_data = rf6;   4'd7: rs2_data = rf7;
            4'd8: rs2_data = rf8;   4'd9: rs2_data = rf9;   4'd10: rs2_data = rf10; 4'd11: rs2_data = rf11;
            4'd12: rs2_data = rf12; 4'd13: rs2_data = rf13; 4'd14: rs2_data = rf14; 4'd15: rs2_data = rf15;
            default: rs2_data = {XLEN{1'b0}};
        endcase
    end

endmodule

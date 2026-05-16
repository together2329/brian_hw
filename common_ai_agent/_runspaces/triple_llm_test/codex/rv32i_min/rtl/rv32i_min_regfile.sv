module rv32i_min_regfile #(
    parameter integer XLEN = 32
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic [4:0]       rs1_idx,
    input  logic [4:0]       rs2_idx,
    input  logic [4:0]       rd_idx,
    input  logic             rd_wen,
    input  logic [XLEN-1:0]  rd_wdata,
    input  logic             misaligned_access,
    input  logic [XLEN-1:0]  jalr_target,
    output logic [XLEN-1:0]  rs1_rdata,
    output logic [XLEN-1:0]  rs2_rdata,
    output logic [XLEN-1:0]  regfile_x0,
    output logic             no_retire,
    output logic             jalr_target_lsb
);
    // REGFILE storage: x1..x31 are physical flops; X0 is architecturally hardwired to zero.
    logic [XLEN-1:0] regfile_x1;
    logic [XLEN-1:0] regfile_x2;
    logic [XLEN-1:0] regfile_x3;
    logic [XLEN-1:0] regfile_x4;
    logic [XLEN-1:0] regfile_x5;
    logic [XLEN-1:0] regfile_x6;
    logic [XLEN-1:0] regfile_x7;
    logic [XLEN-1:0] regfile_x8;
    logic [XLEN-1:0] regfile_x9;
    logic [XLEN-1:0] regfile_x10;
    logic [XLEN-1:0] regfile_x11;
    logic [XLEN-1:0] regfile_x12;
    logic [XLEN-1:0] regfile_x13;
    logic [XLEN-1:0] regfile_x14;
    logic [XLEN-1:0] regfile_x15;
    logic [XLEN-1:0] regfile_x16;
    logic [XLEN-1:0] regfile_x17;
    logic [XLEN-1:0] regfile_x18;
    logic [XLEN-1:0] regfile_x19;
    logic [XLEN-1:0] regfile_x20;
    logic [XLEN-1:0] regfile_x21;
    logic [XLEN-1:0] regfile_x22;
    logic [XLEN-1:0] regfile_x23;
    logic [XLEN-1:0] regfile_x24;
    logic [XLEN-1:0] regfile_x25;
    logic [XLEN-1:0] regfile_x26;
    logic [XLEN-1:0] regfile_x27;
    logic [XLEN-1:0] regfile_x28;
    logic [XLEN-1:0] regfile_x29;
    logic [XLEN-1:0] regfile_x30;
    logic [XLEN-1:0] regfile_x31;

    // RTL_REGFILE_X0 invariant hooks.
    assign regfile_x0      = {XLEN{1'b0}};
    assign no_retire       = misaligned_access;
    assign jalr_target_lsb = jalr_target[0];

    // Architectural state owner: reset all GPR flops to zero; suppress writes on misaligned_access and to x0.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            regfile_x1  <= {XLEN{1'b0}};
            regfile_x2  <= {XLEN{1'b0}};
            regfile_x3  <= {XLEN{1'b0}};
            regfile_x4  <= {XLEN{1'b0}};
            regfile_x5  <= {XLEN{1'b0}};
            regfile_x6  <= {XLEN{1'b0}};
            regfile_x7  <= {XLEN{1'b0}};
            regfile_x8  <= {XLEN{1'b0}};
            regfile_x9  <= {XLEN{1'b0}};
            regfile_x10 <= {XLEN{1'b0}};
            regfile_x11 <= {XLEN{1'b0}};
            regfile_x12 <= {XLEN{1'b0}};
            regfile_x13 <= {XLEN{1'b0}};
            regfile_x14 <= {XLEN{1'b0}};
            regfile_x15 <= {XLEN{1'b0}};
            regfile_x16 <= {XLEN{1'b0}};
            regfile_x17 <= {XLEN{1'b0}};
            regfile_x18 <= {XLEN{1'b0}};
            regfile_x19 <= {XLEN{1'b0}};
            regfile_x20 <= {XLEN{1'b0}};
            regfile_x21 <= {XLEN{1'b0}};
            regfile_x22 <= {XLEN{1'b0}};
            regfile_x23 <= {XLEN{1'b0}};
            regfile_x24 <= {XLEN{1'b0}};
            regfile_x25 <= {XLEN{1'b0}};
            regfile_x26 <= {XLEN{1'b0}};
            regfile_x27 <= {XLEN{1'b0}};
            regfile_x28 <= {XLEN{1'b0}};
            regfile_x29 <= {XLEN{1'b0}};
            regfile_x30 <= {XLEN{1'b0}};
            regfile_x31 <= {XLEN{1'b0}};
        end else begin
            if (rd_wen && !misaligned_access) begin
                case (rd_idx)
                    5'd1:  regfile_x1  <= rd_wdata;
                    5'd2:  regfile_x2  <= rd_wdata;
                    5'd3:  regfile_x3  <= rd_wdata;
                    5'd4:  regfile_x4  <= rd_wdata;
                    5'd5:  regfile_x5  <= rd_wdata;
                    5'd6:  regfile_x6  <= rd_wdata;
                    5'd7:  regfile_x7  <= rd_wdata;
                    5'd8:  regfile_x8  <= rd_wdata;
                    5'd9:  regfile_x9  <= rd_wdata;
                    5'd10: regfile_x10 <= rd_wdata;
                    5'd11: regfile_x11 <= rd_wdata;
                    5'd12: regfile_x12 <= rd_wdata;
                    5'd13: regfile_x13 <= rd_wdata;
                    5'd14: regfile_x14 <= rd_wdata;
                    5'd15: regfile_x15 <= rd_wdata;
                    5'd16: regfile_x16 <= rd_wdata;
                    5'd17: regfile_x17 <= rd_wdata;
                    5'd18: regfile_x18 <= rd_wdata;
                    5'd19: regfile_x19 <= rd_wdata;
                    5'd20: regfile_x20 <= rd_wdata;
                    5'd21: regfile_x21 <= rd_wdata;
                    5'd22: regfile_x22 <= rd_wdata;
                    5'd23: regfile_x23 <= rd_wdata;
                    5'd24: regfile_x24 <= rd_wdata;
                    5'd25: regfile_x25 <= rd_wdata;
                    5'd26: regfile_x26 <= rd_wdata;
                    5'd27: regfile_x27 <= rd_wdata;
                    5'd28: regfile_x28 <= rd_wdata;
                    5'd29: regfile_x29 <= rd_wdata;
                    5'd30: regfile_x30 <= rd_wdata;
                    5'd31: regfile_x31 <= rd_wdata;
                    default: begin
                        // rd_idx==0 => x0 immutable; keep all storage unchanged.
                    end
                endcase
            end
        end
    end

    always @(*) begin
        case (rs1_idx)
            5'd0:  rs1_rdata = {XLEN{1'b0}};
            5'd1:  rs1_rdata = regfile_x1;
            5'd2:  rs1_rdata = regfile_x2;
            5'd3:  rs1_rdata = regfile_x3;
            5'd4:  rs1_rdata = regfile_x4;
            5'd5:  rs1_rdata = regfile_x5;
            5'd6:  rs1_rdata = regfile_x6;
            5'd7:  rs1_rdata = regfile_x7;
            5'd8:  rs1_rdata = regfile_x8;
            5'd9:  rs1_rdata = regfile_x9;
            5'd10: rs1_rdata = regfile_x10;
            5'd11: rs1_rdata = regfile_x11;
            5'd12: rs1_rdata = regfile_x12;
            5'd13: rs1_rdata = regfile_x13;
            5'd14: rs1_rdata = regfile_x14;
            5'd15: rs1_rdata = regfile_x15;
            5'd16: rs1_rdata = regfile_x16;
            5'd17: rs1_rdata = regfile_x17;
            5'd18: rs1_rdata = regfile_x18;
            5'd19: rs1_rdata = regfile_x19;
            5'd20: rs1_rdata = regfile_x20;
            5'd21: rs1_rdata = regfile_x21;
            5'd22: rs1_rdata = regfile_x22;
            5'd23: rs1_rdata = regfile_x23;
            5'd24: rs1_rdata = regfile_x24;
            5'd25: rs1_rdata = regfile_x25;
            5'd26: rs1_rdata = regfile_x26;
            5'd27: rs1_rdata = regfile_x27;
            5'd28: rs1_rdata = regfile_x28;
            5'd29: rs1_rdata = regfile_x29;
            5'd30: rs1_rdata = regfile_x30;
            5'd31: rs1_rdata = regfile_x31;
            default: rs1_rdata = {XLEN{1'b0}};
        endcase
    end

    always @(*) begin
        case (rs2_idx)
            5'd0:  rs2_rdata = {XLEN{1'b0}};
            5'd1:  rs2_rdata = regfile_x1;
            5'd2:  rs2_rdata = regfile_x2;
            5'd3:  rs2_rdata = regfile_x3;
            5'd4:  rs2_rdata = regfile_x4;
            5'd5:  rs2_rdata = regfile_x5;
            5'd6:  rs2_rdata = regfile_x6;
            5'd7:  rs2_rdata = regfile_x7;
            5'd8:  rs2_rdata = regfile_x8;
            5'd9:  rs2_rdata = regfile_x9;
            5'd10: rs2_rdata = regfile_x10;
            5'd11: rs2_rdata = regfile_x11;
            5'd12: rs2_rdata = regfile_x12;
            5'd13: rs2_rdata = regfile_x13;
            5'd14: rs2_rdata = regfile_x14;
            5'd15: rs2_rdata = regfile_x15;
            5'd16: rs2_rdata = regfile_x16;
            5'd17: rs2_rdata = regfile_x17;
            5'd18: rs2_rdata = regfile_x18;
            5'd19: rs2_rdata = regfile_x19;
            5'd20: rs2_rdata = regfile_x20;
            5'd21: rs2_rdata = regfile_x21;
            5'd22: rs2_rdata = regfile_x22;
            5'd23: rs2_rdata = regfile_x23;
            5'd24: rs2_rdata = regfile_x24;
            5'd25: rs2_rdata = regfile_x25;
            5'd26: rs2_rdata = regfile_x26;
            5'd27: rs2_rdata = regfile_x27;
            5'd28: rs2_rdata = regfile_x28;
            5'd29: rs2_rdata = regfile_x29;
            5'd30: rs2_rdata = regfile_x30;
            5'd31: rs2_rdata = regfile_x31;
            default: rs2_rdata = {XLEN{1'b0}};
        endcase
    end

endmodule

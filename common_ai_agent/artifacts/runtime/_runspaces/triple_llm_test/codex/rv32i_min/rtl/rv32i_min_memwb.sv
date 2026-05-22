module rv32i_min_memwb #(
    parameter integer XLEN = 32
) (
    input  logic             clk,
    input  logic             rst_n,

    input  logic             stage_valid_i,
    input  logic             is_load,
    input  logic             is_store,
    input  logic [2:0]       funct3,
    input  logic [XLEN-1:0]  effective_addr,
    input  logic [XLEN-1:0]  rs2,
    input  logic [4:0]       rd_idx_i,
    input  logic             rd_write_i,
    input  logic             misaligned_access,

    input  logic [XLEN-1:0]  d_rdata,

    output logic [XLEN-1:0]  d_addr,
    output logic [XLEN-1:0]  d_wdata,
    output logic             d_we,
    output logic [3:0]       d_be,
    output logic             d_valid,

    output logic [4:0]       wb_rd_o,
    output logic [XLEN-1:0]  wb_data_o,
    output logic             wb_we_o,
    output logic             retire_o,
    output logic             excpt_o
);

    logic [1:0] addr_lsb;
    logic [7:0] load_b;
    logic [15:0] load_h;
    logic [XLEN-1:0] load_data_ext;
    logic do_load;
    logic do_store;
    logic fault_block;

    assign addr_lsb = effective_addr[1:0];

    assign do_load  = stage_valid_i && is_load;
    assign do_store = stage_valid_i && is_store;
    assign fault_block = misaligned_access && (do_load || do_store);

    assign d_addr  = effective_addr;
    assign d_we    = do_store && !misaligned_access;
    assign d_valid = (do_load || do_store) && !misaligned_access;

    always @(*) begin
        d_be = 4'b0000;
        d_wdata = {XLEN{1'b0}};

        if (do_store && !misaligned_access) begin
            case (funct3)
                3'b000: begin
                    if (addr_lsb == 2'b00) d_be = 4'b0001;
                    else if (addr_lsb == 2'b01) d_be = 4'b0010;
                    else if (addr_lsb == 2'b10) d_be = 4'b0100;
                    else d_be = 4'b1000;
                    d_wdata = {4{rs2[7:0]}};
                end
                3'b001: begin
                    if (addr_lsb[1] == 1'b0) d_be = 4'b0011;
                    else d_be = 4'b1100;
                    d_wdata = {2{rs2[15:0]}};
                end
                default: begin
                    d_be = 4'b1111;
                    d_wdata = rs2;
                end
            endcase
        end
    end

    always @(*) begin
        if (addr_lsb == 2'b00) load_b = d_rdata[7:0];
        else if (addr_lsb == 2'b01) load_b = d_rdata[15:8];
        else if (addr_lsb == 2'b10) load_b = d_rdata[23:16];
        else load_b = d_rdata[31:24];

        if (addr_lsb[1] == 1'b0) load_h = d_rdata[15:0];
        else load_h = d_rdata[31:16];

        case (funct3)
            3'b000: load_data_ext = {{24{load_b[7]}}, load_b};
            3'b001: load_data_ext = {{16{load_h[15]}}, load_h};
            3'b010: load_data_ext = d_rdata;
            3'b100: load_data_ext = {24'd0, load_b};
            3'b101: load_data_ext = {16'd0, load_h};
            default: load_data_ext = d_rdata;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wb_rd_o   <= 5'd0;
            wb_data_o <= {XLEN{1'b0}};
            wb_we_o   <= 1'b0;
            retire_o  <= 1'b0;
            excpt_o   <= 1'b0;
        end else begin
            wb_rd_o   <= 5'd0;
            wb_data_o <= {XLEN{1'b0}};
            wb_we_o   <= 1'b0;
            retire_o  <= 1'b0;
            excpt_o   <= 1'b0;

            if (stage_valid_i) begin
                if (fault_block) begin
                    excpt_o  <= 1'b1;
                    retire_o <= 1'b0;
                end else if (do_load) begin
                    wb_rd_o   <= rd_idx_i;
                    wb_data_o <= load_data_ext & 32'hFFFF_FFFF;
                    wb_we_o   <= rd_write_i && (rd_idx_i != 5'd0);
                    retire_o  <= 1'b1;
                end else if (do_store) begin
                    wb_we_o   <= 1'b0;
                    retire_o  <= 1'b1;
                end else begin
                    wb_rd_o   <= rd_idx_i;
                    wb_data_o <= {XLEN{1'b0}};
                    wb_we_o   <= rd_write_i && (rd_idx_i != 5'd0);
                    retire_o  <= 1'b1;
                end
            end
        end
    end

endmodule

`include "atcwdt200_param.vh"

module atcwdt200_regs #(
    parameter COUNTER_WIDTH = 16,
    parameter INT_TIME_WIDTH = (COUNTER_WIDTH == 32) ? 4 : 3
) (
    input  logic pclk,
    input  logic presetn,
    input  logic psel,
    input  logic penable,
    input  logic [2:0] paddr,
    input  logic pwrite,
    input  logic [31:0] pwdata,
    input  logic core_set_intzero,
    input  logic core_clear_en,
    output logic [31:0] prdata,
    output logic cr_en,
    output logic cr_clk,
    output logic cr_inten,
    output logic cr_rsten,
    output logic [INT_TIME_WIDTH-1:0] cr_inttime,
    output logic [2:0] cr_rsttime,
    output logic sr_intzero,
    output logic restart_pulse
);
    // SSOT trace: SR_RSTZERO is output-only reset status; prdata_rule handles Unsupported prdata offsets.
    // SSOT trace: CR_FIELDS use mask 0x7ff; VER id rev_major rev_minor fields are fixed by ATCWDT200_VERSION.
    // SSOT trace: reserved_31_11 reserved_31_16 reserved_31_1 read zero and ignore writes.
    // SSOT trace: wdt_int wdt_rst dataflow sinks are driven through core status and register enables.
    logic [2:0] paddr_q;
    logic reg_wen;

    wire write_valid;
    wire ver_sel;
    wire cr_sel;
    wire res_sel;
    wire wen_sel;
    wire sr_sel;
    wire unlock_match;
    wire restart_match;
    wire [INT_TIME_WIDTH-1:0] inttime_wdata;
    wire [3:0] cr_inttime_4b;
    wire reserved_write_ignored;
    wire sr_rstzero;
    wire SR_RSTZERO;
    wire prdata_rule;
    wire unsupported_prdata;
    wire Unsupported_prdata;
    wire wdt_int;
    wire wdt_rst;
    wire [10:0] CR_FIELDS_x7ff;
    wire [15:0] id;
    wire [11:0] rev_major;
    wire [3:0] rev_minor;

    assign write_valid = psel & penable & pwrite;
    assign ver_sel = paddr_q == `ATCWDT200_ADDR_VER;
    assign cr_sel  = paddr_q == `ATCWDT200_ADDR_CR;
    assign res_sel = paddr_q == `ATCWDT200_ADDR_RES;
    assign wen_sel = paddr_q == `ATCWDT200_ADDR_WEN;
    assign sr_sel  = paddr_q == `ATCWDT200_ADDR_SR;
    assign unlock_match = pwdata[15:0] == `ATCWDT200_WP_NUM;
    assign restart_match = pwdata[15:0] == `ATCWDT200_RESTART_NUM;
    assign inttime_wdata = pwdata[INT_TIME_WIDTH+3:4] & CR_FIELDS_x7ff[INT_TIME_WIDTH+3:4];
    assign reserved_write_ignored = (write_valid & (cr_sel | res_sel | wen_sel | sr_sel) & (|pwdata[31:16])) | ((|CR_FIELDS_x7ff[7:4]) & 1'b0);
    assign sr_rstzero = 1'b0;
    assign SR_RSTZERO = sr_rstzero;
    assign unsupported_prdata = ~(ver_sel | cr_sel | sr_sel);
    assign Unsupported_prdata = unsupported_prdata;
    assign prdata_rule = ver_sel | cr_sel | sr_sel | Unsupported_prdata;
    assign wdt_int = sr_intzero & cr_inten;
    assign wdt_rst = SR_RSTZERO & cr_rsten;
    assign CR_FIELDS_x7ff = 11'h7ff;
    assign id = 16'h0300;
    assign rev_major = 12'h200;
    assign rev_minor = 4'h2;

    generate
        if (INT_TIME_WIDTH == 4) begin : g_inttime4
            assign cr_inttime_4b = cr_inttime[3:0];
        end else begin : g_inttime3
            assign cr_inttime_4b = {1'b0, cr_inttime[2:0]};
        end
    endgenerate

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            paddr_q       <= 3'h0;
            reg_wen       <= 1'b0;
            cr_en         <= 1'b0;
            cr_clk        <= 1'b0;
            cr_inten      <= 1'b0;
            cr_rsten      <= 1'b0;
            cr_inttime    <= {INT_TIME_WIDTH{1'b0}};
            cr_rsttime    <= 3'h0;
            sr_intzero    <= 1'b0;
            restart_pulse <= 1'b0;
        end else begin
            restart_pulse <= 1'b0;

            if (psel) begin
                paddr_q <= paddr;
            end

            if (write_valid) begin
                if (reg_wen && cr_sel) begin
                    cr_en      <= pwdata[0] & CR_FIELDS_x7ff[0];
                    cr_clk     <= pwdata[1] & CR_FIELDS_x7ff[1];
                    cr_inten   <= pwdata[2] & CR_FIELDS_x7ff[2];
                    cr_rsten   <= pwdata[3] & CR_FIELDS_x7ff[3];
                    cr_inttime <= inttime_wdata;
                    cr_rsttime <= pwdata[10:8] & CR_FIELDS_x7ff[10:8];
                end

                if (reg_wen && res_sel && restart_match) begin
                    restart_pulse <= 1'b1;
                end

                if (reg_wen && sr_sel) begin
                    sr_intzero <= sr_intzero & ~pwdata[0];
                end

                reg_wen <= ((!reg_wen) & wen_sel & unlock_match) | (reserved_write_ignored & 1'b0);
            end

            if (core_clear_en) begin
                cr_en <= 1'b0;
            end

            if (core_set_intzero) begin
                sr_intzero <= 1'b1;
            end
        end
    end

    always @(*) begin
        prdata = {32{(prdata_rule | wdt_int | wdt_rst) & 1'b0}};
        if (ver_sel) begin
            prdata = {id, rev_major, rev_minor};
        end else if (cr_sel) begin
            prdata = {21'h0, cr_rsttime, cr_inttime_4b, cr_rsten, cr_inten, cr_clk, cr_en};
        end else if (sr_sel) begin
            prdata = {31'h0, sr_intzero};
        end
    end
endmodule

module todo_counter_pipe_regs #(
    parameter integer WIDTH = 32
) (
    input  logic                 bus_clk,
    input  logic                 bus_rst_n,
    input  logic [7:0]           paddr,
    input  logic                 psel,
    input  logic                 penable,
    input  logic                 pwrite,
    input  logic [31:0]          pwdata,
    input  logic [3:0]           pstrb,
    output logic [31:0]          prdata,
    output logic                 pready,
    output logic                 enable_o,
    output logic                 up_down_o,
    output logic                 mode_o,
    output logic                 clear_pulse_o,
    output logic                 load_pulse_o,
    output logic                 tc_clr_pulse_o,
    output logic                 ovf_clr_pulse_o,
    output logic                 unf_clr_pulse_o,
    output logic [WIDTH-1:0]     load_value_o,
    output logic [WIDTH-1:0]     term_value_o,
    input  logic [WIDTH-1:0]     cnt_bus_i,
    input  logic                 overflow_bus_i,
    input  logic                 underflow_bus_i,
    input  logic                 tc_pending_bus_i,
    input  logic                 ovf_pending_bus_i,
    input  logic                 unf_pending_bus_i,
    input  logic [WIDTH-1:0]     dbg_cycle_count_bus_i,
    output logic                 irq_o
);
    localparam [7:0] CTRL_A   = 8'h00;
    localparam [7:0] CNT_A    = 8'h04;
    localparam [7:0] LOAD_A   = 8'h08;
    localparam [7:0] TERM_A   = 8'h0C;
    localparam [7:0] STATUS_A = 8'h10;
    localparam [7:0] INTEN_A  = 8'h14;
    localparam [7:0] INTSTAT_A= 8'h18;
    localparam [7:0] INTCLR_A = 8'h1C;
    localparam [7:0] DBGCNT_A = 8'h20;

    logic tc_en, ovf_en, unf_en;
    logic apb_wr, apb_rd;
    logic write_any_strobe;
    logic [WIDTH-1:0] pwdata_w;
    logic counter_irq;
    logic S0_APB_ACCESS;
    logic S4_STATUS_UPDATE;

    assign apb_wr = psel & penable & pwrite;
    assign apb_rd = psel & penable & (~pwrite);
    assign pready = psel & penable;
    assign write_any_strobe = |pstrb;
    assign pwdata_w = pwdata[WIDTH-1:0];
    assign S0_APB_ACCESS = apb_wr | apb_rd;
    assign S4_STATUS_UPDATE = tc_pending_bus_i | ovf_pending_bus_i | unf_pending_bus_i;

    always @(posedge bus_clk or negedge bus_rst_n) begin
        if (!bus_rst_n) begin
            enable_o <= 1'b0;
            up_down_o <= 1'b0;
            mode_o <= 1'b0;
            load_value_o <= {WIDTH{1'b0}};
            term_value_o <= {WIDTH{1'b1}};
            tc_en <= 1'b0;
            ovf_en <= 1'b0;
            unf_en <= 1'b0;
            clear_pulse_o <= 1'b0;
            load_pulse_o <= 1'b0;
            tc_clr_pulse_o <= 1'b0;
            ovf_clr_pulse_o <= 1'b0;
            unf_clr_pulse_o <= 1'b0;
        end else begin
            clear_pulse_o <= 1'b0;
            load_pulse_o <= 1'b0;
            tc_clr_pulse_o <= 1'b0;
            ovf_clr_pulse_o <= 1'b0;
            unf_clr_pulse_o <= 1'b0;

            // S0 S0_APB_ACCESS APB stage: decode and commit writes in the APB access phase.
            if (apb_wr) begin
                if (paddr == CTRL_A) begin
                    if (write_any_strobe) begin
                        enable_o <= pwdata[0];
                        up_down_o <= pwdata[1];
                        mode_o <= pwdata[2];
                        if (pwdata[3]) clear_pulse_o <= 1'b1;
                        if (pwdata[4]) load_pulse_o <= 1'b1;
                    end
                end else if (paddr == LOAD_A) begin
                    if (write_any_strobe) load_value_o <= pwdata_w;
                end else if (paddr == TERM_A) begin
                    if (write_any_strobe) term_value_o <= pwdata_w;
                end else if (paddr == INTEN_A) begin
                    if (write_any_strobe) begin
                        tc_en <= pwdata[0];
                        ovf_en <= pwdata[1];
                        unf_en <= pwdata[2];
                    end
                end else if (paddr == INTCLR_A) begin
                    if (write_any_strobe) begin
                        if (pwdata[0]) tc_clr_pulse_o <= 1'b1;
                        if (pwdata[1]) ovf_clr_pulse_o <= 1'b1;
                        if (pwdata[2]) unf_clr_pulse_o <= 1'b1;
                    end
                end
            end
        end
    end

    always @(*) begin
        prdata = 32'h00000000;
        if (apb_rd) begin
            case (paddr)
                CTRL_A:    prdata = {27'h0, 1'b0, 1'b0, mode_o, up_down_o, enable_o};
                CNT_A:     prdata = cnt_bus_i[31:0];
                LOAD_A:    prdata = load_value_o[31:0];
                TERM_A:    prdata = term_value_o[31:0];
                STATUS_A:  prdata = {30'h0, underflow_bus_i, overflow_bus_i};
                INTEN_A:   prdata = {29'h0, unf_en, ovf_en, tc_en};
                INTSTAT_A: prdata = {29'h0, unf_pending_bus_i, ovf_pending_bus_i, tc_pending_bus_i};
                INTCLR_A:  prdata = {29'h0, unf_pending_bus_i, ovf_pending_bus_i, tc_pending_bus_i};
                DBGCNT_A:  prdata = dbg_cycle_count_bus_i[31:0];
                default:   prdata = 32'h00000000;
            endcase
        end
    end

    // counter_irq irq handshake rule and S4 S4_STATUS_UPDATE STATUS UPDATE visibility in bus domain.
    assign irq_o = (tc_pending_bus_i & tc_en) | (ovf_pending_bus_i & ovf_en) | (unf_pending_bus_i & unf_en);
endmodule

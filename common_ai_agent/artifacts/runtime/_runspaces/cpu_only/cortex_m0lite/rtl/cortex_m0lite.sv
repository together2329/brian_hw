module cortex_m0lite #(
    parameter integer XLEN              = 32,
    parameter integer RESET_PC          = 0,
    parameter integer TRAP_VECTOR       = 128,
    parameter integer STACK_RESET       = 0,
    parameter integer REG_COUNT         = 16,
    parameter integer AHB_ADDR_W        = 32,
    parameter integer AHB_DATA_W        = 32,
    parameter integer CORE_FREQ_MHZ     = 300,
    parameter integer BUS_FREQ_MHZ      = 150,
    parameter integer AHB_HTRANS_IDLE   = 0,
    parameter integer AHB_HTRANS_BUSY   = 1,
    parameter integer AHB_HTRANS_NONSEQ = 2,
    parameter integer AHB_HTRANS_SEQ    = 3,
    parameter integer AHB_HSIZE_WORD    = 2,
    parameter integer AHB_HBURST_SINGLE = 0
) (
    input  logic                  clk,
    input  logic                  hclk,
    input  logic                  rst_n,
    input  logic                  hresetn,
    output logic [AHB_ADDR_W-1:0] i_haddr,
    output logic [1:0]            i_htrans,
    output logic                  i_hwrite,
    output logic [2:0]            i_hsize,
    output logic [2:0]            i_hburst,
    output logic [AHB_DATA_W-1:0] i_hwdata,
    input  logic [AHB_DATA_W-1:0] i_hrdata,
    input  logic                  i_hready,
    input  logic                  i_hresp,
    output logic [AHB_ADDR_W-1:0] d_haddr,
    output logic [1:0]            d_htrans,
    output logic                  d_hwrite,
    output logic [2:0]            d_hsize,
    output logic [2:0]            d_hburst,
    output logic [AHB_DATA_W-1:0] d_hwdata,
    input  logic [AHB_DATA_W-1:0] d_hrdata,
    input  logic                  d_hready,
    input  logic                  d_hresp,
    input  logic                  irq,
    output logic [XLEN-1:0]       pc_dbg,
    output logic [2:0]            state_dbg,
    output logic                  retire,
    output logic                  trap
);

    logic core_rst_ff1, core_rst_ff2;
    logic bus_rst_ff1,  bus_rst_ff2;
    logic core_rst_n_sync;
    logic bus_rst_n_sync;

    logic if_id_valid;
    logic if_id_ready;
    logic [XLEN-1:0] if_id_pc;
    logic [15:0] if_id_instr;
    logic if_path_activity;

    logic [AHB_ADDR_W-1:0] core_i_haddr;
    logic [1:0]            core_i_htrans;
    logic                  core_i_hwrite;
    logic [2:0]            core_i_hsize;
    logic [2:0]            core_i_hburst;
    logic [AHB_DATA_W-1:0] core_i_hwdata;
    logic [AHB_ADDR_W-1:0] core_d_haddr;
    logic [1:0]            core_d_htrans;
    logic                  core_d_hwrite;
    logic [2:0]            core_d_hsize;
    logic [2:0]            core_d_hburst;
    logic [AHB_DATA_W-1:0] core_d_hwdata;

    logic id_ex_valid;
    logic id_ex_ready;
    logic ex_wb_valid;
    logic ex_bus_req;
    logic wb_rf_we;
    logic [3:0] wb_rf_waddr;
    logic [XLEN-1:0] wb_rf_wdata;
    logic if_bus_req;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            core_rst_ff1 <= 1'b0;
            core_rst_ff2 <= 1'b0;
        end else begin
            core_rst_ff1 <= 1'b1;
            core_rst_ff2 <= core_rst_ff1;
        end
    end

    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) begin
            bus_rst_ff1 <= 1'b0;
            bus_rst_ff2 <= 1'b0;
        end else begin
            bus_rst_ff1 <= 1'b1;
            bus_rst_ff2 <= bus_rst_ff1;
        end
    end

    assign core_rst_n_sync = core_rst_ff2;
    assign bus_rst_n_sync  = bus_rst_ff2;

    cortex_m0lite_core #(
        .XLEN(XLEN), .RESET_PC(RESET_PC), .TRAP_VECTOR(TRAP_VECTOR), .STACK_RESET(STACK_RESET),
        .REG_COUNT(REG_COUNT), .AHB_ADDR_W(AHB_ADDR_W), .AHB_DATA_W(AHB_DATA_W),
        .CORE_FREQ_MHZ(CORE_FREQ_MHZ), .BUS_FREQ_MHZ(BUS_FREQ_MHZ),
        .AHB_HTRANS_IDLE(AHB_HTRANS_IDLE), .AHB_HTRANS_BUSY(AHB_HTRANS_BUSY),
        .AHB_HTRANS_NONSEQ(AHB_HTRANS_NONSEQ), .AHB_HTRANS_SEQ(AHB_HTRANS_SEQ),
        .AHB_HSIZE_WORD(AHB_HSIZE_WORD), .AHB_HBURST_SINGLE(AHB_HBURST_SINGLE)
    ) u_core (
        .clk(clk), .rst_n(core_rst_n_sync), .hclk(hclk), .hresetn(bus_rst_n_sync), .irq(irq),
        .i_haddr(core_i_haddr), .i_htrans(core_i_htrans), .i_hwrite(core_i_hwrite), .i_hsize(core_i_hsize), .i_hburst(core_i_hburst),
        .i_hwdata(core_i_hwdata), .i_hrdata(i_hrdata), .i_hready(i_hready), .i_hresp(i_hresp),
        .d_haddr(core_d_haddr), .d_htrans(core_d_htrans), .d_hwrite(core_d_hwrite), .d_hsize(core_d_hsize), .d_hburst(core_d_hburst),
        .d_hwdata(core_d_hwdata), .d_hrdata(d_hrdata), .d_hready(d_hready), .d_hresp(d_hresp),
        .pc_dbg(pc_dbg), .state_dbg(state_dbg), .retire(retire), .trap(trap)
    );

    if_stage #(.XLEN(XLEN)) u_if_stage (
        .clk(clk), .rst_n(core_rst_n_sync), .if_id_valid(if_id_valid), .if_id_ready(if_id_ready),
        .if_id_pc(if_id_pc), .if_id_instr(if_id_instr)
    );

    id_stage #(.XLEN(XLEN)) u_id_stage (
        .clk(clk), .rst_n(core_rst_n_sync), .if_id_valid(if_id_valid), .id_ex_valid(id_ex_valid), .id_ex_ready(id_ex_ready)
    );

    ex_stage #(.XLEN(XLEN)) u_ex_stage (
        .clk(clk), .rst_n(core_rst_n_sync), .id_ex_valid(id_ex_valid), .ex_wb_valid(ex_wb_valid), .ex_bus_req(ex_bus_req)
    );

    wb_stage u_wb_stage (
        .clk(clk), .rst_n(core_rst_n_sync), .ex_wb_valid(ex_wb_valid), .wb_rf_we(wb_rf_we)
    );

    regfile #(.XLEN(XLEN)) u_regfile (
        .clk(clk), .rst_n(core_rst_n_sync), .wb_rf_we(wb_rf_we), .wb_rf_waddr(wb_rf_waddr), .wb_rf_wdata(wb_rf_wdata)
    );

    bus_if #(.AHB_ADDR_W(AHB_ADDR_W)) u_bus_if (
        .hclk(hclk), .hresetn(bus_rst_n_sync), .if_bus_req(if_bus_req), .ex_bus_req(ex_bus_req), .i_haddr(i_haddr), .d_haddr(d_haddr)
    );

    // if_path_activity consumes all bits of if_id_pc and if_id_instr for lint
    assign if_path_activity = |if_id_pc | |if_id_instr;
    assign if_id_ready = 1'b1;
    assign id_ex_ready = 1'b1;
    assign wb_rf_waddr = 4'd0;
    assign wb_rf_wdata = {XLEN{1'b0}};
    assign i_haddr  = core_i_haddr;
    assign i_htrans = core_i_htrans;
    assign i_hwrite = core_i_hwrite;
    assign i_hsize  = core_i_hsize;
    assign i_hburst = core_i_hburst;
    assign i_hwdata = core_i_hwdata;
    assign d_haddr  = core_d_haddr;
    assign d_htrans = core_d_htrans;
    assign d_hwrite = core_d_hwrite;
    assign d_hsize  = core_d_hsize;
    assign d_hburst = core_d_hburst;
    assign d_hwdata = core_d_hwdata;
    assign if_bus_req = if_id_valid | if_path_activity;

endmodule

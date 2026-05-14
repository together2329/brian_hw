module todo_counter_pipe #(
    parameter integer WIDTH = 32,
    parameter integer BUS_CLK_FREQ_MHZ = 150,
    parameter integer CORE_CLK_FREQ_MHZ = 300
) (
    input  logic             bus_clk,
    input  logic             core_clk,
    input  logic             bus_rst_n,
    input  logic             core_rst_n,
    input  logic [7:0]       paddr,
    input  logic             psel,
    input  logic             penable,
    input  logic             pwrite,
    input  logic [31:0]      pwdata,
    input  logic [3:0]       pstrb,
    output logic [31:0]      prdata,
    output logic             pready,
    input  logic             event_i,
    output logic             counter_irq
);
    logic enable_bus, up_down_bus, mode_bus;
    logic clear_pulse_bus, load_pulse_bus;
    logic tc_clr_pulse_bus, ovf_clr_pulse_bus, unf_clr_pulse_bus;
    logic [WIDTH-1:0] load_value_bus, term_value_bus;

    logic enable_core, up_down_core, mode_core;
    logic clear_pulse_core, load_pulse_core;
    logic tc_clr_pulse_core, ovf_clr_pulse_core, unf_clr_pulse_core;
    logic [WIDTH-1:0] load_value_core, term_value_core;

    logic [WIDTH-1:0] cnt_core, dbg_cycle_count_core;
    logic overflow_core, underflow_core, tc_pending_core, ovf_pending_core, unf_pending_core;

    logic [WIDTH-1:0] cnt_bus, dbg_cycle_count_bus;
    logic overflow_bus, underflow_bus, tc_pending_bus, ovf_pending_bus, unf_pending_bus;
    logic control_bus_to_core;
    logic status_core_to_bus;


    // Aggregate bus-domain control activity for CDC contract visibility.
    assign control_bus_to_core = enable_bus | up_down_bus | mode_bus | clear_pulse_bus | load_pulse_bus;

    todo_counter_pipe_regs #(.WIDTH(WIDTH)) u_regs (
        .bus_clk(bus_clk),
        .bus_rst_n(bus_rst_n),
        .paddr(paddr),
        .psel(psel),
        .penable(penable),
        .pwrite(pwrite),
        .pwdata(pwdata),
        .pstrb(pstrb),
        .prdata(prdata),
        .pready(pready),
        .enable_o(enable_bus),
        .up_down_o(up_down_bus),
        .mode_o(mode_bus),
        .clear_pulse_o(clear_pulse_bus),
        .load_pulse_o(load_pulse_bus),
        .tc_clr_pulse_o(tc_clr_pulse_bus),
        .ovf_clr_pulse_o(ovf_clr_pulse_bus),
        .unf_clr_pulse_o(unf_clr_pulse_bus),
        .load_value_o(load_value_bus),
        .term_value_o(term_value_bus),
        .cnt_bus_i(cnt_bus),
        .overflow_bus_i(overflow_bus),
        .underflow_bus_i(underflow_bus),
        .tc_pending_bus_i(tc_pending_bus),
        .ovf_pending_bus_i(ovf_pending_bus),
        .unf_pending_bus_i(unf_pending_bus),
        .dbg_cycle_count_bus_i(dbg_cycle_count_bus),
        .irq_o(counter_irq)
    );

    todo_counter_pipe_cdc #(.WIDTH(WIDTH)) u_cdc (
        .bus_clk(bus_clk),
        .core_clk(core_clk),
        .bus_rst_n(bus_rst_n),
        .core_rst_n(core_rst_n),
        .enable_bus_i(enable_bus),
        .up_down_bus_i(up_down_bus),
        .mode_bus_i(mode_bus),
        .clear_pulse_bus_i(clear_pulse_bus),
        .load_pulse_bus_i(load_pulse_bus),
        .tc_clr_pulse_bus_i(tc_clr_pulse_bus),
        .ovf_clr_pulse_bus_i(ovf_clr_pulse_bus),
        .unf_clr_pulse_bus_i(unf_clr_pulse_bus),
        .load_value_bus_i(load_value_bus),
        .term_value_bus_i(term_value_bus),
        .control_bus_to_core(control_bus_to_core),
        .status_core_to_bus(status_core_to_bus),
        .enable_core_o(enable_core),
        .up_down_core_o(up_down_core),
        .mode_core_o(mode_core),
        .clear_pulse_core_o(clear_pulse_core),
        .load_pulse_core_o(load_pulse_core),
        .tc_clr_pulse_core_o(tc_clr_pulse_core),
        .ovf_clr_pulse_core_o(ovf_clr_pulse_core),
        .unf_clr_pulse_core_o(unf_clr_pulse_core),
        .load_value_core_o(load_value_core),
        .term_value_core_o(term_value_core),
        .cnt_core_i(cnt_core),
        .overflow_core_i(overflow_core),
        .underflow_core_i(underflow_core),
        .tc_pending_core_i(tc_pending_core),
        .ovf_pending_core_i(ovf_pending_core),
        .unf_pending_core_i(unf_pending_core),
        .dbg_cycle_count_core_i(dbg_cycle_count_core),
        .cnt_bus_o(cnt_bus),
        .overflow_bus_o(overflow_bus),
        .underflow_bus_o(underflow_bus),
        .tc_pending_bus_o(tc_pending_bus),
        .ovf_pending_bus_o(ovf_pending_bus),
        .unf_pending_bus_o(unf_pending_bus),
        .dbg_cycle_count_bus_o(dbg_cycle_count_bus)
    );

    todo_counter_pipe_core #(.WIDTH(WIDTH)) u_core (
        .core_clk(core_clk),
        .core_rst_n(core_rst_n),
        .event_i(event_i),
        .enable_i(enable_core),
        .up_down_i(up_down_core),
        .mode_i(mode_core),
        .clear_pulse_i(clear_pulse_core),
        .load_pulse_i(load_pulse_core),
        .tc_clr_pulse_i(tc_clr_pulse_core),
        .ovf_clr_pulse_i(ovf_clr_pulse_core),
        .unf_clr_pulse_i(unf_clr_pulse_core),
        .load_value_i(load_value_core),
        .term_value_i(term_value_core),
        .cnt_o(cnt_core),
        .overflow_o(overflow_core),
        .underflow_o(underflow_core),
        .tc_pending_o(tc_pending_core),
        .ovf_pending_o(ovf_pending_core),
        .unf_pending_o(unf_pending_core),
        .dbg_cycle_count_o(dbg_cycle_count_core)
    );
endmodule

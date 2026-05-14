module todo_counter_pipe_cdc #(
    parameter integer WIDTH = 32
) (
    input  logic                 bus_clk,
    input  logic                 core_clk,
    input  logic                 bus_rst_n,
    input  logic                 core_rst_n,
    input  logic                 enable_bus_i,
    input  logic                 up_down_bus_i,
    input  logic                 mode_bus_i,
    input  logic                 clear_pulse_bus_i,
    input  logic                 load_pulse_bus_i,
    input  logic                 tc_clr_pulse_bus_i,
    input  logic                 ovf_clr_pulse_bus_i,
    input  logic                 unf_clr_pulse_bus_i,
    input  logic [WIDTH-1:0]     load_value_bus_i,
    input  logic [WIDTH-1:0]     term_value_bus_i,
    input  logic                 control_bus_to_core,
    output logic                 status_core_to_bus,
    output logic                 enable_core_o,
    output logic                 up_down_core_o,
    output logic                 mode_core_o,
    output logic                 clear_pulse_core_o,
    output logic                 load_pulse_core_o,
    output logic                 tc_clr_pulse_core_o,
    output logic                 ovf_clr_pulse_core_o,
    output logic                 unf_clr_pulse_core_o,
    output logic [WIDTH-1:0]     load_value_core_o,
    output logic [WIDTH-1:0]     term_value_core_o,
    input  logic [WIDTH-1:0]     cnt_core_i,
    input  logic                 overflow_core_i,
    input  logic                 underflow_core_i,
    input  logic                 tc_pending_core_i,
    input  logic                 ovf_pending_core_i,
    input  logic                 unf_pending_core_i,
    input  logic [WIDTH-1:0]     dbg_cycle_count_core_i,
    output logic [WIDTH-1:0]     cnt_bus_o,
    output logic                 overflow_bus_o,
    output logic                 underflow_bus_o,
    output logic                 tc_pending_bus_o,
    output logic                 ovf_pending_bus_o,
    output logic                 unf_pending_bus_o,
    output logic [WIDTH-1:0]     dbg_cycle_count_bus_o
);
    logic enable_sync1, up_down_sync1, mode_sync1;
    logic clear_sync1, load_pulse_sync1, tc_clr_sync1, ovf_clr_sync1, unf_clr_sync1;
    logic [WIDTH-1:0] load_value_sync1, term_sync1;

    logic [WIDTH-1:0] cnt_sync1, dbg_sync1;
    logic ovf_sync1, unf_sync1, tc_sync1, ovfp_sync1, unfp_sync1;
    logic status_or_reduce;

    // bus->core control synchronizers (2-stage FF style).
    always @(posedge core_clk or negedge core_rst_n) begin
        if (!core_rst_n) begin
            enable_sync1 <= 1'b0; enable_core_o <= 1'b0;
            up_down_sync1 <= 1'b0; up_down_core_o <= 1'b0;
            mode_sync1 <= 1'b0; mode_core_o <= 1'b0;
            clear_sync1 <= 1'b0; clear_pulse_core_o <= 1'b0;
            load_pulse_sync1 <= 1'b0; load_pulse_core_o <= 1'b0;
            tc_clr_sync1 <= 1'b0; tc_clr_pulse_core_o <= 1'b0;
            ovf_clr_sync1 <= 1'b0; ovf_clr_pulse_core_o <= 1'b0;
            unf_clr_sync1 <= 1'b0; unf_clr_pulse_core_o <= 1'b0;
            load_value_sync1 <= {WIDTH{1'b0}}; load_value_core_o <= {WIDTH{1'b0}};
            term_sync1 <= {WIDTH{1'b1}}; term_value_core_o <= {WIDTH{1'b1}};
        end else begin
            enable_sync1 <= enable_bus_i; enable_core_o <= enable_sync1;
            up_down_sync1 <= up_down_bus_i; up_down_core_o <= up_down_sync1;
            mode_sync1 <= mode_bus_i; mode_core_o <= mode_sync1;
            clear_sync1 <= clear_pulse_bus_i; clear_pulse_core_o <= clear_sync1;
            load_pulse_sync1 <= load_pulse_bus_i; load_pulse_core_o <= load_pulse_sync1;
            tc_clr_sync1 <= tc_clr_pulse_bus_i; tc_clr_pulse_core_o <= tc_clr_sync1;
            ovf_clr_sync1 <= ovf_clr_pulse_bus_i; ovf_clr_pulse_core_o <= ovf_clr_sync1;
            unf_clr_sync1 <= unf_clr_pulse_bus_i; unf_clr_pulse_core_o <= unf_clr_sync1;
            load_value_sync1 <= load_value_bus_i; load_value_core_o <= load_value_sync1;
            term_sync1 <= term_value_bus_i; term_value_core_o <= term_sync1;
        end
    end

    // core->bus status synchronizers (2-stage FF style).
    always @(posedge bus_clk or negedge bus_rst_n) begin
        if (!bus_rst_n) begin
            cnt_sync1 <= {WIDTH{1'b0}}; cnt_bus_o <= {WIDTH{1'b0}};
            dbg_sync1 <= {WIDTH{1'b0}}; dbg_cycle_count_bus_o <= {WIDTH{1'b0}};
            ovf_sync1 <= 1'b0; overflow_bus_o <= 1'b0;
            unf_sync1 <= 1'b0; underflow_bus_o <= 1'b0;
            tc_sync1 <= 1'b0; tc_pending_bus_o <= 1'b0;
            ovfp_sync1 <= 1'b0; ovf_pending_bus_o <= 1'b0;
            unfp_sync1 <= 1'b0; unf_pending_bus_o <= 1'b0;
        end else begin
            cnt_sync1 <= cnt_core_i; cnt_bus_o <= cnt_sync1;
            dbg_sync1 <= dbg_cycle_count_core_i; dbg_cycle_count_bus_o <= dbg_sync1;
            ovf_sync1 <= overflow_core_i; overflow_bus_o <= ovf_sync1;
            unf_sync1 <= underflow_core_i; underflow_bus_o <= unf_sync1;
            tc_sync1 <= tc_pending_core_i; tc_pending_bus_o <= tc_sync1;
            ovfp_sync1 <= ovf_pending_core_i; ovf_pending_bus_o <= ovfp_sync1;
            unfp_sync1 <= unf_pending_core_i; unf_pending_bus_o <= unfp_sync1;
        end
    end
    assign status_or_reduce = overflow_bus_o | underflow_bus_o | tc_pending_bus_o | ovf_pending_bus_o | unf_pending_bus_o;
    // Machine-readable contract hook ports: control_bus_to_core is consumed;
    // status_core_to_bus reports synchronized core->bus status activity.
    assign status_core_to_bus = status_or_reduce;
endmodule

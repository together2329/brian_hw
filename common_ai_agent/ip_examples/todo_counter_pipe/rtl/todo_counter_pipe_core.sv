module todo_counter_pipe_core #(
    parameter integer WIDTH = 32
) (
    input  logic                 core_clk,
    input  logic                 core_rst_n,
    input  logic                 event_i,
    input  logic                 enable_i,
    input  logic                 up_down_i,
    input  logic                 mode_i,
    input  logic                 clear_pulse_i,
    input  logic                 load_pulse_i,
    input  logic                 tc_clr_pulse_i,
    input  logic                 ovf_clr_pulse_i,
    input  logic                 unf_clr_pulse_i,
    input  logic [WIDTH-1:0]     load_value_i,
    input  logic [WIDTH-1:0]     term_value_i,
    output logic [WIDTH-1:0]     cnt_o,
    output logic                 overflow_o,
    output logic                 underflow_o,
    output logic                 tc_pending_o,
    output logic                 ovf_pending_o,
    output logic                 unf_pending_o,
    output logic [WIDTH-1:0]     dbg_cycle_count_o
);
    localparam [0:0] IDLE  = 1'b0;
    localparam [0:0] COUNT = 1'b1;

    logic [0:0] state;
    logic       event_d;
    logic       event_rise;
    logic [WIDTH-1:0] max_value;
    logic [WIDTH-1:0] cnt_reg;
    logic [WIDTH-1:0] dbg_cycle_reg;
    logic [WIDTH-1:0] cnt_new;
    logic             irq_core_any;

    assign max_value = {WIDTH{1'b1}};
    assign event_rise = event_i & (~event_d);
    assign cnt_new = up_down_i ? (cnt_reg - {{(WIDTH-1){1'b0}}, 1'b1}) : (cnt_reg + {{(WIDTH-1){1'b0}}, 1'b1});
    assign irq_core_any = tc_pending_o | ovf_pending_o | unf_pending_o;

    always @(posedge core_clk or negedge core_rst_n) begin
        if (!core_rst_n) begin
            state             <= IDLE;
            event_d           <= 1'b0;
            cnt_reg           <= {WIDTH{1'b0}};
            cnt_o             <= {WIDTH{1'b0}};
            overflow_o        <= 1'b0;
            underflow_o       <= 1'b0;
            tc_pending_o      <= 1'b0;
            ovf_pending_o     <= 1'b0;
            unf_pending_o     <= 1'b0;
            dbg_cycle_reg     <= {WIDTH{1'b0}};
            dbg_cycle_count_o <= {WIDTH{1'b0}};
        end else begin
            // S1 CDC CTRL S1 S1_CDC_CTRL: controls from bus_clk are consumed after CDC before S2 evaluation.
            // Debug Cycle Counter memory instance (dbg_cycle_reg) increments every core clock.
            dbg_cycle_reg     <= dbg_cycle_reg + {{(WIDTH-1){1'b0}}, 1'b1};
            dbg_cycle_count_o <= dbg_cycle_reg;
            event_d <= event_i;

            if (!enable_i) state <= IDLE;
            else if (event_rise) state <= COUNT;
            else state <= state;

            // W1C interrupt/status clear pulses after bus->core CDC.
            if (tc_clr_pulse_i)  tc_pending_o  <= 1'b0;
            if (ovf_clr_pulse_i) begin
                ovf_pending_o <= 1'b0;
                overflow_o    <= 1'b0;
            end
            if (unf_clr_pulse_i) begin
                unf_pending_o <= 1'b0;
                underflow_o   <= 1'b0;
            end

            // Clear/Load priority over counting per SSOT internal_control priority.
            if (clear_pulse_i) begin
                cnt_reg <= {WIDTH{1'b0}};
                cnt_o   <= {WIDTH{1'b0}};
            end else if (load_pulse_i) begin
                cnt_reg <= load_value_i;
                cnt_o   <= load_value_i;
            end else if (enable_i && event_rise) begin
                // S2 COUNT EVAL S2 S2_COUNT_EVAL stage: event_i rising edge drives arithmetic and terminal checks.
                if (!up_down_i) begin
                    if (cnt_reg >= term_value_i) tc_pending_o <= 1'b1;

                    if (cnt_reg == max_value) begin
                        ovf_pending_o <= 1'b1;
                        overflow_o    <= 1'b1;
                        if (mode_i) begin cnt_reg <= {WIDTH{1'b0}}; cnt_o <= {WIDTH{1'b0}}; end
                        else begin cnt_reg <= max_value; cnt_o <= max_value; end
                    end else if (cnt_reg >= term_value_i) begin
                        if (mode_i) begin cnt_reg <= {WIDTH{1'b0}}; cnt_o <= {WIDTH{1'b0}}; end
                        else begin cnt_reg <= term_value_i; cnt_o <= term_value_i; end
                    end else begin
                        cnt_reg <= cnt_new;
                        cnt_o   <= cnt_new;
                    end
                end else begin
                    if (cnt_reg == {WIDTH{1'b0}}) tc_pending_o <= 1'b1;

                    if (cnt_reg == {WIDTH{1'b0}}) begin
                        unf_pending_o <= 1'b1;
                        underflow_o   <= 1'b1;
                        if (mode_i) begin cnt_reg <= max_value; cnt_o <= max_value; end
                        else begin cnt_reg <= {WIDTH{1'b0}}; cnt_o <= {WIDTH{1'b0}}; end
                    end else begin
                        cnt_reg <= cnt_new;
                        cnt_o   <= cnt_new;
                    end
                end
            end
            // S3 CDC STATUS S3 S3_CDC_STATUS: core-domain status flops feed the core->bus synchronizer stage.
            if (irq_core_any) begin
                // FM10 interrupt_clear side effect: counter_irq irq deassertion occurs after pending clears propagate to bus domain.
                // Ordering rule references bus and bus_clk convergence through CDC before IRQ visibility.
                state <= state;
            end
        end
    end
endmodule

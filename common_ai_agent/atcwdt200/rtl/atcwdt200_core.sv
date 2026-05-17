`include "atcwdt200_param.vh"

module atcwdt200_core #(
    parameter COUNTER_WIDTH = 16,
    parameter INT_TIME_WIDTH = (COUNTER_WIDTH == 32) ? 4 : 3
) (
    input  logic pclk,
    input  logic presetn,
    input  logic cr_en,
    input  logic cr_clk,
    input  logic cr_inten,
    input  logic cr_rsten,
    input  logic [INT_TIME_WIDTH-1:0] cr_inttime,
    input  logic [2:0] cr_rsttime,
    input  logic sr_intzero,
    input  logic restart_pulse,
    input  logic extclk_rise,
    input  logic wdt_pause_sync,
    output logic core_set_intzero,
    output logic core_set_rstzero,
    output logic core_clear_en,
    output logic wdt_int,
    output logic wdt_rst
);
    localparam ST_INTTIME = 1'b0;
    localparam ST_RSTTIME = 1'b1;

    logic [COUNTER_WIDTH-1:0] counter;
    logic state;
    logic sr_rstzero;
    logic time_end;

    wire [31:0] counter_32b;
    wire [3:0] cr_inttime_4b;
    wire interval_en;
    wire selected_tick;
    wire counter_en;
    wire inttime_end;
    wire rsttime_end;
    wire [COUNTER_WIDTH-1:0] counter_inc;
    wire [COUNTER_WIDTH-1:0] counter_nxt;

    assign counter_32b = counter;
    assign cr_inttime_4b = cr_inttime;
    assign interval_en = (state == ST_INTTIME) ? 1'b1 : cr_rsten;
    assign selected_tick = cr_clk ? 1'b1 : extclk_rise;
    assign inttime_end = cr_en & (state == ST_INTTIME) & time_end;
    assign rsttime_end = cr_en & (state == ST_RSTTIME) & time_end;
    assign counter_en = (~wdt_pause_sync) & ((cr_en & interval_en & selected_tick) | restart_pulse | inttime_end);
    assign counter_inc = counter + {{COUNTER_WIDTH-1{1'b0}}, 1'b1};
    assign counter_nxt = (restart_pulse | inttime_end) ? {COUNTER_WIDTH{1'b0}} : counter_inc;

    always @(*) begin
        time_end = 1'b0;
        if (state == ST_INTTIME) begin
            case (cr_inttime_4b)
                4'h0: time_end = counter_32b[6];
                4'h1: time_end = counter_32b[8];
                4'h2: time_end = counter_32b[10];
                4'h3: time_end = counter_32b[11];
                4'h4: time_end = counter_32b[12];
                4'h5: time_end = counter_32b[13];
                4'h6: time_end = counter_32b[14];
                4'h7: time_end = counter_32b[15];
                4'h8: time_end = counter_32b[17];
                4'h9: time_end = counter_32b[19];
                4'ha: time_end = counter_32b[21];
                4'hb: time_end = counter_32b[23];
                4'hc: time_end = counter_32b[25];
                4'hd: time_end = counter_32b[27];
                4'he: time_end = counter_32b[29];
                default: time_end = counter_32b[31];
            endcase
        end else begin
            case (cr_rsttime)
                3'h0: time_end = counter_32b[7];
                3'h1: time_end = counter_32b[8];
                3'h2: time_end = counter_32b[9];
                3'h3: time_end = counter_32b[10];
                3'h4: time_end = counter_32b[11];
                3'h5: time_end = counter_32b[12];
                3'h6: time_end = counter_32b[13];
                default: time_end = counter_32b[14];
            endcase
        end
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            counter          <= {COUNTER_WIDTH{1'b0}};
            state            <= ST_INTTIME;
            sr_rstzero       <= 1'b0;
            core_set_intzero <= 1'b0;
            core_set_rstzero <= 1'b0;
            core_clear_en    <= 1'b0;
        end else begin
            core_set_intzero <= 1'b0;
            core_set_rstzero <= 1'b0;
            core_clear_en    <= 1'b0;

            if (counter_en) begin
                counter <= counter_nxt;
            end

            if (cr_en | restart_pulse) begin
                if (state == ST_INTTIME) begin
                    if (inttime_end & ~restart_pulse) begin
                        state <= ST_RSTTIME;
                    end else begin
                        state <= ST_INTTIME;
                    end
                end else begin
                    if (restart_pulse) begin
                        state <= ST_INTTIME;
                    end else begin
                        state <= ST_RSTTIME;
                    end
                end
            end

            if (restart_pulse) begin
                sr_rstzero <= 1'b0;
            end else if (rsttime_end) begin
                sr_rstzero <= 1'b1;
            end

            if (inttime_end) begin
                core_set_intzero <= 1'b1;
            end

            if (rsttime_end) begin
                core_set_rstzero <= 1'b1;
                core_clear_en    <= 1'b1;
            end
        end
    end

    always @(*) begin
        wdt_int = sr_intzero & cr_inten;
        wdt_rst = sr_rstzero & cr_rsten;
    end
endmodule

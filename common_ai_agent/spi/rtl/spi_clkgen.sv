// spi_clkgen.sv — PCLK-based SCLK half-period ticker from SSOT cycle_model/timing
module spi_clkgen #(
    `include "spi_param.vh"
) (
    input  logic                      PCLK,
    input  logic                      PRESETn,
    input  logic                      soft_reset,
    input  logic                      busy,
    input  logic                      cpol,
    input  logic [PRESCALE_WIDTH-1:0] prescale_div,
    output logic                      sclk_o,
    output logic                      prescale_tick,
    output logic                      sample_edge,
    output logic                      shift_edge
);
    logic [PRESCALE_WIDTH-1:0] prescale_cnt;
    logic edge_phase;
    logic tick_next;

    always @(*) begin
        tick_next = 1'b0;
        if (busy && (prescale_cnt == prescale_div)) begin
            tick_next = 1'b1;
        end
    end

    // SSOT timing: each SCLK half-period lasts divisor+1 PCLK cycles.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            prescale_cnt <= {PRESCALE_WIDTH{1'b0}};
            prescale_tick <= 1'b0;
            edge_phase <= 1'b0;
            sclk_o <= CPOL_RESET[0];
        end else if (soft_reset) begin
            prescale_cnt <= {PRESCALE_WIDTH{1'b0}};
            prescale_tick <= 1'b0;
            edge_phase <= 1'b0;
            sclk_o <= cpol;
        end else begin
            prescale_tick <= tick_next;
            if (!busy) begin
                prescale_cnt <= {PRESCALE_WIDTH{1'b0}};
                edge_phase <= 1'b0;
                sclk_o <= cpol;
            end else if (tick_next) begin
                prescale_cnt <= {PRESCALE_WIDTH{1'b0}};
                edge_phase <= ~edge_phase;
                sclk_o <= ~sclk_o;
            end else begin
                prescale_cnt <= prescale_cnt + {{(PRESCALE_WIDTH-1){1'b0}}, 1'b1};
            end
        end
    end

    // The shift engine combines these alternating edges with CPHA for launch/sample order.
    always @(*) begin
        shift_edge = 1'b0;
        sample_edge = 1'b0;
        if (prescale_tick) begin
            if (edge_phase == 1'b0) begin
                shift_edge = 1'b1;
            end else begin
                sample_edge = 1'b1;
            end
        end
    end
endmodule

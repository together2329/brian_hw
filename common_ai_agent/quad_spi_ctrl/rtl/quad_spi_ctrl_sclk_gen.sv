// quad_spi_ctrl_sclk_gen.sv — SCLK waveform generation from PCLK prescaler
// SSOT refs: cycle_model.handshake_rules.sclk_o, cycle_model.handshake_rules.sample_edge,
//            cycle_model.pipeline, timing.protocol_timing
module quad_spi_ctrl_sclk_gen #(
  parameter PRESCALE_WIDTH = 16
) (
  input  wire        PCLK,
  input  wire        PRESETn,

  // Control
  input  wire [PRESCALE_WIDTH-1:0] prescale_div,
  input  wire                      cpol,
  input  wire                      cpha,
  input  wire                      sclk_enable,
  input  wire                      sw_reset,

  // SCLK output
  output wire        sclk_o,

  // Edge indicators for FSM
  output wire        sclk_rising,
  output wire        sclk_falling,
  output wire        sclk_sample_edge,
  output wire        prescale_tick
);

  reg [PRESCALE_WIDTH-1:0] prescale_cnt;
  reg                      sclk_r;
  reg                      sclk_prev;
  reg                      tick;
  wire [PRESCALE_WIDTH:0] half_period = {1'b0, prescale_div} + 1'b1;

  // Prescaler counter
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      prescale_cnt <= '0;
      tick         <= 1'b0;
    end else if (sw_reset) begin
      prescale_cnt <= '0;
      tick         <= 1'b0;
    end else if (sclk_enable) begin
      if (prescale_cnt >= half_period - 1'b1) begin
        prescale_cnt <= '0;
        tick         <= 1'b1;
      end else begin
        prescale_cnt <= prescale_cnt + 1'b1;
        tick         <= 1'b0;
      end
    end else begin
      prescale_cnt <= '0;
      tick         <= 1'b0;
    end
  end

  assign prescale_tick = tick;

  // SCLK toggle
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      sclk_r    <= cpol_from_rst();
      sclk_prev <= cpol_from_rst();
    end else if (sw_reset) begin
      sclk_r    <= cpol;
      sclk_prev <= cpol;
    end else if (sclk_enable && tick) begin
      sclk_prev <= sclk_r;
      sclk_r    <= ~sclk_r;
    end else begin
      sclk_prev <= sclk_r;
    end
  end

  // initial block helper for synthesis-safe reset
  function automatic cpol_from_rst();
    return 1'b0; // CPOL is 0 at reset, so idle-low
  endfunction

  assign sclk_o    = sclk_r;
  assign sclk_rising  = (sclk_r && !sclk_prev) ? 1'b1 : 1'b0;
  assign sclk_falling = (!sclk_r && sclk_prev) ? 1'b1 : 1'b0;

  // Sample edge: CPHA=0 → first edge (after CS assertion, which is on rising edge of launch gate)
  // CPHA=1 → second edge
  assign sclk_sample_edge = (cpha == 1'b0) ? sclk_falling : sclk_rising;

endmodule

// =============================================================================
// System Timer Controller — RTL Implementation (Verilog-2001)
// =============================================================================
// 32-bit countdown timer with auto-reload, configurable prescaler,
// periodic and one-shot modes, interrupt on expiry, APB4 slave interface.
// =============================================================================

module timer #(
  parameter COUNTER_WIDTH   = 32,
  parameter PRESCALER_WIDTH = 16,
  parameter ADDR_WIDTH      = 8
)(
  // ---- APB4 Slave Interface ----
  input  wire                  pclk,
  input  wire                  preset_n,
  input  wire                  psel,
  input  wire                  penable,
  input  wire                  pwrite,
  input  wire [ADDR_WIDTH-1:0] paddr,
  input  wire [31:0]          pwdata,
  output reg  [31:0]          prdata,
  output wire                  pready,
  output wire                  pslverr,

  // ---- Interrupt ----
  output wire                  irq
);

  // =========================================================================
  // APB decode
  // =========================================================================
  wire       apb_write = psel & penable & pwrite;
  wire       apb_read  = psel & penable & ~pwrite;
  wire [3:0] reg_sel   = paddr[3:0];

  assign pready  = 1'b1;
  assign pslverr = 1'b0;

  // =========================================================================
  // Internal registers
  // =========================================================================
  reg [COUNTER_WIDTH-1:0]   reg_load;
  reg                       reg_enable;
  reg                       reg_mode;       // 0=periodic, 1=one-shot
  reg [PRESCALER_WIDTH-1:0] reg_prescaler;
  reg                       reg_int_en;

  // =========================================================================
  // Counter and prescaler
  // =========================================================================
  reg [COUNTER_WIDTH-1:0]   counter;
  reg [PRESCALER_WIDTH-1:0] prescaler_cnt;
  reg                       int_status;

  // Prescaled tick: asserted when prescaler reaches zero
  wire prescaler_tick = (prescaler_cnt == {PRESCALER_WIDTH{1'b0}});

  // Counter expire event
  wire counter_expired = prescaler_tick & (counter == {COUNTER_WIDTH{1'b0}});

  // =========================================================================
  // APB Read Mux (combinational)
  // =========================================================================
  always @(*) begin
    prdata = 32'd0;
    case (reg_sel)
      4'h0: begin
        // LOAD
        prdata[COUNTER_WIDTH-1:0] = reg_load;
      end
      4'h4: begin
        // VALUE
        prdata[COUNTER_WIDTH-1:0] = counter;
      end
      4'h8: begin
        // CTRL
        prdata[0]    = reg_enable;
        prdata[1]    = reg_mode;
        prdata[17:2] = reg_prescaler;
        prdata[18]   = reg_int_en;
      end
      4'hC: begin
        // INT_STATUS
        prdata[0] = int_status;
      end
      default: prdata = 32'd0;
    endcase
  end

  // =========================================================================
  // Main sequential logic — all register writes in a single always block
  // to avoid multiple-driver issues.
  // =========================================================================
  always @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      reg_load      <= {COUNTER_WIDTH{1'b0}};
      reg_enable    <= 1'b0;
      reg_mode      <= 1'b0;
      reg_prescaler <= {PRESCALER_WIDTH{1'b0}};
      reg_int_en    <= 1'b0;
      counter       <= {COUNTER_WIDTH{1'b0}};
      prescaler_cnt <= {PRESCALER_WIDTH{1'b0}};
      int_status    <= 1'b0;
    end else begin

      // ------------------------------------------------------------------
      // APB register writes
      // ------------------------------------------------------------------
      if (apb_write) begin
        case (reg_sel)
          4'h0: begin // LOAD
            reg_load <= pwdata[COUNTER_WIDTH-1:0];
          end
          4'h8: begin // CTRL
            // If timer being newly enabled, load counter from reg_load
            if (!reg_enable && pwdata[0])
              counter <= reg_load;
            reg_enable    <= pwdata[0];
            reg_mode      <= pwdata[1];
            reg_prescaler <= pwdata[17:2];
            reg_int_en    <= pwdata[18];
          end
          4'hC: begin // INT_STATUS — W1C
            int_status <= int_status & ~pwdata[0];
          end
          default: ;
        endcase
      end

      // ------------------------------------------------------------------
      // Prescaler
      // ------------------------------------------------------------------
      if (reg_enable) begin
        if (prescaler_cnt == {PRESCALER_WIDTH{1'b0}})
          prescaler_cnt <= reg_prescaler;
        else
          prescaler_cnt <= prescaler_cnt - 1'b1;
      end else begin
        prescaler_cnt <= reg_prescaler;
      end

      // ------------------------------------------------------------------
      // Counter & expiry logic (only when not writing CTRL with new-enable)
      // ------------------------------------------------------------------
      if (reg_enable && !apb_write) begin
        if (counter_expired) begin
          // Set interrupt flag
          int_status <= 1'b1;
          if (reg_mode == 1'b0) begin
            // Periodic: auto-reload
            counter <= reg_load;
          end else begin
            // One-shot: auto-disable
            reg_enable <= 1'b0;
          end
        end else if (prescaler_tick) begin
          counter <= counter - 1'b1;
        end
      end

    end
  end

  // =========================================================================
  // IRQ output
  // =========================================================================
  assign irq = int_status & reg_int_en;

endmodule

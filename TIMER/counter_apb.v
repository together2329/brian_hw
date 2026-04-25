`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: counter_apb
// Description: APB3 slave interface wrapping the 64-bit counter core.
//
// Register Map (word-aligned, PADDR[7:0]):
//   Offset 0x00  CTRL       R/W  [0]=enable, [1]=load (W1P), [2]=up_down
//   Offset 0x04  COUNT_LO   R/W  [31:0] lower 32 bits of counter
//   Offset 0x08  COUNT_HI   R/W  [31:0] upper 32 bits of counter
//   Offset 0x0C  TC_STATUS  R    [0]=tc_sticky (cleared on read)
//
// APB3 Signals:
//   PCLK     - Bus clock
//   PRESETn  - Active-low bus reset
//   PSEL     - Select signal
//   PENABLE  - Enable signal
//   PWRITE   - Write strobe
//   PADDR    - Address bus [7:0]
//   PWDATA   - Write data [31:0]
//   PRDATA   - Read data [31:0]
//   PREADY   - Transfer ready (always 1)
//   PSLVERR  - Slave error (always 0)
//
// Note: The 64-bit counter value is accessed via two 32-bit registers.
// COUNT_LO (0x04) and COUNT_HI (0x08). Writes to each half update
// independently. For atomic updates, write both registers then pulse
// load via CTRL.
//----------------------------------------------------------------------------

module counter_apb (
    input  wire         PCLK,
    input  wire         PRESETn,
    input  wire         PSEL,
    input  wire         PENABLE,
    input  wire         PWRITE,
    input  wire [7:0]   PADDR,
    input  wire [31:0]  PWDATA,
    output wire [31:0]  PRDATA,
    output wire         PREADY,
    output wire         PSLVERR,

    // Counter interrupt output
    output wire         irq
);

    //--------------------------------------------------------------------------
    // Internal register storage
    //--------------------------------------------------------------------------
    reg        ctrl_enable;
    reg        ctrl_load_pulse;
    reg        ctrl_up_down;
    reg [31:0] count_lo_shadow;   // Lower 32 bits for load
    reg [31:0] count_hi_shadow;   // Upper 32 bits for load
    reg        tc_sticky;

    //--------------------------------------------------------------------------
    // Address decode
    //--------------------------------------------------------------------------
    wire [2:0] addr_word = PADDR[4:2];

    wire sel_ctrl      = (addr_word == 3'd0);
    wire sel_count_lo  = (addr_word == 3'd1);
    wire sel_count_hi  = (addr_word == 3'd2);
    wire sel_tc_status = (addr_word == 3'd3);

    // APB write/read strobes
    wire apb_write = PSEL && PENABLE && PWRITE;
    wire apb_read  = PSEL && PENABLE && !PWRITE;

    //--------------------------------------------------------------------------
    // Register write logic
    //--------------------------------------------------------------------------
    always @(posedge PCLK) begin
        if (!PRESETn) begin
            ctrl_enable     <= 1'b0;
            ctrl_load_pulse <= 1'b0;
            ctrl_up_down    <= 1'b0;
            count_lo_shadow <= 32'd0;
            count_hi_shadow <= 32'd0;
            tc_sticky       <= 1'b0;
        end else begin
            // Auto-clear the load pulse after one clock
            ctrl_load_pulse <= 1'b0;

            // Latch tc_sticky from counter core
            if (counter_tc) begin
                tc_sticky <= 1'b1;
            end

            if (apb_write) begin
                case (addr_word)
                    3'd0: begin // CTRL
                        ctrl_enable     <= PWDATA[0];
                        ctrl_load_pulse <= PWDATA[1];  // W1P
                        ctrl_up_down    <= PWDATA[2];
                    end
                    3'd1: begin // COUNT_LO
                        count_lo_shadow <= PWDATA;
                    end
                    3'd2: begin // COUNT_HI
                        count_hi_shadow <= PWDATA;
                    end
                    // TC_STATUS: read-only, ignore writes
                    default: ;
                endcase
            end

            // Clear sticky tc on TC_STATUS register read
            if (apb_read && sel_tc_status) begin
                tc_sticky <= 1'b0;
            end
        end
    end

    //--------------------------------------------------------------------------
    // Counter core signals
    //--------------------------------------------------------------------------
    wire [63:0] counter_value;
    wire        counter_tc;

    //--------------------------------------------------------------------------
    // Instantiate counter core
    //--------------------------------------------------------------------------
    counter u_counter (
        .clk     (PCLK),
        .rst_n   (PRESETn),
        .enable  (ctrl_enable),
        .load    (ctrl_load_pulse),
        .up_down (ctrl_up_down),
        .din     ({count_hi_shadow, count_lo_shadow}),
        .count   (counter_value),
        .tc      (counter_tc)
    );

    //--------------------------------------------------------------------------
    // Read data mux
    //--------------------------------------------------------------------------
    reg [31:0] prdata_reg;

    always @(*) begin
        prdata_reg = 32'd0;  // Default: return 0 for unmapped addresses
        case (addr_word)
            3'd0:    prdata_reg = {29'd0, ctrl_up_down, ctrl_load_pulse, ctrl_enable};
            3'd1:    prdata_reg = counter_value[31:0];
            3'd2:    prdata_reg = counter_value[63:32];
            3'd3:    prdata_reg = {31'd0, tc_sticky};
            default: prdata_reg = 32'd0;
        endcase
    end

    assign PRDATA  = prdata_reg;
    assign PREADY  = 1'b1;   // No wait states
    assign PSLVERR = 1'b0;   // No slave errors

    //--------------------------------------------------------------------------
    // IRQ output: level-sensitive, asserted when tc_sticky is set
    //--------------------------------------------------------------------------
    assign irq = tc_sticky;

endmodule

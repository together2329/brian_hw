`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: timer_apb
// Description: APB3 slave interface wrapping the 32-bit timer core.
//
// Register Map (word-aligned, PADDR[7:0]):
//   Offset 0x00  CTRL       R/W  [0]=enable, [1]=auto_reload, [2]=load (W1P)
//   Offset 0x04  PERIOD     R/W  [31:0] countdown start value
//   Offset 0x08  PRESCALER  R/W  [15:0] clock divider
//   Offset 0x0C  VALUE      R    [31:0] current counter value (read-only)
//   Offset 0x10  STATUS     R    [0]=running, [1]=done_sticky (cleared on read)
//
// APB3 Signals:
//   PCLK     - Bus clock (connected to timer clk)
//   PRESETn  - Active-low bus reset (connected to timer rst_n)
//   PSEL     - Select signal
//   PENABLE  - Enable signal
//   PWRITE   - Write strobe (1=write, 0=read)
//   PADDR    - Address bus [7:0]
//   PWDATA   - Write data [31:0]
//   PRDATA   - Read data [31:0]
//   PREADY   - Transfer ready (always 1, no wait states)
//   PSLVERR  - Slave error (always 0)
//----------------------------------------------------------------------------

module timer_apb (
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

    // Timer interrupt output
    output wire         irq
);

    //--------------------------------------------------------------------------
    // Internal register storage
    //--------------------------------------------------------------------------
    reg        ctrl_enable;
    reg        ctrl_auto_reload;
    reg        ctrl_load_pulse;
    reg [31:0] reg_period;
    reg [15:0] reg_prescaler;
    reg        done_sticky;

    //--------------------------------------------------------------------------
    // Address decode
    //--------------------------------------------------------------------------
    wire [2:0] addr_word = PADDR[4:2];  // Word-aligned address index

    wire sel_ctrl      = (addr_word == 3'd0);
    wire sel_period    = (addr_word == 3'd1);
    wire sel_prescaler = (addr_word == 3'd2);
    wire sel_value     = (addr_word == 3'd3);
    wire sel_status    = (addr_word == 3'd4);

    // APB write on access phase
    wire apb_write = PSEL && PENABLE && PWRITE;
    wire apb_read  = PSEL && PENABLE && !PWRITE;

    //--------------------------------------------------------------------------
    // Register write logic
    //--------------------------------------------------------------------------
    always @(posedge PCLK) begin
        if (!PRESETn) begin
            ctrl_enable     <= 1'b0;
            ctrl_auto_reload<= 1'b0;
            ctrl_load_pulse <= 1'b0;
            reg_period      <= 32'd0;
            reg_prescaler   <= 16'd1;
            done_sticky     <= 1'b0;
        end else begin
            // Auto-clear the load pulse after one clock
            ctrl_load_pulse <= 1'b0;

            // Latch done_sticky from timer core (set on done, clear on STATUS read)
            if (timer_done) begin
                done_sticky <= 1'b1;
            end

            if (apb_write) begin
                case (addr_word)
                    3'd0: begin // CTRL
                        ctrl_enable     <= PWDATA[0];
                        ctrl_auto_reload<= PWDATA[1];
                        ctrl_load_pulse <= PWDATA[2];  // W1P: set on write
                    end
                    3'd1: begin // PERIOD
                        reg_period <= PWDATA;
                    end
                    3'd2: begin // PRESCALER
                        reg_prescaler <= PWDATA[15:0];
                    end
                    // VALUE (0x0C): read-only, ignore writes
                    // STATUS (0x10): read-only, but reading clears done_sticky
                    default: ;
                endcase
            end

            // Clear sticky done on STATUS register read
            if (apb_read && sel_status) begin
                done_sticky <= 1'b0;
            end
        end
    end

    //--------------------------------------------------------------------------
    // Timer core signals
    //--------------------------------------------------------------------------
    wire [31:0] timer_value;
    wire        timer_done;
    wire        timer_running;

    //--------------------------------------------------------------------------
    // Instantiate timer core
    //--------------------------------------------------------------------------
    timer u_timer (
        .clk         (PCLK),
        .rst_n       (PRESETn),
        .enable      (ctrl_enable),
        .load        (ctrl_load_pulse),
        .prescaler   (reg_prescaler),
        .period      (reg_period),
        .auto_reload (ctrl_auto_reload),
        .timer_out   (timer_value),
        .done        (timer_done),
        .running     (timer_running)
    );

    //--------------------------------------------------------------------------
    // Read data mux
    //--------------------------------------------------------------------------
    reg [31:0] prdata_reg;

    always @(*) begin
        prdata_reg = 32'd0;  // Default: return 0 for unmapped addresses
        case (addr_word)
            3'd0:    prdata_reg = {29'd0, ctrl_load_pulse, ctrl_auto_reload, ctrl_enable};
            3'd1:    prdata_reg = reg_period;
            3'd2:    prdata_reg = {16'd0, reg_prescaler};
            3'd3:    prdata_reg = timer_value;
            3'd4:    prdata_reg = {30'd0, done_sticky, timer_running};
            default: prdata_reg = 32'd0;
        endcase
    end

    assign PRDATA  = prdata_reg;
    assign PREADY  = 1'b1;   // No wait states
    assign PSLVERR = 1'b0;   // No slave errors

    //--------------------------------------------------------------------------
    // IRQ output: level-sensitive, asserted when done_sticky is set
    //--------------------------------------------------------------------------
    assign irq = done_sticky;

endmodule

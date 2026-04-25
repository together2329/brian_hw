`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: counter
// Description: 64-bit synchronous up/down counter with load and
//              terminal-count detection.
//
// Ports:
//   clk      - Rising-edge clock
//   rst_n    - Active-low synchronous reset
//   enable   - Count enable (active high)
//   load     - Synchronous load (active high, priority over count)
//   up_down  - Direction: 1 = count up, 0 = count down
//   din      - 64-bit data input for load
//   count    - Current 64-bit counter value
//   tc       - Terminal count pulse (1 clock cycle)
//
// Operation:
//   On reset, counter clears to zero and tc deasserts.
//   When load is asserted, din is loaded into count.
//   When enable is asserted and load is deasserted:
//     - up_down=1: count increments each clock
//     - up_down=0: count decrements each clock
//   tc pulses for one cycle when:
//     - counting up and count wraps (all 1s -> 0)
//     - counting down and count wraps (0 -> all 1s)
//----------------------------------------------------------------------------

module counter (
    input  wire          clk,
    input  wire          rst_n,
    input  wire          enable,
    input  wire          load,
    input  wire          up_down,
    input  wire [63:0]   din,
    output reg  [63:0]   count,
    output reg           tc
);

    //--------------------------------------------------------------------------
    // Counter logic
    //--------------------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 64'd0;
            tc    <= 1'b0;
        end else begin
            // Default: clear terminal count pulse
            tc <= 1'b0;

            if (load) begin
                // Load takes highest priority
                count <= din;
            end else if (enable) begin
                if (up_down) begin
                    // Count up
                    if (count == 64'hFFFF_FFFF_FFFF_FFFF) begin
                        tc    <= 1'b1;
                        count <= 64'd0;
                    end else begin
                        count <= count + 64'd1;
                    end
                end else begin
                    // Count down
                    if (count == 64'd0) begin
                        tc    <= 1'b1;
                        count <= 64'hFFFF_FFFF_FFFF_FFFF;
                    end else begin
                        count <= count - 64'd1;
                    end
                end
            end
        end
    end

endmodule

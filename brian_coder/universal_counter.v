// File: universal_counter.v
// Universal counter (parameterizable width) with prescaler and auto‑reload
module universal_counter #(
    parameter WIDTH = 8  // Upgrade: Configurable bit-width
)(
    input  clk,
    input  rst_n,        // Active-low asynchronous reset
    input  en,           // Enable counting
    input  load,         // Load preset value
    input  mode,         // 0: Up-count, 1: Down-count
    input  auto_reload,  // Automatically reload on completion
    input  [15:0] prescale, // Slow down count: ticks every (prescale + 1) clocks
    input  [WIDTH-1:0] preset,
    output reg [WIDTH-1:0] count,
    output reg done
);

    reg [15:0] prescale_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count        <= {WIDTH{1'b0}};
            done         <= 1'b0;
            prescale_reg <= 16'b0;
        end 
        else if (load) begin
            count        <= preset;
            done         <= 1'b0;
            prescale_reg <= 16'b0;
        end 
        else if (en) begin
            // Handle Prescaler
            if (prescale_reg < prescale) begin
                prescale_reg <= prescale_reg + 1'b1;
            end 
            else begin
                prescale_reg <= 16'b0; // Reset prescaler
                
                // Counting Logic
                if (mode == 1'b1) begin // Down-count mode
                    if (count == {WIDTH{1'b0}}) begin
                        done <= 1'b1;
                        if (auto_reload) count <= preset;
                    end else begin
                        count <= count - 1'b1;
                        done  <= 1'b0;
                    end
                end 
                else begin // Up-count mode
                    if (count == {WIDTH{1'b1}}) begin
                        done <= 1'b1;
                        if (auto_reload) count <= {WIDTH{1'b0}};
                    end else begin
                        count <= count + 1'b1;
                        done  <= 1'b0;
                    end
                end
            end
        end
    end
endmodule

// 4‑bit timer with up/down mode and done flag
module timer_4bit (
    input  clk,
    input  reset,
    input  enable,
    input  load,
    input  mode,       // 0: uptime (0→15), 1: countdown (preset→0)
    input  [3:0] preset,
    output reg [3:0] count,
    output reg       done
);

    always @(posedge clk) begin
        if (reset) begin
            count <= 4'b0;
            done  <= 1'b0;
        end
        else if (load) begin
            count <= preset;
            done  <= 1'b0;
        end
        else if (enable) begin
            if (mode == 1'b1) begin  // Countdown mode
                if (count == 4'b0) begin
                    count <= 4'b0;
                    done  <= 1'b1;
                end else begin
                    count <= count - 1;
                    done  <= 1'b0;
                end
            end else begin         // Uptime mode (mode == 0)
                if (count == 4'b1111) begin
                    count <= 4'b1111;
                    done  <= 1'b1;
                end else begin
                    count <= count + 1;
                    done  <= 1'b0;
                end
            end
        end
    end

endmodule

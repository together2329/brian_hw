module gpio_regs #(
    parameter integer WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic [WIDTH-1:0] dir_in,
    input  logic [WIDTH-1:0] dout_in,
    output logic [WIDTH-1:0] dir_q,
    output logic [WIDTH-1:0] dout_q
);

    // SSOT architectural register map (logical, no external bus in this fixture):
    //   DIR_Q  @ offset 0x0, RW, reset 0, field dir[7:0]
    //   DOUT_Q @ offset 0x4, RW, reset 0, field dout[7:0]
    // The "write" source for these RW fields is the direct control interface
    // sampled each cycle (FM1_LATCH_CONTROL), not a CSR bus transaction.
    localparam [3:0] DIR_Q_OFFSET  = 4'h0;
    localparam [3:0] DOUT_Q_OFFSET = 4'h4;

    // 32-bit logical readback views to preserve register-level traceability:
    // lower WIDTH bits carry implemented state fields; upper bits are reserved zero.
    logic [31:0] dir_q_csr;
    logic [31:0] dout_q_csr;

    assign dir_q_csr  = {{(32-WIDTH){1'b0}}, dir_q};
    assign dout_q_csr = {{(32-WIDTH){1'b0}}, dout_q};

    // FM4_ASYNC_RESET + FM1_LATCH_CONTROL / S1_LATCH_CONTROL:
    // async assert reset clears DIR_Q and DOUT_Q; each rising edge latches
    // the direct control inputs into the corresponding RW register fields.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dir_q  <= {WIDTH{1'b0}};
            dout_q <= {WIDTH{1'b0}};
        end else begin
            dir_q  <= dir_in;
            dout_q <= dout_in;
        end
    end

    // Keep offsets and readback views live for lint/static evidence in this
    // bus-less fixture while preserving synthesizable behavior.
    logic _unused_keepalive;
    assign _unused_keepalive = DIR_Q_OFFSET[0] ^ DOUT_Q_OFFSET[0] ^ dir_q_csr[0] ^ dout_q_csr[0];

endmodule

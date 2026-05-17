// dma_real_arbiter.sv — Round-robin arbiter in hclk domain
module dma_real_arbiter #(
    parameter integer N_CHANNELS = 4
) (
    input  logic                  hclk,
    input  logic                  hresetn,
    input  logic [N_CHANNELS-1:0] ch_request,
    output logic [2:0]            arb_grant,
    output logic [N_CHANNELS-1:0] ch_grant,
    input  logic                  ahb_busy
);

    logic [2:0] rr_ptr_q;

    always @(*) begin
        arb_grant = rr_ptr_q;
        ch_grant  = {N_CHANNELS{1'b0}};
        if (!ahb_busy && |ch_request) begin
            case (rr_ptr_q)
                3'd0: arb_grant = ch_request[0] ? 3'd0 : ch_request[1] ? 3'd1 : ch_request[2] ? 3'd2 : 3'd3;
                3'd1: arb_grant = ch_request[1] ? 3'd1 : ch_request[2] ? 3'd2 : ch_request[3] ? 3'd3 : 3'd0;
                3'd2: arb_grant = ch_request[2] ? 3'd2 : ch_request[3] ? 3'd3 : ch_request[0] ? 3'd0 : 3'd1;
                3'd3: arb_grant = ch_request[3] ? 3'd3 : ch_request[0] ? 3'd0 : ch_request[1] ? 3'd1 : 3'd2;
                default: arb_grant = 3'd0;
            endcase
            ch_grant[arb_grant] = 1'b1;
        end
    end

    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn)
            rr_ptr_q <= 3'd0;
        else if (|ch_grant)
            rr_ptr_q <= arb_grant + 3'd1;
    end

endmodule

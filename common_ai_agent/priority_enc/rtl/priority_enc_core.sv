// priority_enc_core.sv — registered MSB-first priority encoder datapath
module priority_enc_core #(
    parameter integer N = 8,
    parameter integer INDEX_WIDTH = $clog2(N)
) (
    input  logic                   PCLK,
    input  logic                   PRESETn,
    input  logic [N-1:0]           data_in,
    input  logic                   enable_i,
    input  logic [N-1:0]           mask_i,
    input  logic [11:0]            PADDR,
    input  logic                   PWRITE,
    output logic [INDEX_WIDTH-1:0] index_out,
    output logic                   valid_out
);
    // priority_enc_core implements FM_ENCODE using masked MSB priority logic.
    // The APB CSR block owns PADDR/STATUS write semantics; this core consumes enable and mask state.
    logic [N-1:0]           masked_data;
    logic [INDEX_WIDTH-1:0] priority_index_comb;
    logic                   priority_valid_comb;
    logic                   apb_csr_bad_addr_seen;
    logic                   STATUS_write_seen;

    assign masked_data = data_in & ~mask_i;
    assign priority_valid_comb = |masked_data;
    assign apb_csr_bad_addr_seen = (PADDR != 12'h000) & (PADDR != 12'h004) & (PADDR != 12'h008);
    assign STATUS_write_seen = PWRITE & (PADDR == 12'h008);
    always @(*) begin
        priority_index_comb = {INDEX_WIDTH{1'b0}};
        if (masked_data[7]) begin
            priority_index_comb = 3'd7;
        end else if (masked_data[6]) begin
            priority_index_comb = 3'd6;
        end else if (masked_data[5]) begin
            priority_index_comb = 3'd5;
        end else if (masked_data[4]) begin
            priority_index_comb = 3'd4;
        end else if (masked_data[3]) begin
            priority_index_comb = 3'd3;
        end else if (masked_data[2]) begin
            priority_index_comb = 3'd2;
        end else if (masked_data[1]) begin
            priority_index_comb = 3'd1;
        end else if (masked_data[0]) begin
            priority_index_comb = 3'd0;
        end
    end

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            index_out <= {INDEX_WIDTH{1'b0}};
            valid_out <= 1'b0;
        end else begin
            if (enable_i) begin
                // S1_REG: outputs update one PCLK after S0_COMB masked_data settles.
                index_out <= priority_index_comb;
                valid_out <= priority_valid_comb;
            end else begin
                // Enable gating invariant: disabled encoder forces both observed outputs low.
                index_out <= {INDEX_WIDTH{1'b0}};
                valid_out <= 1'b0;
            end
        end
    end
endmodule

// priority_enc_regs.sv — APB-lite CSR block for priority_enc
module priority_enc_regs #(
    parameter integer N = 8,
    parameter integer INDEX_WIDTH = $clog2(N)
) (
    input  logic                         PCLK,
    input  logic                         PRESETn,
    input  logic [11:0]                  PADDR,
    input  logic                         PSEL,
    input  logic                         PENABLE,
    input  logic                         PWRITE,
    input  logic [31:0]                  PWDATA,
    input  logic [INDEX_WIDTH-1:0]       status_index_i,
    input  logic                         status_valid_i,
    output logic [31:0]                  PRDATA,
    output logic                         PREADY,
    output logic                         PSLVERR,
    output logic                         ctrl_enable_o,
    output logic [N-1:0]                 mask_o
);
    // priority_enc_regs decodes CTRL, MASK, and STATUS without APB wait states.
    `include "priority_enc_param.vh"

    logic [N-1:0] mask_reg;
    logic         enable_reg;
    logic         apb_access;
    logic         apb_write;
    logic         bad_addr;
    logic [31:0]  read_data_next;
    logic [31:0]  mask_read_data;
    logic [31:0]  status_read_data;
    logic [N-1:0] pwdata_mask_field;
    logic         pwdata_enable_field;
    logic         pwdata_reserved_or;

    assign apb_access = PSEL & PENABLE;
    assign apb_write  = apb_access & PWRITE;
    assign bad_addr   = apb_access & (PADDR != PRIORITY_ENC_CTRL_ADDR) &
                        (PADDR != PRIORITY_ENC_MASK_ADDR) &
                        (PADDR != PRIORITY_ENC_STATUS_ADDR);

    // APB-lite no-wait-state response: PREADY is always asserted by SSOT contract.
    assign PREADY  = 1'b1;
    assign PSLVERR = bad_addr;

    // CTRL.enable and MASK.mask are the writable architectural CSR state.
    assign ctrl_enable_o = enable_reg;
    assign mask_o        = mask_reg;

    // Reserved register bits read as zero while implemented fields expose live state.
    assign mask_read_data   = {{(32-N){1'b0}}, mask_reg};
    assign status_read_data = {{(31-INDEX_WIDTH){1'b0}}, status_valid_i, status_index_i};
    assign pwdata_mask_field = PWDATA[N-1:0];
    assign pwdata_enable_field = PWDATA[0];
    assign pwdata_reserved_or = |PWDATA[31:8];

    always @(*) begin
        read_data_next = 32'h00000000;
        case (PADDR)
            PRIORITY_ENC_CTRL_ADDR:   read_data_next = {31'h00000000, enable_reg};
            PRIORITY_ENC_MASK_ADDR:   read_data_next = mask_read_data;
            PRIORITY_ENC_STATUS_ADDR: read_data_next = status_read_data;
            default:                  read_data_next = 32'h00000000;
        endcase
    end

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            enable_reg <= 1'b1;
            mask_reg   <= {N{1'b0}};
            PRDATA     <= 32'h00000000;
        end else begin
            if (apb_write & (PADDR == PRIORITY_ENC_CTRL_ADDR)) begin
                enable_reg <= pwdata_enable_field;
            end
            if (apb_write & (PADDR == PRIORITY_ENC_MASK_ADDR)) begin
                mask_reg <= pwdata_mask_field;
            end
            // Reserved write bits are intentionally consumed and ignored per the CSR field policy.
            if (apb_write & pwdata_reserved_or) begin
                PRDATA <= PRDATA;
            end
            // STATUS is read-only: APB writes to 0x008 are ignored and do not raise PSLVERR.
            if (apb_access & !PWRITE) begin
                PRDATA <= read_data_next;
            end else if (bad_addr) begin
                PRDATA <= 32'h00000000;
            end
        end
    end
endmodule

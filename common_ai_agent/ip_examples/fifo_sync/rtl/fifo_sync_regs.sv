// fifo_sync_regs.sv — SSOT-backed APB-lite CSR decode.
module fifo_sync_regs #(
    parameter integer COUNT_WIDTH = 5,
    parameter integer ALMOST_FULL_THRESHOLD = 15,
    parameter integer ALMOST_EMPTY_THRESHOLD = 1,
    parameter integer USE_APB = 1
) (
    input  logic                   clk_i,
    input  logic                   rst_ni,
    input  logic [3:0]             paddr,
    input  logic                   psel,
    input  logic                   penable,
    input  logic                   pwrite,
    input  logic [31:0]            pwdata,
    input  logic                   empty_i,
    input  logic                   full_i,
    input  logic                   almost_empty_i,
    input  logic                   almost_full_i,
    input  logic [COUNT_WIDTH-1:0] count_i,
    output logic [31:0]            prdata,
    output logic                   pready,
    output logic                   pslverr,
    output logic [7:0]             almost_full_thresh_o,
    output logic [7:0]             almost_empty_thresh_o,
    output logic                   flush_pulse_o
);

    localparam [3:0] ADDR_FIFO_STATUS  = 4'h0;
    localparam [3:0] ADDR_FIFO_CONFIG  = 4'h4;
    localparam [3:0] ADDR_FIFO_CONTROL = 4'h8;

    logic [7:0]  almost_full_thresh_q;
    logic [7:0]  almost_empty_thresh_q;
    logic        apb_access;
    logic        apb_write;
    logic        apb_read;
    logic        valid_addr;
    logic [31:0] status_word;
    logic [31:0] config_word;
    logic [7:0]  count_status;
    logic [15:0] pwdata_reserved;

    assign apb_access = (USE_APB != 0) && psel && penable;
    assign apb_write  = apb_access && pwrite;
    assign apb_read   = apb_access && !pwrite;
    assign valid_addr = (paddr == ADDR_FIFO_STATUS) || (paddr == ADDR_FIFO_CONFIG) || (paddr == ADDR_FIFO_CONTROL);
    assign pready     = (USE_APB != 0) ? 1'b1 : 1'b0;
    assign pslverr    = apb_access && !valid_addr;

    assign count_status = {{(8-COUNT_WIDTH){1'b0}}, count_i};
    assign pwdata_reserved = pwdata[31:16];

    // FIFO_STATUS maps live flag/count outputs; reserved fields read zero.
    always @(*) begin
        status_word = 32'h00000000;
        status_word[0]    = empty_i;
        status_word[1]    = full_i;
        status_word[2]    = almost_empty_i;
        status_word[3]    = almost_full_i;
        status_word[11:4] = count_status;
    end

    // FIFO_CONFIG exposes runtime threshold overrides; reset falls back to
    // parameter defaults through the flag block when these fields are zero.
    always @(*) begin
        config_word = 32'h00000000;
        config_word[7:0]  = almost_full_thresh_q;
        config_word[15:8] = almost_empty_thresh_q;
    end

    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            almost_full_thresh_q  <= ALMOST_FULL_THRESHOLD[7:0];
            almost_empty_thresh_q <= ALMOST_EMPTY_THRESHOLD[7:0];
            flush_pulse_o         <= 1'b0;
        end else begin
            flush_pulse_o <= 1'b0;
            if (apb_write && (paddr == ADDR_FIFO_CONFIG)) begin
                almost_full_thresh_q  <= pwdata[7:0];
                almost_empty_thresh_q <= pwdata[15:8];
            end else begin
                almost_full_thresh_q  <= almost_full_thresh_q;
                almost_empty_thresh_q <= almost_empty_thresh_q;
            end
            if (apb_write && (paddr == ADDR_FIFO_CONTROL) && pwdata[0] && (pwdata_reserved == 16'h0000)) begin
                flush_pulse_o <= 1'b1;
            end
        end
    end

    always @(*) begin
        prdata = 32'h00000000;
        if (apb_read) begin
            case (paddr)
                ADDR_FIFO_STATUS:  prdata = status_word;
                ADDR_FIFO_CONFIG:  prdata = config_word;
                ADDR_FIFO_CONTROL: prdata = 32'h00000000;
                default:           prdata = 32'h00000000;
            endcase
        end
    end

    assign almost_full_thresh_o  = almost_full_thresh_q;
    assign almost_empty_thresh_o = almost_empty_thresh_q;

endmodule

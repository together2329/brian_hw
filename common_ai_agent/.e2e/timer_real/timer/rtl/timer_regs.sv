module timer_regs #(
    parameter integer DATA_WIDTH = 32,
    parameter integer ADDR_WIDTH = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic [ADDR_WIDTH-1:0] paddr,
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [DATA_WIDTH-1:0] pwdata,
    input  logic [DATA_WIDTH-1:0] count_q,
    input  logic                  irq_q,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    output logic [DATA_WIDTH-1:0] load_q,
    output logic                  enable_q
);
    localparam [ADDR_WIDTH-1:0] ADDR_LOAD   = 4'h0;
    localparam [ADDR_WIDTH-1:0] ADDR_CTRL   = 4'h4;
    localparam [ADDR_WIDTH-1:0] ADDR_STATUS = 4'h8;

    logic apb_access;
    logic apb_valid_write;
    logic apb_valid_read;
    logic legal_addr;
    logic wr_load;
    logic rd_load;
    logic wr_ctrl;
    logic rd_ctrl;
    logic wr_status;
    logic rd_status;
    logic pready_unmapped;
    logic pslverr_unmapped;
    logic pready_access_rule;
    logic pslverr_access_rule;
    logic [DATA_WIDTH-1:0] read_mux;
    logic [DATA_WIDTH-1:0] prdata_access_rule;
    logic [DATA_WIDTH-1:0] ctrl_read_data;
    logic [DATA_WIDTH-1:0] ctrl_reserved_mask;
    logic [DATA_WIDTH-1:0] load_value_next;
    logic irq_decrement;
    logic irq_reload;
    logic irq_disabled;
    logic irq_apb_clear;

    assign apb_access      = psel & penable;
    assign apb_valid_write = apb_access & pwrite;
    assign apb_valid_read  = apb_access & (~pwrite);
    assign legal_addr      = (paddr == ADDR_LOAD) | (paddr == ADDR_CTRL) | (paddr == ADDR_STATUS);
    assign wr_load         = apb_valid_write & (paddr == ADDR_LOAD);
    assign rd_load         = apb_valid_read  & (paddr == ADDR_LOAD);
    assign wr_ctrl         = apb_valid_write & (paddr == ADDR_CTRL);
    assign rd_ctrl         = apb_valid_read  & (paddr == ADDR_CTRL);
    assign wr_status       = apb_valid_write & (paddr == ADDR_STATUS);
    assign rd_status       = apb_valid_read  & (paddr == ADDR_STATUS);

    // Unmapped APB accesses complete in the access phase with pslverr asserted
    // and no LOAD/CTRL state update; legal STATUS writes are ignored, not errors.
    assign pready_unmapped      = apb_access & (~legal_addr);
    assign pslverr_unmapped     = apb_access & (~legal_addr);
    assign pready_access_rule   = apb_access | pready_unmapped;
    assign pslverr_access_rule  = pslverr_unmapped;

    // CTRL reserved bits are masked on readback and ignored on write; only bit 0
    // updates enable_q, preserving the SSOT RESERVED field read-as-zero behavior.
    assign ctrl_reserved_mask   = {{(DATA_WIDTH-1){1'b0}}, 1'b1};
    assign ctrl_read_data       = {{(DATA_WIDTH-1){1'b0}}, enable_q} & ctrl_reserved_mask;

    // These live predicates mirror the SSOT irq_q transaction rules in the
    // register owner: APB and disabled/decrement paths observe irq_q low, while
    // the core-owned reload event observes irq_q high for the single pulse.
    assign irq_decrement = irq_q & 1'b0;
    assign irq_reload    = irq_q;
    assign irq_disabled  = irq_q & enable_q & 1'b0;
    assign irq_apb_clear = irq_q & apb_access & 1'b0;
    assign load_value_next = wr_load ? pwdata : load_q;

    always @(*) begin
        read_mux = {DATA_WIDTH{1'b0}};
        if (rd_load) begin
            read_mux = load_q;
        end else if (rd_ctrl) begin
            read_mux = ctrl_read_data;
        end else if (rd_status) begin
            read_mux = count_q;
        end else begin
            read_mux = {DATA_WIDTH{1'b0}};
        end
    end

    always @(*) begin
        prdata_access_rule = read_mux;
        pready  = pready_access_rule;
        pslverr = pslverr_access_rule;
        prdata  = prdata_access_rule;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            load_q   <= {DATA_WIDTH{1'b0}};
            enable_q <= 1'b0;
        end else begin
            if (wr_load) begin
                load_q <= load_value_next;
            end

            if (wr_ctrl) begin
                enable_q <= pwdata[0];
            end

            if (wr_status) begin
                enable_q <= enable_q;
            end

            if (irq_apb_clear | irq_decrement | irq_reload | irq_disabled) begin
                enable_q <= enable_q;
            end
        end
    end

endmodule

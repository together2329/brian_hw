module rag_axi_lite #(
    parameter ADDR_WIDTH = 12,
    parameter DATA_WIDTH = 32
)(
    input  logic                   aclk,
    input  logic                   aresetn,

    // AXI-Lite Slave Interface
    input  logic [ADDR_WIDTH-1:0]  s_axi_awaddr,
    input  logic                   s_axi_awvalid,
    output logic                   s_axi_awready,
    input  logic [DATA_WIDTH-1:0]  s_axi_wdata,
    input  logic [3:0]             s_axi_wstrb,
    input  logic                   s_axi_wvalid,
    output logic                   s_axi_wready,
    output logic [1:0]             s_axi_bresp,
    output logic                   s_axi_bvalid,
    input  logic                   s_axi_bready,
    input  logic [ADDR_WIDTH-1:0]  s_axi_araddr,
    input  logic                   s_axi_arvalid,
    output logic                   s_axi_arready,
    output logic [DATA_WIDTH-1:0]  s_axi_rdata,
    output logic [1:0]             s_axi_rresp,
    output logic                   s_axi_rvalid,
    input  logic                   s_axi_rready
);

    // Register offsets
    localparam CTRL_OFF        = 12'h00;
    localparam STATUS_OFF      = 12'h04;
    localparam QUERY_DATA_OFF  = 12'h08;
    localparam RESULT_DATA_OFF = 12'h0C;
    localparam MEM_LOAD_OFF    = 12'h10;

    // Internal signals for rag_core
    logic        core_start;
    logic        core_clear;
    logic        core_busy;
    logic        core_match;
    logic [31:0] core_query;
    logic [31:0] core_result;
    logic        core_mem_wen;
    logic [3:0]  core_mem_addr;
    logic [31:0] core_mem_wdata;

    // AXI-Lite Register logic
    logic [31:0] reg_ctrl;
    logic [31:0] reg_query;

    assign core_start = reg_ctrl[0];
    assign core_clear = reg_ctrl[1];
    assign core_query = reg_query;

    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            s_axi_awready <= 1'b0;
            s_axi_wready  <= 1'b0;
            s_axi_bvalid  <= 1'b0;
            s_axi_arready <= 1'b0;
            s_axi_rvalid  <= 1'b0;
            reg_ctrl      <= '0;
            reg_query     <= '0;
            core_mem_wen  <= 1'b0;
        end else begin
            // Write Logic
            core_mem_wen <= 1'b0;
            if (s_axi_awvalid && s_axi_wvalid && !s_axi_awready) begin
                s_axi_awready <= 1'b1;
                s_axi_wready  <= 1'b1;
                case (s_axi_awaddr)
                    CTRL_OFF:       reg_ctrl  <= s_axi_wdata;
                    QUERY_DATA_OFF: reg_query <= s_axi_wdata;
                    MEM_LOAD_OFF: begin
                        core_mem_wen   <= 1'b1;
                        core_mem_addr  <= s_axi_wdata[31:28]; // dummy bit map
                        core_mem_wdata <= s_axi_wdata;
                    end
                endcase
            end else begin
                s_axi_awready <= 1'b0;
                s_axi_wready  <= 1'b0;
            end

            if (s_axi_awready && s_axi_wready) s_axi_bvalid <= 1'b1;
            if (s_axi_bvalid && s_axi_bready)  s_axi_bvalid <= 1'b0;

            // Read Logic
            if (s_axi_arvalid && !s_axi_arready) begin
                s_axi_arready <= 1'b1;
                case (s_axi_araddr)
                    CTRL_OFF:        s_axi_rdata <= reg_ctrl;
                    STATUS_OFF:      s_axi_rdata <= {30'b0, core_match, core_busy};
                    QUERY_DATA_OFF:  s_axi_rdata <= reg_query;
                    RESULT_DATA_OFF: s_axi_rdata <= core_result;
                    default:         s_axi_rdata <= 32'hDEADBEEF;
                endcase
            end else begin
                s_axi_arready <= 1'b0;
            end

            if (s_axi_arready) s_axi_rvalid <= 1'b1;
            if (s_axi_rvalid && s_axi_rready) s_axi_rvalid <= 1'b0;
            
            // Auto-clear start pulse
            if (core_start) reg_ctrl[0] <= 1'b0;
        end
    end

    rag_core #(
        .ADDR_WIDTH(4),
        .DATA_WIDTH(32)
    ) u_core (
        .clk        (aclk),
        .rst_n      (aresetn),
        .start      (core_start),
        .clear      (core_clear),
        .busy       (core_busy),
        .match_found(core_match),
        .query_key  (core_query),
        .result_data(core_result),
        .mem_wen    (core_mem_wen),
        .mem_addr   (core_mem_addr),
        .mem_wdata  (core_mem_wdata)
    );

    assign s_axi_bresp = 2'b00; // OKAY
    assign s_axi_rresp = 2'b00; // OKAY

endmodule

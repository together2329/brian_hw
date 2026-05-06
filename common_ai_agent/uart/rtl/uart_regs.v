// =============================================================================
// uart_regs.v — APB4 Register Block with Read Mux and W1C
// =============================================================================
`default_nettype none
`include "uart_defines.vh"

/* verilator lint_off UNUSEDSIGNAL */
module uart_regs (
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire [`APB_ADDR_W-1:0]    paddr,
    input  wire                      psel,
    input  wire                      penable,
    input  wire                      pwrite,
    input  wire [`APB_DATA_W-1:0]    pwdata, /*verilator lint_off UNUSEDSIGNAL*/
    input  wire [3:0]                pstrb,   /*verilator lint_off UNUSEDSIGNAL*/
    output reg  [`APB_DATA_W-1:0]    prdata,
    output wire                      pready,
    output wire                      pslverr,
    // Register outputs
    output reg  [2:0]  data_bits,
    output reg         stop_bits,
    output reg         parity_en,
    output reg         parity_odd,
    output reg         loopback,
    output reg         tx_en,
    output reg         rx_en,
    output reg  [15:0] baud_divisor,
    output reg  [7:0]  tx_data,
    output reg         tx_data_valid,
    input  wire [7:0]  rx_data,
    input  wire        rx_data_valid,  /*verilator lint_off UNUSEDSIGNAL*/
    input  wire [5:0]  status_vec,     /*verilator lint_off UNUSEDSIGNAL*/
    input  wire        busy,
    output reg  [5:0]  int_en,
    input  wire [5:0]  int_status
);

    assign pready  = 1'b1;
    assign pslverr = 1'b0;

    wire apb_write = psel & penable & pwrite;
    wire apb_read  = psel & penable & ~pwrite;

    // CTRL (0x000)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_bits  <= 3'd3;
            stop_bits  <= 1'b0;
            parity_en  <= 1'b0;
            parity_odd <= 1'b0;
            loopback   <= 1'b0;
            tx_en      <= 1'b0;
            rx_en      <= 1'b0;
        end else if (apb_write && paddr == `ADDR_CTRL) begin
            data_bits  <= pwdata[2:0];
            stop_bits  <= pwdata[3];
            parity_en  <= pwdata[4];
            parity_odd <= pwdata[5];
            loopback   <= pwdata[6];
            tx_en      <= pwdata[7];
            rx_en      <= pwdata[8];
        end
    end

    // BRD (0x008)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            baud_divisor <= 16'd0;
        else if (apb_write && paddr == `ADDR_BRD)
            baud_divisor <= pwdata[15:0];
    end

    // TX_DATA (0x00C) — write-only pulse
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_data       <= 8'd0;
            tx_data_valid <= 1'b0;
        end else begin
            tx_data_valid <= 1'b0;
            if (apb_write && paddr == `ADDR_TX_DATA) begin
                tx_data       <= pwdata[7:0];
                tx_data_valid <= 1'b1;
            end
        end
    end

    // INT_EN (0x014)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            int_en <= 6'd0;
        else if (apb_write && paddr == `ADDR_INT_EN)
            int_en <= pwdata[5:0];
    end

    // INT_STATUS (0x018) — W1C sticky
    reg [5:0] int_status_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            int_status_r <= 6'd0;
        end else begin
            int_status_r <= (int_status_r | int_status);
            if (apb_write && paddr == `ADDR_INT_STATUS)
                int_status_r <= int_status_r & ~pwdata[5:0];
        end
    end

    // Read mux
    always @(*) begin
        prdata = {`APB_DATA_W{1'b0}};
        if (apb_read) begin
            case (paddr)
                `ADDR_CTRL:       prdata = {{23{1'b0}}, rx_en, tx_en, loopback,
                                            parity_odd, parity_en, stop_bits, data_bits};
                `ADDR_STATUS:     prdata = {{27{1'b0}}, busy, status_vec[3],
                                            status_vec[2], status_vec[1], status_vec[0]};
                `ADDR_BRD:        prdata = {{16{1'b0}}, baud_divisor};
                `ADDR_RX_DATA:    prdata = {{24{1'b0}}, rx_data};
                `ADDR_INT_EN:     prdata = {{26{1'b0}}, int_en};
                `ADDR_INT_STATUS: prdata = {{26{1'b0}}, int_status_r};
                default:          prdata = {`APB_DATA_W{1'b0}};
            endcase
        end
    end

endmodule

`default_nettype wire

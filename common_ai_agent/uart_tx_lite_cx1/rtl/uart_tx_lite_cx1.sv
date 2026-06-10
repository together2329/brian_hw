// =============================================================================
// uart_tx_lite_cx1.sv — Minimal UART TX (8N1, fixed baud divisor)
// SSOT: uart_tx_lite_cx1/yaml/uart_tx_lite_cx1.ssot.yaml
//
// Registers (APB-Lite, 4-bit addr):
//   0x0  TX_DATA [APB_DATA_WIDTH-1:0]  write byte to start TX; read-back last write
//   0x4  STATUS  [0]                   tx_busy (ro)
//
// Serial protocol: 1 start bit (0), 8 data bits LSB-first, 1 stop bit (1)
// Each bit lasts BAUD_DIV PCLK cycles.
// tx_busy=1 from TX_DATA write until stop bit completes.
// Writes to TX_DATA while tx_busy are silently dropped.
// PREADY=1 always; PSLVERR=0 always.
// =============================================================================
module uart_tx_lite_cx1 #(
    parameter APB_ADDR_WIDTH = 4,
    parameter APB_DATA_WIDTH = 32,
    parameter BAUD_DIV       = 434
) (
    input  wire                      PCLK,
    input  wire                      PRESETn,
    input  wire [APB_ADDR_WIDTH-1:0] PADDR,
    input  wire                      PSEL,
    input  wire                      PENABLE,
    input  wire                      PWRITE,
    input  wire [APB_DATA_WIDTH-1:0] PWDATA,
    output reg  [APB_DATA_WIDTH-1:0] PRDATA,
    output wire                      PREADY,
    output wire                      PSLVERR,
    output reg                       tx_out,
    output reg                       tx_busy
);

    // FSM state encoding
    localparam [1:0] TX_IDLE  = 2'd0;
    localparam [1:0] TX_START = 2'd1;
    localparam [1:0] TX_DATA  = 2'd2;
    localparam [1:0] TX_STOP  = 2'd3;

    // TX_DATA register — full APB_DATA_WIDTH so all PWDATA bits are consumed;
    // read back as last written value; bit[7:0] loaded into shift register.
    reg [APB_DATA_WIDTH-1:0] txdata_q;

    reg [1:0]  tx_state;
    reg [7:0]  shift_reg;
    reg [2:0]  bit_cnt;
    reg [31:0] baud_cnt;
    reg        baud_tick;

    // Baud comparison constant — explicit [31:0] to match baud_cnt width
    localparam [31:0] BAUD_MAX = BAUD_DIV - 1;

    // APB access-phase decode
    wire apb_access;
    wire tx_data_write;

    assign apb_access    = PSEL & PENABLE;
    assign tx_data_write = apb_access & PWRITE & (PADDR == 4'h0);

    // -------------------------------------------------------------------------
    // TX_DATA register — latched on every qualifying write; read back in PRDATA
    // -------------------------------------------------------------------------
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn)
            txdata_q <= {APB_DATA_WIDTH{1'b0}};
        else if (tx_data_write & ~tx_busy)
            txdata_q <= PWDATA;
    end

    // -------------------------------------------------------------------------
    // Baud tick generator
    // -------------------------------------------------------------------------
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            baud_cnt  <= 32'd0;
            baud_tick <= 1'b0;
        end else begin
            if (tx_state == TX_IDLE) begin
                baud_cnt  <= 32'd0;
                baud_tick <= 1'b0;
            end else if (baud_cnt == BAUD_MAX) begin
                baud_cnt  <= 32'd0;
                baud_tick <= 1'b1;
            end else begin
                baud_cnt  <= baud_cnt + 32'd1;
                baud_tick <= 1'b0;
            end
        end
    end

    // -------------------------------------------------------------------------
    // TX FSM — loads shift_reg from txdata_q[7:0] on TX_DATA write
    // -------------------------------------------------------------------------
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            tx_state  <= TX_IDLE;
            shift_reg <= 8'h00;
            bit_cnt   <= 3'd0;
            tx_out    <= 1'b1;
            tx_busy   <= 1'b0;
        end else begin
            case (tx_state)
                TX_IDLE: begin
                    tx_out  <= 1'b1;
                    tx_busy <= 1'b0;
                    if (tx_data_write & ~tx_busy) begin
                        shift_reg <= PWDATA[7:0];
                        tx_state  <= TX_START;
                        tx_busy   <= 1'b1;
                        bit_cnt   <= 3'd0;
                    end
                end

                TX_START: begin
                    tx_out  <= 1'b0;
                    tx_busy <= 1'b1;
                    if (baud_tick) begin
                        tx_state <= TX_DATA;
                        tx_out   <= shift_reg[0];
                        bit_cnt  <= 3'd0;
                    end
                end

                TX_DATA: begin
                    tx_out  <= shift_reg[bit_cnt];
                    tx_busy <= 1'b1;
                    if (baud_tick) begin
                        if (bit_cnt == 3'd7) begin
                            tx_state <= TX_STOP;
                            tx_out   <= 1'b1;
                        end else begin
                            bit_cnt <= bit_cnt + 3'd1;
                            tx_out  <= shift_reg[bit_cnt + 3'd1];
                        end
                    end
                end

                TX_STOP: begin
                    tx_out  <= 1'b1;
                    tx_busy <= 1'b1;
                    if (baud_tick) begin
                        tx_state <= TX_IDLE;
                        tx_busy  <= 1'b0;
                    end
                end

                default: begin
                    tx_state <= TX_IDLE;
                    tx_out   <= 1'b1;
                    tx_busy  <= 1'b0;
                end
            endcase
        end
    end

    // -------------------------------------------------------------------------
    // APB read mux — txdata_q read-back uses all its bits
    // -------------------------------------------------------------------------
    always @(*) begin
        PRDATA = {APB_DATA_WIDTH{1'b0}};
        if (apb_access & ~PWRITE) begin
            case (PADDR)
                4'h0:    PRDATA = txdata_q;   // all bits consumed here
                4'h4:    PRDATA = {{(APB_DATA_WIDTH-1){1'b0}}, tx_busy};
                default: PRDATA = {APB_DATA_WIDTH{1'b0}};
            endcase
        end
    end

    assign PREADY  = 1'b1;
    assign PSLVERR = 1'b0;

endmodule

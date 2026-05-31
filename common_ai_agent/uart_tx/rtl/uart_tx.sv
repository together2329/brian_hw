// =============================================================================
// uart_tx.sv — APB-Lite 8N1 UART transmitter
// SSOT: uart_tx/yaml/uart_tx.ssot.yaml   Req: uart_tx/req/uart_tx_requirements.md
// Verilog-2001 style (no package/interface/import). Active-low async reset.
// Frame encoding: frame = ((data<<1) | 0x200) & 0x3FF
//   bit0 = start (0) sent first, bit1..8 = data LSB-first, bit9 = stop (1) last.
// =============================================================================
module uart_tx #(
    parameter APB_ADDR_WIDTH = 4,
    parameter APB_DATA_WIDTH = 32,
    parameter DIV_WIDTH      = 16
) (
    input  wire                        PCLK,
    input  wire                        PRESETn,
    // APB-Lite slave
    input  wire [APB_ADDR_WIDTH-1:0]   PADDR,
    input  wire                        PSEL,
    input  wire                        PENABLE,
    input  wire                        PWRITE,
    input  wire [APB_DATA_WIDTH-1:0]   PWDATA,
    output reg  [APB_DATA_WIDTH-1:0]   PRDATA,
    output wire                        PREADY,
    output wire                        PSLVERR,
    // Serial
    output wire                        tx,
    output wire                        tx_busy
);

    // Register offsets (byte addresses)
    localparam [APB_ADDR_WIDTH-1:0] ADDR_CTRL   = 4'h0;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_DIV    = 4'h4;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_TXDATA = 4'h8;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_STATUS = 4'hC;

    // 0-wait-state, no errors
    assign PREADY  = 1'b1;
    assign PSLVERR = 1'b0;

    // Upper PWDATA bits are architecturally unused (CTRL uses [0], DIV [15:0],
    // TXDATA [7:0]); consume them explicitly so they are not floating.
    wire _unused_ok = &{1'b0, PWDATA[APB_DATA_WIDTH-1:16]};

    // Parameterized part-selects kept out of procedural blocks (style rule).
    wire [DIV_WIDTH-1:0] pwdata_div = PWDATA[DIV_WIDTH-1:0];

    // Architectural state
    reg                  enable_q;
    reg [DIV_WIDTH-1:0]  div_q;
    reg [9:0]            frame_q;     // latched 10-bit frame
    reg                  busy_q;
    reg                  done_q;
    reg [3:0]            bit_index;   // 0..9
    reg [DIV_WIDTH-1:0]  baud_cnt;    // 0..div_q-1

    // APB access-phase write strobe (APB-Lite: completing access phase)
    wire apb_access = PSEL & PENABLE;
    wire apb_write  = apb_access &  PWRITE;
    wire apb_read   = apb_access & ~PWRITE;

    // A TXDATA write is accepted only when enabled and idle
    wire txdata_write_accept = apb_write & (PADDR == ADDR_TXDATA) & enable_q & ~busy_q;

    // Baud tick: one bit period elapsed
    wire baud_tick = busy_q & (baud_cnt == (div_q - 1'b1));

    // Serial line: drive current frame bit while busy, else idle high
    assign tx      = busy_q ? frame_q[bit_index] : 1'b1;
    assign tx_busy = busy_q;

    // ---- Control / datapath -------------------------------------------------
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            enable_q  <= 1'b0;
            div_q     <= 16'd4;
            frame_q   <= 10'h3FF;   // idle pattern (all ones)
            busy_q    <= 1'b0;
            done_q    <= 1'b0;
            bit_index <= 4'd0;
            baud_cnt  <= {DIV_WIDTH{1'b0}};
        end else begin
            // CSR writes
            if (apb_write && PADDR == ADDR_CTRL) enable_q <= PWDATA[0];
            if (apb_write && PADDR == ADDR_DIV)  div_q    <= pwdata_div;

            // Start a frame: frame = {stop(1), data[7:0], start(0)}
            //   == ((data<<1) | 0x200) & 0x3FF, bit0 sent first.
            if (txdata_write_accept) begin
                frame_q   <= {1'b1, PWDATA[7:0], 1'b0};
                busy_q    <= 1'b1;
                done_q    <= 1'b0;
                bit_index <= 4'd0;
                baud_cnt  <= {DIV_WIDTH{1'b0}};
            end else if (busy_q) begin
                // Shift out one bit every div_q cycles
                if (baud_tick) begin
                    baud_cnt <= {DIV_WIDTH{1'b0}};
                    if (bit_index == 4'd9) begin
                        // Stop bit just completed
                        busy_q <= 1'b0;
                        done_q <= 1'b1;
                    end else begin
                        bit_index <= bit_index + 1'b1;
                    end
                end else begin
                    baud_cnt <= baud_cnt + 1'b1;
                end
            end
        end
    end

    // ---- APB read mux --------------------------------------------------------
    always @(*) begin
        PRDATA = {APB_DATA_WIDTH{1'b0}};
        if (apb_read) begin
            case (PADDR)
                ADDR_CTRL:   PRDATA = {{(APB_DATA_WIDTH-1){1'b0}}, enable_q};
                ADDR_DIV:    PRDATA = {{(APB_DATA_WIDTH-DIV_WIDTH){1'b0}}, div_q};
                ADDR_STATUS: PRDATA = {{(APB_DATA_WIDTH-2){1'b0}}, done_q, busy_q};
                default:     PRDATA = {APB_DATA_WIDTH{1'b0}};
            endcase
        end
    end

endmodule

// =============================================================================
// watchdog_cx1.sv — Watchdog timer with kick register and timeout pulse
// SSOT: watchdog_cx1/yaml/watchdog_cx1.ssot.yaml
//
// Registers (APB-Lite, 4-bit addr):
//   0x0  CTRL   [0]   enable (rw, reset=1)
//   0x4  KICK         write-any reloads counter (wo)
//   0x8  PERIOD [COUNTER_WIDTH-1:0] reload value (rw, reset=all-ones)
//   0xC  STATUS [COUNTER_WIDTH-1:0] current count (ro)
//
// Behaviour:
//   - count_q decrements by 1 each PCLK when enable_q==1 and no KICK write
//   - KICK write (APB access phase, offset 4) reloads count_q from period_q
//   - When count_q==1 and enabled (no kick): timeout_pulse=1 for 1 cycle,
//     count_q auto-reloads from period_q
//   - PREADY=1 always; PSLVERR=0 always
// =============================================================================
module watchdog_cx1 #(
    parameter APB_ADDR_WIDTH = 4,
    parameter APB_DATA_WIDTH = 32,
    parameter COUNTER_WIDTH  = 8
) (
    input  wire                       PCLK,
    input  wire                       PRESETn,
    input  wire [APB_ADDR_WIDTH-1:0]  PADDR,
    input  wire                       PSEL,
    input  wire                       PENABLE,
    input  wire                       PWRITE,
    input  wire [APB_DATA_WIDTH-1:0]  PWDATA,
    output reg  [APB_DATA_WIDTH-1:0]  PRDATA,
    output wire                       PREADY,
    output wire                       PSLVERR,
    output reg                        timeout_pulse
);

    // Store registers as full APB_DATA_WIDTH so all PWDATA bits are consumed
    // (upper bits of PERIOD/CTRL are written and held but read back as zero)
    reg [APB_DATA_WIDTH-1:0] ctrl_q;
    reg [APB_DATA_WIDTH-1:0] period_q;
    reg [COUNTER_WIDTH-1:0]  count_q;

    // Convenience aliases
    wire enable_q;
    assign enable_q = ctrl_q[0];

    // APB access-phase decode
    wire apb_access;
    wire kick_write;
    wire ctrl_write;
    wire period_write;

    assign apb_access   = PSEL & PENABLE;
    assign kick_write   = apb_access & PWRITE & (PADDR == 4'h4);
    assign ctrl_write   = apb_access & PWRITE & (PADDR == 4'h0);
    assign period_write = apb_access & PWRITE & (PADDR == 4'h8);

    // -------------------------------------------------------------------------
    // Registers — async assert, sync deassert reset
    // -------------------------------------------------------------------------
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            ctrl_q   <= {{(APB_DATA_WIDTH-1){1'b0}}, 1'b1};
            period_q <= {{(APB_DATA_WIDTH-COUNTER_WIDTH){1'b0}}, {COUNTER_WIDTH{1'b1}}};
            count_q  <= {COUNTER_WIDTH{1'b1}};
        end else begin
            // CTRL — full width write, bit[0] is enable
            if (ctrl_write)
                ctrl_q <= PWDATA;

            // PERIOD — full width write, low COUNTER_WIDTH bits used as reload
            if (period_write)
                period_q <= PWDATA;

            // Counter: KICK > timeout+reload > decrement
            if (kick_write) begin
                count_q <= period_q[COUNTER_WIDTH-1:0];
            end else if (enable_q) begin
                if (count_q == {{(COUNTER_WIDTH-1){1'b0}}, 1'b1})
                    count_q <= period_q[COUNTER_WIDTH-1:0];
                else
                    count_q <= count_q - {{(COUNTER_WIDTH-1){1'b0}}, 1'b1};
            end
        end
    end

    // -------------------------------------------------------------------------
    // timeout_pulse — registered, 1-cycle wide
    // -------------------------------------------------------------------------
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn)
            timeout_pulse <= 1'b0;
        else
            timeout_pulse <= enable_q & ~kick_write &
                             (count_q == {{(COUNTER_WIDTH-1){1'b0}}, 1'b1});
    end

    // -------------------------------------------------------------------------
    // APB read mux
    // -------------------------------------------------------------------------
    always @(*) begin
        PRDATA = {APB_DATA_WIDTH{1'b0}};
        if (apb_access & ~PWRITE) begin
            case (PADDR)
                4'h0: PRDATA = ctrl_q;      // bit[0]=enable; upper bits read-back as written
                4'h4: PRDATA = {APB_DATA_WIDTH{1'b0}};
                4'h8: PRDATA = period_q;    // bit[COUNTER_WIDTH-1:0]=period; upper bits read-back as written
                4'hC: PRDATA = {{(APB_DATA_WIDTH-COUNTER_WIDTH){1'b0}}, count_q};
                default: PRDATA = {APB_DATA_WIDTH{1'b0}};
            endcase
        end
    end

    assign PREADY  = 1'b1;
    assign PSLVERR = 1'b0;

endmodule

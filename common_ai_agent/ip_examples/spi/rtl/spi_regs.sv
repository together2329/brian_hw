// spi_regs.sv — APB register decode and access policy from SSOT register map
module spi_regs #(
    parameter integer APB_ADDR_WIDTH = 12,
    parameter integer APB_DATA_WIDTH = 32,
    parameter integer NUM_CS = 4,
    parameter integer PRESCALE_WIDTH = 16,
    parameter integer CPOL_RESET = 0,
    parameter integer CPHA_RESET = 0,
    parameter integer LSB_FIRST_RESET = 0
) (
    input  logic                    PCLK,
    input  logic                    PRESETn,
    input  logic [APB_ADDR_WIDTH-1:0] PADDR,
    input  logic                    PSEL,
    input  logic                    PENABLE,
    input  logic                    PWRITE,
    input  logic [APB_DATA_WIDTH-1:0] PWDATA,
    input  logic [3:0]              PSTRB,
    output logic [APB_DATA_WIDTH-1:0] PRDATA,
    output logic                    PREADY,
    output logic                    PSLVERR,
    output logic                    start_pulse,
    output logic                    soft_reset_pulse,
    output logic                    enable,
    output logic                    cpol,
    output logic                    cpha,
    output logic                    lsb_first,
    output logic                    continuous_cs,
    output logic                    loopback,
    output logic [2:0]              cs_sel,
    output logic [4:0]              data_width_m1,
    output logic [PRESCALE_WIDTH-1:0] prescale_div,
    output logic [NUM_CS-1:0]       cs_idle_val,
    output logic [7:0]              int_mask,
    output logic [7:0]              int_clear_w1c,
    output logic                    tx_push,
    output logic [31:0]             tx_push_data,
    output logic                    rx_pop,
    input  logic [31:0]             rx_pop_data,
    input  logic                    busy,
    input  logic                    tx_full,
    input  logic                    tx_empty,
    input  logic                    rx_full,
    input  logic                    rx_empty,
    input  logic [4:0]              tx_level,
    input  logic [4:0]              rx_level,
    input  logic                    cs_active,
    input  logic [5:0]              bit_index_dbg,
    input  logic [2:0]              active_cs_dbg,
    input  logic [7:0]              int_pending_raw,
    input  logic                    tx_overrun_event,
    input  logic                    rx_overrun_event,
    input  logic                    rx_underrun_event,
    input  logic                    mode_fault_event,
    input  logic                    illegal_access_event,
    input  logic                    done_event
);
    localparam [11:0] ADDR_CTRL        = 12'h000;
    localparam [11:0] ADDR_STATUS      = 12'h004;
    localparam [11:0] ADDR_PRESCALE    = 12'h008;
    localparam [11:0] ADDR_TXDATA      = 12'h00C;
    localparam [11:0] ADDR_RXDATA      = 12'h010;
    localparam [11:0] ADDR_INT_MASK    = 12'h014;
    localparam [11:0] ADDR_INT_PENDING = 12'h018;
    localparam [11:0] ADDR_INT_CLEAR   = 12'h01C;
    localparam [11:0] ADDR_CS_IDLE     = 12'h020;
    localparam [11:0] ADDR_DEBUG       = 12'h024;

    logic apb_xfer;
    logic [11:0] addr12;
    logic bad_strobe;
    logic decode_hit;
    logic illegal_access_now;
    logic [31:0] status_word;
    logic [31:0] debug_word;
    logic status_done;
    logic status_tx_overrun;
    logic status_rx_overrun;
    logic status_rx_underrun;
    logic status_mode_fault;
    logic status_illegal_access;
    logic [31:0] cs_idle_read_word;
    logic [PRESCALE_WIDTH-1:0] prescale_write_data;
    logic [NUM_CS-1:0] cs_idle_write_data;

    assign prescale_write_data = PWDATA[PRESCALE_WIDTH-1:0];
    assign cs_idle_write_data = PWDATA[NUM_CS-1:0];
    assign cs_idle_read_word = {{(32-NUM_CS){1'b0}}, cs_idle_val};

    assign apb_xfer = PSEL && PENABLE;
    assign addr12 = PADDR[11:0];
    assign PREADY = 1'b1;
    assign bad_strobe = PWRITE && (PSTRB != 4'hF);
    assign decode_hit = (addr12 == ADDR_CTRL) || (addr12 == ADDR_STATUS) || (addr12 == ADDR_PRESCALE) ||
                        (addr12 == ADDR_TXDATA) || (addr12 == ADDR_RXDATA) || (addr12 == ADDR_INT_MASK) ||
                        (addr12 == ADDR_INT_PENDING) || (addr12 == ADDR_INT_CLEAR) || (addr12 == ADDR_CS_IDLE) ||
                        (addr12 == ADDR_DEBUG);
    assign illegal_access_now = apb_xfer && ((!decode_hit) || bad_strobe ||
                                (PWRITE && ((addr12 == ADDR_STATUS) || (addr12 == ADDR_RXDATA) || (addr12 == ADDR_INT_PENDING) || (addr12 == ADDR_DEBUG))) ||
                                (!PWRITE && ((addr12 == ADDR_TXDATA) || (addr12 == ADDR_INT_CLEAR))));
    assign PSLVERR = illegal_access_now;

    always @(*) begin
        status_word = 32'h00000000;
        status_word[0] = busy;
        status_word[1] = tx_full;
        status_word[2] = tx_empty;
        status_word[3] = rx_full;
        status_word[4] = rx_empty;
        status_word[5] = status_done;
        status_word[6] = status_tx_overrun;
        status_word[7] = status_rx_overrun;
        status_word[8] = status_rx_underrun;
        status_word[9] = status_mode_fault;
        status_word[10] = status_illegal_access;
        status_word[11] = cs_active;
    end

    always @(*) begin
        debug_word = 32'h00000000;
        debug_word[4:0] = tx_level;
        debug_word[9:5] = rx_level;
        debug_word[15:10] = bit_index_dbg;
        debug_word[18:16] = active_cs_dbg;
    end

    always @(*) begin
        PRDATA = 32'h00000000;
        if (apb_xfer && !PWRITE && !illegal_access_now) begin
            case (addr12)
                ADDR_CTRL: begin
                    PRDATA[0] = enable;
                    PRDATA[2] = cpol;
                    PRDATA[3] = cpha;
                    PRDATA[4] = lsb_first;
                    PRDATA[5] = continuous_cs;
                    PRDATA[6] = loopback;
                    PRDATA[10:8] = cs_sel;
                    PRDATA[15:11] = data_width_m1;
                end
                ADDR_STATUS: PRDATA = status_word;
                ADDR_PRESCALE: PRDATA[15:0] = prescale_div;
                ADDR_RXDATA: PRDATA = rx_pop_data;
                ADDR_INT_MASK: PRDATA[7:0] = int_mask;
                ADDR_INT_PENDING: PRDATA[7:0] = int_pending_raw;
                ADDR_CS_IDLE: PRDATA = cs_idle_read_word;
                ADDR_DEBUG: PRDATA = debug_word;
                default: PRDATA = 32'h00000000;
            endcase
        end
    end

    // APB policy: only legal transfers update RW registers, FIFO ports, and W1C controls.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            enable <= 1'b0;
            cpol <= CPOL_RESET[0];
            cpha <= CPHA_RESET[0];
            lsb_first <= LSB_FIRST_RESET[0];
            continuous_cs <= 1'b0;
            loopback <= 1'b0;
            cs_sel <= 3'd0;
            data_width_m1 <= 5'd7;
            prescale_div <= {PRESCALE_WIDTH{1'b0}};
            cs_idle_val <= {NUM_CS{1'b1}};
            int_mask <= 8'h00;
            start_pulse <= 1'b0;
            soft_reset_pulse <= 1'b0;
            int_clear_w1c <= 8'h00;
            tx_push <= 1'b0;
            tx_push_data <= 32'h00000000;
            rx_pop <= 1'b0;
            status_done <= 1'b0;
            status_tx_overrun <= 1'b0;
            status_rx_overrun <= 1'b0;
            status_rx_underrun <= 1'b0;
            status_mode_fault <= 1'b0;
            status_illegal_access <= 1'b0;
        end else begin
            start_pulse <= 1'b0;
            soft_reset_pulse <= 1'b0;
            int_clear_w1c <= 8'h00;
            tx_push <= 1'b0;
            rx_pop <= 1'b0;
            if (done_event) status_done <= 1'b1;
            if (tx_overrun_event) status_tx_overrun <= 1'b1;
            if (rx_overrun_event) status_rx_overrun <= 1'b1;
            if (rx_underrun_event) status_rx_underrun <= 1'b1;
            if (mode_fault_event) status_mode_fault <= 1'b1;
            if (illegal_access_event || illegal_access_now) status_illegal_access <= 1'b1;
            if (apb_xfer && !illegal_access_now) begin
                if (PWRITE) begin
                    case (addr12)
                        ADDR_CTRL: begin
                            enable <= PWDATA[0];
                            start_pulse <= PWDATA[1];
                            cpol <= PWDATA[2];
                            cpha <= PWDATA[3];
                            lsb_first <= PWDATA[4];
                            continuous_cs <= PWDATA[5];
                            loopback <= PWDATA[6];
                            soft_reset_pulse <= PWDATA[7];
                            cs_sel <= PWDATA[10:8];
                            data_width_m1 <= PWDATA[15:11];
                        end
                        ADDR_PRESCALE: prescale_div <= prescale_write_data;
                        ADDR_TXDATA: begin
                            tx_push <= 1'b1;
                            tx_push_data <= PWDATA;
                        end
                        ADDR_INT_MASK: int_mask <= PWDATA[7:0];
                        ADDR_INT_CLEAR: begin
                            int_clear_w1c <= PWDATA[7:0];
                            if (PWDATA[0]) status_done <= 1'b0;
                            if (PWDATA[1]) status_tx_overrun <= 1'b0;
                            if (PWDATA[2]) status_rx_overrun <= 1'b0;
                            if (PWDATA[3]) status_rx_underrun <= 1'b0;
                            if (PWDATA[4]) status_mode_fault <= 1'b0;
                            if (PWDATA[5]) status_illegal_access <= 1'b0;
                        end
                        ADDR_CS_IDLE: cs_idle_val <= cs_idle_write_data;
                        default: begin
                            enable <= enable;
                        end
                    endcase
                end else if (addr12 == ADDR_RXDATA) begin
                    rx_pop <= 1'b1;
                end
            end
            if (soft_reset_pulse) begin
                status_done <= 1'b0;
                status_tx_overrun <= 1'b0;
                status_rx_overrun <= 1'b0;
                status_rx_underrun <= 1'b0;
                status_mode_fault <= 1'b0;
                status_illegal_access <= 1'b0;
            end
        end
    end
endmodule

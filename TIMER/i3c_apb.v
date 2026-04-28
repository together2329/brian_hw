
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: i3c_apb
// Description: APB3 slave interface wrapping the I3C master controller core.
//
// Register Map (word-aligned, PADDR[7:0]):
//   Offset 0x00  CTRL      R/W  [0]=enable, [1]=start_w1p, [2]=ibi_en, [3]=read
//   Offset 0x04  STATUS    R    [0]=busy, [1]=done_sticky (cleared on read),
//                                [2]=ibi_rcvd_sticky, [3]=error_sticky
//   Offset 0x08  TX_DATA   R/W  [7:0] transmit data byte
//   Offset 0x0C  RX_DATA   R    [7:0] received data byte (read clears done/error)
//   Offset 0x10  CMD       R/W  [7:0] command byte
//   Offset 0x14  DEV_ADDR  R/W  [7:0] device address (7-bit, upper 7)
//   Offset 0x18  CLK_DIV   R/W  [15:0] SCL half-period divider
//
// APB3 Signals:
//   PCLK     - Bus clock (connected to i3c clk)
//   PRESETn  - Active-low bus reset (connected to i3c rst_n)
//   PSEL     - Select signal
//   PENABLE  - Enable signal
//   PWRITE   - Write strobe (1=write, 0=read)
//   PADDR    - Address bus [7:0]
//   PWDATA   - Write data [31:0]
//   PRDATA   - Read data [31:0]
//   PREADY   - Transfer ready (always 1, no wait states)
//   PSLVERR  - Slave error (always 0)
//----------------------------------------------------------------------------

module i3c_apb (
    input  wire         PCLK,
    input  wire         PRESETn,
    input  wire         PSEL,
    input  wire         PENABLE,
    input  wire         PWRITE,
    input  wire [7:0]   PADDR,
    input  wire [31:0]  PWDATA,
    output wire [31:0]  PRDATA,
    output wire         PREADY,
    output wire         PSLVERR,

    // I3C external pins (bidirectional SDA)
    input  wire         sda_in,
    output wire         sda_out,
    output wire         sda_oe,
    output wire         scl_out,
    output wire         scl_oe,

    // I3C interrupt output
    output wire         irq
);

    //--------------------------------------------------------------------------
    // Internal register storage
    //--------------------------------------------------------------------------
    reg        ctrl_enable;
    reg        ctrl_start_pulse;
    reg        ctrl_ibi_en;
    reg        ctrl_read;
    reg [7:0]  reg_tx_data;
    reg [7:0]  reg_cmd;
    reg [7:0]  reg_dev_addr;
    reg [15:0] reg_clk_div;
    reg        done_sticky;
    reg        error_sticky;
    reg        ibi_rcvd_sticky;

    //--------------------------------------------------------------------------
    // Address decode
    //--------------------------------------------------------------------------
    wire [2:0] addr_word = PADDR[4:2];  // Word-aligned address index

    wire sel_ctrl     = (addr_word == 3'd0);
    wire sel_status   = (addr_word == 3'd1);
    wire sel_tx_data  = (addr_word == 3'd2);
    wire sel_rx_data  = (addr_word == 3'd3);
    wire sel_cmd      = (addr_word == 3'd4);
    wire sel_dev_addr = (addr_word == 3'd5);
    wire sel_clk_div  = (addr_word == 3'd6);

    // APB write on access phase
    wire apb_write = PSEL && PENABLE && PWRITE;
    wire apb_read  = PSEL && PENABLE && !PWRITE;

    //--------------------------------------------------------------------------
    // Register write logic
    //--------------------------------------------------------------------------
    always @(posedge PCLK) begin
        if (!PRESETn) begin
            ctrl_enable      <= 1'b0;
            ctrl_start_pulse <= 1'b0;
            ctrl_ibi_en      <= 1'b0;
            ctrl_read        <= 1'b0;
            reg_tx_data      <= 8'd0;
            reg_cmd          <= 8'd0;
            reg_dev_addr     <= 8'd0;
            reg_clk_div      <= 16'd1;
            done_sticky      <= 1'b0;
            error_sticky     <= 1'b0;
            ibi_rcvd_sticky  <= 1'b0;
        end else begin
            // Auto-clear start pulse after one clock
            ctrl_start_pulse <= 1'b0;

            // Latch done_sticky from i3c core (set on done, cleared on STATUS read)
            if (i3c_done) begin
                done_sticky <= 1'b1;
            end

            // Latch error_sticky from i3c core
            if (i3c_error) begin
                error_sticky <= 1'b1;
            end

            // Latch ibi_rcvd_sticky from i3c core
            if (i3c_ibi_rcvd) begin
                ibi_rcvd_sticky <= 1'b1;
            end

            if (apb_write) begin
                case (addr_word)
                    3'd0: begin // CTRL
                        ctrl_enable  <= PWDATA[0];
                        ctrl_start_pulse <= PWDATA[1];  // W1P: set on write
                        ctrl_ibi_en  <= PWDATA[2];
                        ctrl_read    <= PWDATA[3];
                    end
                    3'd2: begin // TX_DATA
                        reg_tx_data <= PWDATA[7:0];
                    end
                    3'd4: begin // CMD
                        reg_cmd <= PWDATA[7:0];
                    end
                    3'd5: begin // DEV_ADDR
                        reg_dev_addr <= PWDATA[7:0];
                    end
                    3'd6: begin // CLK_DIV
                        reg_clk_div <= PWDATA[15:0];
                    end
                    // STATUS (0x04): read-only, ignore writes
                    // RX_DATA (0x0C): read-only, ignore writes
                    default: ;
                endcase
            end

            // Clear sticky done, error, and ibi_rcvd on STATUS register read
            if (apb_read && sel_status) begin
                done_sticky     <= 1'b0;
                error_sticky    <= 1'b0;
                ibi_rcvd_sticky <= 1'b0;
            end
        end
    end

    //--------------------------------------------------------------------------
    // I3C core signals
    //--------------------------------------------------------------------------
    wire i3c_busy;
    wire i3c_done;
    wire i3c_error;
    wire i3c_ibi_rcvd;
    wire [7:0] i3c_rx_data;

    //--------------------------------------------------------------------------
    // RX read strobe: pulse ack back to core when RX_DATA is read
    // The i3c core latches rx_data on NACK state, so we don't need to clear it
    // But we wire it through for compatibility
    //--------------------------------------------------------------------------

    //--------------------------------------------------------------------------
    // Instantiate I3C core
    //--------------------------------------------------------------------------
    i3c u_i3c (
        .clk      (PCLK),
        .rst_n    (PRESETn),
        .enable   (ctrl_enable),
        .read     (ctrl_read),
        .start    (ctrl_start_pulse),
        .tx_data  (reg_tx_data),
        .rx_data  (i3c_rx_data),
        .dev_addr (reg_dev_addr),
        .cmd      (reg_cmd),
        .sda_in   (sda_in),
        .sda_out  (sda_out),
        .sda_oe   (sda_oe),
        .scl_out  (scl_out),
        .scl_oe   (scl_oe),
        .busy     (i3c_busy),
        .done     (i3c_done),
        .error    (i3c_error),
        .ibi_en   (ctrl_ibi_en),
        .ibi_rcvd (i3c_ibi_rcvd),
        .clk_div  (reg_clk_div)
    );

    //--------------------------------------------------------------------------
    // Read data mux
    //--------------------------------------------------------------------------
    reg [31:0] prdata_reg;

    always @(*) begin
        prdata_reg = 32'd0;  // Default: return 0 for unmapped addresses
        case (addr_word)
            3'd0: prdata_reg = {28'd0, ctrl_read, ctrl_ibi_en, ctrl_start_pulse, ctrl_enable};
            3'd1: prdata_reg = {28'd0, error_sticky, ibi_rcvd_sticky, done_sticky, i3c_busy};
            3'd2: prdata_reg = {24'd0, reg_tx_data};
            3'd3: prdata_reg = {24'd0, i3c_rx_data};
            3'd4: prdata_reg = {24'd0, reg_cmd};
            3'd5: prdata_reg = {24'd0, reg_dev_addr};
            3'd6: prdata_reg = {16'd0, reg_clk_div};
            default: prdata_reg = 32'd0;
        endcase
    end

    assign PRDATA  = prdata_reg;
    assign PREADY  = 1'b1;   // No wait states
    assign PSLVERR = 1'b0;   // No slave errors

    //--------------------------------------------------------------------------
    // IRQ output: level-sensitive, asserted when done_sticky is set
    //--------------------------------------------------------------------------
    assign irq = done_sticky;

endmodule

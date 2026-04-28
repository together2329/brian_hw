
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: smbus_apb
// Description: APB3 slave interface wrapping the SMBus master controller core.
//
// Register Map (word-aligned, PADDR[7:0]):
//   Offset 0x00  CTRL      R/W  [0]=enable, [1]=start_w1p, [2]=pec_en, [3]=rw
//   Offset 0x04  STATUS    R    [0]=busy, [1]=done_sticky (cleared on read),
//                                [2]=timeout_sticky, [3]=pec_error_sticky
//   Offset 0x08  TX_DATA   R/W  [7:0] transmit data byte
//   Offset 0x0C  RX_DATA   R    [7:0] received data byte
//   Offset 0x10  CMD       R/W  [7:0] command byte
//   Offset 0x14  DEV_ADDR  R/W  [7:0] device address (7-bit, upper 7)
//   Offset 0x18  CLK_DIV   R/W  [15:0] SMBCLK half-period divider
//
// APB3 Signals:
//   PCLK     - Bus clock (connected to smbus clk)
//   PRESETn  - Active-low bus reset (connected to smbus rst_n)
//   PSEL     - Select signal
//   PENABLE  - Enable signal
//   PWRITE   - Write strobe (1=write, 0=read)
//   PADDR    - Address bus [7:0]
//   PWDATA   - Write data [31:0]
//   PRDATA   - Read data [31:0]
//   PREADY   - Transfer ready (always 1, no wait states)
//   PSLVERR  - Slave error (always 0)
//----------------------------------------------------------------------------

module smbus_apb (
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

    // SMBus external pins (bidirectional SMBDAT)
    input  wire         smbdat_in,
    output wire         smbdat_out,
    output wire         smbdat_oe,
    output wire         smbclk_out,
    output wire         smbclk_oe,

    // SMBus interrupt output
    output wire         irq
);

    //--------------------------------------------------------------------------
    // Internal register storage
    //--------------------------------------------------------------------------
    reg        ctrl_enable;
    reg        ctrl_start_pulse;
    reg        ctrl_pec_en;
    reg        ctrl_rw;
    reg [7:0]  reg_tx_data;
    reg [7:0]  reg_cmd;
    reg [7:0]  reg_dev_addr;
    reg [15:0] reg_clk_div;
    reg        done_sticky;
    reg        timeout_sticky;
    reg        pec_error_sticky;

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
            ctrl_pec_en      <= 1'b0;
            ctrl_rw          <= 1'b0;
            reg_tx_data      <= 8'd0;
            reg_cmd          <= 8'd0;
            reg_dev_addr     <= 8'd0;
            reg_clk_div      <= 16'd1;
            done_sticky      <= 1'b0;
            timeout_sticky   <= 1'b0;
            pec_error_sticky <= 1'b0;
        end else begin
            // Auto-clear start pulse after one clock
            ctrl_start_pulse <= 1'b0;

            // Latch done_sticky from smbus core
            if (smbus_done) begin
                done_sticky <= 1'b1;
            end

            // Latch timeout_sticky from smbus core
            if (smbus_timeout) begin
                timeout_sticky <= 1'b1;
            end

            // Latch pec_error_sticky from smbus core
            if (smbus_pec_error) begin
                pec_error_sticky <= 1'b1;
            end

            if (apb_write) begin
                case (addr_word)
                    3'd0: begin // CTRL
                        ctrl_enable      <= PWDATA[0];
                        ctrl_start_pulse <= PWDATA[1];  // W1P: set on write
                        ctrl_pec_en      <= PWDATA[2];
                        ctrl_rw          <= PWDATA[3];
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

            // Clear sticky bits on STATUS register read
            if (apb_read && sel_status) begin
                done_sticky      <= 1'b0;
                timeout_sticky   <= 1'b0;
                pec_error_sticky <= 1'b0;
            end
        end
    end

    //--------------------------------------------------------------------------
    // SMBus core signals
    //--------------------------------------------------------------------------
    wire smbus_busy;
    wire smbus_done;
    wire smbus_error;
    wire smbus_timeout;
    wire smbus_pec_error;
    wire [7:0] smbus_rx_data;

    //--------------------------------------------------------------------------
    // Instantiate SMBus core
    //--------------------------------------------------------------------------
    smbus u_smbus (
        .clk        (PCLK),
        .rst_n      (PRESETn),
        .enable     (ctrl_enable),
        .rw         (ctrl_rw),
        .start      (ctrl_start_pulse),
        .tx_data    (reg_tx_data),
        .rx_data    (smbus_rx_data),
        .dev_addr   (reg_dev_addr),
        .cmd        (reg_cmd),
        .smbdat_in  (smbdat_in),
        .smbdat_out (smbdat_out),
        .smbdat_oe  (smbdat_oe),
        .smbclk_out (smbclk_out),
        .smbclk_oe  (smbclk_oe),
        .busy       (smbus_busy),
        .done       (smbus_done),
        .error      (smbus_error),
        .timeout    (smbus_timeout),
        .pec_error  (smbus_pec_error),
        .pec_en     (ctrl_pec_en),
        .clk_div    (reg_clk_div)
    );

    //--------------------------------------------------------------------------
    // Read data mux
    //--------------------------------------------------------------------------
    reg [31:0] prdata_reg;

    always @(*) begin
        prdata_reg = 32'd0;  // Default: return 0 for unmapped addresses
        case (addr_word)
            3'd0: prdata_reg = {28'd0, ctrl_rw, ctrl_pec_en, ctrl_start_pulse, ctrl_enable};
            3'd1: prdata_reg = {28'd0, pec_error_sticky, timeout_sticky, done_sticky, smbus_busy};
            3'd2: prdata_reg = {24'd0, reg_tx_data};
            3'd3: prdata_reg = {24'd0, smbus_rx_data};
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
    // IRQ output: level-sensitive, asserted when done or timeout sticky is set
    //--------------------------------------------------------------------------
    assign irq = done_sticky || timeout_sticky;

endmodule

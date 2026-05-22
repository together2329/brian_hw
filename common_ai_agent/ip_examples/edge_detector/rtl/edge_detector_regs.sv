// edge_detector_regs.sv -- APB CSR block generated from edge_detector SSOT
module edge_detector_regs #(
    // Width of the detected input vector; STATUS exposes up to 8 sticky lanes.
    parameter integer WIDTH = 1,
    // CONTROL.edge_mode reset/default selected by the SSOT EDGE_MODE parameter.
    parameter integer EDGE_MODE_RESET = 2
) (
    input  logic        PCLK,
    input  logic        PRESETn,
    input  logic [11:0] PADDR,
    input  logic        PSEL,
    input  logic        PENABLE,
    input  logic        PWRITE,
    input  logic [31:0] PWDATA,
    input  logic [3:0]  PSTRB,
    input  logic [WIDTH-1:0] edge_pulse_i,
    output logic [1:0]  edge_mode_o,
    output logic        enable_o,
    output logic        irq_enable_o,
    output logic [31:0] PRDATA,
    output logic        PREADY,
    output logic        PSLVERR,
    output logic        irq_o
);
    localparam [11:0] ADDR_CONTROL    = 12'h000;
    localparam [11:0] ADDR_STATUS     = 12'h004;
    localparam [11:0] ADDR_RAW_STATUS = 12'h008;

    logic        apb_access;
    logic        apb_write;
    logic        apb_read;
    logic        valid_addr;
    logic [7:0]  edge_pulse_8;
    logic [7:0]  status_edge_sticky;
    logic        status_overflow;
    logic [31:0] control_reg;
    logic [31:0] status_value;
    logic [31:0] raw_status_value;
    logic        any_edge_pulse;
    logic        w1c_status_write;
    logic [1:0]  edge_mode_reset_value;
    logic [3:0]  control_write_data;
    logic [8:0]  status_w1c_mask;
    logic [22:0] reserved_write_data;
    logic        ignored_reserved_write;

    assign edge_mode_reset_value = EDGE_MODE_RESET[1:0];
    assign control_write_data = PWDATA[3:0];
    assign status_w1c_mask = {PWDATA[8], PWDATA[7:0]};
    assign reserved_write_data = PWDATA[31:9];
    assign ignored_reserved_write = |reserved_write_data;
    assign apb_access = PSEL & PENABLE;
    assign apb_write  = apb_access & PWRITE;
    assign apb_read   = apb_access & ~PWRITE;
    assign valid_addr = (PADDR == ADDR_CONTROL) | (PADDR == ADDR_STATUS) | (PADDR == ADDR_RAW_STATUS);

    // The SSOT STATUS/RAW_STATUS maps at most eight lanes; upper bits read as reserved zero.
    assign edge_pulse_8 = {{(8-WIDTH){1'b0}}, edge_pulse_i};
    assign any_edge_pulse = |edge_pulse_i;
    assign w1c_status_write = apb_write & (PADDR == ADDR_STATUS);

    assign edge_mode_o   = control_reg[1:0];
    assign enable_o      = control_reg[2];
    assign irq_enable_o  = control_reg[3];
    assign status_value  = {23'h000000, status_overflow, status_edge_sticky};
    assign raw_status_value = {24'h000000, edge_pulse_8};

    // PREADY is zero-wait-state per SSOT custom assumption; PSLVERR flags unmapped access only.
    assign PREADY  = 1'b1;
    assign PSLVERR = apb_access & ~valid_addr;

    // CONTROL is byte-strobe writable; reserved bits are not stored architecturally.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            control_reg <= {28'h0000000, 2'b00, edge_mode_reset_value};
        end else if (apb_write & (PADDR == ADDR_CONTROL)) begin
            if (PSTRB[0]) begin
                control_reg[7:0] <= {4'h0, control_write_data};
            end
            if (PSTRB[1]) begin
                control_reg[15:8] <= 8'h00;
            end
            if (PSTRB[2]) begin
                control_reg[23:16] <= 8'h00;
            end
            if (PSTRB[3]) begin
                control_reg[31:24] <= 8'h00;
            end
        end
    end

    // STATUS implements SSOT W1C sticky bits and overflow-on-edge-while-sticky behavior.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            status_edge_sticky <= 8'h00;
            status_overflow <= 1'b0;
        end else begin
            status_edge_sticky <= (status_edge_sticky | edge_pulse_8) & ~( {8{w1c_status_write}} & status_w1c_mask[7:0] );
            status_overflow <= ((status_overflow | (|(edge_pulse_8 & status_edge_sticky))) & ~(w1c_status_write & status_w1c_mask[8])) | (ignored_reserved_write & 1'b0);
        end
    end

    // APB read data is valid during the completing ACCESS phase.
    always @(*) begin
        PRDATA = 32'h00000000;
        if (apb_read) begin
            case (PADDR)
                ADDR_CONTROL:    PRDATA = control_reg;
                ADDR_STATUS:     PRDATA = status_value;
                ADDR_RAW_STATUS: PRDATA = raw_status_value;
                default:         PRDATA = 32'h00000000;
            endcase
        end
    end

    // irq_o is level-sensitive: set by sticky status while irq_enable is configured.
    always @(*) begin
        irq_o = irq_enable_o & (any_edge_pulse | (|status_edge_sticky));
    end
endmodule

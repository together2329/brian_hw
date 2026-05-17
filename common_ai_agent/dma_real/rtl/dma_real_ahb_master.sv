// dma_real_ahb_master.sv — AHB-Lite master protocol engine
//
// SSOT refs: io_list.interfaces.ahb_master, cycle_model.pipeline,
//   cycle_model.handshake_rules

module dma_real_ahb_master #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer BURST_MAX  = 16
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // Control from channel
    input  logic                  xfer_start,
    input  logic                  xfer_write,
    input  logic [ADDR_WIDTH-1:0] xfer_addr,
    input  logic [15:0]           xfer_len,
    output logic                  xfer_done,
    output logic                  xfer_error,
    // Data interface
    output logic [DATA_WIDTH-1:0] write_data,
    input  logic [DATA_WIDTH-1:0] read_data,
    // AHB-Lite master interface
    output logic [ADDR_WIDTH-1:0] haddr,
    output logic                  hwrite,
    output logic [1:0]            htrans,
    output logic [2:0]            hsize,
    output logic [2:0]            hburst,
    output logic [DATA_WIDTH-1:0] hwdata,
    input  logic [DATA_WIDTH-1:0] hrdata,
    input  logic                  hready,
    input  logic                  hresp,
    output logic                  hbusreq,
    input  logic                  hgrant
);

    // AHB transfer encoding
    localparam [1:0] HTRANS_IDLE   = 2'b00;
    localparam [1:0] HTRANS_NONSEQ = 2'b10;
    localparam [1:0] HTRANS_SEQ    = 2'b11;

    // AHB burst encoding
    localparam [2:0] HBURST_SINGLE = 3'b000;
    localparam [2:0] HBURST_INCR4  = 3'b001;
    localparam [2:0] HBURST_INCR8  = 3'b010;
    localparam [2:0] HBURST_INCR16 = 3'b011;

    // State machine
    localparam [2:0] ST_IDLE   = 3'd0;
    localparam [2:0] ST_ADDR   = 3'd1;
    localparam [2:0] ST_DATA   = 3'd2;
    localparam [2:0] ST_DONE   = 3'd3;
    localparam [2:0] ST_ERROR  = 3'd4;

    logic [2:0] state_q, next_state;
    logic [15:0] beat_count_q;
    logic [15:0] burst_len_q;
    logic [ADDR_WIDTH-1:0] addr_q;
    logic write_q;
    logic first_beat_q;

    // Bus request
    assign hbusreq = xfer_start;

    // Burst length calculation
    wire [15:0] actual_burst = (xfer_len < BURST_MAX[15:0]) ? xfer_len : BURST_MAX[15:0];

    // Burst encoding
    always @(*) begin
        hburst = HBURST_SINGLE;
        if (burst_len_q >= 16)
            hburst = HBURST_INCR16;
        else if (burst_len_q >= 8)
            hburst = HBURST_INCR8;
        else if (burst_len_q >= 4)
            hburst = HBURST_INCR4;
    end

    // AHB outputs
    assign hsize = 3'b010; // 32-bit word

    always @(*) begin
        htrans  = HTRANS_IDLE;
        haddr   = addr_q;
        hwrite  = write_q;
        hwdata  = write_data;
        xfer_done  = 1'b0;
        xfer_error = 1'b0;

        case (state_q)
            ST_ADDR: begin
                htrans = first_beat_q ? HTRANS_NONSEQ : HTRANS_SEQ;
                haddr  = addr_q;
                hwrite = write_q;
            end
            ST_DATA: begin
                hwdata = write_data;
            end
            ST_DONE: begin
                xfer_done = 1'b1;
            end
            ST_ERROR: begin
                xfer_error = 1'b1;
            end
            default: begin
                htrans = HTRANS_IDLE;
            end
        endcase
    end

    // State register
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            state_q      <= ST_IDLE;
            beat_count_q <= 16'd0;
            burst_len_q  <= 16'd0;
            addr_q       <= {ADDR_WIDTH{1'b0}};
            write_q      <= 1'b0;
            first_beat_q <= 1'b0;
        end else begin
            state_q <= next_state;
            case (state_q)
                ST_IDLE: begin
                    if (xfer_start && hgrant) begin
                        addr_q       <= xfer_addr;
                        write_q      <= xfer_write;
                        burst_len_q  <= actual_burst;
                        beat_count_q <= 16'd0;
                        first_beat_q <= 1'b1;
                    end
                end
                ST_ADDR: begin
                    first_beat_q <= 1'b0;
                    if (hready) begin
                        beat_count_q <= beat_count_q + 16'd1;
                        addr_q <= addr_q + {{ADDR_WIDTH-2{1'b0}}, 2'b10};
                        if (beat_count_q + 16'd1 >= burst_len_q)
                            ; // will transition to ST_DATA then ST_DONE
                    end
                end
                ST_DATA: begin
                    if (hready && hresp) begin
                        // Bus error
                    end
                end
                default: begin
                    // ST_DONE, ST_ERROR: auto-clear to IDLE
                end
            endcase
        end
    end

    // Next-state logic
    always @(*) begin
        next_state = state_q;
        case (state_q)
            ST_IDLE: begin
                if (xfer_start && hgrant)
                    next_state = ST_ADDR;
            end
            ST_ADDR: begin
                if (hready && !hresp) begin
                    if (beat_count_q + 16'd1 >= burst_len_q)
                        next_state = ST_DATA;
                end else if (hresp) begin
                    next_state = ST_ERROR;
                end
            end
            ST_DATA: begin
                if (hready) begin
                    if (hresp)
                        next_state = ST_ERROR;
                    else
                        next_state = ST_DONE;
                end
            end
            ST_DONE: begin
                next_state = ST_IDLE;
            end
            ST_ERROR: begin
                next_state = ST_IDLE;
            end
            default: begin
                next_state = ST_IDLE;
            end
        endcase
    end

endmodule

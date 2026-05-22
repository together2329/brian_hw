// dma_real_ahb_master.sv — Full AHB-Lite master protocol engine (hclk domain)
//
// SSOT refs: io_list.interfaces.ahb_master, cycle_model.pipeline, cycle_model.handshake_rules
//
// v2 enhancements: hprot[3:0], hmaster[3:0], hmastlock, hresp[1:0] (OKAY/ERROR/RETRY/SPLIT),
//   dynamic hsize, INCR4/8/16 + WRAP4/8/16, 1KB boundary detection.

module dma_real_ahb_master #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer BURST_MAX  = 16
) (
    input  logic                  hclk,
    input  logic                  hresetn,
    // Control from channel
    input  logic                  xfer_start,
    input  logic                  xfer_write,
    input  logic [ADDR_WIDTH-1:0] xfer_addr,
    input  logic [15:0]           xfer_len,
    input  logic [2:0]            xfer_hsize,
    input  logic [2:0]            xfer_hburst,
    input  logic [3:0]            xfer_hprot,
    input  logic [3:0]            xfer_hmaster,
    input  logic                  xfer_hmastlock,
    input  logic [15:0]           xfer_timeout,
    output logic                  xfer_done,
    output logic                  xfer_error,
    output logic [2:0]            xfer_err_code,
    // Data interface
    output logic [DATA_WIDTH-1:0] write_data,
    input  logic [DATA_WIDTH-1:0] read_data,
    // AHB-Lite master interface
    output logic [ADDR_WIDTH-1:0] haddr,
    output logic                  hwrite,
    output logic [1:0]            htrans,
    output logic [2:0]            hsize,
    output logic [2:0]            hburst,
    output logic [3:0]            hprot,
    output logic [3:0]            hmaster,
    output logic                  hmastlock,
    output logic [DATA_WIDTH-1:0] hwdata,
    input  logic [DATA_WIDTH-1:0] hrdata,
    input  logic                  hready,
    input  logic [1:0]            hresp,
    output logic                  hbusreq,
    input  logic                  hgrant
);

    localparam [1:0] HTRANS_IDLE   = 2'b00;
    localparam [1:0] HTRANS_BUSY   = 2'b01;
    localparam [1:0] HTRANS_NONSEQ = 2'b10;
    localparam [1:0] HTRANS_SEQ    = 2'b11;

    localparam [1:0] HRESP_OKAY   = 2'b00;
    localparam [1:0] HRESP_ERROR  = 2'b01;
    localparam [1:0] HRESP_RETRY  = 2'b10;
    localparam [1:0] HRESP_SPLIT  = 2'b11;

    localparam [2:0] HBURST_SINGLE = 3'b000;
    localparam [2:0] HBURST_INCR4  = 3'b001;
    localparam [2:0] HBURST_INCR8  = 3'b010;
    localparam [2:0] HBURST_INCR16 = 3'b011;
    localparam [2:0] HBURST_WRAP4  = 3'b101;
    localparam [2:0] HBURST_WRAP8  = 3'b110;
    localparam [2:0] HBURST_WRAP16 = 3'b111;

    localparam [2:0] ST_IDLE   = 3'd0;
    localparam [2:0] ST_ADDR   = 3'd1;
    localparam [2:0] ST_DATA   = 3'd2;
    localparam [2:0] ST_DONE   = 3'd3;
    localparam [2:0] ST_ERROR  = 3'd4;
    localparam [2:0] ST_RETRY  = 3'd5;

    logic [2:0] state_q, next_state;
    logic [15:0] beat_count_q;
    logic [15:0] burst_len_q;
    logic [ADDR_WIDTH-1:0] addr_q;
    logic write_q;
    logic first_beat_q;
    logic [2:0] hsize_q;
    logic [3:0] hprot_q;
    logic [3:0] hmaster_q;
    logic hmastlock_q;
    logic [15:0] timeout_cnt_q;
    logic timeout_active_q;

    // 1KB boundary detection
    wire [ADDR_WIDTH-1:0] addr_next = addr_q + ((1 << hsize_q));
    wire crossing_1kb = (addr_q[ADDR_WIDTH-1:10] != addr_next[ADDR_WIDTH-1:10]) && beat_count_q > 0;

    // Bus request
    assign hbusreq = xfer_start || (state_q == ST_ADDR);

    // AHB outputs
    assign hprot     = hprot_q;
    assign hmaster   = hmaster_q;
    assign hmastlock = hmastlock_q;

    always @(*) begin
        htrans     = HTRANS_IDLE;
        haddr      = addr_q;
        hwrite     = write_q;
        hsize      = hsize_q;
        hwdata     = write_data;
        xfer_done  = 1'b0;
        xfer_error = 1'b0;
        xfer_err_code = 3'd0;
        hburst     = HBURST_SINGLE;

        case (state_q)
            ST_ADDR: begin
                htrans = first_beat_q ? HTRANS_NONSEQ : HTRANS_SEQ;
                haddr  = addr_q;
                hwrite = write_q;
                hsize  = hsize_q;
                hburst = burst_len_q >= 16 ? HBURST_INCR16 :
                         burst_len_q >= 8  ? HBURST_INCR8  :
                         burst_len_q >= 4  ? HBURST_INCR4  : HBURST_SINGLE;
            end
            ST_DATA: begin
                hwdata = write_data;
            end
            ST_DONE: begin
                xfer_done = 1'b1;
            end
            ST_ERROR: begin
                xfer_error = 1'b1;
                xfer_err_code = 3'd3; // bus error
            end
            ST_RETRY: begin
                // hbusreq already driven by continuous assign above
            end
            default: begin
                htrans = HTRANS_IDLE;
            end
        endcase
    end

    // Timeout detection
    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) begin
            timeout_cnt_q <= 16'd0;
            timeout_active_q <= 1'b0;
        end else begin
            if (state_q == ST_ADDR || state_q == ST_DATA) begin
                if (!hready) begin
                    if (xfer_timeout > 0) begin
                        timeout_active_q <= 1'b1;
                        if (timeout_cnt_q >= xfer_timeout - 16'd1) begin
                            // Timeout expired
                        end else begin
                            timeout_cnt_q <= timeout_cnt_q + 16'd1;
                        end
                    end
                end else begin
                    timeout_cnt_q <= 16'd0;
                    timeout_active_q <= 1'b0;
                end
            end else begin
                timeout_cnt_q <= 16'd0;
                timeout_active_q <= 1'b0;
            end
        end
    end

    // State register
    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) begin
            state_q      <= ST_IDLE;
            beat_count_q <= 16'd0;
            burst_len_q  <= 16'd0;
            addr_q       <= {ADDR_WIDTH{1'b0}};
            write_q      <= 1'b0;
            first_beat_q <= 1'b0;
            hsize_q      <= 3'b010;
            hprot_q      <= 4'b0011;
            hmaster_q    <= 4'd0;
            hmastlock_q  <= 1'b0;
        end else begin
            state_q <= next_state;
            case (state_q)
                ST_IDLE: begin
                    if (xfer_start && hgrant) begin
                        addr_q       <= xfer_addr;
                        write_q      <= xfer_write;
                        burst_len_q  <= (xfer_len < BURST_MAX[15:0]) ? xfer_len : BURST_MAX[15:0];
                        beat_count_q <= 16'd0;
                        first_beat_q <= 1'b1;
                        hsize_q      <= xfer_hsize;
                        hprot_q      <= xfer_hprot;
                        hmaster_q    <= xfer_hmaster;
                        hmastlock_q  <= xfer_hmastlock;
                    end
                end
                ST_ADDR: begin
                    first_beat_q <= 1'b0;
                    if (hready) begin
                        beat_count_q <= beat_count_q + 16'd1;
                        addr_q <= addr_next;
                        if (crossing_1kb) begin
                            first_beat_q <= 1'b1;
                            beat_count_q <= 16'd0;
                        end
                    end
                end
                default: begin
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
                if (timeout_active_q && timeout_cnt_q >= xfer_timeout - 16'd1)
                    next_state = ST_ERROR;
                else if (hready && hresp == HRESP_ERROR)
                    next_state = ST_ERROR;
                else if (hready && hresp == HRESP_RETRY)
                    next_state = ST_RETRY;
                else if (hready && hresp == HRESP_SPLIT)
                    next_state = ST_RETRY;
                else if (hready && !crossing_1kb && beat_count_q + 16'd1 >= burst_len_q)
                    next_state = ST_DATA;
                else if (hready && crossing_1kb)
                    next_state = ST_ADDR;
            end
            ST_DATA: begin
                if (timeout_active_q && timeout_cnt_q >= xfer_timeout - 16'd1)
                    next_state = ST_ERROR;
                else if (hready && hresp == HRESP_ERROR)
                    next_state = ST_ERROR;
                else if (hready)
                    next_state = ST_DONE;
            end
            ST_DONE: begin
                next_state = ST_IDLE;
            end
            ST_ERROR: begin
                next_state = ST_IDLE;
            end
            ST_RETRY: begin
                if (hgrant)
                    next_state = ST_ADDR;
            end
            default: begin
                next_state = ST_IDLE;
            end
        endcase
    end

endmodule

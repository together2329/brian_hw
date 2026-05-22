module pl330realverify_datapath #(
    parameter integer DATA_WIDTH    = 64,
    parameter integer ADDR_WIDTH    = 32,
    parameter integer SUPPORT_UNALIGNED = 0
) (
    input  logic                         clk_i,
    input  logic                         rst_ni,

    input  logic                         start_cmd_i,
    input  logic                         halt_cmd_i,
    input  logic                         fault_inject_i,
    input  logic                         debug_reject_i,

    input  logic [ADDR_WIDTH-1:0]        cfg_sar_i,
    input  logic [ADDR_WIDTH-1:0]        cfg_dar_i,
    input  logic [7:0]                   cfg_loop_count_i,
    input  logic [3:0]                   cfg_burst_len_i,

    input  logic                         r_done_ok_i,
    input  logic                         r_done_err_i,
    input  logic                         b_done_ok_i,
    input  logic                         b_done_err_i,
    input  logic [DATA_WIDTH-1:0]        rd_data_i,

    output logic [ADDR_WIDTH-1:0]        src_addr_o,
    output logic [ADDR_WIDTH-1:0]        dst_addr_o,
    output logic [3:0]                   burst_len_o,
    output logic [DATA_WIDTH-1:0]        wr_data_o,
    output logic [(DATA_WIDTH/8)-1:0]    wr_strb_o,

    output logic                         addresses_aligned_o,
    output logic                         loop_is_last_o,
    output logic [3:0]                   status_o,
    output logic [3:0]                   error_code_o,
    output logic [7:0]                   loop_remaining_o,

    output logic                         set_complete_pulse_o,
    output logic                         set_fault_pulse_o,
    output logic                         set_dbg_done_pulse_o
);
    localparam integer BYTES_PER_BEAT = DATA_WIDTH / 8;
    localparam [3:0] STATUS_STOPPED = 4'd0;
    localparam [3:0] STATUS_EXEC    = 4'd1;
    localparam [3:0] STATUS_WFP     = 4'd2;
    localparam [3:0] STATUS_DONE    = 4'd6;
    localparam [3:0] STATUS_FAULT   = 4'd8;

    localparam [3:0] ERR_NONE         = 4'd0;
    localparam [3:0] ERR_DEBUG_REJECT = 4'd1;
    localparam [3:0] ERR_UNALIGNED    = 4'd2;
    localparam [3:0] ERR_AXI_RD       = 4'd3;
    localparam [3:0] ERR_AXI_WR       = 4'd4;

    logic [ADDR_WIDTH-1:0] sar_q;
    logic [ADDR_WIDTH-1:0] dar_q;
    logic [7:0]            loop_remaining_q;
    logic [3:0]            status_q;
    logic [3:0]            error_q;
    logic [DATA_WIDTH-1:0] rd_buf_q;

    logic [ADDR_WIDTH-1:0] align_mask;
    logic [ADDR_WIDTH-1:0] bytes_per_beat_w;
    logic [ADDR_WIDTH-1:0] sar_align_bits;
    logic [ADDR_WIDTH-1:0] dar_align_bits;

    assign bytes_per_beat_w = BYTES_PER_BEAT;
    assign align_mask = bytes_per_beat_w - {{(ADDR_WIDTH-1){1'b0}}, 1'b1};
    assign sar_align_bits = sar_q & align_mask;
    assign dar_align_bits = dar_q & align_mask;
    assign addresses_aligned_o = (SUPPORT_UNALIGNED != 0) ? 1'b1 : ((sar_align_bits == {ADDR_WIDTH{1'b0}}) && (dar_align_bits == {ADDR_WIDTH{1'b0}}));

    assign src_addr_o = sar_q;
    assign dst_addr_o = dar_q;
    assign burst_len_o = cfg_burst_len_i;
    assign wr_data_o = rd_buf_q;
    assign wr_strb_o = {(DATA_WIDTH/8){1'b1}};
    assign loop_is_last_o = (loop_remaining_q <= 8'd1);

    assign status_o = status_q;
    assign error_code_o = error_q;
    assign loop_remaining_o = loop_remaining_q;

    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            sar_q <= {ADDR_WIDTH{1'b0}};
            dar_q <= {ADDR_WIDTH{1'b0}};
            loop_remaining_q <= 8'h00;
            status_q <= STATUS_STOPPED;
            error_q <= ERR_NONE;
            rd_buf_q <= {DATA_WIDTH{1'b0}};

            set_complete_pulse_o <= 1'b0;
            set_fault_pulse_o <= 1'b0;
            set_dbg_done_pulse_o <= 1'b0;
        end else begin
            set_complete_pulse_o <= 1'b0;
            set_fault_pulse_o <= 1'b0;
            set_dbg_done_pulse_o <= 1'b0;

            if (debug_reject_i) begin
                status_q <= STATUS_FAULT;
                error_q <= ERR_DEBUG_REJECT;
                set_dbg_done_pulse_o <= 1'b1;
                set_fault_pulse_o <= 1'b1;
            end

            if (start_cmd_i) begin
                if (halt_cmd_i) status_q <= STATUS_STOPPED;
                sar_q <= cfg_sar_i;
                dar_q <= cfg_dar_i;
                loop_remaining_q <= cfg_loop_count_i + 8'd1;
                error_q <= ERR_NONE;
                if (fault_inject_i) begin
                    status_q <= STATUS_FAULT;
                    error_q <= ERR_UNALIGNED;
                    set_fault_pulse_o <= 1'b1;
                end else if (!addresses_aligned_o) begin
                    status_q <= STATUS_FAULT;
                    error_q <= ERR_UNALIGNED;
                    set_fault_pulse_o <= 1'b1;
                end else begin
                    status_q <= STATUS_EXEC;
                end
            end

            // Read error has priority over successful capture in the same cycle.
            if (r_done_err_i) begin
                status_q <= STATUS_FAULT;
                error_q <= ERR_AXI_RD;
                set_fault_pulse_o <= 1'b1;
            end else if (r_done_ok_i) begin
                rd_buf_q <= rd_data_i;
                if (status_q == STATUS_WFP) status_q <= STATUS_EXEC;
            end

            // Architectural counters update only on successful B response per SSOT state_updates.
            if (b_done_err_i) begin
                status_q <= STATUS_FAULT;
                error_q <= ERR_AXI_WR;
                set_fault_pulse_o <= 1'b1;
            end else if (b_done_ok_i) begin
                sar_q <= sar_q + bytes_per_beat_w;
                dar_q <= dar_q + bytes_per_beat_w;
                if (loop_remaining_q > 8'd0) loop_remaining_q <= loop_remaining_q - 8'd1;

                if (loop_remaining_q <= 8'd1) begin
                    status_q <= STATUS_DONE;
                    set_complete_pulse_o <= 1'b1;
                end else begin
                    status_q <= STATUS_EXEC;
                end
            end
        end
    end

endmodule

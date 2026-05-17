module pl330realverify_regs #(
    parameter integer NUM_CHANNELS   = 8,
    parameter integer REG_ADDR_WIDTH = 12,
    parameter integer ADDR_WIDTH     = 32
) (
    input  logic                           clk_i,
    input  logic                           rst_ni,
    input  logic [REG_ADDR_WIDTH-1:0]      paddr_i,
    input  logic                           psel_i,
    input  logic                           penable_i,
    input  logic                           pwrite_i,
    input  logic [31:0]                    pwdata_i,
    input  logic [3:0]                     pstrb_i,
    output logic [31:0]                    prdata_o,
    output logic                           pready_o,
    output logic                           pslverr_o,

    input  logic [31:0]                    intstatus_i,
    input  logic [3:0]                     csr_status_ch0_i,
    input  logic [3:0]                     csr_error_ch0_i,
    input  logic [7:0]                     csr_loop_remaining_ch0_i,
    input  logic                           manager_busy_i,

    output logic [31:0]                    inten_o,
    output logic [ADDR_WIDTH-1:0]          sar_ch0_o,
    output logic [ADDR_WIDTH-1:0]          dar_ch0_o,
    output logic [7:0]                     loop_count_ch0_o,
    output logic [3:0]                     burst_len_ch0_o,
    output logic                           wfp_enable_ch0_o,
    output logic [4:0]                     wfp_event_ch0_o,
    output logic                           fault_inject_ch0_o,
    output logic [ADDR_WIDTH-1:0]          pc_ch0_o,

    output logic                           start_cmd_ch0_pulse_o,
    output logic                           halt_cmd_ch0_pulse_o,
    output logic                           debug_execute_pulse_o,
    output logic                           debug_reject_pulse_o,
    output logic [2:0]                     dbg_channel_o,
    output logic                           intstatus_w1c_valid_o,
    output logic [31:0]                    intstatus_w1c_mask_o
);
    localparam [REG_ADDR_WIDTH-1:0] ADDR_DBGSTATUS  = 12'h000;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_DBGCMD     = 12'h00C;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_INTEN      = 12'h020;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_INTSTATUS  = 12'h024;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_CSR_CH0    = 12'h100;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_SAR_CH0    = 12'h108;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_DAR_CH0    = 12'h10C;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_LOOP_CH0   = 12'h110;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_CTRL_CH0   = 12'h114;
    localparam [REG_ADDR_WIDTH-1:0] ADDR_PC_CH0     = 12'h118;

    logic apb_access;
    logic apb_write;
    logic apb_read;
    logic illegal_apb;

    logic [31:0] inten_q;
    logic [ADDR_WIDTH-1:0] pwdata_addr_w;
    logic [ADDR_WIDTH-1:0] sar_ch0_q;
    logic [ADDR_WIDTH-1:0] dar_ch0_q;
    logic [7:0] loop_count_ch0_q;
    logic [3:0] burst_len_ch0_q;
    logic wfp_enable_ch0_q;
    logic [4:0] wfp_event_ch0_q;
    logic fault_inject_ch0_q;
    logic [ADDR_WIDTH-1:0] pc_ch0_q;

    assign apb_access = psel_i & penable_i;
    assign apb_write  = apb_access & pwrite_i;
    assign apb_read   = apb_access & (~pwrite_i);
    assign pwdata_addr_w = pwdata_i[ADDR_WIDTH-1:0];

    assign pready_o = apb_access;

    always @(*) begin
        illegal_apb = 1'b0;
        if (apb_access) begin
            case (paddr_i)
                ADDR_DBGSTATUS,
                ADDR_DBGCMD,
                ADDR_INTEN,
                ADDR_INTSTATUS,
                ADDR_CSR_CH0,
                ADDR_SAR_CH0,
                ADDR_DAR_CH0,
                ADDR_LOOP_CH0,
                ADDR_CTRL_CH0,
                ADDR_PC_CH0: illegal_apb = 1'b0;
                default: illegal_apb = 1'b1;
            endcase
            if ((pstrb_i != 4'hF) && pwrite_i) begin
                illegal_apb = 1'b1;
            end
        end
    end

    assign pslverr_o = apb_access & illegal_apb;

    // Start/halt/debug are one-cycle command pulses emitted on legal completing writes.
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            start_cmd_ch0_pulse_o <= 1'b0;
            halt_cmd_ch0_pulse_o <= 1'b0;
            debug_execute_pulse_o <= 1'b0;
            debug_reject_pulse_o <= 1'b0;
            dbg_channel_o <= 3'd0;
            intstatus_w1c_valid_o <= 1'b0;
            intstatus_w1c_mask_o <= 32'h0000_0000;
        end else begin
            start_cmd_ch0_pulse_o <= 1'b0;
            halt_cmd_ch0_pulse_o <= 1'b0;
            debug_execute_pulse_o <= 1'b0;
            debug_reject_pulse_o <= 1'b0;
            intstatus_w1c_valid_o <= 1'b0;
            intstatus_w1c_mask_o <= 32'h0000_0000;

            if (apb_write && !illegal_apb) begin
                if (paddr_i == ADDR_CTRL_CH0) begin
                    if (pwdata_i[0]) start_cmd_ch0_pulse_o <= 1'b1;
                    if (pwdata_i[1]) halt_cmd_ch0_pulse_o <= 1'b1;
                end
                if (paddr_i == ADDR_DBGCMD) begin
                    dbg_channel_o <= pwdata_i[6:4];
                    if (pwdata_i[1:0] == 2'b00) begin
                        if (manager_busy_i == 1'b0) debug_execute_pulse_o <= 1'b1;
                        else debug_reject_pulse_o <= 1'b1;
                    end
                end
                if (paddr_i == ADDR_INTSTATUS) begin
                    intstatus_w1c_valid_o <= 1'b1;
                    intstatus_w1c_mask_o <= pwdata_i;
                end
            end
        end
    end

    // Configuration state; this subset exposes channel 0 programming while preserving fixed reset values.
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            inten_q <= 32'h0000_0000;
            sar_ch0_q <= {ADDR_WIDTH{1'b0}};
            dar_ch0_q <= {ADDR_WIDTH{1'b0}};
            loop_count_ch0_q <= 8'h00;
            burst_len_ch0_q <= 4'h0;
            wfp_enable_ch0_q <= 1'b0;
            wfp_event_ch0_q <= 5'd0;
            fault_inject_ch0_q <= 1'b0;
            pc_ch0_q <= {ADDR_WIDTH{1'b0}};
        end else begin
            if (apb_write && !illegal_apb) begin
                case (paddr_i)
                    ADDR_INTEN: begin
                        inten_q <= pwdata_i;
                    end
                    ADDR_SAR_CH0: begin
                        sar_ch0_q <= pwdata_addr_w;
                    end
                    ADDR_DAR_CH0: begin
                        dar_ch0_q <= pwdata_addr_w;
                    end
                    ADDR_LOOP_CH0: begin
                        loop_count_ch0_q <= pwdata_i[7:0];
                        burst_len_ch0_q <= pwdata_i[11:8];
                    end
                    ADDR_CTRL_CH0: begin
                        wfp_enable_ch0_q <= pwdata_i[4];
                        wfp_event_ch0_q <= pwdata_i[12:8];
                        fault_inject_ch0_q <= pwdata_i[16];
                    end
                    ADDR_PC_CH0: begin
                        pc_ch0_q <= pwdata_addr_w;
                    end
                    default: begin
                        inten_q <= inten_q;
                    end
                endcase
            end
        end
    end

    always @(*) begin
        prdata_o = 32'h0000_0000;
        if (apb_read) begin
            case (paddr_i)
                ADDR_DBGSTATUS: begin
                    prdata_o[0] = manager_busy_i;
                    // NUM_CHANNELS minus one is software-discoverable per SSOT DBGSTATUS field.
                    prdata_o[7:4] = NUM_CHANNELS[3:0] - 4'd1;
                end
                ADDR_DBGCMD: begin
                    prdata_o = 32'h0000_0000;
                end
                ADDR_INTEN: begin
                    prdata_o = inten_q;
                end
                ADDR_INTSTATUS: begin
                    prdata_o = intstatus_i;
                end
                ADDR_CSR_CH0: begin
                    prdata_o[3:0] = csr_status_ch0_i;
                    prdata_o[7:4] = csr_error_ch0_i;
                    prdata_o[15:8] = csr_loop_remaining_ch0_i;
                end
                ADDR_SAR_CH0: begin
                    prdata_o = sar_ch0_q;
                end
                ADDR_DAR_CH0: begin
                    prdata_o = dar_ch0_q;
                end
                ADDR_LOOP_CH0: begin
                    prdata_o[7:0] = loop_count_ch0_q;
                    prdata_o[11:8] = burst_len_ch0_q;
                end
                ADDR_CTRL_CH0: begin
                    prdata_o[4] = wfp_enable_ch0_q;
                    prdata_o[12:8] = wfp_event_ch0_q;
                    prdata_o[16] = fault_inject_ch0_q;
                end
                ADDR_PC_CH0: begin
                    prdata_o = pc_ch0_q;
                end
                default: begin
                    prdata_o = 32'h0000_0000;
                end
            endcase
        end
    end

    assign inten_o = inten_q;
    assign sar_ch0_o = sar_ch0_q;
    assign dar_ch0_o = dar_ch0_q;
    assign loop_count_ch0_o = loop_count_ch0_q;
    assign burst_len_ch0_o = burst_len_ch0_q;
    assign wfp_enable_ch0_o = wfp_enable_ch0_q;
    assign wfp_event_ch0_o = wfp_event_ch0_q;
    assign fault_inject_ch0_o = fault_inject_ch0_q;
    assign pc_ch0_o = pc_ch0_q;

endmodule

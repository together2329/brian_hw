// ============================================================================
// DMA Controller Module
// ============================================================================
// Description:
//   A multi-channel Direct Memory Access (DMA) controller supporting
//   configurable source/destination addresses, transfer counts, burst
//   transfers, and interrupt generation upon completion.
//
// Features:
//   - Configurable number of channels (default: 4)
//   - 32-bit address and data bus
//   - Single and burst transfer modes
//   - Source/destination address incrementing
//   - Interrupt on transfer completion
//   - Priority-based channel arbitration
//   - Software-triggered and hardware-triggered transfers
//
// Interface:
//   - Clock and reset (active-low async reset)
//   - Bus master interface (read/write to memory)
//   - Register configuration interface (CSR)
//   - Per-channel interrupt outputs
//   - Per-channel hardware request inputs
// ============================================================================

module dma #(
    parameter int NUM_CHANNELS  = 4,
    parameter int ADDR_WIDTH    = 32,
    parameter int DATA_WIDTH    = 32,
    parameter int BURST_MAX     = 16,
    parameter int MAX_TRANSFER  = 65536
)(
    // Clock and reset
    input  logic                          clk,
    input  logic                          rst_n,

    // Bus Master Interface (read)
    output logic [ADDR_WIDTH-1:0]         m_rd_addr,
    output logic                          m_rd_valid,
    input  logic [DATA_WIDTH-1:0]         m_rd_data,
    input  logic                          m_rd_ready,

    // Bus Master Interface (write)
    output logic [ADDR_WIDTH-1:0]         m_wr_addr,
    output logic [DATA_WIDTH-1:0]         m_wr_data,
    output logic                          m_wr_valid,
    input  logic                          m_wr_ready,

    // Bus arbitration
    output logic                          m_bus_req,
    input  logic                          m_bus_grant,

    // CSR Interface (slave)
    input  logic [ADDR_WIDTH-1:0]         csr_addr,
    input  logic [DATA_WIDTH-1:0]         csr_wr_data,
    input  logic                          csr_wr_en,
    input  logic                          csr_rd_en,
    output logic [DATA_WIDTH-1:0]         csr_rd_data,
    output logic                          csr_rd_valid,

    // Hardware request inputs (per channel)
    input  logic [NUM_CHANNELS-1:0]       hw_req,

    // Interrupt outputs (per channel)
    output logic [NUM_CHANNELS-1:0]       irq
);

    // =========================================================================
    // Local Parameters and Types
    // =========================================================================

    localparam int CH_IDX_WIDTH      = $clog2(NUM_CHANNELS);
    localparam int XFER_COUNT_WIDTH  = $clog2(MAX_TRANSFER + 1);
    localparam int BURST_WIDTH       = $clog2(BURST_MAX + 1);

    // Register offsets (byte addresses, word-aligned)
    localparam logic [ADDR_WIDTH-1:0] CSR_CH_SELECT   = ADDR_WIDTH'(32'h000);
    localparam logic [ADDR_WIDTH-1:0] CSR_SRC_ADDR_LO = ADDR_WIDTH'(32'h004);
    localparam logic [ADDR_WIDTH-1:0] CSR_DST_ADDR_LO = ADDR_WIDTH'(32'h00C);
    localparam logic [ADDR_WIDTH-1:0] CSR_XFER_COUNT  = ADDR_WIDTH'(32'h014);
    localparam logic [ADDR_WIDTH-1:0] CSR_CONTROL     = ADDR_WIDTH'(32'h018);
    localparam logic [ADDR_WIDTH-1:0] CSR_STATUS       = ADDR_WIDTH'(32'h01C);
    localparam logic [ADDR_WIDTH-1:0] CSR_INT_STATUS  = ADDR_WIDTH'(32'h020);
    localparam logic [ADDR_WIDTH-1:0] CSR_INT_ENABLE  = ADDR_WIDTH'(32'h024);
    localparam logic [ADDR_WIDTH-1:0] CSR_INT_CLEAR   = ADDR_WIDTH'(32'h028);

    // Control register bit definitions
    localparam int CTRL_ENABLE_BIT   = 0;
    localparam int CTRL_START_BIT    = 1;
    localparam int CTRL_STOP_BIT     = 2;
    localparam int CTRL_SRC_INC_BIT  = 3;
    localparam int CTRL_DST_INC_BIT  = 4;
    localparam int CTRL_BURST_EN_BIT = 5;
    localparam int CTRL_HW_TRIG_BIT  = 6;
    localparam int CTRL_INT_EN_BIT   = 7;
    localparam int CTRL_MODE_LO_BIT  = 8;
    localparam int CTRL_MODE_HI_BIT  = 9;

    // Transfer mode encoding
    typedef enum logic [1:0] {
        XFER_MODE_SINGLE = 2'b00,
        XFER_MODE_BURST  = 2'b01,
        XFER_MODE_CYCLIC = 2'b10,
        XFER_MODE_RSVD   = 2'b11
    } xfer_mode_e;

    // Channel state machine encoding
    typedef enum logic [2:0] {
        CH_IDLE       = 3'b000,
        CH_REQUEST    = 3'b001,
        CH_READ       = 3'b010,
        CH_READ_WAIT  = 3'b011,
        CH_WRITE      = 3'b100,
        CH_WRITE_WAIT = 3'b101,
        CH_DONE       = 3'b110,
        CH_ERROR      = 3'b111
    } ch_state_e;

    // Channel register set
    typedef struct packed {
        logic [ADDR_WIDTH-1:0]       src_addr;
        logic [ADDR_WIDTH-1:0]       dst_addr;
        logic [XFER_COUNT_WIDTH-1:0] xfer_count;
        logic [XFER_COUNT_WIDTH-1:0] xfer_remaining;
        logic                        enable;
        logic                        start;
        logic                        stop;
        logic                        src_inc;
        logic                        dst_inc;
        logic                        burst_en;
        logic                        hw_trigger;
        logic                        int_en;
        xfer_mode_e                  mode;
        ch_state_e                   state;
        logic                        active;
        logic                        done;
        logic                        error;
        logic [DATA_WIDTH-1:0]       read_data;
        logic [ADDR_WIDTH-1:0]       curr_src_addr;
        logic [ADDR_WIDTH-1:0]       curr_dst_addr;
        logic [BURST_WIDTH-1:0]      burst_count;
    } channel_regs_t;

    // =========================================================================
    // Internal Signals
    // =========================================================================

    channel_regs_t [NUM_CHANNELS-1:0] channels;

    logic [CH_IDX_WIDTH-1:0] selected_ch;
    logic [CH_IDX_WIDTH-1:0] active_ch;
    logic                    any_active;
    logic [NUM_CHANNELS-1:0] ch_request;
    logic [NUM_CHANNELS-1:0] ch_done_pulse;
    logic [NUM_CHANNELS-1:0] int_status;
    logic [NUM_CHANNELS-1:0] int_enable;
    logic                    bus_owned;

    // Arbitration
    logic [CH_IDX_WIDTH-1:0] grant_idx;

    // =========================================================================
    // Selected Channel Read Mux (Icarus workaround)
    // =========================================================================
    channel_regs_t selected_channel_r;

    always_comb begin
        selected_channel_r = '0;
        for (int i = 0; i < NUM_CHANNELS; i++) begin
            if (i == selected_ch)
                selected_channel_r = channels[i];
        end
    end

    // =========================================================================
    // CSR Read/Write Interface
    // =========================================================================

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            selected_ch <= '0;
            csr_rd_data  <= '0;
            csr_rd_valid <= 1'b0;
            int_enable   <= '0;
        end else begin
            csr_rd_valid <= csr_rd_en;

            if (csr_wr_en) begin
                unique case (csr_addr)
                    CSR_CH_SELECT: begin
                        selected_ch <= csr_wr_data[CH_IDX_WIDTH-1:0];
                    end

                    CSR_SRC_ADDR_LO: begin
                        for (int _ch = 0; _ch < NUM_CHANNELS; _ch++) begin
                            if (_ch == selected_ch) begin
                                channels[_ch].src_addr      <= csr_wr_data[ADDR_WIDTH-1:0];
                                channels[_ch].curr_src_addr <= csr_wr_data[ADDR_WIDTH-1:0];
                            end
                        end
                    end

                    CSR_DST_ADDR_LO: begin
                        for (int _ch = 0; _ch < NUM_CHANNELS; _ch++) begin
                            if (_ch == selected_ch) begin
                                channels[_ch].dst_addr      <= csr_wr_data[ADDR_WIDTH-1:0];
                                channels[_ch].curr_dst_addr <= csr_wr_data[ADDR_WIDTH-1:0];
                            end
                        end
                    end

                    CSR_XFER_COUNT: begin
                        for (int _ch = 0; _ch < NUM_CHANNELS; _ch++) begin
                            if (_ch == selected_ch) begin
                                channels[_ch].xfer_count     <= csr_wr_data[XFER_COUNT_WIDTH-1:0];
                                channels[_ch].xfer_remaining <= csr_wr_data[XFER_COUNT_WIDTH-1:0];
                            end
                        end
                    end

                    CSR_CONTROL: begin
                        for (int _ch = 0; _ch < NUM_CHANNELS; _ch++) begin
                            if (_ch == selected_ch) begin
                                channels[_ch].enable     <= csr_wr_data[CTRL_ENABLE_BIT];
                                channels[_ch].src_inc    <= csr_wr_data[CTRL_SRC_INC_BIT];
                                channels[_ch].dst_inc    <= csr_wr_data[CTRL_DST_INC_BIT];
                                channels[_ch].burst_en   <= csr_wr_data[CTRL_BURST_EN_BIT];
                                channels[_ch].hw_trigger <= csr_wr_data[CTRL_HW_TRIG_BIT];
                                channels[_ch].int_en     <= csr_wr_data[CTRL_INT_EN_BIT];
                                channels[_ch].mode       <= xfer_mode_e'(csr_wr_data[CTRL_MODE_HI_BIT:CTRL_MODE_LO_BIT]);

                                // Start bit: edge-triggered
                                if (csr_wr_data[CTRL_START_BIT] && channels[_ch].enable &&
                                    channels[_ch].state == CH_IDLE) begin
                                    channels[_ch].start          <= 1'b1;
                                    channels[_ch].xfer_remaining <= channels[_ch].xfer_count;
                                    channels[_ch].curr_src_addr  <= channels[_ch].src_addr;
                                    channels[_ch].curr_dst_addr  <= channels[_ch].dst_addr;
                                    channels[_ch].done           <= 1'b0;
                                    channels[_ch].error          <= 1'b0;
                                end else begin
                                    channels[_ch].start <= 1'b0;
                                end

                                // Stop bit
                                if (csr_wr_data[CTRL_STOP_BIT]) begin
                                    channels[_ch].stop   <= 1'b1;
                                    channels[_ch].active <= 1'b0;
                                end else begin
                                    channels[_ch].stop <= 1'b0;
                                end
                            end
                        end
                    end

                    CSR_INT_ENABLE: begin
                        int_enable <= csr_wr_data[NUM_CHANNELS-1:0];
                    end

                    CSR_INT_CLEAR: begin
                        for (int i = 0; i < NUM_CHANNELS; i++) begin
                            if (csr_wr_data[i]) begin
                                channels[i].done <= 1'b0;
                                int_status[i]    <= 1'b0;
                            end
                        end
                    end

                    default: ; // No action on reserved/unused addresses
                endcase
            end

            if (csr_rd_en) begin
                unique case (csr_addr)
                    CSR_CH_SELECT: begin
                        csr_rd_data <= {{(DATA_WIDTH-CH_IDX_WIDTH){1'b0}}, selected_ch};
                    end

                    CSR_SRC_ADDR_LO: begin
                        csr_rd_data <= selected_channel_r.src_addr;
                    end

                    CSR_DST_ADDR_LO: begin
                        csr_rd_data <= selected_channel_r.dst_addr;
                    end

                    CSR_XFER_COUNT: begin
                        csr_rd_data <= {{(DATA_WIDTH-XFER_COUNT_WIDTH){1'b0}}, selected_channel_r.xfer_count};
                    end

                    CSR_CONTROL: begin
                        csr_rd_data <= {
                            {(DATA_WIDTH-10){1'b0}},
                            selected_channel_r.mode,
                            selected_channel_r.int_en,
                            selected_channel_r.hw_trigger,
                            selected_channel_r.burst_en,
                            selected_channel_r.dst_inc,
                            selected_channel_r.src_inc,
                            1'b0, // stop is pulse, read as 0
                            1'b0, // start is pulse, read as 0
                            selected_channel_r.enable
                        };
                    end

                    CSR_STATUS: begin
                        csr_rd_data <= {
                            {(DATA_WIDTH-3){1'b0}},
                            selected_channel_r.error,
                            selected_channel_r.done,
                            selected_channel_r.active
                        };
                    end

                    CSR_INT_STATUS: begin
                        csr_rd_data <= {{(DATA_WIDTH-NUM_CHANNELS){1'b0}}, int_status};
                    end

                    CSR_INT_ENABLE: begin
                        csr_rd_data <= {{(DATA_WIDTH-NUM_CHANNELS){1'b0}}, int_enable};
                    end

                    default: begin
                        csr_rd_data <= '0;
                    end
                endcase
            end
        end
    end

    // =========================================================================
    // Channel Request Generation
    // =========================================================================

    always_comb begin
        ch_request = '0;
        for (int i = 0; i < NUM_CHANNELS; i++) begin
            if (channels[i].start && channels[i].enable && channels[i].state == CH_IDLE) begin
                ch_request[i] = 1'b1;
            end else if (channels[i].hw_trigger && hw_req[i] && channels[i].enable &&
                        channels[i].state == CH_IDLE && !channels[i].done) begin
                ch_request[i] = 1'b1;
            end
        end
    end

    // =========================================================================
    // Priority Arbiter (fixed priority: channel 0 highest)
    // =========================================================================

    always_comb begin
        grant_idx = '0;
        for (int i = NUM_CHANNELS - 1; i >= 0; i--) begin
            if (ch_request[i]) begin
                grant_idx = i[CH_IDX_WIDTH-1:0];
            end
        end
    end

    logic [NUM_CHANNELS-1:0] active_vec;
    always_comb begin
        for (int i = 0; i < NUM_CHANNELS; i++) begin
            active_vec[i] = channels[i].active;
        end
    end
    assign any_active = |active_vec;

    // =========================================================================
    // Bus Request Logic
    // =========================================================================

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_bus_req  <= 1'b0;
            bus_owned  <= 1'b0;
            active_ch  <= '0;
        end else begin
            if (!bus_owned) begin
                if (|ch_request) begin
                    m_bus_req <= 1'b1;
                    if (m_bus_grant) begin
                        bus_owned <= 1'b1;
                        active_ch <= grant_idx;
                        m_bus_req <= 1'b0;
                    end
                end
            end else if (!any_active) begin
                bus_owned <= 1'b0;
            end
        end
    end

    // =========================================================================
    // Per-Channel State Machine
    // =========================================================================

    genvar gi;
    generate
        for (gi = 0; gi < NUM_CHANNELS; gi++) begin : gen_channel
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    channels[gi].state          <= CH_IDLE;
                    channels[gi].active         <= 1'b0;
                    channels[gi].done           <= 1'b0;
                    channels[gi].error          <= 1'b0;
                    channels[gi].start          <= 1'b0;
                    channels[gi].stop           <= 1'b0;
                    channels[gi].src_addr       <= '0;
                    channels[gi].dst_addr       <= '0;
                    channels[gi].xfer_count     <= '0;
                    channels[gi].xfer_remaining <= '0;
                    channels[gi].curr_src_addr  <= '0;
                    channels[gi].curr_dst_addr  <= '0;
                    channels[gi].read_data      <= '0;
                    channels[gi].enable         <= 1'b0;
                    channels[gi].src_inc        <= 1'b1;
                    channels[gi].dst_inc        <= 1'b1;
                    channels[gi].burst_en       <= 1'b0;
                    channels[gi].hw_trigger     <= 1'b0;
                    channels[gi].int_en         <= 1'b0;
                    channels[gi].mode           <= XFER_MODE_SINGLE;
                    channels[gi].burst_count    <= '0;
                    ch_done_pulse[gi]           <= 1'b0;
                end else begin
                    ch_done_pulse[gi] <= 1'b0;

                    case (channels[gi].state)
                        CH_IDLE: begin
                            channels[gi].active <= 1'b0;
                            if (channels[gi].stop) begin
                                channels[gi].stop <= 1'b0;
                            end
                            if ((channels[gi].start || (channels[gi].hw_trigger && hw_req[gi])) &&
                                channels[gi].enable && bus_owned &&
                                (active_ch == CH_IDX_WIDTH'(gi))) begin
                                channels[gi].state  <= CH_REQUEST;
                                channels[gi].active <= 1'b1;
                                channels[gi].start  <= 1'b0;
                            end
                        end

                        CH_REQUEST: begin
                            if (channels[gi].stop) begin
                                channels[gi].state <= CH_DONE;
                                channels[gi].stop  <= 1'b0;
                            end else if (channels[gi].xfer_remaining == '0) begin
                                channels[gi].state <= CH_DONE;
                            end else begin
                                channels[gi].state <= CH_READ;
                            end
                        end

                        CH_READ: begin
                            if (channels[gi].stop) begin
                                channels[gi].state <= CH_DONE;
                                channels[gi].stop  <= 1'b0;
                            end else begin
                                channels[gi].state <= CH_READ_WAIT;
                            end
                        end

                        CH_READ_WAIT: begin
                            if (m_rd_ready) begin
                                channels[gi].read_data <= m_rd_data;
                                channels[gi].state     <= CH_WRITE;
                            end
                        end

                        CH_WRITE: begin
                            if (channels[gi].stop) begin
                                channels[gi].state <= CH_DONE;
                                channels[gi].stop  <= 1'b0;
                            end else begin
                                channels[gi].state <= CH_WRITE_WAIT;
                            end
                        end

                        CH_WRITE_WAIT: begin
                            if (m_wr_ready) begin
                                // Update addresses
                                if (channels[gi].src_inc) begin
                                    channels[gi].curr_src_addr <= channels[gi].curr_src_addr + (DATA_WIDTH / 8);
                                end
                                if (channels[gi].dst_inc) begin
                                    channels[gi].curr_dst_addr <= channels[gi].curr_dst_addr + (DATA_WIDTH / 8);
                                end

                                // Decrement transfer count
                                if (channels[gi].xfer_remaining > '0) begin
                                    channels[gi].xfer_remaining <= channels[gi].xfer_remaining - 1'b1;
                                end

                                // Check if done or more transfers
                                if (channels[gi].xfer_remaining <= XFER_COUNT_WIDTH'(1)) begin
                                    channels[gi].state <= CH_DONE;
                                end else begin
                                    channels[gi].state <= CH_REQUEST;
                                end
                            end
                        end

                        CH_DONE: begin
                            channels[gi].active <= 1'b0;
                            channels[gi].done   <= 1'b1;
                            ch_done_pulse[gi]   <= 1'b1;

                            if (channels[gi].mode == XFER_MODE_CYCLIC) begin
                                // Reload for cyclic mode
                                channels[gi].xfer_remaining <= channels[gi].xfer_count;
                                channels[gi].curr_src_addr  <= channels[gi].src_addr;
                                channels[gi].curr_dst_addr  <= channels[gi].dst_addr;
                                channels[gi].state <= CH_IDLE;
                                channels[gi].done  <= 1'b0;
                            end else begin
                                channels[gi].state <= CH_IDLE;
                            end
                        end

                        CH_ERROR: begin
                            channels[gi].active <= 1'b0;
                            channels[gi].error  <= 1'b1;
                            channels[gi].state  <= CH_IDLE;
                        end

                        default: begin
                            channels[gi].state <= CH_IDLE;
                        end
                    endcase
                end
            end
        end
    endgenerate

    // =========================================================================
    // Bus Master Read/Write Interface (MUX from active channel)
    // =========================================================================

    always_comb begin
        m_rd_addr  = '0;
        m_rd_valid = 1'b0;
        m_wr_addr  = '0;
        m_wr_data  = '0;
        m_wr_valid = 1'b0;

        for (int i = 0; i < NUM_CHANNELS; i++) begin
            if (channels[i].state == CH_READ) begin
                m_rd_addr  = channels[i].curr_src_addr;
                m_rd_valid = 1'b1;
            end
            if (channels[i].state == CH_WRITE) begin
                m_wr_addr  = channels[i].curr_dst_addr;
                m_wr_data  = channels[i].read_data;
                m_wr_valid = 1'b1;
            end
        end
    end

    // =========================================================================
    // Interrupt Generation
    // =========================================================================

    logic [NUM_CHANNELS-1:0] ch_int_en_vec;
    always_comb begin
        for (int i = 0; i < NUM_CHANNELS; i++)
            ch_int_en_vec[i] = channels[i].int_en;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            int_status <= '0;
            irq        <= '0;
        end else begin
            for (int i = 0; i < NUM_CHANNELS; i++) begin
                // Set interrupt on transfer done
                if (ch_done_pulse[i]) begin
                    int_status[i] <= 1'b1;
                end

                // Generate IRQ output
                irq[i] <= int_status[i] & int_enable[i] & ch_int_en_vec[i];
            end
        end
    end

endmodule

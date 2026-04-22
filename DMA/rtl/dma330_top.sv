// =============================================================================
// dma330_top.sv — DMA-330 Top-Level Integration
//
// Top-level module instantiating all DMA-330 submodules and wiring internal
// buses. External ports expose AXI4 master, dual APB slave, peripheral
// handshake, and interrupt lines.
// =============================================================================

module dma330_top #(
    parameter int unsigned NUM_CHANNELS    = 4,
    parameter int unsigned DATA_WIDTH      = 32,
    parameter int unsigned ADDR_WIDTH      = 32,
    parameter int unsigned MFIFO_DEPTH     = 64,
    parameter int unsigned NUM_PERIPHERALS = 4,
    parameter int unsigned NUM_EVENTS      = 8
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // AXI4 Master Interface
    // =========================================================================
    // AW channel
    output logic [ADDR_WIDTH-1:0]         m_awaddr,
    output logic [7:0]                    m_awlen,
    output logic [2:0]                    m_awsize,
    output logic [1:0]                    m_awburst,
    output logic                          m_awvalid,
    input  logic                          m_awready,
    // W channel
    output logic [DATA_WIDTH-1:0]         m_wdata,
    output logic [(DATA_WIDTH/8)-1:0]     m_wstrb,
    output logic                          m_wlast,
    output logic                          m_wvalid,
    input  logic                          m_wready,
    // B channel
    input  logic [1:0]                    m_bresp,
    input  logic                          m_bvalid,
    output logic                          m_bready,
    // AR channel
    output logic [ADDR_WIDTH-1:0]         m_araddr,
    output logic [7:0]                    m_arlen,
    output logic [2:0]                    m_arsize,
    output logic [1:0]                    m_arburst,
    output logic                          m_arvalid,
    input  logic                          m_arready,
    // R channel
    input  logic [DATA_WIDTH-1:0]         m_rdata,
    input  logic [1:0]                    m_rresp,
    input  logic                          m_rlast,
    input  logic                          m_rvalid,
    output logic                          m_rready,

    // =========================================================================
    // APB Secure Slave Interface
    // =========================================================================
    input  logic                          psel_s,
    input  logic                          penable_s,
    input  logic                          pwrite_s,
    input  logic [11:0]                   paddr_s,
    input  logic [31:0]                   pwdata_s,
    output logic [31:0]                   prdata_s,
    output logic                          pready_s,
    output logic                          pslverr_s,

    // =========================================================================
    // APB Non-Secure Slave Interface
    // =========================================================================
    input  logic                          psel_ns,
    input  logic                          penable_ns,
    input  logic                          pwrite_ns,
    input  logic [11:0]                   paddr_ns,
    input  logic [31:0]                   pwdata_ns,
    output logic [31:0]                   prdata_ns,
    output logic                          pready_ns,
    output logic                          pslverr_ns,

    // =========================================================================
    // Peripheral DMA Request/Acknowledge
    // =========================================================================
    input  logic [NUM_PERIPHERALS-1:0]    dmareq,
    output logic [NUM_PERIPHERALS-1:0]    dmaack,

    // =========================================================================
    // Interrupt Outputs (events + fault)
    // =========================================================================
    output logic [NUM_EVENTS:0]           irq
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Derived constants
    // =========================================================================
    localparam int unsigned NUM_REQUESTERS = NUM_CHANNELS + 2; // channels + 1 manager + 1 cache
    localparam int unsigned CH_WIDTH       = $clog2(NUM_CHANNELS);

    // =========================================================================
    // Internal Buses
    // =========================================================================

    // AXI master internal req/resp (NUM_REQUESTERS = NUM_CHANNELS + 2)
    axi_req_t  axi_req   [0:NUM_REQUESTERS-1];
    axi_resp_t axi_resp  [0:NUM_REQUESTERS-1];
    logic [NUM_REQUESTERS-1:0] axi_grant;
    logic [NUM_REQUESTERS-1:0] axi_w_grant;  // per-requester write grant

    // Requester ID mapping:
    //   0            = instruction cache
    //   1            = manager thread
    //   2..N+1       = channel threads 0..N-1
    localparam int unsigned REQ_ID_CACHE   = 0;
    localparam int unsigned REQ_ID_MGR     = 1;
    // Channel i maps to REQ_ID_CH0 + i
    localparam int unsigned REQ_ID_CH0     = 2;

    // Register file ↔ APB slave interface
    logic [11:0]  reg_addr;
    logic [31:0]  reg_wdata;
    logic [31:0]  reg_rdata;
    logic         reg_we;
    logic         reg_re;
    logic         reg_secure_access;

    // Channel register/state buses
    channel_regs_t   ch_regs         [0:NUM_CHANNELS-1];  // from regfile (APB view)
    channel_regs_t   ch_regs_from_ch [0:NUM_CHANNELS-1];  // from channel threads
    logic [31:0]     ch_pc           [0:NUM_CHANNELS-1];
    channel_state_t  ch_state        [0:NUM_CHANNELS-1];

    // Manager state
    manager_state_t  mgr_state;
    logic [31:0]     mgr_pc;

    // Event bus (OR-reduced from all channels + manager)
    logic [NUM_EVENTS-1:0] event_bus;

    // Per-channel one-hot event decode for OR-reduction into event_bus
    // event_send_o is a 4-bit event number pulse; decode to 1-hot NUM_EVENTS vector
    logic [NUM_EVENTS-1:0] ch_event_hot [0:NUM_CHANNELS-1];

    // Fault bus
    logic                 fault_bus;

    // Channel start/kill from manager
    logic [NUM_CHANNELS-1:0] ch_start_req;
    logic [32*NUM_CHANNELS-1:0] ch_start_pc_flat;
    logic [NUM_CHANNELS-1:0] ch_start_ack;
    logic [NUM_CHANNELS-1:0] ch_kill_req;

    // Peripheral interface ↔ channels
    logic [NUM_CHANNELS-1:0]                            ch_periph_req;
    logic [NUM_CHANNELS-1:0]                            ch_periph_ack_from_intf;
    logic [$clog2(NUM_PERIPHERALS)-1:0]                 ch_periph_num [0:NUM_CHANNELS-1];
    logic [NUM_CHANNELS-1:0]                            ch_periph_req_from_intf;

    // MFIFO interface
    logic [CH_WIDTH-1:0]  mfifo_wr_ch_id;
    logic [DATA_WIDTH-1:0] mfifo_wr_data_arr;
    logic                  mfifo_wr_valid_arr;
    logic                  mfifo_wr_ready_arr;
    logic [CH_WIDTH-1:0]  mfifo_rd_ch_id;
    logic [DATA_WIDTH-1:0] mfifo_rd_data_arr;
    logic                  mfifo_rd_valid_arr;
    logic                  mfifo_rd_ready_arr;
    logic [NUM_CHANNELS-1:0] mfifo_ch_full;
    logic [NUM_CHANNELS-1:0] mfifo_ch_empty;
    logic [$clog2(MFIFO_DEPTH):0] mfifo_ch_count [0:NUM_CHANNELS-1];
    logic [$clog2(MFIFO_DEPTH):0] mfifo_alloc_depth [0:NUM_CHANNELS-1];
    logic                  mfifo_overflow_fault;
    logic                  mfifo_underflow_fault;

    // Per-channel MFIFO connections (arbitrated to single MFIFO write/read port)
    logic [NUM_CHANNELS-1:0]            ch_mfifo_wr_valid;
    logic [NUM_CHANNELS-1:0]            ch_mfifo_wr_ready;
    logic [DATA_WIDTH-1:0]              ch_mfifo_wr_data  [0:NUM_CHANNELS-1];
    logic [NUM_CHANNELS-1:0]            ch_mfifo_rd_valid;
    logic [NUM_CHANNELS-1:0]            ch_mfifo_rd_ready;
    logic [DATA_WIDTH-1:0]              ch_mfifo_rd_data  [0:NUM_CHANNELS-1];

    // Instruction cache interface
    logic [ADDR_WIDTH-1:0] cache_lookup_addr;
    logic                  cache_lookup_valid;
    logic                  cache_lookup_ready;
    logic                  cache_lookup_hit;
    logic [511:0]          cache_lookup_data;  // LINE_SIZE*8 = 64*8
    logic [ADDR_WIDTH-1:0] cache_fill_addr;
    logic [511:0]          cache_fill_data;
    logic                  cache_fill_valid;
    logic                  cache_fill_ready;

    // Instruction fetch arbiter (shared cache → 5 decoders: 1 mgr + 4 channels)
    // FSM: IDLE → LOOKUP → HIT (feed decoder) → IDLE
    //            └→ MISS_WAIT (cache AXI fetch) → IDLE (retry)
    localparam int unsigned NUM_FETCH = NUM_CHANNELS + 1; // mgr=0, ch0=1, ch1=2, ...
    logic [1:0]                feed_state;   // 0=IDLE, 1=LOOKUP, 2=HIT, 3=MISS_WAIT
    logic [2:0]                feed_winner;  // registered winner (who owns current fetch)
    logic [2:0]                feed_sel;     // combinational winner selection
    logic [NUM_FETCH-1:0]      fetch_req;    // per-requester fetch request

    // Byte offset within cache line for the winning requester's PC
    // Cache line is 64 bytes; PC[5:0] gives byte offset; shift data so
    // the instruction bytes at that offset appear at [47:0].
    logic [5:0]                feed_byte_offset;
    logic [511:0]              shifted_cache_data;
    logic                      mgr_instr_valid;
    logic [NUM_CHANNELS-1:0]   ch_instr_valid_vec;

    // Cache AXI (direct connection to AXI master req slot 0)
    axi_req_t  cache_axi_req;
    axi_resp_t cache_axi_resp;

    // Instruction decoders (1 per channel + 1 for manager)
    decoded_instr_t mgr_decoded;
    logic           mgr_decoded_valid;
    logic           mgr_decoded_ready;

    decoded_instr_t ch_decoded     [0:NUM_CHANNELS-1];
    logic           ch_decoded_valid [0:NUM_CHANNELS-1];
    logic           ch_decoded_ready [0:NUM_CHANNELS-1];

    // Debug interface
    logic [31:0]    dbginst0;
    logic [31:0]    dbginst1;
    logic [3:0]     dbgcmd;
    logic           dbg_status;

    // Debug injection: shadow DBGINST0/DBGINST1, construct decoded_instr_t on DBGCMD write
    logic [31:0]          dbg_inst0_shadow;
    logic [31:0]          dbg_inst1_shadow;
    logic                 dbgcmd_pulse;
    decoded_instr_t       dbg_decoded_instr;
    logic                 dbg_clear_fault_pulse;

    // IRQ controller interface
    logic [NUM_EVENTS-1:0] irq_inten_wdata;
    logic                  irq_inten_we;
    logic [NUM_EVENTS-1:0] irq_intclr_wdata;  // Use lower bits for event clear
    logic                  irq_intclr_we;

    // APB write detection: forward INTEN/INTCLR writes to IRQ controller
    assign irq_inten_we    = reg_we && (reg_addr[11:0] == INTEN_OFFSET);
    assign irq_inten_wdata = reg_wdata[NUM_EVENTS-1:0];
    assign irq_intclr_we    = reg_we && (reg_addr[11:0] == INTCLR_OFFSET);
    assign irq_intclr_wdata = reg_wdata[NUM_EVENTS-1:0];

    // =========================================================================
    // 1. AXI Master — External AXI + internal req/resp array
    // =========================================================================
    dma330_axi_master #(
        .DATA_WIDTH     (DATA_WIDTH),
        .ADDR_WIDTH     (ADDR_WIDTH),
        .NUM_REQUESTERS (NUM_REQUESTERS)
    ) u_axi_master (
        .clk        (clk),
        .rst_n      (rst_n),
        // AXI AW
        .m_awaddr   (m_awaddr),
        .m_awlen    (m_awlen),
        .m_awsize   (m_awsize),
        .m_awburst  (m_awburst),
        .m_awvalid  (m_awvalid),
        .m_awready  (m_awready),
        // AXI W
        .m_wdata    (m_wdata),
        .m_wstrb    (m_wstrb),
        .m_wlast    (m_wlast),
        .m_wvalid   (m_wvalid),
        .m_wready   (m_wready),
        // AXI B
        .m_bresp    (m_bresp),
        .m_bvalid   (m_bvalid),
        .m_bready   (m_bready),
        // AXI AR
        .m_araddr   (m_araddr),
        .m_arlen    (m_arlen),
        .m_arsize   (m_arsize),
        .m_arburst  (m_arburst),
        .m_arvalid  (m_arvalid),
        .m_arready  (m_arready),
        // AXI R
        .m_rdata    (m_rdata),
        .m_rresp    (m_rresp),
        .m_rlast    (m_rlast),
        .m_rvalid   (m_rvalid),
        .m_rready   (m_rready),
        // Internal
        .req_i      (axi_req),
        .resp_o     (axi_resp),
        .grant_o    (axi_grant),
        .w_grant_o  (axi_w_grant),
        .error_o    ()
    );

    // =========================================================================
    // 2. APB Slave — External APB → internal register interface
    // =========================================================================
    dma330_apb_slave #(
        .APB_ADDR_WIDTH (12)
    ) u_apb_slave (
        .clk               (clk),
        .rst_n             (rst_n),
        // Secure APB
        .psel_s            (psel_s),
        .penable_s         (penable_s),
        .pwrite_s          (pwrite_s),
        .paddr_s           (paddr_s),
        .pwdata_s          (pwdata_s),
        .prdata_s          (prdata_s),
        .pready_s          (pready_s),
        .pslverr_s         (pslverr_s),
        // Non-secure APB
        .psel_ns           (psel_ns),
        .penable_ns        (penable_ns),
        .pwrite_ns         (pwrite_ns),
        .paddr_ns          (paddr_ns),
        .pwdata_ns         (pwdata_ns),
        .prdata_ns         (prdata_ns),
        .pready_ns         (pready_ns),
        .pslverr_ns        (pslverr_ns),
        // Register interface
        .reg_addr          (reg_addr),
        .reg_wdata         (reg_wdata),
        .reg_rdata         (reg_rdata),
        .reg_we            (reg_we),
        .reg_re            (reg_re),
        .reg_secure_access (reg_secure_access)
    );

    // =========================================================================
    // 3. Register File
    // =========================================================================
    dma330_regfile #(
        .NUM_CHANNELS (NUM_CHANNELS),
        .NUM_EVENTS   (NUM_EVENTS)
    ) u_regfile (
        .clk               (clk),
        .rst_n             (rst_n),
        // APB interface
        .reg_addr          (reg_addr),
        .reg_wdata         (reg_wdata),
        .reg_rdata         (reg_rdata),
        .reg_we            (reg_we),
        .reg_re            (reg_re),
        .reg_secure_access (reg_secure_access),
        // Channel registers (output from regfile — but we connect channel output here)
        .ch_regs           (ch_regs),
        .ch_regs_we        ({NUM_CHANNELS{1'b1}}),  // always write back live channel state
        .ch_regs_wdata     (ch_regs_from_ch),        // live channel register state
        .ch_state          (ch_state),
        .ch_pc             (ch_pc),
        // Manager state
        .mgr_state         (mgr_state),
        .mgr_pc            (mgr_pc),
        // Events & faults
        .event_trigger     (event_bus),
        .fault_trigger     (fault_bus),
        // Debug
        .dbginst0          (32'd0),
        .dbginst1          (32'd0),
        .dbgcmd            (4'd0),
        .dbg_status        (),
        // IRQ (to register file for INT_STATUS)
        .irq_o             ()
    );

    // =========================================================================
    // 4. Instruction Cache
    // =========================================================================
    dma330_instr_cache #(
        .CACHE_LINES (16),
        .LINE_SIZE   (64),
        .ADDR_WIDTH  (ADDR_WIDTH)
    ) u_instr_cache (
        .clk           (clk),
        .rst_n         (rst_n),
        // Lookup interface
        .lookup_addr   (cache_lookup_addr),
        .lookup_valid  (cache_lookup_valid),
        .lookup_ready  (cache_lookup_ready),
        .lookup_hit    (cache_lookup_hit),
        .lookup_data   (cache_lookup_data),
        // Fill interface
        .fill_addr     (cache_fill_addr),
        .fill_data     (cache_fill_data),
        .fill_valid    (cache_fill_valid),
        .fill_ready    (cache_fill_ready),
        // AXI fetch
        .axi_req_o     (cache_axi_req),
        .axi_resp_i    (cache_axi_resp)
    );

    // Cache AXI request holder: the cache issues a 1-cycle valid pulse for
    // line fills.  Icarus Verilog may not reliably propagate struct field
    // extractions from generate blocks within a single delta cycle, so we
    // latch the request and hold it until the AXI master grants it.
    axi_req_t  cache_axi_req_held;
    logic      cache_req_latched;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cache_axi_req_held <= '0;
            cache_req_latched  <= 1'b0;
        end else begin
            if (cache_axi_req.valid && !cache_req_latched) begin
                cache_axi_req_held <= cache_axi_req;
                cache_req_latched  <= 1'b1;
            end
            if (cache_req_latched && axi_grant[REQ_ID_CACHE]) begin
                cache_req_latched <= 1'b0;
                cache_axi_req_held <= '0;
            end
        end
    end

    assign axi_req[REQ_ID_CACHE]  = cache_req_latched ? cache_axi_req_held : cache_axi_req;

    // Bypass the internal axi_resp[] unpacked array — Icarus Verilog cannot
    // properly propagate packed struct values through unpacked array port
    // connections from always_comb blocks.  Instead, directly construct the
    // cache's response from the external AXI R-channel signals when the
    // AXI master has granted the cache's request.
    //   axi_resp_t = { data[31:0], last, resp[1:0], valid, error }
    assign cache_axi_resp = axi_grant[REQ_ID_CACHE] ?
        {m_rdata, (m_rlast & m_rvalid & m_rready), m_rresp, (m_rvalid & m_rready), 1'b0} :
        '0;

    // Icarus work-around: bypass axi_resp[] for channels too.
    // Direct response wires constructed from external AXI signals.
    // axi_resp_t = { data[31:0], last, resp[1:0], valid, error }
    // For reads: valid when granted and R-channel handshake occurs
    // For writes: valid when granted and B-channel handshake occurs
    // Note: only one grant is active at a time, so checking axi_grant works.

    // =========================================================================
    // 5. Manager Thread
    // =========================================================================
    dma330_manager_thread #(
        .ADDR_WIDTH   (ADDR_WIDTH),
        .NUM_CHANNELS (NUM_CHANNELS)
    ) u_manager (
        .clk              (clk),
        .rst_n            (rst_n),
        // Decoded instruction
        .decoded_instr_i  (mgr_decoded),
        .decoded_valid_i  (mgr_decoded_valid),
        .decoded_ready_o  (mgr_decoded_ready),
        // AXI (manager doesn't do data transfers, but has port)
        .axi_req_o        (axi_req[REQ_ID_MGR]),
        .axi_resp_i       (axi_resp[REQ_ID_MGR]),
        // Channel control
        .ch_start_req     (ch_start_req),
        .ch_start_pc_flat (ch_start_pc_flat),
        .ch_start_ack     (ch_start_ack),
        .ch_kill_req      (ch_kill_req),
        // Events
        .event_wait_num   (),
        .event_received   (event_bus),
        // Fault
        .fault_o          (fault_bus),
        .fault_type_o     (),
        // State
        .mgr_state_o      (mgr_state),
        .mgr_pc_o         (mgr_pc),
        // Debug (from registered APB DBGINST0/DBGINST1/DBGCMD injection)
        .dbginject_valid  (dbg_inject_valid_r),
        .dbginject_instr  (dbg_inject_instr_r),
        .dbgcmd_clear_fault (dbg_clear_fault_r)
    );

    // =========================================================================
    // 6. Manager Instruction Decoder
    // =========================================================================
    // (Simplified: direct decode from cache data for manager)
    dma330_instr_decoder u_mgr_decoder (
        .clk             (clk),
        .rst_n           (rst_n),
        .instr_bytes     (shifted_cache_data[47:0]),
        .instr_bytes_cnt (3'd6),
        .instr_valid     (mgr_instr_valid),
        .instr_ready     (),
        .decoded_o       (mgr_decoded),
        .decoded_valid   (mgr_decoded_valid),
        .decoded_ready   (mgr_decoded_ready),
        .current_pc      (mgr_pc)
    );

    // =========================================================================
    // 7. MFIFO
    // =========================================================================
    dma330_mfifo #(
        .MFIFO_DEPTH  (MFIFO_DEPTH),
        .DATA_WIDTH   (DATA_WIDTH),
        .NUM_CHANNELS (NUM_CHANNELS)
    ) u_mfifo (
        .clk              (clk),
        .rst_n            (rst_n),
        // Write port
        .wr_ch_id         (mfifo_wr_ch_id),
        .wr_data          (mfifo_wr_data_arr),
        .wr_valid         (mfifo_wr_valid_arr),
        .wr_ready         (mfifo_wr_ready_arr),
        // Read port
        .rd_ch_id         (mfifo_rd_ch_id),
        .rd_data          (mfifo_rd_data_arr),
        .rd_valid         (mfifo_rd_valid_arr),
        .rd_ready         (mfifo_rd_ready_arr),
        // Status
        .ch_full          (mfifo_ch_full),
        .ch_empty         (mfifo_ch_empty),
        .ch_count         (mfifo_ch_count),
        .allocated_depth  (mfifo_alloc_depth),
        .overflow_fault   (mfifo_overflow_fault),
        .underflow_fault  (mfifo_underflow_fault),
        .fault_clear      (1'b0)
    );

    // Default MFIFO alloc depth (equal share)
    generate
        for (genvar gi = 0; gi < NUM_CHANNELS; gi++) begin : gen_mfifo_alloc
            assign mfifo_alloc_depth[gi] = MFIFO_DEPTH / NUM_CHANNELS;
        end
    endgenerate

    // =========================================================================
    // 8. Channel Threads (generate block)
    // =========================================================================
    generate
        for (genvar ch = 0; ch < NUM_CHANNELS; ch++) begin : gen_ch
            // Event wire for this channel (used in one-hot decode below)
            logic [3:0] ch_event_send;

            // Icarus Verilog work-around: explicit intermediate wires for
            // unpacked array port connections.  Icarus may not propagate
            // signals correctly through array-indexed generate port connections.
            logic        ch_start_req_w;
            logic [31:0] ch_start_pc_w;
            logic        ch_kill_req_w;
            assign ch_start_req_w = ch_start_req[ch];
            assign ch_start_pc_w  = ch_start_pc_flat[32*ch +: 32];
            assign ch_kill_req_w  = ch_kill_req[ch];

            // Icarus work-around: struct-typed ports need explicit wires
            // for both request (output) and response (input) directions
            dma330_pkg::axi_req_t  ch_axi_req_w;
            dma330_pkg::axi_resp_t ch_axi_resp_w;
            assign axi_req[REQ_ID_CH0 + ch]  = ch_axi_req_w;
            // Bypass axi_resp[] array — construct directly from external AXI signals
            // when this channel is granted.  Same approach as cache_axi_resp.
            //   axi_resp_t = { data[31:0], last, resp[1:0], valid, error }
            // Read response: valid on R-channel handshake (not a write grant)
            // Write response: valid on B-channel handshake (is a write grant)
            assign ch_axi_resp_w = axi_grant[REQ_ID_CH0 + ch] ? (
                axi_w_grant[REQ_ID_CH0 + ch] ?
                    // Write response — B-channel
                    {(DATA_WIDTH)'(0), 1'b1, m_bresp,
                     (m_bvalid & m_bready), (m_bresp != 2'b00)} :
                    // Read response — R-channel
                    {m_rdata, (m_rlast & m_rvalid & m_rready), m_rresp,
                     (m_rvalid & m_rready), 1'b0}
            ) : '0;

            // Icarus work-around: struct-typed register output and decoder output
            dma330_pkg::channel_regs_t   ch_regs_w;
            dma330_pkg::decoded_instr_t ch_decoded_w;
            assign ch_regs_from_ch[ch]  = ch_regs_w;
            assign ch_decoded[ch]       = ch_decoded_w;

                // Channel thread
                dma330_channel_thread #(
                .CHANNEL_ID (ch),
                .ADDR_WIDTH (ADDR_WIDTH),
                .DATA_WIDTH (DATA_WIDTH)
            ) u_ch_thread (
                .clk              (clk),
                .rst_n            (rst_n),
                // Start/kill
                .start_i          (ch_start_req_w),
                .start_pc_i       (ch_start_pc_w),
                .start_security_i (1'b0),
                .kill_i           (ch_kill_req_w),
                // Instruction (decoded_instr_i via Icarus work-around wire)
                .decoded_instr_i  (ch_decoded_w),
                .decoded_valid_i  (ch_decoded_valid[ch]),
                .decoded_ready_o  (ch_decoded_ready[ch]),
                // AXI (via Icarus work-around wires)
                .axi_req_o        (ch_axi_req_w),
                .axi_resp_i       (ch_axi_resp_w),
                // MFIFO write
                .mfifo_wr_data    (ch_mfifo_wr_data[ch]),
                .mfifo_wr_valid   (ch_mfifo_wr_valid[ch]),
                .mfifo_wr_ready   (ch_mfifo_wr_ready[ch]),
                // MFIFO read
                .mfifo_rd_data    (ch_mfifo_rd_data[ch]),
                .mfifo_rd_valid   (ch_mfifo_rd_valid[ch]),
                .mfifo_rd_ready   (ch_mfifo_rd_ready[ch]),
                // Peripheral
                .periph_req_i     (ch_periph_ack_from_intf[ch]),
                .periph_ack_o     (ch_periph_req[ch]),
                .periph_num_o     (ch_periph_num[ch]),
                // Events
                .event_send_o     (ch_event_send),
                .event_recv_i     (event_bus),
                // Barrier
                .barrier_o        (),
                .barrier_ack_i    (1'b1),  // Simplified: immediate ack
                // Register/state output (via Icarus work-around wires)
                .ch_regs_o        (ch_regs_w),
                .ch_state_o       (ch_state[ch])
            );

            // Event decode: event_send_o (4-bit event number pulse) → one-hot event_bus bit
            // event_send_o is non-zero for exactly 1 cycle when DMASEV executes
            assign ch_event_hot[ch] = (|ch_event_send) ?
                                      (NUM_EVENTS'(1) << ch_event_send[EVENT_WIDTH-1:0]) : '0;

            // Channel instruction decoder
            dma330_instr_decoder u_ch_decoder (
                .clk             (clk),
                .rst_n           (rst_n),
                .instr_bytes     (shifted_cache_data[47:0]),
                .instr_bytes_cnt (3'd6),
                .instr_valid     (ch_instr_valid_vec[ch]),
                .instr_ready     (),
                .decoded_o       (ch_decoded_w),
                .decoded_valid   (ch_decoded_valid[ch]),
                .decoded_ready   (ch_decoded_ready[ch]),
                .current_pc      (ch_pc[ch])
            );

            // Start acknowledge: channel leaves STOPPED on start
            assign ch_start_ack[ch] = (ch_state[ch] != channel_state_t'(0)); // non-stopped
        end
    endgenerate

    // =========================================================================
    // 8b. Instruction Fetch Arbiter (shared cache → 5 decoders)
    // =========================================================================
    // Priority arbiter: manager (0) > ch0 (1) > ch1 (2) > ch2 (3) > ch3 (4)
    // FSM states: 0=IDLE, 1=LOOKUP, 2=HIT, 3=MISS_WAIT
    //
    // IDLE       : Scan for EXECUTING requesters needing instructions
    // LOOKUP     : Cache processing our lookup (1 cycle)
    // HIT        : Feed cache data to winner's decoder (instr_valid=1)
    // MISS_WAIT  : Cache fetching line via AXI, wait for cache_lookup_ready

    // --- Fetch requests: requester is EXECUTING and ready for next instruction ---
    assign fetch_req[0] = (mgr_state == MGR_EXECUTING) && mgr_decoded_ready;
    assign fetch_req[1] = (ch_state[0] == CH_EXECUTING) && ch_decoded_ready[0];
    assign fetch_req[2] = (ch_state[1] == CH_EXECUTING) && ch_decoded_ready[1];
    assign fetch_req[3] = (ch_state[2] == CH_EXECUTING) && ch_decoded_ready[2];
    assign fetch_req[4] = (ch_state[3] == CH_EXECUTING) && ch_decoded_ready[3];

    // --- Combinational: priority winner selection ---
    always_comb begin
        feed_sel = '0;
        if      (fetch_req[0]) feed_sel = 3'd0;
        else if (fetch_req[1]) feed_sel = 3'd1;
        else if (fetch_req[2]) feed_sel = 3'd2;
        else if (fetch_req[3]) feed_sel = 3'd3;
        else if (fetch_req[4]) feed_sel = 3'd4;
    end

    // --- Cache lookup control ---
    // Assert lookup_valid for 1 cycle when IDLE + request + cache ready
    assign cache_lookup_valid = (feed_state == 2'd0) && (|fetch_req) && cache_lookup_ready;

    // Address MUX: route winner's PC to cache
    always_comb begin
        case (feed_sel)
            3'd0:    cache_lookup_addr = mgr_pc;
            3'd1:    cache_lookup_addr = ch_pc[0];
            3'd2:    cache_lookup_addr = ch_pc[1];
            3'd3:    cache_lookup_addr = ch_pc[2];
            3'd4:    cache_lookup_addr = ch_pc[3];
            default: cache_lookup_addr = '0;
        endcase
    end

    // --- Arbiter FSM ---
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            feed_state  <= 2'd0; // IDLE
            feed_winner <= '0;
        end else begin
            case (feed_state)
                2'd0: begin // IDLE
                    if (cache_lookup_valid) begin
                        feed_winner <= feed_sel;
                        feed_state  <= 2'd1; // → LOOKUP
                    end
                end
                2'd1: begin // LOOKUP: cache has processed our request
                    if (cache_lookup_hit)
                        feed_state <= 2'd2; // → HIT
                    else
                        feed_state <= 2'd3; // → MISS_WAIT
                end
                2'd2: begin // HIT: decoder captured instruction
                    feed_state <= 2'd0; // → IDLE
                end
                2'd3: begin // MISS_WAIT: wait for cache to return to IDLE
                    if (cache_lookup_ready)
                        feed_state <= 2'd0; // → IDLE (retry next cycle)
                end
            endcase
        end
    end

    // --- Decoder instr_valid: assert for winner on cache hit ---
    assign mgr_instr_valid = (feed_state == 2'd1) && cache_lookup_hit && (feed_winner == 3'd0);

    assign ch_instr_valid_vec[0] = (feed_state == 2'd1) && cache_lookup_hit && (feed_winner == 3'd1);
    assign ch_instr_valid_vec[1] = (feed_state == 2'd1) && cache_lookup_hit && (feed_winner == 3'd2);
    assign ch_instr_valid_vec[2] = (feed_state == 2'd1) && cache_lookup_hit && (feed_winner == 3'd3);
    assign ch_instr_valid_vec[3] = (feed_state == 2'd1) && cache_lookup_hit && (feed_winner == 3'd4);

    // --- Byte offset within cache line for the winning requester's PC ---
    // The cache returns the full 64-byte line.  We shift it right so that the
    // bytes starting at the winner's PC offset appear at the LSBs ([47:0]).
    // Decoders always read shifted_cache_data[47:0] (first 6 bytes of the
    // shifted result), which corresponds to the correct instruction bytes.
    always_comb begin
        case (feed_winner)
            3'd0:    feed_byte_offset = mgr_pc[5:0];
            3'd1:    feed_byte_offset = ch_pc[0][5:0];
            3'd2:    feed_byte_offset = ch_pc[1][5:0];
            3'd3:    feed_byte_offset = ch_pc[2][5:0];
            3'd4:    feed_byte_offset = ch_pc[3][5:0];
            default: feed_byte_offset = '0;
        endcase
    end
    assign shifted_cache_data = cache_lookup_data >> (feed_byte_offset * 8);

    // =========================================================================
    // 9. Peripheral Interface
    // =========================================================================
    dma330_periph_intf #(
        .NUM_PERIPHERALS (NUM_PERIPHERALS),
        .NUM_CHANNELS    (NUM_CHANNELS)
    ) u_periph_intf (
        .clk               (clk),
        .rst_n             (rst_n),
        // External
        .dmareq_i          (dmareq),
        .dmaack_o          (dmaack),
        // Channel interface
        .ch_periph_req_i   (ch_periph_req),
        .ch_periph_ack_i   (ch_periph_ack_from_intf),
        .ch_periph_num     (ch_periph_num),
        .ch_periph_ack_o   (ch_periph_ack_from_intf),
        // Flush (from channel DMAFLUSHP — simplified: OR-reduce periph_req pulses)
        .flush_req_i       (|ch_periph_req),
        .flush_periph_num_i (ch_periph_num[0])  // simplified: use first channel's periph_num
    );

    // =========================================================================
    // 10. IRQ Controller
    // =========================================================================
    dma330_irq_controller #(
        .NUM_EVENTS (NUM_EVENTS)
    ) u_irq_ctrl (
        .clk            (clk),
        .rst_n          (rst_n),
        // Events
        .event_i        (event_bus),
        .fault_i        (fault_bus),
        // APB control (from regfile INTEN/INTCLR write detection)
        .inten_wdata    ({{(32-NUM_EVENTS){1'b0}}, irq_inten_wdata}),
        .inten_we       (irq_inten_we),
        .intclr_wdata   ({{(32-NUM_EVENTS){1'b0}}, irq_intclr_wdata}),
        .intclr_we      (irq_intclr_we),
        // Status
        .int_event_ris_o (),
        .intmis_o       (),
        // IRQ
        .irq_o          (irq)
    );

    // =========================================================================
    // Event bus: OR-reduce event_send from all channels
    // =========================================================================
    // Each channel's event_send_o is decoded to a one-hot ch_event_hot[N] vector.
    // event_bus is the OR of all channels' one-hot event vectors.
    assign event_bus = ch_event_hot[0] | ch_event_hot[1] |
                       ch_event_hot[2] | ch_event_hot[3];

    // =========================================================================
    // MFIFO Write/Read Arbitration
    // =========================================================================
    // 4 channels share a single MFIFO write and read port.
    // Priority arbiter: lowest channel ID wins.
    // Write path: channel DMALD → AXI read → MFIFO write (buffer load data)
    // Read path:  MFIFO read (get store data) → AXI write → channel DMAST

    // --- Write arbitration ---
    always_comb begin
        mfifo_wr_ch_id     = '0;
        mfifo_wr_valid_arr = 1'b0;
        mfifo_wr_data_arr  = '0;
        if (ch_mfifo_wr_valid[0]) begin
            mfifo_wr_ch_id = 'd0; mfifo_wr_valid_arr = 1'b1;
            mfifo_wr_data_arr = ch_mfifo_wr_data[0];
        end else if (ch_mfifo_wr_valid[1]) begin
            mfifo_wr_ch_id = 'd1; mfifo_wr_valid_arr = 1'b1;
            mfifo_wr_data_arr = ch_mfifo_wr_data[1];
        end else if (ch_mfifo_wr_valid[2]) begin
            mfifo_wr_ch_id = 'd2; mfifo_wr_valid_arr = 1'b1;
            mfifo_wr_data_arr = ch_mfifo_wr_data[2];
        end else if (ch_mfifo_wr_valid[3]) begin
            mfifo_wr_ch_id = 'd3; mfifo_wr_valid_arr = 1'b1;
            mfifo_wr_data_arr = ch_mfifo_wr_data[3];
        end
    end

    // Route MFIFO wr_ready back to the winning channel only
    always_comb begin
        ch_mfifo_wr_ready = '0;
        if (mfifo_wr_ready_arr) begin
            if (ch_mfifo_wr_valid[0])      ch_mfifo_wr_ready[0] = 1'b1;
            else if (ch_mfifo_wr_valid[1]) ch_mfifo_wr_ready[1] = 1'b1;
            else if (ch_mfifo_wr_valid[2]) ch_mfifo_wr_ready[2] = 1'b1;
            else if (ch_mfifo_wr_valid[3]) ch_mfifo_wr_ready[3] = 1'b1;
        end
    end

    // --- Read arbitration ---
    always_comb begin
        mfifo_rd_ch_id     = '0;
        mfifo_rd_valid_arr = 1'b0;
        if (ch_mfifo_rd_valid[0]) begin
            mfifo_rd_ch_id = 'd0; mfifo_rd_valid_arr = 1'b1;
        end else if (ch_mfifo_rd_valid[1]) begin
            mfifo_rd_ch_id = 'd1; mfifo_rd_valid_arr = 1'b1;
        end else if (ch_mfifo_rd_valid[2]) begin
            mfifo_rd_ch_id = 'd2; mfifo_rd_valid_arr = 1'b1;
        end else if (ch_mfifo_rd_valid[3]) begin
            mfifo_rd_ch_id = 'd3; mfifo_rd_valid_arr = 1'b1;
        end
    end

    // Broadcast MFIFO read data to all channels (only winner samples it via ready)
    assign ch_mfifo_rd_data[0] = mfifo_rd_data_arr;
    assign ch_mfifo_rd_data[1] = mfifo_rd_data_arr;
    assign ch_mfifo_rd_data[2] = mfifo_rd_data_arr;
    assign ch_mfifo_rd_data[3] = mfifo_rd_data_arr;

    // Route MFIFO rd_ready back to the winning channel only
    always_comb begin
        ch_mfifo_rd_ready = '0;
        if (mfifo_rd_ready_arr) begin
            if (ch_mfifo_rd_valid[0])      ch_mfifo_rd_ready[0] = 1'b1;
            else if (ch_mfifo_rd_valid[1]) ch_mfifo_rd_ready[1] = 1'b1;
            else if (ch_mfifo_rd_valid[2]) ch_mfifo_rd_ready[2] = 1'b1;
            else if (ch_mfifo_rd_valid[3]) ch_mfifo_rd_ready[3] = 1'b1;
        end
    end

    // =========================================================================
    // Debug Injection: APB DBGINST0/DBGINST1 → DBGCMD → decoded_instr_t → manager
    // =========================================================================
    // Shadow copies of APB-written DBGINST0/DBGINST1 (raw instruction bytes)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dbg_inst0_shadow <= '0;
            dbg_inst1_shadow <= '0;
        end else begin
            if (reg_we && reg_addr[11:0] == DBGINST0_OFFSET)
                dbg_inst0_shadow <= reg_wdata;
            if (reg_we && reg_addr[11:0] == DBGINST1_OFFSET)
                dbg_inst1_shadow <= reg_wdata;
        end
    end

    // DBGCMD write detection (combinational, used to capture injection)
    logic dbgcmd_pulse_comb;
    assign dbgcmd_pulse_comb = reg_we && (reg_addr[11:0] == DBGCMD_OFFSET);

    // Register the debug injection to ensure clean timing.
    // The combinational pulse from the APB ACCESS phase may have delta-cycle
    // issues with the struct-based decoded instruction in Icarus Verilog.
    // Registering both the pulse and the decoded instruction ensures the
    // manager always sees stable, clean values.
    logic                 dbg_inject_valid_r;
    decoded_instr_t       dbg_inject_instr_r;
    logic                 dbg_clear_fault_r;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dbg_inject_valid_r <= 1'b0;
            dbg_inject_instr_r <= '0;
            dbg_clear_fault_r  <= 1'b0;
        end else begin
            // Capture pulse and instruction on the clock edge after APB write
            dbg_inject_valid_r <= dbgcmd_pulse_comb;
            dbg_clear_fault_r  <= dbgcmd_pulse_comb && reg_wdata[0];
            if (dbgcmd_pulse_comb) begin
                dbg_inject_instr_r <= dbg_decoded_instr;
            end
        end
    end

    // Legacy signal names (kept for compatibility with other wiring)
    assign dbgcmd_pulse        = dbg_inject_valid_r;
    assign dbg_clear_fault_pulse = dbg_clear_fault_r;

    // Simplified instruction decoder for debug injection
    // DBGINST0[31:24]=byte0, [23:16]=byte1, [15:8]=byte2, [7:0]=byte3
    // DBGINST1[31:24]=byte4, [23:16]=byte5
    // PL330 6-byte instructions store 32-bit immediate in little-endian:
    //   byte2=imm[7:0], byte3=imm[15:8], byte4=imm[23:16], byte5=imm[31:24]
    // Key debug opcodes: DMAGO(0xA0), DMAEND(0x00), DMAKILL(0x01), DMANOP(0x02)
    always_comb begin
        dbg_decoded_instr = '0;
        dbg_decoded_instr.valid = 1'b1;
        case (dbg_inst0_shadow[31:24])  // byte 0 = opcode
            8'hA0: begin  // DMAGO
                dbg_decoded_instr.opcode    = OPC_DMAGO;
                dbg_decoded_instr.instr_len = 2'd3;  // 6-byte
                dbg_decoded_instr.periph_num = dbg_inst0_shadow[22:20]; // byte1[5:3]
                // Reconstruct imm32 from little-endian bytes 2-5
                dbg_decoded_instr.imm32     = {dbg_inst1_shadow[23:16],  // byte5=imm[31:24]
                                               dbg_inst1_shadow[31:24],   // byte4=imm[23:16]
                                               dbg_inst0_shadow[7:0],     // byte3=imm[15:8]
                                               dbg_inst0_shadow[15:8]};   // byte2=imm[7:0]
            end
            8'hBC: begin  // DMAMOV
                dbg_decoded_instr.opcode    = OPC_DMAMOV;
                dbg_decoded_instr.instr_len = 2'd3;
                dbg_decoded_instr.reg_select = dbg_inst0_shadow[22:21]; // byte1[3:2]
                // Same little-endian reconstruction as DMAGO
                dbg_decoded_instr.imm32     = {dbg_inst1_shadow[23:16],
                                               dbg_inst1_shadow[31:24],
                                               dbg_inst0_shadow[7:0],
                                               dbg_inst0_shadow[15:8]};
            end
            8'h00: begin  // DMAEND
                dbg_decoded_instr.opcode    = OPC_DMAEND;
                dbg_decoded_instr.instr_len = 2'd0;  // 1-byte
            end
            8'h01: begin  // DMAKILL
                dbg_decoded_instr.opcode    = OPC_DMAKILL;
                dbg_decoded_instr.instr_len = 2'd0;
            end
            8'h02: begin  // DMANOP
                dbg_decoded_instr.opcode    = OPC_DMANOP;
                dbg_decoded_instr.instr_len = 2'd0;
            end
            default: begin
                dbg_decoded_instr.opcode    = OPC_INVALID;
                dbg_decoded_instr.fault     = 1'b1;
            end
        endcase
    end

    // =========================================================================
    // PC extraction from channel regs (Icarus work-around for struct field
    // access from unpacked array in generate blocks)
    // channel_regs_t: SA[208:177] DA[176:145] CC[144:113] PC[112:81]
    // =========================================================================
    genvar gi;
    generate
        for (gi = 0; gi < NUM_CHANNELS; gi++) begin : gen_ch_pc
            assign ch_pc[gi] = ch_regs_from_ch[gi][112:81];
        end
    endgenerate

endmodule : dma330_top

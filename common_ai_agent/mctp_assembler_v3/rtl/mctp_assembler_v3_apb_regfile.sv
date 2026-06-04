// mctp_assembler_v3_apb_regfile.sv
// APB4 control/status/interrupt/counter/descriptor/debug register file.
// Implements registers.register_list + interrupts + error_handling.
// Runs entirely in the pclk domain; no CDC here — all sts_*/evt_* inputs
// are already synchronised into pclk by cdc_sync.
// Drives cfg_*/cmd_* outputs (to cdc_sync) and irq_o.
`default_nettype none
module mctp_assembler_v3_apb_regfile #(
    parameter integer CONTEXT_COUNT       = 15,
    parameter integer BASELINE_MTU_BYTES  = 64
) (
    input  wire        pclk,
    input  wire        presetn,

    // APB4 slave
    input  wire [15:0] paddr,
    input  wire        psel,
    input  wire        penable,
    input  wire        pwrite,
    input  wire [31:0] pwdata,
    input  wire  [3:0] pstrb,
    output reg  [31:0] prdata,
    output reg         pready,
    output reg         pslverr,

    // combined level interrupt
    output reg         irq_o,

    // cfg_* outputs → cdc_sync (pclk level)
    output reg         cfg_enable,
    output reg         cfg_drop_when_disabled,
    output reg         cfg_dest_filter_enable,
    output reg         cfg_accept_broadcast_eid,
    output reg         cfg_accept_null_eid,
    output reg         cfg_raw_sram_debug_read_enable,
    output reg  [7:0]  cfg_local_eid,
    output reg  [7:0]  cfg_debug_context_select,
    output reg  [12:0] cfg_tu_bytes,
    output reg  [12:0] cfg_max_message_bytes,
    output reg  [23:0] cfg_timeout_cycles,
    output reg  [15:0] cfg_sram_base,
    output reg  [15:0] cfg_sram_limit,

    // cmd_* pulses → cdc_sync
    output reg         cmd_soft_reset,
    output reg         cmd_descriptor_pop,
    output reg         cmd_counter_clear,

    // evt_* inputs from cdc_sync (pclk pulses)
    input  wire        evt_descriptor_ready,
    input  wire        evt_packet_drop,
    input  wire        evt_assembly_drop,
    input  wire        evt_context_timeout,
    input  wire        evt_sram_overflow,
    input  wire        evt_descriptor_queue_full,
    input  wire        evt_axi_write_malformed,
    input  wire        evt_axi_read_error,
    input  wire        evt_fatal_internal_error,

    // sts_* inputs from cdc_sync (pclk levels)
    input  wire        sts_descriptor_available,
    input  wire        sts_descriptor_queue_full,
    input  wire  [5:0] sts_active_context_count,
    input  wire        sts_context_active_any,
    input  wire        sts_context_error_any,
    input  wire        sts_ingress_busy,
    input  wire        sts_axi_read_busy,
    input  wire        sts_sram_write_busy,
    input  wire        sts_sram_read_busy,
    input  wire  [1:0] sts_last_drop_class,
    input  wire  [5:0] sts_last_drop_reason,
    input  wire  [3:0] sts_last_error_context_id,

    // wide read words from cdc_sync (already-synced 32-bit mux outputs)
    input  wire [31:0] cnt_block_in,
    input  wire [31:0] ctx_state_in,
    input  wire [31:0] desc_word_in,
    input  wire [31:0] debug_ctx_in
);

    // -----------------------------------------------------------------------
    // Register address offsets (SSOT registers.register_list)
    // -----------------------------------------------------------------------
    localparam [15:0] ADDR_CONTROL        = 16'h0000; // offset   0
    localparam [15:0] ADDR_CFG_TU         = 16'h0004; // offset   4
    localparam [15:0] ADDR_CFG_TIMEOUT    = 16'h0008; // offset   8
    localparam [15:0] ADDR_SRAM_BASE      = 16'h000C; // offset  12
    localparam [15:0] ADDR_SRAM_LIMIT     = 16'h0010; // offset  16
    localparam [15:0] ADDR_STATUS         = 16'h0020; // offset  32
    localparam [15:0] ADDR_INTR_RAW       = 16'h0100; // offset 256
    localparam [15:0] ADDR_INTR_ENABLE    = 16'h0104; // offset 260
    localparam [15:0] ADDR_INTR_STATUS    = 16'h0108; // offset 264
    localparam [15:0] ADDR_INTR_CLEAR     = 16'h010C; // offset 268
    localparam [15:0] ADDR_CNT_BASE       = 16'h0200; // offset 512  (CNT_TLP_SEEN block)
    localparam [15:0] ADDR_CNT_END        = 16'h027C; // inclusive end of counter block
    localparam [15:0] ADDR_DESC_VALID     = 16'h0300; // offset 768  (DESC_VALID + body)
    localparam [15:0] ADDR_DESC_END       = 16'h034C; // inclusive end of DESC body
    localparam [15:0] ADDR_DEBUG_CTX      = 16'h0380; // offset 896
    localparam [15:0] ADDR_CTX_STATE_BASE = 16'h0400; // offset 1024 (CTX_STATE[0])
    // CTX_STATE stride 0x40 × CONTEXT_COUNT = 0x0400..0x05C0

    // -----------------------------------------------------------------------
    // APB access helpers
    // -----------------------------------------------------------------------
    wire apb_access  = psel & penable;
    wire apb_write   = apb_access & pwrite;
    wire apb_read    = apb_access & ~pwrite;

    // address decode helpers
    wire wr_control       = apb_write & (paddr == ADDR_CONTROL);
    wire rd_control       = apb_read  & (paddr == ADDR_CONTROL);
    wire wr_cfg_tu        = apb_write & (paddr == ADDR_CFG_TU);
    wire rd_cfg_tu        = apb_read  & (paddr == ADDR_CFG_TU);
    wire wr_cfg_timeout   = apb_write & (paddr == ADDR_CFG_TIMEOUT);
    wire rd_cfg_timeout   = apb_read  & (paddr == ADDR_CFG_TIMEOUT);
    wire wr_sram_base     = apb_write & (paddr == ADDR_SRAM_BASE);
    wire rd_sram_base     = apb_read  & (paddr == ADDR_SRAM_BASE);
    wire wr_sram_limit    = apb_write & (paddr == ADDR_SRAM_LIMIT);
    wire rd_sram_limit    = apb_read  & (paddr == ADDR_SRAM_LIMIT);
    wire rd_status        = apb_read  & (paddr == ADDR_STATUS);
    wire rd_intr_raw      = apb_read  & (paddr == ADDR_INTR_RAW);
    wire wr_intr_enable   = apb_write & (paddr == ADDR_INTR_ENABLE);
    wire rd_intr_enable   = apb_read  & (paddr == ADDR_INTR_ENABLE);
    wire rd_intr_status   = apb_read  & (paddr == ADDR_INTR_STATUS);
    wire wr_intr_clear    = apb_write & (paddr == ADDR_INTR_CLEAR);
    wire rd_intr_clear    = apb_read  & (paddr == ADDR_INTR_CLEAR);
    wire rd_cnt           = apb_read  & (paddr >= ADDR_CNT_BASE) & (paddr <= ADDR_CNT_END);
    wire rd_desc          = apb_read  & (paddr >= ADDR_DESC_VALID) & (paddr <= ADDR_DESC_END);
    wire rd_debug_ctx     = apb_read  & (paddr == ADDR_DEBUG_CTX);
    wire rd_ctx_state     = apb_read  & (paddr >= ADDR_CTX_STATE_BASE) &
                            (paddr < (ADDR_CTX_STATE_BASE + 16'(CONTEXT_COUNT) * 16'h40));

    // legal address detection for pslverr
    wire addr_legal = (paddr == ADDR_CONTROL)     |
                      (paddr == ADDR_CFG_TU)       |
                      (paddr == ADDR_CFG_TIMEOUT)  |
                      (paddr == ADDR_SRAM_BASE)     |
                      (paddr == ADDR_SRAM_LIMIT)    |
                      (paddr == ADDR_STATUS)        |
                      (paddr == ADDR_INTR_RAW)      |
                      (paddr == ADDR_INTR_ENABLE)   |
                      (paddr == ADDR_INTR_STATUS)   |
                      (paddr == ADDR_INTR_CLEAR)    |
                      ((paddr >= ADDR_CNT_BASE)     & (paddr <= ADDR_CNT_END))  |
                      ((paddr >= ADDR_DESC_VALID)   & (paddr <= ADDR_DESC_END)) |
                      (paddr == ADDR_DEBUG_CTX)     |
                      ((paddr >= ADDR_CTX_STATE_BASE) &
                       (paddr < (ADDR_CTX_STATE_BASE + 16'(CONTEXT_COUNT) * 16'h40)));

    // RO addresses (writes to these are illegal)
    wire addr_ro = (paddr == ADDR_STATUS)     |
                   (paddr == ADDR_INTR_RAW)   |
                   (paddr == ADDR_INTR_STATUS)|
                   ((paddr >= ADDR_CNT_BASE)  & (paddr <= ADDR_CNT_END))  |
                   ((paddr >= ADDR_DESC_VALID)& (paddr <= ADDR_DESC_END)) |
                   (paddr == ADDR_DEBUG_CTX)  |
                   ((paddr >= ADDR_CTX_STATE_BASE) &
                    (paddr < (ADDR_CTX_STATE_BASE + 16'(CONTEXT_COUNT) * 16'h40)));

    // -----------------------------------------------------------------------
    // CONTROL register storage  (offset 0x000, reset 0)
    // CONTROL[0]    = enable
    // CONTROL[1]    = drop_when_disabled
    // CONTROL[2]    = soft_reset  (self-clearing pulse, not stored)
    // CONTROL[3]    = dest_filter_enable
    // CONTROL[4]    = accept_broadcast_eid
    // CONTROL[5]    = accept_null_eid
    // CONTROL[6]    = raw_sram_debug_read_enable
    // CONTROL[7]    = descriptor_pop  (self-clearing pulse, not stored)
    // CONTROL[8]    = counter_clear   (self-clearing pulse, not stored)
    // CONTROL[23:16]= local_eid
    // CONTROL[31:24]= debug_context_select
    // -----------------------------------------------------------------------
    // cfg_* are the persistent storage; cmd_* are one-cycle pulses derived
    // from the write then immediately self-clear.

    // cfg_* latched registers — byte-strobe applied field-by-field
    // CONTROL layout:
    //  [0]     enable               (pstrb[0])
    //  [1]     drop_when_disabled   (pstrb[0])
    //  [2]     soft_reset           (pstrb[0]) — pulse only, not stored
    //  [3]     dest_filter_enable   (pstrb[0])
    //  [4]     accept_broadcast_eid (pstrb[0])
    //  [5]     accept_null_eid      (pstrb[0])
    //  [6]     raw_sram_debug_read_enable (pstrb[0])
    //  [7]     descriptor_pop       (pstrb[0]) — pulse only, not stored
    //  [8]     counter_clear        (pstrb[1]) — pulse only, not stored
    //  [23:16] local_eid            (pstrb[2])
    //  [31:24] debug_context_select (pstrb[3])
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cfg_enable                     <= 1'b0;
            cfg_drop_when_disabled         <= 1'b0;
            cfg_dest_filter_enable         <= 1'b0;
            cfg_accept_broadcast_eid       <= 1'b0;
            cfg_accept_null_eid            <= 1'b0;
            cfg_raw_sram_debug_read_enable <= 1'b0;
            cfg_local_eid                  <= 8'h00;
            cfg_debug_context_select       <= 8'h00;
        end else if (wr_control) begin
            if (pstrb[0]) begin
                cfg_enable                     <= pwdata[0];
                cfg_drop_when_disabled         <= pwdata[1];
                // pwdata[2] = soft_reset: pulse only, not stored here
                cfg_dest_filter_enable         <= pwdata[3];
                cfg_accept_broadcast_eid       <= pwdata[4];
                cfg_accept_null_eid            <= pwdata[5];
                cfg_raw_sram_debug_read_enable <= pwdata[6];
                // pwdata[7] = descriptor_pop: pulse only, not stored here
            end
            // pwdata[8] = counter_clear in pstrb[1]: pulse only, not stored
            if (pstrb[2]) cfg_local_eid          <= pwdata[23:16];
            if (pstrb[3]) cfg_debug_context_select <= pwdata[31:24];
        end
    end

    // cmd_soft_reset / cmd_descriptor_pop / cmd_counter_clear: one-cycle pulses
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cmd_soft_reset      <= 1'b0;
            cmd_descriptor_pop  <= 1'b0;
            cmd_counter_clear   <= 1'b0;
        end else begin
            cmd_soft_reset     <= wr_control & pstrb[0] & pwdata[2];
            cmd_descriptor_pop <= wr_control & pstrb[0] & pwdata[7];
            cmd_counter_clear  <= wr_control & pstrb[1] & pwdata[8];
        end
    end

    // -----------------------------------------------------------------------
    // CFG_TU register (offset 0x004, reset 0x1000_0040 = 268435520)
    // [12:0]  = transmission_unit_bytes  reset=64   (pstrb[0] bits[7:0], pstrb[1] bits[12:8])
    // [15:13] = reserved
    // [28:16] = max_message_bytes        reset=4096 (pstrb[2] bits[23:16], pstrb[3] bits[28:24])
    // [31:29] = reserved
    // -----------------------------------------------------------------------
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cfg_tu_bytes          <= 13'(BASELINE_MTU_BYTES);
            cfg_max_message_bytes <= 13'd4096;
        end else if (wr_cfg_tu) begin
            if (pstrb[0]) cfg_tu_bytes[7:0]          <= pwdata[7:0];
            if (pstrb[1]) cfg_tu_bytes[12:8]          <= pwdata[12:8];
            if (pstrb[2]) cfg_max_message_bytes[7:0]  <= pwdata[23:16];
            if (pstrb[3]) cfg_max_message_bytes[12:8] <= pwdata[28:24];
        end
    end

    // -----------------------------------------------------------------------
    // CFG_TIMEOUT register (offset 0x008, reset 0)
    // [23:0]  = assembly_timeout_cycles  reset=0
    // [31:24] = reserved
    // -----------------------------------------------------------------------
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cfg_timeout_cycles <= 24'd0;
        end else if (wr_cfg_timeout) begin
            if (pstrb[0]) cfg_timeout_cycles[7:0]  <= pwdata[7:0];
            if (pstrb[1]) cfg_timeout_cycles[15:8]  <= pwdata[15:8];
            if (pstrb[2]) cfg_timeout_cycles[23:16] <= pwdata[23:16];
            // pstrb[3] covers reserved bits [31:24] — ignore
        end
    end

    // -----------------------------------------------------------------------
    // SRAM_BASE register (offset 0x00C, reset 0)
    // [15:0]  = sram_base  reset=0
    // [31:16] = reserved
    // -----------------------------------------------------------------------
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cfg_sram_base <= 16'h0000;
        end else if (wr_sram_base) begin
            if (pstrb[0]) cfg_sram_base[7:0]  <= pwdata[7:0];
            if (pstrb[1]) cfg_sram_base[15:8]  <= pwdata[15:8];
            // pstrb[2/3] covers reserved bits [31:16] — ignore
        end
    end

    // -----------------------------------------------------------------------
    // SRAM_LIMIT register (offset 0x010, reset 65535)
    // [15:0]  = sram_limit  reset=0xFFFF
    // [31:16] = reserved
    // -----------------------------------------------------------------------
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cfg_sram_limit <= 16'hFFFF;
        end else if (wr_sram_limit) begin
            if (pstrb[0]) cfg_sram_limit[7:0]  <= pwdata[7:0];
            if (pstrb[1]) cfg_sram_limit[15:8]  <= pwdata[15:8];
            // pstrb[2/3] covers reserved bits [31:16] — ignore
        end
    end

    // -----------------------------------------------------------------------
    // STATUS register (offset 0x020, read-only) — assembled combinatorially
    // from sts_* inputs already in pclk domain.
    //
    // [0]     ingress_busy
    // [1]     axi_read_busy
    // [2]     sram_write_busy
    // [3]     sram_read_busy
    // [4]     descriptor_available
    // [5]     descriptor_queue_full
    // [6]     context_active_any
    // [7]     context_error_any
    // [8]     packet_drop_seen    (sticky, set by evt_packet_drop)
    // [9]     assembly_drop_seen  (sticky, set by evt_assembly_drop)
    // [15:10] active_context_count
    // [17:16] last_drop_class
    // [23:18] last_drop_reason
    // [27:24] last_error_context_id
    // [31:28] reserved = 0
    // -----------------------------------------------------------------------
    reg packet_drop_seen_r;
    reg assembly_drop_seen_r;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            packet_drop_seen_r   <= 1'b0;
            assembly_drop_seen_r <= 1'b0;
        end else begin
            if (evt_packet_drop)   packet_drop_seen_r   <= 1'b1;
            if (evt_assembly_drop) assembly_drop_seen_r <= 1'b1;
        end
    end

    wire [31:0] status_word = {
        4'h0,                                    // [31:28] reserved
        sts_last_error_context_id,               // [27:24]
        sts_last_drop_reason,                    // [23:18]
        sts_last_drop_class,                     // [17:16]
        sts_active_context_count[5:0],           // [15:10]
        assembly_drop_seen_r,                    // [9]
        packet_drop_seen_r,                      // [8]
        sts_context_error_any,                   // [7]
        sts_context_active_any,                  // [6]
        sts_descriptor_queue_full,               // [5]
        sts_descriptor_available,                // [4]
        sts_sram_read_busy,                      // [3]
        sts_sram_write_busy,                     // [2]
        sts_axi_read_busy,                       // [1]
        sts_ingress_busy                         // [0]
    };

    // -----------------------------------------------------------------------
    // Interrupt registers
    //
    // intr_raw[8:0]:  W1C sticky bits, set by evt_* pulses
    //   [0] descriptor_ready
    //   [1] packet_drop
    //   [2] assembly_drop
    //   [3] context_timeout
    //   [4] sram_overflow
    //   [5] descriptor_queue_full
    //   [6] axi_write_malformed
    //   [7] axi_read_error
    //   [8] fatal_internal_error
    //
    // intr_enable[8:0]: rw mask
    // intr_status[8:0] = intr_raw & intr_enable  (combinatorial)
    // irq_o            = |intr_status            (level)
    // -----------------------------------------------------------------------
    reg  [8:0] intr_raw;
    reg  [8:0] intr_enable;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            intr_raw <= 9'h000;
        end else begin
            // set bits from event pulses
            if (evt_descriptor_ready)      intr_raw[0] <= 1'b1;
            if (evt_packet_drop)           intr_raw[1] <= 1'b1;
            if (evt_assembly_drop)         intr_raw[2] <= 1'b1;
            if (evt_context_timeout)       intr_raw[3] <= 1'b1;
            if (evt_sram_overflow)         intr_raw[4] <= 1'b1;
            if (evt_descriptor_queue_full) intr_raw[5] <= 1'b1;
            if (evt_axi_write_malformed)   intr_raw[6] <= 1'b1;
            if (evt_axi_read_error)        intr_raw[7] <= 1'b1;
            if (evt_fatal_internal_error)  intr_raw[8] <= 1'b1;
            // W1C via INTR_CLEAR write: clear bits where pwdata[i]==1
            if (wr_intr_clear) begin
                if (pstrb[0]) intr_raw[7:0] <= intr_raw[7:0] & ~pwdata[7:0];
                if (pstrb[1]) intr_raw[8]   <= intr_raw[8]   & ~pwdata[8];
            end
        end
    end

    // INTR_ENABLE [8:0] spans pstrb[0] (bits[7:0]) and pstrb[1] (bit[8])
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            intr_enable <= 9'h000;
        end else if (wr_intr_enable) begin
            if (pstrb[0]) intr_enable[7:0] <= pwdata[7:0];
            if (pstrb[1]) intr_enable[8]   <= pwdata[8];
            // pstrb[2/3] covers reserved bits [31:9] — ignore
        end
    end

    wire [8:0] intr_status = intr_raw & intr_enable;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            irq_o <= 1'b0;
        end else begin
            irq_o <= |intr_status;
        end
    end

    // -----------------------------------------------------------------------
    // APB read data mux and pready / pslverr
    // pready is driven combinatorially (single-cycle APB); pslverr on illegal
    // or write-to-RO access.
    // -----------------------------------------------------------------------
    always @(*) begin
        pready  = 1'b0;
        pslverr = 1'b0;
        prdata  = 32'h0000_0000;

        if (apb_access) begin
            pready = 1'b1;

            if (!addr_legal || (pwrite && addr_ro)) begin
                // illegal address or write to read-only register
                pslverr = 1'b1;
            end else if (apb_read) begin
                if (rd_control) begin
                    prdata = {cfg_debug_context_select,
                              cfg_local_eid,
                              7'h00,
                              1'b0,         // counter_clear (self-clearing, reads 0)
                              1'b0,         // descriptor_pop (self-clearing, reads 0)
                              cfg_raw_sram_debug_read_enable,
                              cfg_accept_null_eid,
                              cfg_accept_broadcast_eid,
                              cfg_dest_filter_enable,
                              1'b0,         // soft_reset (self-clearing, reads 0)
                              cfg_drop_when_disabled,
                              cfg_enable};
                end else if (rd_cfg_tu) begin
                    prdata = {3'h0, cfg_max_message_bytes, 3'h0, cfg_tu_bytes};
                end else if (rd_cfg_timeout) begin
                    prdata = {8'h00, cfg_timeout_cycles};
                end else if (rd_sram_base) begin
                    prdata = {16'h0000, cfg_sram_base};
                end else if (rd_sram_limit) begin
                    prdata = {16'h0000, cfg_sram_limit};
                end else if (rd_status) begin
                    prdata = status_word;
                end else if (rd_intr_raw) begin
                    prdata = {23'h0, intr_raw};
                end else if (rd_intr_enable) begin
                    prdata = {23'h0, intr_enable};
                end else if (rd_intr_status) begin
                    prdata = {23'h0, intr_status};
                end else if (rd_intr_clear) begin
                    // INTR_CLEAR reads back 0 (W1C register, not stored)
                    prdata = 32'h0000_0000;
                end else if (rd_cnt) begin
                    // counter block: cdc_sync presents selected 32-bit word
                    prdata = cnt_block_in;
                end else if (rd_desc) begin
                    // descriptor block: cdc_sync presents selected 32-bit word
                    prdata = desc_word_in;
                end else if (rd_debug_ctx) begin
                    prdata = debug_ctx_in;
                end else if (rd_ctx_state) begin
                    prdata = ctx_state_in;
                end
            end
            // write path: pready already set, no prdata needed
        end
    end

endmodule
`default_nettype wire

`timescale 1ns/1ps
// PCIe Message Receiver with Assembly Support
// Receives AXI write transactions and assembles fragmented messages
// Header format: [127:126]=FragType, [125:124]=PKT_SN, [123:120]=MSG_TAG, [119:0]=TLP

module pcie_msg_receiver (
    input wire clk,
    input wire rst_n,

    // AXI Write Address Channel
    input wire         axi_awvalid,
    input wire  [63:0] axi_awaddr,
    input wire  [11:0] axi_awlen,
    input wire  [2:0]  axi_awsize,
    input wire  [1:0]  axi_awburst,
    output reg         axi_awready,

    // AXI Write Data Channel
    input wire         axi_wvalid,
    input wire  [255:0] axi_wdata,
    input wire  [31:0] axi_wstrb,
    input wire         axi_wlast,
    output reg         axi_wready,

    // AXI Write Response Channel
    output reg        axi_bvalid,
    output reg [1:0]  axi_bresp,
    input wire        axi_bready,

    // SRAM Write Interface
    output reg         sram_wen,
    output reg  [9:0]  sram_waddr,
    output reg  [255:0] sram_wdata,

    // Message info output
    output reg [127:0] msg_header,
    output reg         msg_valid,
    output reg [11:0]  msg_length,  // in beats
    output reg         assembled_valid,
    output reg [3:0]   assembled_tag,

    // SFR Debug Registers
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29,

    // SFR Control Register
    input wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_CONTROL15,

    // SFR Interrupt Registers (15 queues)
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14,

    // Queue Write Pointer Registers (15 queues)
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_1,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_2,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_3,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_5,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_6,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_7,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_8,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_9,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_10,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_11,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_12,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_13,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_14,

    // Queue Initial Address Registers (15 queues)
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14,

    // Interrupt signal
    output reg         o_msg_interrupt
);

    // Fragment type definitions
    localparam S_PKT  = 2'b10;  // Start
    localparam M_PKT  = 2'b00;  // Middle
    localparam L_PKT  = 2'b01;  // Last
    localparam SG_PKT = 2'b11;  // Single (no assembly needed)

    // State machine
    localparam IDLE      = 3'b000;
    localparam W_DATA    = 3'b001;
    localparam W_RESP    = 3'b010;
    localparam ASSEMBLE  = 3'b011;
    localparam SRAM_WR   = 3'b100;

    reg [2:0] state;
    reg       wptr_updated_for_frag;
    reg [63:0] write_addr;
    reg [11:0] beat_count;
    reg [11:0] total_beats;
    reg [9:0] sram_addr_cnt;

    // Header fields
    reg [1:0]  frag_type;
    reg [1:0]  pkt_sn;
    reg [3:0]  msg_tag;
    reg [119:0] tlp_header;
    reg [3:0]  header_version;

    // Expected header version
    localparam EXPECTED_HDR_VER = 4'b0001;

    // Function to calculate OHC size based on OHC field [11:8]
    function automatic [3:0] calc_ohc_size;
        input [3:0] ohc_field;  // header[11:8]
        begin
            calc_ohc_size = 0;
            if (ohc_field[0]) calc_ohc_size = calc_ohc_size + 2;  // OHC-A: +2DW
            if (ohc_field[1]) calc_ohc_size = calc_ohc_size + 2;  // OHC-B: +2DW
            if (ohc_field[2]) calc_ohc_size = calc_ohc_size + 2;  // OHC-C: +2DW
            if (ohc_field[3]) calc_ohc_size = calc_ohc_size + 1;  // OHC-E: +1DW
        end
    endfunction

    // Assembly Queue (15 queues, index 0-14)
    reg [14:0] queue_valid;              // Queue in use
    reg [1:0]  queue_state [0:14];       // 0=IDLE, 1=WAIT_M, 2=WAIT_L, 3=COMPLETE
    reg [1:0]  queue_expected_sn [0:14]; // Next expected PKT_SN
    reg [7:0]  queue_frag_count [0:14];  // Number of fragments
    reg [11:0] queue_total_beats [0:14]; // Total beats across all fragments
    reg [31:0] queue_timeout [0:14];     // Timeout counter for each queue
    reg [7:0]  src_endpoint_id [0:14];   // Source ID for each queue
    reg        tag_owner [0:14];   // Tag Owner bit for each queue
    reg [2:0]  queue_tag [0:14];         // TAG (3 bits) for each queue
    reg [15:0] queue_tx_size [0:14];     // Transmission size (TLP length field) for S/M packets (16-bit)
    reg [15:0] queue_accumulated_tlp_bytes [0:14]; // Accumulated TLP payload bytes

    // Fragment data storage: 15 queues x 16 fragments x 16 beats
    reg [255:0] queue_data [0:14] [0:255];
    reg [11:0]  queue_write_ptr [0:14];  // Write pointer for current queue

    // Current fragment buffer
    reg [255:0] current_frag [0:63];
    reg [11:0] current_frag_beats;
    reg [3:0] current_queue_idx;

    // Assembly write control
    reg [11:0] asm_beat_count;
    reg [11:0] asm_total_beats;
    reg [1:0] asm_padding_bytes;  // Padding bytes from L_PKT header[53:52]
    reg [7:0] asm_tlp_length_dw;  // TLP length in DW for SG_PKT
    reg [15:0] tlp_len_dw;
    reg asm_is_sg_pkt;  // Flag to indicate SG_PKT (for WPTR calculation)
    reg [15:0] asm_accumulated_tlp_bytes;  // Accumulated TLP length for multi-fragment

    // Temporary variables for error checking
    reg [7:0] dest_id;
    reg [11:0] expected_beats;
    reg [31:0] total_bytes;
    reg [15:0] tx_size_dw;       // Extended to 16-bit for 1024B support (256 DW)
    reg [31:0] tx_size_bytes;
    reg [1:0] padding_bytes;
    reg [11:0] payload_beats_with_padding;
    
    // SRAM Write Alignment Registers
    reg [511:0] sram_accumulator;
    reg [9:0]   sram_accumulator_bytes;
    reg [5:0]   sram_header_ohc_bytes;
    reg         sram_alignment_init;

    integer i;
    integer j;
    reg [3:0] allocated_queue_idx;
    reg [2:0] tag_field;
    reg to_field;
    reg [7:0] src_id_field;

    // Function to find or allocate queue based on TAG, TO, SRC_ID
    function [3:0] find_queue;
        input [2:0] tag;
        input to;
        input [7:0] src_id;
        integer k;
        begin
            find_queue = 4'hF;  // Invalid queue by default

            // First, try to find existing queue with matching context
            // Priority: lowest queue number first (Q0, Q1, Q2, ...)
            for (k = 0; k < 15; k = k + 1) begin
                if (queue_valid[k] && queue_state[k] != 2'b00 &&
                    queue_tag[k] == tag &&
                    tag_owner[k] == to &&
                    src_endpoint_id[k] == src_id &&
                    find_queue == 4'hF) begin
                    find_queue = k[3:0];  // Use first matching queue
                end
            end

            // If not found, allocate new queue
            if (find_queue == 4'hF) begin
                for (k = 0; k < 15; k = k + 1) begin
                    if (!queue_valid[k] && find_queue == 4'hF) begin
                        find_queue = k[3:0];
                    end
                end
            end
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        //$display("DEBUG_ALWAYS: clk=%b, rst_n=%b", clk, rst_n);
        // Reset
        if (!rst_n) begin
            state <= IDLE;
            axi_awready <= 1'b0;
            axi_wready <= 1'b0;
            axi_bvalid <= 1'b0;
            $display("[%0t] [MSG_RX] Reset active", $time);
            write_addr <= 64'h0;
            beat_count <= 12'h0;
            total_beats <= 12'h0;
            sram_wen <= 1'b0;
            sram_waddr <= 10'h0;
            sram_wdata <= 256'h0;
            msg_header <= 128'h0;
            msg_valid <= 1'b0;
            msg_length <= 12'h0;
            sram_addr_cnt <= 10'h0;
            assembled_valid <= 1'b0;
            assembled_tag <= 4'h0;

            // Initialize SFR registers
            PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29 <= 32'h0;

            // Initialize Interrupt registers (all 15 queues)
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14 <= 32'h0;

            // Initialize Queue Write Pointers (all 15 queues)
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_1 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_2 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_3 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_5 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_6 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_7 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_8 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_9 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_10 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_11 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_12 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_13 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_14 <= 32'h0;

            // Initialize Queue Initial Address Registers (all 15 queues)
            // Queue N address = N * 64 beats * 32 bytes
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0 <= (0 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1 <= (1 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2 <= (2 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3 <= (3 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4 <= (4 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5 <= (5 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6 <= (6 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7 <= (7 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8 <= (8 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9 <= (9 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10 <= (10 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11 <= (11 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12 <= (12 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13 <= (13 * 64 * 32);
            PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14 <= (14 * 64 * 32);

            // Initialize interrupt signal
            o_msg_interrupt <= 1'b0;

            // Initialize assembly queues
            queue_valid <= 15'h0;
            for (i = 0; i < 15; i = i + 1) begin
                queue_state[i] <= 2'b00;
                queue_expected_sn[i] <= 2'b00;
                queue_frag_count[i] <= 8'h0;
                queue_total_beats[i] <= 12'h0;
                queue_write_ptr[i] <= 12'h0;
                queue_timeout[i] <= 32'h0;
                src_endpoint_id[i] <= 8'h0;
                tag_owner[i] <= 1'b0;
                queue_tag[i] <= 3'h0;
                queue_tx_size[i] <= 16'h0;
                queue_accumulated_tlp_bytes[i] <= 16'h0;
            end

            current_frag_beats <= 12'h0;
            current_queue_idx <= 4'h0;
            asm_beat_count <= 12'h0;
            asm_total_beats <= 12'h0;
            asm_padding_bytes <= 2'h0;
            asm_tlp_length_dw <= 8'h0;
            asm_is_sg_pkt <= 1'b0;
            asm_accumulated_tlp_bytes <= 16'h0;
            
            // Initialize SRAM alignment registers
            sram_alignment_init <= 1'b0;
            sram_accumulator <= 512'h0;
            sram_accumulator_bytes <= 10'h0;
            sram_header_ohc_bytes <= 6'h0;

        end else begin
            // Monitor AWVALID
            if (axi_awvalid) $display("[%0t] [MSG_RX] MONITOR: AWVALID is HIGH", $time);
            
            // AXI Write Address Channel
            if (axi_awready && axi_awvalid) begin
                axi_awready <= 1'b0;
            end
            // Default
            sram_wen <= 1'b0;
            msg_valid <= 1'b0;
            assembled_valid <= 1'b0;

            // Timeout monitoring for all active queues
            for (i = 0; i < 15; i = i + 1) begin
                if (queue_valid[i] && queue_state[i] != 2'b00) begin
                    queue_timeout[i] <= queue_timeout[i] + 1;
                    // Timeout threshold: 10000 cycles (~100us at 100MHz)
                    if (queue_timeout[i] >= 32'd10000) begin
                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[23:16] <=
                            PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[23:16] + 1;
                        $display("[%0t] [TIMEOUT] ERROR: Queue %0d timeout (counter=%0d)",
                                 $time, i, queue_timeout[i]);
                        // Clear the timed-out queue
                        queue_valid[i] <= 1'b0;
                        queue_state[i] <= 2'b00;
                        queue_timeout[i] <= 32'h0;
                    end
                end
            end

            case (state)
                IDLE: begin
                    axi_bvalid <= (axi_bvalid && !axi_bready) ? 1'b1 : 1'b0;

                    if (axi_awvalid) begin
                        $display("DEBUG_FORCE: IDLE state saw AWVALID. Addr=0x%h", axi_awaddr);
                        // Latch address and control signals
                        write_addr <= axi_awaddr;
                        beat_count <= 12'h0;
                        total_beats <= axi_awlen + 1;
                        current_frag_beats <= 12'h0;
                        
                        axi_awready <= 1'b1;
                        state <= W_DATA;
`ifdef DEBUG
                        $display("[%0t] [IDLE] AWVALID received. Addr=0x%h, Len=%0d", $time, axi_awaddr, axi_awlen + 1);
                        $display("[%0t] [MSG_RX] Received write addr: 0x%h, len=%0d beats",
                                 $time, axi_awaddr, axi_awlen + 1);
`endif
                    end else begin
                        axi_awready <= 1'b1;
                        // $display("[%0t] [MSG_RX] IDLE: awready=1, waiting for awvalid", $time);
                    end
                end

                W_DATA: begin
                    axi_wready <= 1'b1;

                    if (axi_wvalid) begin  // axi_wready is always 1 in W_DATA state
                        // First beat: extract header
                        if (beat_count == 0) begin
                            frag_type  <= axi_wdata[127:126];
                            pkt_sn     <= axi_wdata[125:124];
                            msg_tag    <= axi_wdata[123:120];
                            tlp_header <= axi_wdata[119:0];
                            msg_header <= axi_wdata[127:0];
                            header_version <= axi_wdata[99:96];  // Extract header version

`ifdef DEBUG
                            $display("[%0t] [MSG_RX] Header: Type=%0s, SN=%0d, TAG=%0h, Ver=%0h, TLP=0x%h",
                                     $time,
                                     (axi_wdata[127:126] == S_PKT) ? "S" :
                                     (axi_wdata[127:126] == M_PKT) ? "M" :
                                     (axi_wdata[127:126] == L_PKT) ? "L" : "SG",
                                     axi_wdata[125:124], axi_wdata[123:120],
                                     axi_wdata[99:96], axi_wdata[119:0]);

                            // ========================================
                            // Check header version (DEBUG)
                            // ========================================
                            $display("[%0t] [MSG_RX] === HEADER VERSION CHECK ===", $time);
                            $display("[%0t] [MSG_RX]   Expected Version: 0x%h (EXPECTED_HDR_VER)", $time, EXPECTED_HDR_VER);
                            $display("[%0t] [MSG_RX]   Received Version: 0x%h (bits [99:96])", $time, axi_wdata[99:96]);
                            $display("[%0t] [MSG_RX]   Match: %s", $time, (axi_wdata[99:96] == EXPECTED_HDR_VER) ? "YES ✓" : "NO ✗");
`endif

                            if (axi_wdata[99:96] != EXPECTED_HDR_VER) begin
                                PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] <=
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] + 1;
                                $display("[%0t] [MSG_RX] ERROR: BAD HEADER VERSION DETECTED", $time);
                                $display("[%0t] [MSG_RX] ERROR: Expected=0x%h, Received=0x%h",
                                         $time, EXPECTED_HDR_VER, axi_wdata[99:96]);
`ifdef DEBUG
                                $display("[%0t] [MSG_RX] Error counter incremented to: %0d",
                                         $time, PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] + 1);
                                $display("[%0t] [MSG_RX] DEBUG_31[31:24] = 0x%h", $time, PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] + 1);
`endif

                                // Set error interrupt (INTR_STATUS[3] = all queue error)
                                PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3] <= 1'b1;
                                o_msg_interrupt <= 1'b1;
                            end

                            // Check unknown destination ID (if control bit is disabled)
                            if (!PCIE_SFR_AXI_MSG_HANDLER_RX_CONTROL15[8]) begin
                                dest_id = axi_wdata[111:104];
                                if (dest_id != 8'h00 && dest_id != 8'hFF &&
                                    dest_id != 8'h10 && dest_id != 8'h11) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[23:16] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[23:16] + 1;
                                    $display("[%0t] [MSG_RX] ERROR: Unknown destination ID=0x%h",
                                             $time, dest_id);
                                end
                            end

                            // Check tag owner error (TAG=7 with TO=0)
                            // Header: [123]=TO, [122:120]=TAG
                            if (axi_wdata[122:120] == 3'h7 && axi_wdata[123] == 1'b0) begin
                                PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[15:8] <=
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[15:8] + 1;
                                $display("[%0t] [MSG_RX] ERROR: Tag owner error (TAG=7, TO=0)", $time);
                                $display("[%0t] [MSG_RX]   TAG=%0d, TO=%0b (expected TO=1 for TAG=7)",
                                         $time, axi_wdata[122:120], axi_wdata[123]);
                            end

                            // Check unsupported TX unit (TLP length field [31:24])
                            // Valid range: 64B ~ 1024B
                            // TLP length is in DW (4 bytes): 64B=16 DW=0x10, 1024B=256 DW=0x100
                            // Extended to 16-bit [39:24] to support up to 1024B (256 DW)
                            tx_size_dw = axi_wdata[39:24];
                            tx_size_bytes = {16'h0, tx_size_dw} * 4;

                            if (tx_size_bytes < 64 || tx_size_bytes > 1024) begin
                                PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0] <=
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0] + 1;
                                $display("[%0t] [MSG_RX] ERROR: Unsupported TX unit size (%0dB, valid: 64B-1024B)",
                                         $time, tx_size_bytes);
                            end

                            // Check size mismatch (compare axi_awsize with TLP length + OHC)
                            // Expected: 2^axi_awsize bytes per beat
                            // TLP length is in DW (4 bytes) and represents payload only
                            // Total AXI transfer = Header(4DW) + OHC + Payload
                            if (axi_awsize == 3'd5) begin  // 32B per beat
                                reg [3:0] ohc_size_dw;
                                reg [31:0] total_transfer_dw;
                                reg [31:0] total_transfer_bytes;

                                ohc_size_dw = calc_ohc_size(axi_wdata[11:8]);
                                total_transfer_dw = 4 + {28'h0, ohc_size_dw} + {16'h0, axi_wdata[39:24]};
                                total_transfer_bytes = total_transfer_dw * 4;
                                expected_beats = (total_transfer_bytes + 31) / 32;  // Round up

                                if (total_beats != expected_beats) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0] + 1;
                                    $display("[%0t] [MSG_RX] ERROR: Size mismatch (TLP_len=%0d DW, OHC=%0d DW, beats=%0d, expected=%0d)",
                                             $time, axi_wdata[39:24], ohc_size_dw, total_beats, expected_beats);
                                end
                            end
                            
                            // [FIX] Capture TLP Length (Payload Length) from Header [39:24]
                            // This is in DW (4 bytes). We need this for accurate WPTR update later.
                            tlp_len_dw <= axi_wdata[39:24];
                        end

                        // Store fragment data in temporary buffer
                        if (beat_count < 64) begin
                            current_frag[beat_count] <= axi_wdata;
                        end

`ifdef DEBUG
                        $display("[%0t] [MSG_RX] Beat %0d: data=0x%h, last=%0b",
                                 $time, beat_count, axi_wdata, axi_wlast);
`endif

                        beat_count <= beat_count + 1;
                        current_frag_beats <= current_frag_beats + 1;

                        if (axi_wlast) begin
                        axi_wready <= 1'b0;
                        axi_bvalid <= 1'b1;
                        state <= ASSEMBLE;
`ifdef DEBUG
                            $display("[%0t] [W_DATA] Last beat received. Transitioning to ASSEMBLE.", $time);
`endif
                        end else begin
                            // Check for overflow
                            if (beat_count >= total_beats) begin
                                $display("[%0t] [W_DATA] ERROR: Received more beats than expected", $time);
                                state <= W_RESP;
                                axi_bresp <= 2'b10; // SLVERR
                            end
                        end
                    end
                end

                ASSEMBLE: begin
                    // Check header version first
                    if (header_version != EXPECTED_HDR_VER) begin
                        // Skip this fragment due to bad header version
`ifdef DEBUG
                        $display("[%0t] [ASSEMBLE] Skipping fragment due to bad header version", $time);
`endif
                        state <= W_RESP;
                    end else begin
                        // Extract TAG (3 bits), TO (1 bit), SRC_ID from header stored in current_frag[0]
                        tag_field = current_frag[0][122:120];
                        to_field = current_frag[0][123];
                        src_id_field = current_frag[0][119:112];

                        // Find or allocate queue based on TAG, TO, SRC_ID
                        allocated_queue_idx = find_queue(tag_field, to_field, src_id_field);

                        if (allocated_queue_idx == 4'hF) begin
                            $display("[%0t] [ASSEMBLE] ERROR: No available queue for TAG=%0d, TO=%0b, SRC_ID=0x%h",
                                     $time, tag_field, to_field, src_id_field);
                            state <= W_RESP;
                        end else begin
                            // Process the received fragment
                            current_queue_idx <= allocated_queue_idx;

`ifdef DEBUG
                            $display("[%0t] [ASSEMBLE] Allocated/Found Queue %0d for TAG=%0d, TO=%0b, SRC_ID=0x%h",
                                     $time, allocated_queue_idx, tag_field, to_field, src_id_field);
`endif

                            case (frag_type)
                                S_PKT: begin
                                    // Start new assembly
`ifdef DEBUG
                                    $display("[%0t] [ASSEMBLE] START: TAG=%0d, SN=%0d, SRC_ID=0x%h, TO=%0b",
                                             $time, tag_field, pkt_sn, src_id_field, to_field);
`endif

                                // Check restart error (S_PKT received while queue is still active)
                                // Restart error occurs when:
                                // 1. Queue is valid and active (state != IDLE)
                                // 2. Same source ID, tag, and tag owner
                                if (queue_valid[allocated_queue_idx] && queue_state[allocated_queue_idx] != 2'b00) begin
                                    // Check if source ID and tag owner match (same assembly context)
                                    if (src_endpoint_id[allocated_queue_idx] == src_id_field &&
                                        tag_owner[allocated_queue_idx] == to_field &&
                                        queue_tag[allocated_queue_idx] == tag_field) begin
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8] <=
                                            PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8] + 1;
                                        $display("[%0t] [ASSEMBLE] ERROR: Restart error (S_PKT while queue active)", $time);
                                        $display("[%0t] [ASSEMBLE]   Same context: SRC_ID=0x%h, TAG=%0d, TO=%0b",
                                                 $time, src_id_field, tag_field, to_field);
                                    end else begin
                                        $display("[%0t] [ASSEMBLE] WARNING: Different context (allowed)", $time);
`ifdef DEBUG
                                        $display("[%0t] [ASSEMBLE]   Old: SRC_ID=0x%h, TAG=%0d, TO=%0b",
                                                 $time, src_endpoint_id[allocated_queue_idx], queue_tag[allocated_queue_idx], tag_owner[allocated_queue_idx]);
                                        $display("[%0t] [ASSEMBLE]   New: SRC_ID=0x%h, TAG=%0d, TO=%0b",
                                                 $time, src_id_field, tag_field, to_field);
`endif
                                    end
                                end

                                if (pkt_sn == 2'b00) begin
                                    // Valid start
                                    queue_valid[allocated_queue_idx] <= 1'b1;
                                    queue_state[allocated_queue_idx] <= 2'b01;  // WAIT_M or WAIT_L
                                    queue_expected_sn[allocated_queue_idx] <= 2'b01;  // Next SN
                                    queue_frag_count[allocated_queue_idx] <= 8'h1;
                                    queue_write_ptr[allocated_queue_idx] <= 12'h0;
                                    queue_timeout[allocated_queue_idx] <= 32'h0;  // Reset timeout
                                    src_endpoint_id[allocated_queue_idx] <= src_id_field;  // Save source ID
                                    tag_owner[allocated_queue_idx] <= to_field;      // Save tag owner
                                    queue_tag[allocated_queue_idx] <= tag_field;           // Save tag (3 bits)
                                    queue_tx_size[allocated_queue_idx] <= current_frag[0][39:24];      // Save transmission size (TLP length)

                                    // Set Queue Initial Address based on allocated queue index
                                    // Each queue gets 64 beats (2KB = 256 bits * 64 beats)
                                    case (allocated_queue_idx)
                                        4'h0: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0 <= (4'h0 * 12'd64) * 32;  // Queue 0: address 0
                                        4'h1: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1 <= (4'h1 * 12'd64) * 32;  // Queue 1: address 2048
                                        4'h2: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2 <= (4'h2 * 12'd64) * 32;  // Queue 2: address 4096
                                        4'h3: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3 <= (4'h3 * 12'd64) * 32;
                                        4'h4: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4 <= (4'h4 * 12'd64) * 32;
                                        4'h5: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5 <= (4'h5 * 12'd64) * 32;
                                        4'h6: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6 <= (4'h6 * 12'd64) * 32;
                                        4'h7: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7 <= (4'h7 * 12'd64) * 32;
                                        4'h8: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8 <= (4'h8 * 12'd64) * 32;
                                        4'h9: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9 <= (4'h9 * 12'd64) * 32;
                                        4'hA: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10 <= (4'hA * 12'd64) * 32;
                                        4'hB: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11 <= (4'hB * 12'd64) * 32;
                                        4'hC: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12 <= (4'hC * 12'd64) * 32;
                                        4'hD: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13 <= (4'hD * 12'd64) * 32;
                                        4'hE: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14 <= (4'hE * 12'd64) * 32;
                                        default: begin end
                                    endcase

                                    // Prepare for partial SRAM write
                                    asm_total_beats <= current_frag_beats;
                                    asm_beat_count <= 12'h0;
                                    asm_padding_bytes <= 2'b00;
                                    asm_is_sg_pkt <= 1'b1; // Use S_PKT length for WPTR
                                    asm_tlp_length_dw <= current_frag[0][39:24]; // Save length for WPTR
                                    
                                    // Save current queue index for use in SRAM write
                                    current_queue_idx <= allocated_queue_idx;
                                    
                                    // Trigger SRAM write
                                    assembled_valid <= 1'b1;
                                    assembled_tag <= allocated_queue_idx;
                                    state <= SRAM_WR;

                                    // Start TLP length accumulation (for WPTR calculation)
                                    queue_accumulated_tlp_bytes[allocated_queue_idx] <= current_frag[0][39:24] * 4;

                                    // Store header (will be replaced by last fragment's header)
                                    queue_data[allocated_queue_idx][0] <= current_frag[0];

                                    // Copy payload only (skip first beat which is header)
                                    // Copy payload only (skip first beat which is header)
                                    for (i = 1; i < 64; i = i + 1) begin
                                        if (i < current_frag_beats)
                                            queue_data[allocated_queue_idx][i] <= current_frag[i];
                                    end
                                    queue_write_ptr[allocated_queue_idx] <= current_frag_beats;
                                    queue_total_beats[allocated_queue_idx] <= current_frag_beats;

`ifdef DEBUG
                                    $display("[%0t] [ASSEMBLE] Stored S fragment: %0d beats (%0d payload), TLP_len=%0d DW (%0d bytes)",
                                             $time, current_frag_beats, current_frag_beats - 1,
                                             current_frag[0][39:24], current_frag[0][39:24] * 4);
                                    $display("[%0t] [ASSEMBLE] Queue[%0d][0] (Header) = 0x%h", $time, current_queue_idx, queue_data[current_queue_idx][0]);
                        $display("[%0t] [ASSEMBLE] Queue[%0d][1] (Payload) = 0x%h", $time, current_queue_idx, queue_data[current_queue_idx][1]);
                        $display("[%0t] [ASSEMBLE] current_frag[0] = 0x%h", $time, current_frag[0]);
                        $display("[%0t] [ASSEMBLE] TLP Length field = 0x%h", $time, current_frag[0][39:24]);
                        $display("[%0t] [ASSEMBLE] Calculated accumulated bytes = %0d", $time, (current_frag[0][39:24] * 4));
`endif
                                end else begin
                                    $display("[%0t] [ASSEMBLE] ERROR: S fragment with SN != 0", $time);
                                end
                                state <= W_RESP;
                            end

                            M_PKT: begin
                                // Continue assembly
`ifdef DEBUG
                                $display("[%0t] [ASSEMBLE] MIDDLE: Queue=%0d, TAG=%0d, TO=%0b, SRC_ID=0x%h, SN=%0d (expected=%0d)",
                                         $time, allocated_queue_idx, tag_field, to_field, src_id_field, pkt_sn, queue_expected_sn[allocated_queue_idx]);
`endif

                                // Check middle/last without first
                                if (!queue_valid[allocated_queue_idx]) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] + 1;
                                    $display("[%0t] [ASSEMBLE] ERROR: Middle without first (Queue=%0d)", $time, allocated_queue_idx);

                                    // Set error interrupt for this queue
                                    case (allocated_queue_idx)
                                        4'h0: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3] <= 1'b1;
                                        4'h1: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1[3] <= 1'b1;
                                        4'h2: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2[3] <= 1'b1;
                                        4'h3: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3[3] <= 1'b1;
                                        4'h4: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4[3] <= 1'b1;
                                        4'h5: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5[3] <= 1'b1;
                                        4'h6: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6[3] <= 1'b1;
                                        4'h7: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7[3] <= 1'b1;
                                        4'h8: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8[3] <= 1'b1;
                                        4'h9: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9[3] <= 1'b1;
                                        4'hA: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10[3] <= 1'b1;
                                        4'hB: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11[3] <= 1'b1;
                                        4'hC: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12[3] <= 1'b1;
                                        4'hD: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13[3] <= 1'b1;
                                        4'hE: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14[3] <= 1'b1;
                                    endcase
                                    o_msg_interrupt <= 1'b1;
                                end

                                // Check transmission size mismatch (M_PKT must match S_PKT size)
                                if (queue_valid[allocated_queue_idx] && (current_frag[0][39:24] != queue_tx_size[allocated_queue_idx])) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0] + 1;
                                    $display("[%0t] [ASSEMBLE] ERROR: Size mismatch (S_PKT=%0dB, M_PKT=%0dB)",
                                             $time, queue_tx_size[allocated_queue_idx] * 4, current_frag[0][39:24] * 4);

                                    // Set error interrupt for this queue
                                    case (allocated_queue_idx)
                                        4'h0: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3] <= 1'b1;
                                        4'h1: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1[3] <= 1'b1;
                                        4'h2: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2[3] <= 1'b1;
                                        4'h3: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3[3] <= 1'b1;
                                        4'h4: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4[3] <= 1'b1;
                                        4'h5: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5[3] <= 1'b1;
                                        4'h6: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6[3] <= 1'b1;
                                        4'h7: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7[3] <= 1'b1;
                                        4'h8: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8[3] <= 1'b1;
                                        4'h9: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9[3] <= 1'b1;
                                        4'hA: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10[3] <= 1'b1;
                                        4'hB: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11[3] <= 1'b1;
                                        4'hC: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12[3] <= 1'b1;
                                        4'hD: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13[3] <= 1'b1;
                                        4'hE: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14[3] <= 1'b1;
                                    endcase
                                    o_msg_interrupt <= 1'b1;
                                end

                                // Check out-of-sequence
                                if (queue_valid[allocated_queue_idx] && (pkt_sn != queue_expected_sn[allocated_queue_idx])) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] + 1;
                                    $display("[%0t] [ASSEMBLE] ERROR: Out-of-sequence (expected SN=%0d, got SN=%0d)",
                                             $time, queue_expected_sn[allocated_queue_idx], pkt_sn);

                                    // Set error interrupt for this queue
                                    case (allocated_queue_idx)
                                        4'h0: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3] <= 1'b1;
                                        4'h1: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1[3] <= 1'b1;
                                        4'h2: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2[3] <= 1'b1;
                                        4'h3: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3[3] <= 1'b1;
                                        4'h4: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4[3] <= 1'b1;
                                        4'h5: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5[3] <= 1'b1;
                                        4'h6: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6[3] <= 1'b1;
                                        4'h7: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7[3] <= 1'b1;
                                        4'h8: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8[3] <= 1'b1;
                                        4'h9: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9[3] <= 1'b1;
                                        4'hA: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10[3] <= 1'b1;
                                        4'hB: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11[3] <= 1'b1;
                                        4'hC: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12[3] <= 1'b1;
                                        4'hD: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13[3] <= 1'b1;
                                        4'hE: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14[3] <= 1'b1;
                                    endcase
                                    o_msg_interrupt <= 1'b1;
                                end

                                if (queue_valid[allocated_queue_idx] && (pkt_sn == queue_expected_sn[allocated_queue_idx])) begin
                                    // Valid middle fragment
                                    queue_expected_sn[allocated_queue_idx] <= pkt_sn + 1;
                                    queue_frag_count[allocated_queue_idx] <= queue_frag_count[allocated_queue_idx] + 1;
                                    queue_timeout[allocated_queue_idx] <= 32'h0;  // Reset timeout

                                    // Accumulate TLP length
                                    queue_accumulated_tlp_bytes[allocated_queue_idx] <= queue_accumulated_tlp_bytes[allocated_queue_idx] + (current_frag[0][39:24] * 4);

                                    // Append payload only (skip first beat which is header)
                                    // Append payload (copy all beats including header, SRAM_WR will skip header)
                                    for (i = 0; i < current_frag_beats; i = i + 1) begin
                                        queue_data[allocated_queue_idx][queue_write_ptr[allocated_queue_idx] + i] <= current_frag[i];
                                    end
                                    queue_write_ptr[allocated_queue_idx] <= queue_write_ptr[allocated_queue_idx] + current_frag_beats;
                                    queue_total_beats[allocated_queue_idx] <= queue_total_beats[allocated_queue_idx] + current_frag_beats;

                                    // Prepare for partial SRAM write
                                    asm_total_beats <= current_frag_beats;
                                    asm_beat_count <= 12'h0;
                                    asm_padding_bytes <= 2'b00;
                                    asm_is_sg_pkt <= 1'b0; // M_PKT uses accumulated length
                                    
                                    // Save current queue index for use in SRAM write
                                    current_queue_idx <= allocated_queue_idx;
                                    
                                    // Trigger SRAM write
                                    assembled_valid <= 1'b1;
                                    assembled_tag <= allocated_queue_idx;
                                    state <= SRAM_WR;
                                end else begin
                                    $display("[%0t] [ASSEMBLE] ERROR: Invalid M fragment (SN mismatch or invalid queue)", $time);
                                    state <= W_RESP;
                                end
                            end

                            L_PKT: begin
                                // Complete assembly
`ifdef DEBUG
                                $display("[%0t] [ASSEMBLE] LAST: Queue=%0d, TAG=%0d, TO=%0b, SRC_ID=0x%h, SN=%0d (expected=%0d)",
                                         $time, allocated_queue_idx, tag_field, to_field, src_id_field, pkt_sn, queue_expected_sn[allocated_queue_idx]);
`endif

                                // Check middle/last without first
                                if (!queue_valid[allocated_queue_idx]) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] + 1;

                                    // Set error interrupt for the specific queue
                                    case (allocated_queue_idx)
                                        4'h0: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3] <= 1'b1;
                                        4'h1: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1[3] <= 1'b1;
                                        4'h2: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2[3] <= 1'b1;
                                        4'h3: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3[3] <= 1'b1;
                                        4'h4: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4[3] <= 1'b1;
                                        4'h5: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5[3] <= 1'b1;
                                        4'h6: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6[3] <= 1'b1;
                                        4'h7: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7[3] <= 1'b1;
                                        4'h8: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8[3] <= 1'b1;
                                        4'h9: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9[3] <= 1'b1;
                                        4'hA: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10[3] <= 1'b1;
                                        4'hB: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11[3] <= 1'b1;
                                        4'hC: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12[3] <= 1'b1;
                                        4'hD: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13[3] <= 1'b1;
                                        4'hE: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14[3] <= 1'b1;
                                    endcase
                                    o_msg_interrupt <= 1'b1;

                                    $display("[%0t] [ASSEMBLE] ERROR: Last without first (Queue=%0d)", $time, allocated_queue_idx);
                                end

                                // Check out-of-sequence
                                if (queue_valid[allocated_queue_idx] && (pkt_sn != queue_expected_sn[allocated_queue_idx])) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] + 1;

                                    // Set error interrupt for the specific queue
                                    case (allocated_queue_idx)
                                        4'h0: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3] <= 1'b1;
                                        4'h1: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1[3] <= 1'b1;
                                        4'h2: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2[3] <= 1'b1;
                                        4'h3: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3[3] <= 1'b1;
                                        4'h4: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4[3] <= 1'b1;
                                        4'h5: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5[3] <= 1'b1;
                                        4'h6: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6[3] <= 1'b1;
                                        4'h7: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7[3] <= 1'b1;
                                        4'h8: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8[3] <= 1'b1;
                                        4'h9: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9[3] <= 1'b1;
                                        4'hA: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10[3] <= 1'b1;
                                        4'hB: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11[3] <= 1'b1;
                                        4'hC: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12[3] <= 1'b1;
                                        4'hD: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13[3] <= 1'b1;
                                        4'hE: PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14[3] <= 1'b1;
                                    endcase
                                    o_msg_interrupt <= 1'b1;

                                    $display("[%0t] [ASSEMBLE] ERROR: Out-of-sequence (expected SN=%0d, got SN=%0d)",
                                             $time, queue_expected_sn[allocated_queue_idx], pkt_sn);
                                end

                                if (queue_valid[allocated_queue_idx] && (pkt_sn == queue_expected_sn[allocated_queue_idx])) begin
                                    // Valid last fragment
                                    queue_frag_count[allocated_queue_idx] <= queue_frag_count[allocated_queue_idx] + 1;
                                    queue_timeout[allocated_queue_idx] <= 32'h0;  // Reset timeout

                                    // Extract padding from header[53:52]
                                    padding_bytes = current_frag[0][53:52];
                                    asm_padding_bytes <= current_frag[0][53:52];  // Save for WPTR calculation
                                    asm_is_sg_pkt <= 1'b0;  // This is L_PKT (multi-fragment)

                                    // Accumulate final TLP length and save for WPTR calculation
                                    asm_accumulated_tlp_bytes <= queue_accumulated_tlp_bytes[allocated_queue_idx] + (current_frag[0][39:24] * 4);

                                    // Calculate payload beats accounting for padding
                                    // current_frag_beats includes header (beat 0)
                                    // For L_PKT, we need to subtract padding from the last payload beat
                                    // Each beat is 32 bytes, so if padding < 32, it affects only the beat count
                                    // Actual implementation: payload_beats = current_frag_beats - 1 (same as before)
                                    // But we track that the last fragment has 'padding_bytes' of padding
                                    payload_beats_with_padding = current_frag_beats - 1;

                                    // Update header with L_PKT header (replaces S_PKT header)
                                    queue_data[allocated_queue_idx][0] <= current_frag[0];

                                    // Append payload (copy all beats including header, SRAM_WR will skip header)
                                    for (i = 0; i < current_frag_beats; i = i + 1) begin
                                        queue_data[allocated_queue_idx][queue_write_ptr[allocated_queue_idx] + i] <= current_frag[i];
                                    end
                                    asm_total_beats <= current_frag_beats; // Process only this fragment
                                    asm_beat_count <= 12'h0;
                                    
                                    // Mark queue as complete so SRAM_WR clears it
                                    queue_state[allocated_queue_idx] <= 2'b11; // COMPLETE

`ifdef DEBUG
                                    $display("[%0t] [ASSEMBLE] L_PKT padding: %0d bytes (header[53:52]=%0b)",
                                             $time, padding_bytes, current_frag[0][53:52]);
`endif

                                    // Save current queue index for use in SRAM write
                                    current_queue_idx <= allocated_queue_idx;

`ifdef DEBUG
                                    $display("[%0t] [ASSEMBLE] COMPLETE: %0d fragments, %0d total beats (including header)",
                                             $time, queue_frag_count[allocated_queue_idx] + 1,
                                             queue_total_beats[allocated_queue_idx] + current_frag_beats - 1);
`endif

                                    // Write assembled message to SRAM
                                    assembled_valid <= 1'b1;
                                    assembled_tag <= allocated_queue_idx;
                                    state <= SRAM_WR;
                                end else begin
                                    $display("[%0t] [ASSEMBLE] ERROR: Invalid L fragment", $time);
                                    state <= W_RESP;
                                end
                            end

                            SG_PKT: begin
                                // Single packet (no assembly)
`ifdef DEBUG
                                $display("[%0t] [ASSEMBLE] SINGLE: Queue=%0d, TAG=%0d, TO=%0b, SRC_ID=0x%h, direct to SRAM",
                                         $time, allocated_queue_idx, tag_field, to_field, src_id_field);
`endif

                                // Set Queue Initial Address based on allocated queue index
                                case (allocated_queue_idx)
                                    4'h0: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0 <= (4'h0 * 12'd64) * 32;
                                    4'h1: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1 <= (4'h1 * 12'd64) * 32;
                                    4'h2: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2 <= (4'h2 * 12'd64) * 32;
                                    4'h3: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3 <= (4'h3 * 12'd64) * 32;
                                    4'h4: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4 <= (4'h4 * 12'd64) * 32;
                                    4'h5: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5 <= (4'h5 * 12'd64) * 32;
                                    4'h6: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6 <= (4'h6 * 12'd64) * 32;
                                    4'h7: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7 <= (4'h7 * 12'd64) * 32;
                                    4'h8: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8 <= (4'h8 * 12'd64) * 32;
                                    4'h9: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9 <= (4'h9 * 12'd64) * 32;
                                    4'hA: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10 <= (4'hA * 12'd64) * 32;
                                    4'hB: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11 <= (4'hB * 12'd64) * 32;
                                    4'hC: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12 <= (4'hC * 12'd64) * 32;
                                    4'hD: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13 <= (4'hD * 12'd64) * 32;
                                    4'hE: PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14 <= (4'hE * 12'd64) * 32;
                                    default: begin end
                                endcase

                                // Extract padding from header[53:52] for SG_PKT
                                padding_bytes = current_frag[0][53:52];
                                asm_padding_bytes <= current_frag[0][53:52];

                                // Extract TLP length for SG_PKT
                                asm_tlp_length_dw <= current_frag[0][39:24];
                                asm_is_sg_pkt <= 1'b1;

                                // Write directly to SRAM
                                asm_total_beats <= current_frag_beats;
                                asm_beat_count <= 12'h0;

`ifdef DEBUG
                                $display("[%0t] [ASSEMBLE] SG_PKT padding: %0d bytes, TLP_len=%0d DW (header[53:52]=%0b, [31:24]=%0d)",
                                         $time, current_frag[0][53:52], current_frag[0][39:24],
                                         current_frag[0][53:52], current_frag[0][39:24]);
`endif

                                // Copy to queue temporarily
                                for (i = 0; i < 64; i = i + 1) begin
                                    if (i < current_frag_beats)
                                        queue_data[allocated_queue_idx][i] <= current_frag[i];
                                end

                                // Save current queue index for use in SRAM write
                                current_queue_idx <= allocated_queue_idx;

                                assembled_valid <= 1'b1;
                                assembled_tag <= allocated_queue_idx;
                                state <= SRAM_WR;
                            end
                        endcase
                    end
                end
            end

                SRAM_WR: begin
`ifdef DEBUG
                    $display("[%0t] [SRAM_WR] Cycle: asm_beat_count=%0d, total=%0d, acc_bytes=%0d", 
                             $time, asm_beat_count, asm_total_beats, sram_accumulator_bytes);
`endif
                    // Initialize alignment on first cycle
                    if (!sram_alignment_init) begin
                        // Calculate Header + OHC size
                        // queue_data[current_queue_idx][0] is the header
                        // Extract OHC field [11:8] from header (which is at [127:0] of the 256-bit beat)
                        // Wait, header is 128 bits. In queue_data[0], it's at [127:0].
                        // OHC field is at [11:8].
                        sram_header_ohc_bytes = 16 + (calc_ohc_size(queue_data[current_queue_idx][0][11:8]) * 4);
                        
                        $display("[%0t] [SRAM_WR] OHC Debug: Header[11:8]=0x%h, OHC_size=%0d DW, Header+OHC=%0d bytes", 
                                 $time, queue_data[current_queue_idx][0][11:8], 
                                 calc_ohc_size(queue_data[current_queue_idx][0][11:8]), 
                                 sram_header_ohc_bytes);

                        // Load first beat's payload into accumulator
                        // Payload starts at sram_header_ohc_bytes
                        // Total beat is 32 bytes.
                        // We take bytes [31 : sram_header_ohc_bytes]
                        // In Little Endian, this is bits [255 : sram_header_ohc_bytes*8]
                        sram_accumulator = 0;
                        sram_accumulator_bytes = 0;
                        
                        // Extract payload from Beat 0 and align it (Precise Word Alignment)
                        sram_accumulator = 512'h0;
                        sram_accumulator_bytes = 0;
                        for (i = 0; (sram_header_ohc_bytes + i) < 32; i = i + 1) begin
                            sram_accumulator[i*8 +: 8] = queue_data[current_queue_idx][0][(sram_header_ohc_bytes + i)*8 +: 8];
                        end
                        sram_accumulator_bytes = 32 - sram_header_ohc_bytes;
                        
                        asm_beat_count <= 1; // Start reading from Beat 1 next
                        sram_alignment_init <= 1'b1;
                        wptr_updated_for_frag <= 1'b0;
                        sram_wen <= 1'b0; // Ensure write enable is off initially

                        // 3. SRAM Base Address Sync (Using Correct SFR Names)
                        sram_waddr = 0;
                        case (current_queue_idx)
                            4'h0: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:5]);
                            4'h1: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_1[15:5]);
                            4'h2: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_2[15:5]);
                            4'h3: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_3[15:5]);
                            4'h4: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4[15:5]);
                            4'h5: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_5[15:5]);
                            4'h6: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_6[15:5]);
                            4'h7: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_7[15:5]);
                            4'h8: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_8[15:5]);
                            4'h9: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_9[15:5]);
                            4'ha: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_10[15:5]);
                            4'hb: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_11[15:5]);
                            4'hc: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_12[15:5]);
                            4'hd: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_13[15:5]);
                            4'he: sram_waddr = (PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14[31:5]) + (PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_14[15:5]);
                            default: sram_waddr = 10'h0;
                        endcase
                        
                        $display("[%0t] [SRAM_WR] Init: Queue=%0d, sram_waddr=%0d", $time, current_queue_idx, sram_waddr);
                    end else begin
                        // Main Write Loop
                        sram_wen <= 1'b0; // Default to no write
                        
                        if (sram_alignment_init) begin
                            // Address increment must be tightly coupled with the end of a write enable pulse
                            if (sram_wen) begin
                                sram_waddr <= sram_waddr + 1;
                                sram_wen   <= 1'b0;
                            end

                            // 1. Load accumulator from queue_data (Continuous Bit-Stream Alignment)
                            if (!sram_wen && sram_accumulator_bytes < 32 && asm_beat_count < asm_total_beats) begin
                                // Atomic shift and load to prevent data gaps
                                for (i = 0; i < 32; i = i + 1) begin
                                    sram_accumulator[(sram_accumulator_bytes*8) + (i*8) +: 8] <= queue_data[current_queue_idx][asm_beat_count][i*8 +: 8];
                                end
                                sram_accumulator_bytes <= sram_accumulator_bytes + 32;
                                asm_beat_count <= asm_beat_count + 1;
                            end

                            // 2. Verified Atomic Word Write Logic
                            if (sram_accumulator_bytes >= 32) begin
                                if (!sram_wen) begin
                                    sram_wdata <= sram_accumulator[255:0];
                                    sram_wen   <= 1'b1;
                                    sram_accumulator <= (sram_accumulator >> 256);
                                    sram_accumulator_bytes <= sram_accumulator_bytes - 32;
                                    $display("[%0t] [SRAM_WR] Shift Write: addr=%0d", $time, sram_waddr);
                                end else begin
                                    sram_wen   <= 1'b0;
                                    sram_waddr <= sram_waddr + 1;
                                end
                            end else if (asm_beat_count >= asm_total_beats) begin
                                if (sram_accumulator_bytes > 0 && !sram_wen) begin
                                    sram_wdata <= sram_accumulator[255:0];
                                    sram_wen   <= 1'b1;
                                    sram_accumulator_bytes <= 0;
                                    $display("[%0t] [SRAM_WR] Final Flush: addr=%0d", $time, sram_waddr);
                                end                                 else if (!sram_wen) begin
                                    // Completion Cleanup & Full Reset of State
                                    o_msg_interrupt <= 1'b1;
                                    queue_valid[current_queue_idx] <= 1'b0;
                                    sram_accumulator <= 512'h0;
                                    sram_accumulator_bytes <= 0;
                                    sram_alignment_init <= 1'b0;
                                    // Sync physical SRAM address directly back to WPTR
                                    case (current_queue_idx)
                                        4'h0:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0 [31:5]) * 32;
                                        4'h1:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_1[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1 [31:5]) * 32;
                                        4'h2:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_2[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2 [31:5]) * 32;
                                        4'h3:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_3[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3 [31:5]) * 32;
                                        4'h4:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4 [31:5]) * 32;
                                        4'h5:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_5[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5 [31:5]) * 32;
                                        4'h6:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_6[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6 [31:5]) * 32;
                                        4'h7:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_7[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7 [31:5]) * 32;
                                        4'h8:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_8[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8 [31:5]) * 32;
                                        4'h9:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_9[15:0]  <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9 [31:5]) * 32;
                                        4'ha:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_10[15:0] <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10 [31:5]) * 32;
                                        4'hb:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_11[15:0] <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11 [31:5]) * 32;
                                        4'hc:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_12[15:0] <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12 [31:5]) * 32;
                                        4'hd:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_13[15:0] <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13 [31:5]) * 32;
                                        4'he:  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_14[15:0] <= (sram_waddr - PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14 [31:5]) * 32;
                                    endcase
                                    $display("[%0t] [SRAM_WR] Finished. Queue %0d, Next WPTR aligned to sram_waddr=%0d", $time, current_queue_idx, sram_waddr);
                                    state <= IDLE;
                                end
                            end
                        end
                    end
                end

                W_RESP: begin
                    axi_bvalid <= 1'b1;
`ifdef DEBUG
                    $display("[%0t] [MSG_RX] W_RESP state: bvalid=%b, bready=%b", $time, axi_bvalid, axi_bready);
`endif
                    axi_bvalid <= 1'b1;
                    axi_bresp <= 2'b00;  // OKAY

                    if (axi_bvalid && axi_bready) begin
`ifdef DEBUG
                        $display("[%0t] [MSG_RX] Response sent: OKAY\n", $time);
`endif
                        axi_bvalid <= 1'b0;
                        state <= IDLE;
                    end else begin
`ifdef DEBUG
                        $display("[%0t] [MSG_RX] Waiting for handshake (bvalid=%b, bready=%b)", $time, axi_bvalid, axi_bready);
`endif
                    end
                end

                default: state <= IDLE;
            endcase

            // Handle INTR_CLEAR register writes for all queues
            // When software writes 1 to INTR_CLEAR[bit], clear corresponding INTR_STATUS[bit]
            for (i = 0; i < 32; i = i + 1) begin
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0[i]) begin
                    PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[i] <= 1'b0;
                    // Commented out to reduce log spam
                    // if (i == 0) begin
                    //     $display("[%0t] [MSG_RX] Q0 INTR_STATUS[0] cleared (Assembly completion)", $time);
                    // end else if (i == 3) begin
                    //     $display("[%0t] [MSG_RX] Q0 INTR_STATUS[3] cleared (Error)", $time);
                    // end
                end
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13[i] <= 1'b0;
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14[i]) PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14[i] <= 1'b0;
            end
        end
    end

endmodule

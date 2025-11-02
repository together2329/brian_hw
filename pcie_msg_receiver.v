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

    // SFR Interrupt Registers (Queue 0)
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0,
    input  wire [31:0] PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0,

    // Queue Write Pointer Register (Queue 0)
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0,

    // Queue Initial Address Registers (15 queues)
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_1,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_2,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_3,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_4,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_5,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_6,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_7,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_8,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_9,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_10,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_11,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_12,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_13,
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_14,

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

    // Assembly Queue (15 queues, index 0-14)
    reg [14:0] queue_valid;              // Queue in use
    reg [1:0]  queue_state [0:14];       // 0=IDLE, 1=WAIT_M, 2=WAIT_L, 3=COMPLETE
    reg [1:0]  queue_expected_sn [0:14]; // Next expected PKT_SN
    reg [7:0]  queue_frag_count [0:14];  // Number of fragments
    reg [11:0] queue_total_beats [0:14]; // Total beats across all fragments
    reg [31:0] queue_timeout [0:14];     // Timeout counter for each queue
    reg [7:0]  queue_source_id [0:14];   // Source ID for each queue
    reg        queue_tag_owner [0:14];   // Tag Owner bit for each queue

    // Fragment data storage: 15 queues x 16 fragments x 16 beats
    reg [255:0] queue_data [0:14] [0:255];
    reg [11:0]  queue_write_ptr [0:14];  // Write pointer for current queue

    // Current fragment buffer
    reg [255:0] current_frag [0:15];
    reg [11:0] current_frag_beats;
    reg [3:0] current_queue_idx;

    // Assembly write control
    reg [11:0] asm_beat_count;
    reg [11:0] asm_total_beats;

    // Temporary variables for error checking
    reg [7:0] dest_id;
    reg [11:0] expected_beats;
    reg [31:0] total_bytes;
    reg [7:0] tx_size_dw;
    reg [31:0] tx_size_bytes;

    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            axi_awready <= 1'b0;
            axi_wready <= 1'b0;
            axi_bvalid <= 1'b0;
            axi_bresp <= 2'b00;
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

            // Initialize Interrupt registers
            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0 <= 32'h0;

            // Initialize Queue Write Pointer
            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0 <= 32'h0;

            // Initialize Queue Initial Address Registers (all 15 queues)
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_1 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_2 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_3 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_4 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_5 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_6 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_7 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_8 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_9 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_10 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_11 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_12 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_13 <= 32'h0;
            PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_14 <= 32'h0;

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
                queue_source_id[i] <= 8'h0;
                queue_tag_owner[i] <= 1'b0;
            end

            current_frag_beats <= 12'h0;
            current_queue_idx <= 4'h0;
            asm_beat_count <= 12'h0;
            asm_total_beats <= 12'h0;

        end else begin
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
                    axi_bvalid <= 1'b0;

                    if (axi_awvalid) begin
                        axi_awready <= 1'b0;
                        write_addr <= axi_awaddr;
                        total_beats <= axi_awlen + 1;
                        beat_count <= 12'h0;
                        current_frag_beats <= axi_awlen + 1;
                        state <= W_DATA;

                        $display("[%0t] [MSG_RX] Received write addr: 0x%h, len=%0d beats",
                                 $time, axi_awaddr, axi_awlen + 1);
                    end else begin
                        axi_awready <= 1'b1;
                        $display("[%0t] [MSG_RX] IDLE: awready=1, waiting for awvalid", $time);
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

                            if (axi_wdata[99:96] != EXPECTED_HDR_VER) begin
                                PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] <=
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] + 1;
                                $display("[%0t] [MSG_RX] *** BAD HEADER VERSION DETECTED ***", $time);
                                $display("[%0t] [MSG_RX] Expected=0x%h, Received=0x%h",
                                         $time, EXPECTED_HDR_VER, axi_wdata[99:96]);
                                $display("[%0t] [MSG_RX] Error counter incremented to: %0d",
                                         $time, PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] + 1);
                                $display("[%0t] [MSG_RX] DEBUG_31[31:24] = 0x%h", $time, PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] + 1);

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
                            // Since field is 8-bit, max is 0xFF (1020B), so we check < 0x10 or == 0xFF+
                            tx_size_dw = axi_wdata[31:24];
                            tx_size_bytes = {24'h0, tx_size_dw} * 4;

                            if (tx_size_bytes < 64 || tx_size_bytes > 1024) begin
                                PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0] <=
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0] + 1;
                                $display("[%0t] [MSG_RX] ERROR: Unsupported TX unit size (%0dB, valid: 64B-1024B)",
                                         $time, tx_size_bytes);
                            end

                            // Check size mismatch (compare axi_awsize with TLP length)
                            // Expected: 2^axi_awsize bytes per beat
                            // TLP length is in DW (4 bytes), so TLP_len*4 = expected total bytes
                            // For size=5 (32B per beat), we expect specific beat counts
                            if (axi_awsize == 3'd5) begin  // 32B per beat
                                total_bytes = {24'h0, axi_wdata[31:24]} * 4;  // DW to bytes
                                expected_beats = (total_bytes + 31) / 32;  // Round up
                                if (total_beats != expected_beats) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0] + 1;
                                    $display("[%0t] [MSG_RX] ERROR: Size mismatch (TLP_len=%0d DW, beats=%0d, expected=%0d)",
                                             $time, axi_wdata[31:24], total_beats, expected_beats);
                                end
                            end
                        end

                        // Store fragment data in temporary buffer
                        current_frag[beat_count] <= axi_wdata;

                        $display("[%0t] [MSG_RX] Beat %0d: data=0x%h, last=%0b",
                                 $time, beat_count, axi_wdata, axi_wlast);

                        beat_count <= beat_count + 1;

                        if (axi_wlast) begin
                            axi_wready <= 1'b0;
                            state <= ASSEMBLE;
                        end
                    end
                end

                ASSEMBLE: begin
                    // Check header version first
                    if (header_version != EXPECTED_HDR_VER) begin
                        // Skip this fragment due to bad header version
                        $display("[%0t] [ASSEMBLE] Skipping fragment due to bad header version", $time);
                        state <= W_RESP;
                    end else if (msg_tag < 15) begin
                        // Process the received fragment
                        current_queue_idx <= msg_tag;

                        case (frag_type)
                            S_PKT: begin
                                // Start new assembly
                                $display("[%0t] [ASSEMBLE] START: TAG=%0h, SN=%0d, SRC_ID=0x%h, TO=%0b",
                                         $time, msg_tag, pkt_sn, axi_wdata[119:112], axi_wdata[123]);

                                // Check restart error (S_PKT received while queue is still active)
                                // Restart error occurs when:
                                // 1. Queue is valid and active (state != IDLE)
                                // 2. Same source ID, msg tag, and tag owner
                                if (queue_valid[msg_tag] && queue_state[msg_tag] != 2'b00) begin
                                    // Check if source ID and tag owner match (same assembly context)
                                    if (queue_source_id[msg_tag] == axi_wdata[119:112] &&
                                        queue_tag_owner[msg_tag] == axi_wdata[123]) begin
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8] <=
                                            PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8] + 1;
                                        $display("[%0t] [ASSEMBLE] ERROR: Restart error (S_PKT while queue active)", $time);
                                        $display("[%0t] [ASSEMBLE]   Same context: SRC_ID=0x%h, TAG=%0h, TO=%0b",
                                                 $time, axi_wdata[119:112], msg_tag, axi_wdata[123]);
                                    end else begin
                                        $display("[%0t] [ASSEMBLE] WARNING: Different context on same tag (allowed)", $time);
                                        $display("[%0t] [ASSEMBLE]   Old: SRC_ID=0x%h, TO=%0b",
                                                 $time, queue_source_id[msg_tag], queue_tag_owner[msg_tag]);
                                        $display("[%0t] [ASSEMBLE]   New: SRC_ID=0x%h, TO=%0b",
                                                 $time, axi_wdata[119:112], axi_wdata[123]);
                                    end
                                end

                                if (pkt_sn == 2'b00) begin
                                    // Valid start
                                    queue_valid[msg_tag] <= 1'b1;
                                    queue_state[msg_tag] <= 2'b01;  // WAIT_M or WAIT_L
                                    queue_expected_sn[msg_tag] <= 2'b01;  // Next SN
                                    queue_frag_count[msg_tag] <= 8'h1;
                                    queue_write_ptr[msg_tag] <= 12'h0;
                                    queue_timeout[msg_tag] <= 32'h0;  // Reset timeout
                                    queue_source_id[msg_tag] <= axi_wdata[119:112];  // Save source ID
                                    queue_tag_owner[msg_tag] <= axi_wdata[123];      // Save tag owner

                                    // Set Queue Initial Address based on tag
                                    // Each queue gets 64 beats (2KB = 256 bits * 64 beats) starting from tag*64
                                    case (msg_tag)
                                        4'h0: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0 <= (4'h0 * 12'd64) * 32;  // Queue 0: address 0
                                        4'h1: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_1 <= (4'h1 * 12'd64) * 32;  // Queue 1: address 2048
                                        4'h2: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_2 <= (4'h2 * 12'd64) * 32;  // Queue 2: address 4096
                                        4'h3: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_3 <= (4'h3 * 12'd64) * 32;
                                        4'h4: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_4 <= (4'h4 * 12'd64) * 32;
                                        4'h5: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_5 <= (4'h5 * 12'd64) * 32;
                                        4'h6: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_6 <= (4'h6 * 12'd64) * 32;
                                        4'h7: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_7 <= (4'h7 * 12'd64) * 32;
                                        4'h8: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_8 <= (4'h8 * 12'd64) * 32;
                                        4'h9: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_9 <= (4'h9 * 12'd64) * 32;
                                        4'hA: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_10 <= (4'hA * 12'd64) * 32;
                                        4'hB: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_11 <= (4'hB * 12'd64) * 32;
                                        4'hC: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_12 <= (4'hC * 12'd64) * 32;
                                        4'hD: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_13 <= (4'hD * 12'd64) * 32;
                                        4'hE: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_14 <= (4'hE * 12'd64) * 32;
                                        default: begin end
                                    endcase

                                    // Save current queue index for use in SRAM write
                                    current_queue_idx <= msg_tag;

                                    // Store header (will be replaced by last fragment's header)
                                    queue_data[msg_tag][0] <= current_frag[0];

                                    // Copy payload only (skip first beat which is header)
                                    for (i = 1; i < 16; i = i + 1) begin
                                        if (i < current_frag_beats)
                                            queue_data[msg_tag][i] <= current_frag[i];
                                    end
                                    queue_write_ptr[msg_tag] <= current_frag_beats;
                                    queue_total_beats[msg_tag] <= current_frag_beats;

                                    $display("[%0t] [ASSEMBLE] Stored S fragment: %0d beats (%0d payload)",
                                             $time, current_frag_beats, current_frag_beats - 1);
                                end else begin
                                    $display("[%0t] [ASSEMBLE] ERROR: S fragment with SN != 0", $time);
                                end
                                state <= W_RESP;
                            end

                            M_PKT: begin
                                // Continue assembly
                                $display("[%0t] [ASSEMBLE] MIDDLE: TAG=%0h, SN=%0d (expected=%0d)",
                                         $time, msg_tag, pkt_sn, queue_expected_sn[msg_tag]);

                                // Check middle/last without first
                                if (!queue_valid[msg_tag]) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] + 1;
                                    $display("[%0t] [ASSEMBLE] ERROR: Middle without first (TAG=%0h)", $time, msg_tag);
                                end

                                // Check out-of-sequence
                                if (queue_valid[msg_tag] && (pkt_sn != queue_expected_sn[msg_tag])) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] + 1;
                                    $display("[%0t] [ASSEMBLE] ERROR: Out-of-sequence (expected SN=%0d, got SN=%0d)",
                                             $time, queue_expected_sn[msg_tag], pkt_sn);
                                end

                                if (queue_valid[msg_tag] && (pkt_sn == queue_expected_sn[msg_tag])) begin
                                    // Valid middle fragment
                                    queue_expected_sn[msg_tag] <= pkt_sn + 1;
                                    queue_frag_count[msg_tag] <= queue_frag_count[msg_tag] + 1;
                                    queue_timeout[msg_tag] <= 32'h0;  // Reset timeout

                                    // Append payload only (skip first beat which is header)
                                    for (i = 1; i < 16; i = i + 1) begin
                                        if (i < current_frag_beats)
                                            queue_data[msg_tag][queue_write_ptr[msg_tag] + i - 1] <= current_frag[i];
                                    end
                                    queue_write_ptr[msg_tag] <= queue_write_ptr[msg_tag] + current_frag_beats - 1;
                                    queue_total_beats[msg_tag] <= queue_total_beats[msg_tag] + current_frag_beats - 1;

                                    // Save current queue index for use in SRAM write
                                    current_queue_idx <= msg_tag;

                                    $display("[%0t] [ASSEMBLE] Appended M fragment: %0d payload beats (total=%0d)",
                                             $time, current_frag_beats - 1, queue_total_beats[msg_tag] + current_frag_beats - 1);
                                end else begin
                                    $display("[%0t] [ASSEMBLE] ERROR: Invalid M fragment (SN mismatch or invalid queue)", $time);
                                end
                                state <= W_RESP;
                            end

                            L_PKT: begin
                                // Complete assembly
                                $display("[%0t] [ASSEMBLE] LAST: TAG=%0h, SN=%0d (expected=%0d)",
                                         $time, msg_tag, pkt_sn, queue_expected_sn[msg_tag]);

                                // Check middle/last without first
                                if (!queue_valid[msg_tag]) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] + 1;
                                    $display("[%0t] [ASSEMBLE] ERROR: Last without first (TAG=%0h)", $time, msg_tag);
                                end

                                // Check out-of-sequence
                                if (queue_valid[msg_tag] && (pkt_sn != queue_expected_sn[msg_tag])) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] + 1;
                                    $display("[%0t] [ASSEMBLE] ERROR: Out-of-sequence (expected SN=%0d, got SN=%0d)",
                                             $time, queue_expected_sn[msg_tag], pkt_sn);
                                end

                                if (queue_valid[msg_tag] && (pkt_sn == queue_expected_sn[msg_tag])) begin
                                    // Valid last fragment
                                    queue_frag_count[msg_tag] <= queue_frag_count[msg_tag] + 1;
                                    queue_timeout[msg_tag] <= 32'h0;  // Reset timeout

                                    // Update header with L_PKT header (replaces S_PKT header)
                                    queue_data[msg_tag][0] <= current_frag[0];

                                    // Append payload only (skip first beat which is header)
                                    for (i = 1; i < 16; i = i + 1) begin
                                        if (i < current_frag_beats)
                                            queue_data[msg_tag][queue_write_ptr[msg_tag] + i - 1] <= current_frag[i];
                                    end
                                    asm_total_beats <= queue_total_beats[msg_tag] + current_frag_beats - 1;
                                    asm_beat_count <= 12'h0;

                                    // Save current queue index for use in SRAM write
                                    current_queue_idx <= msg_tag;

                                    $display("[%0t] [ASSEMBLE] COMPLETE: %0d fragments, %0d total beats (including header)",
                                             $time, queue_frag_count[msg_tag] + 1,
                                             queue_total_beats[msg_tag] + current_frag_beats - 1);

                                    // Write assembled message to SRAM
                                    assembled_valid <= 1'b1;
                                    assembled_tag <= msg_tag;
                                    state <= SRAM_WR;
                                end else begin
                                    $display("[%0t] [ASSEMBLE] ERROR: Invalid L fragment", $time);
                                    state <= W_RESP;
                                end
                            end

                            SG_PKT: begin
                                // Single packet (no assembly)
                                $display("[%0t] [ASSEMBLE] SINGLE: TAG=%0h, direct to SRAM",
                                         $time, msg_tag);

                                // Set Queue Initial Address based on tag (same as S_PKT)
                                case (msg_tag)
                                    4'h0: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0 <= (4'h0 * 12'd64) * 32;
                                    4'h1: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_1 <= (4'h1 * 12'd64) * 32;
                                    4'h2: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_2 <= (4'h2 * 12'd64) * 32;
                                    4'h3: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_3 <= (4'h3 * 12'd64) * 32;
                                    4'h4: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_4 <= (4'h4 * 12'd64) * 32;
                                    4'h5: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_5 <= (4'h5 * 12'd64) * 32;
                                    4'h6: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_6 <= (4'h6 * 12'd64) * 32;
                                    4'h7: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_7 <= (4'h7 * 12'd64) * 32;
                                    4'h8: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_8 <= (4'h8 * 12'd64) * 32;
                                    4'h9: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_9 <= (4'h9 * 12'd64) * 32;
                                    4'hA: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_10 <= (4'hA * 12'd64) * 32;
                                    4'hB: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_11 <= (4'hB * 12'd64) * 32;
                                    4'hC: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_12 <= (4'hC * 12'd64) * 32;
                                    4'hD: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_13 <= (4'hD * 12'd64) * 32;
                                    4'hE: PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_14 <= (4'hE * 12'd64) * 32;
                                    default: begin end
                                endcase

                                // Write directly to SRAM
                                asm_total_beats <= current_frag_beats;
                                asm_beat_count <= 12'h0;

                                // Copy to queue temporarily
                                for (i = 0; i < 16; i = i + 1) begin
                                    if (i < current_frag_beats)
                                        queue_data[msg_tag][i] <= current_frag[i];
                                end

                                // Save current queue index for use in SRAM write
                                current_queue_idx <= msg_tag;

                                assembled_valid <= 1'b1;
                                assembled_tag <= msg_tag;
                                state <= SRAM_WR;
                            end
                        endcase
                    end else begin
                        $display("[%0t] [ASSEMBLE] ERROR: Invalid MSG_TAG=%0h", $time, msg_tag);
                        state <= W_RESP;
                    end
                end

                SRAM_WR: begin
                    // Write assembled payload to SRAM (skip header beat 0)
                    if (asm_beat_count == 12'h0) begin
                        // Display assembled header (not stored in SRAM)
                        $display("[%0t] [SRAM_WR] Assembled Header (not stored): 0x%h",
                                 $time, queue_data[current_queue_idx][0]);
                    end

                    if (asm_beat_count < asm_total_beats - 1) begin
                        sram_wen <= 1'b1;
                        // Calculate base address from Q_INIT_ADDR based on current_queue_idx
                        case (current_queue_idx)
                            4'h0: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0[9:0] + asm_beat_count;
                            4'h1: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_1[9:0] + asm_beat_count;
                            4'h2: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_2[9:0] + asm_beat_count;
                            4'h3: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_3[9:0] + asm_beat_count;
                            4'h4: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_4[9:0] + asm_beat_count;
                            4'h5: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_5[9:0] + asm_beat_count;
                            4'h6: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_6[9:0] + asm_beat_count;
                            4'h7: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_7[9:0] + asm_beat_count;
                            4'h8: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_8[9:0] + asm_beat_count;
                            4'h9: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_9[9:0] + asm_beat_count;
                            4'hA: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_10[9:0] + asm_beat_count;
                            4'hB: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_11[9:0] + asm_beat_count;
                            4'hC: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_12[9:0] + asm_beat_count;
                            4'hD: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_13[9:0] + asm_beat_count;
                            4'hE: sram_waddr <= PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_14[9:0] + asm_beat_count;
                            default: sram_waddr <= asm_beat_count;
                        endcase
                        sram_wdata <= queue_data[current_queue_idx][asm_beat_count + 1];  // +1 to skip header

                        $display("[%0t] [SRAM_WR] Payload beat %0d/%0d: addr=%0h, data=0x%h",
                                 $time, asm_beat_count, asm_total_beats-2,
                                 sram_waddr,
                                 queue_data[current_queue_idx][asm_beat_count + 1]);

                        asm_beat_count <= asm_beat_count + 1;
                    end else begin
                        // Done writing to SRAM
                        sram_wen <= 1'b0;

                        // Clear the queue if it was L_PKT or SG_PKT
                        if (frag_type == L_PKT || frag_type == SG_PKT) begin
                            queue_valid[current_queue_idx] <= 1'b0;
                            queue_state[current_queue_idx] <= 2'b00;
                            $display("[%0t] [SRAM_WR] Queue %0h cleared", $time, current_queue_idx);

                            // Set interrupt status - completion of assembly (L_PKT or SG_PKT)
                            // INTR_STATUS[0] = completion of queue
                            PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[0] <= 1'b1;

                            // Update write pointer (byte count: each beat is 32 bytes = 256 bits)
                            // Total payload bytes = (asm_total_beats - 1) * 32
                            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:0] <= (asm_total_beats - 1) * 32;

                            // Assert interrupt signal
                            o_msg_interrupt <= 1'b1;

                            $display("[%0t] [SRAM_WR] Interrupt asserted - Assembly complete, WPTR=%0d bytes",
                                     $time, (asm_total_beats - 1) * 32);
                        end

                        state <= W_RESP;
                    end
                end

                W_RESP: begin
                    $display("[%0t] [MSG_RX] W_RESP state: bvalid=%b, bready=%b", $time, axi_bvalid, axi_bready);
                    axi_bvalid <= 1'b1;
                    axi_bresp <= 2'b00;  // OKAY

                    if (axi_bvalid && axi_bready) begin
                        $display("[%0t] [MSG_RX] Response sent: OKAY\n", $time);
                        axi_bvalid <= 1'b0;
                        state <= IDLE;
                    end else begin
                        $display("[%0t] [MSG_RX] Waiting for handshake (bvalid=%b, bready=%b)", $time, axi_bvalid, axi_bready);
                    end
                end

                default: state <= IDLE;
            endcase

            // Handle INTR_CLEAR register writes
            // When software writes 1 to INTR_CLEAR[bit], clear corresponding INTR_STATUS[bit]
            for (i = 0; i < 32; i = i + 1) begin
                if (PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0[i]) begin
                    PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[i] <= 1'b0;
                    if (i == 0) begin
                        $display("[%0t] [MSG_RX] INTR_STATUS[0] cleared (Assembly completion)", $time);
                    end else if (i == 3) begin
                        $display("[%0t] [MSG_RX] INTR_STATUS[3] cleared (Error)", $time);
                    end
                end
            end
        end
    end

endmodule

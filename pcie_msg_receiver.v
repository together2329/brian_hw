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
                    axi_awready <= 1'b1;
                    axi_bvalid <= 1'b0;

                    if (axi_awvalid && axi_awready) begin
                        write_addr <= axi_awaddr;
                        total_beats <= axi_awlen + 1;
                        beat_count <= 12'h0;
                        current_frag_beats <= axi_awlen + 1;
                        axi_awready <= 1'b0;
                        state <= W_DATA;

                        $display("[%0t] [MSG_RX] Received write addr: 0x%h, len=%0d beats",
                                 $time, axi_awaddr, axi_awlen + 1);
                    end
                end

                W_DATA: begin
                    axi_wready <= 1'b1;

                    if (axi_wvalid && axi_wready) begin
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

                            // Check header version
                            if (axi_wdata[99:96] != EXPECTED_HDR_VER) begin
                                PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] <=
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] + 1;
                                $display("[%0t] [MSG_RX] ERROR: Bad header version! Expected=0x%h, Received=0x%h",
                                         $time, EXPECTED_HDR_VER, axi_wdata[99:96]);
                                $display("[%0t] [MSG_RX] Bad header version counter: %0d",
                                         $time, PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] + 1);

                                // Set error interrupt (INTR_STATUS[3] = all queue error)
                                PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3] <= 1'b1;
                                o_msg_interrupt <= 1'b1;
                            end

                            // Check unknown destination ID (if control bit is disabled)
                            if (!PCIE_SFR_AXI_MSG_HANDLER_RX_CONTROL15[8]) begin
                                reg [7:0] dest_id;
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
                            if (axi_wdata[123:120] == 4'h7 && axi_wdata[100] == 1'b0) begin
                                PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[15:8] <=
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[15:8] + 1;
                                $display("[%0t] [MSG_RX] ERROR: Tag owner error (TAG=7, TO=0)", $time);
                            end

                            // Check unsupported TX unit (TLP length field [31:24])
                            // 32B = 8 DW = 0x08
                            if (axi_wdata[31:24] == 8'h08) begin
                                PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0] <=
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0] + 1;
                                $display("[%0t] [MSG_RX] ERROR: Unsupported TX unit (32B detected)", $time);
                            end

                            // Check size mismatch (compare axi_awsize with TLP length)
                            // Expected: 2^axi_awsize bytes per beat
                            // TLP length is in DW (4 bytes), so TLP_len*4 = expected total bytes
                            // For size=5 (32B per beat), we expect specific beat counts
                            if (axi_awsize == 3'd5) begin  // 32B per beat
                                reg [11:0] expected_beats;
                                reg [31:0] total_bytes;
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
                                $display("[%0t] [ASSEMBLE] START: TAG=%0h, SN=%0d",
                                         $time, msg_tag, pkt_sn);

                                // Check restart error (S_PKT received while queue is still active)
                                if (queue_valid[msg_tag] && queue_state[msg_tag] != 2'b00) begin
                                    PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8] <=
                                        PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8] + 1;
                                    $display("[%0t] [ASSEMBLE] ERROR: Restart error (S_PKT while queue active)", $time);
                                end

                                if (pkt_sn == 2'b00) begin
                                    // Valid start
                                    queue_valid[msg_tag] <= 1'b1;
                                    queue_state[msg_tag] <= 2'b01;  // WAIT_M or WAIT_L
                                    queue_expected_sn[msg_tag] <= 2'b01;  // Next SN
                                    queue_frag_count[msg_tag] <= 8'h1;
                                    queue_write_ptr[msg_tag] <= 12'h0;
                                    queue_timeout[msg_tag] <= 32'h0;  // Reset timeout

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

                                // Write directly to SRAM
                                asm_total_beats <= current_frag_beats;
                                asm_beat_count <= 12'h0;

                                // Copy to queue temporarily
                                for (i = 0; i < 16; i = i + 1) begin
                                    if (i < current_frag_beats)
                                        queue_data[msg_tag][i] <= current_frag[i];
                                end

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
                        sram_waddr <= write_addr[9:0] + asm_beat_count;
                        sram_wdata <= queue_data[current_queue_idx][asm_beat_count + 1];  // +1 to skip header

                        $display("[%0t] [SRAM_WR] Payload beat %0d/%0d: addr=%0h, data=0x%h",
                                 $time, asm_beat_count, asm_total_beats-2,
                                 write_addr[9:0] + asm_beat_count,
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

                            // Update write pointer (total beats written to SRAM)
                            PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:0] <= asm_total_beats - 1;

                            // Assert interrupt signal
                            o_msg_interrupt <= 1'b1;

                            $display("[%0t] [SRAM_WR] Interrupt asserted - Assembly complete, WPTR=%0d",
                                     $time, asm_total_beats - 1);
                        end

                        state <= W_RESP;
                    end
                end

                W_RESP: begin
                    axi_bvalid <= 1'b1;
                    axi_bresp <= 2'b00;  // OKAY

                    if (axi_bvalid && axi_bready) begin
                        $display("[%0t] [MSG_RX] Response sent: OKAY\n", $time);
                        axi_bvalid <= 1'b0;
                        state <= IDLE;
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

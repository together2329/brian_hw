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

    // SFR Debug Register
    output reg [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31
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

            // Initialize SFR register
            PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31 <= 32'h0;

            // Initialize assembly queues
            queue_valid <= 15'h0;
            for (i = 0; i < 15; i = i + 1) begin
                queue_state[i] <= 2'b00;
                queue_expected_sn[i] <= 2'b00;
                queue_frag_count[i] <= 8'h0;
                queue_total_beats[i] <= 12'h0;
                queue_write_ptr[i] <= 12'h0;
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

                                if (pkt_sn == 2'b00) begin
                                    // Valid start
                                    queue_valid[msg_tag] <= 1'b1;
                                    queue_state[msg_tag] <= 2'b01;  // WAIT_M or WAIT_L
                                    queue_expected_sn[msg_tag] <= 2'b01;  // Next SN
                                    queue_frag_count[msg_tag] <= 8'h1;
                                    queue_write_ptr[msg_tag] <= 12'h0;

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

                                if (queue_valid[msg_tag] && (pkt_sn == queue_expected_sn[msg_tag])) begin
                                    // Valid middle fragment
                                    queue_expected_sn[msg_tag] <= pkt_sn + 1;
                                    queue_frag_count[msg_tag] <= queue_frag_count[msg_tag] + 1;

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

                                if (queue_valid[msg_tag] && (pkt_sn == queue_expected_sn[msg_tag])) begin
                                    // Valid last fragment
                                    queue_frag_count[msg_tag] <= queue_frag_count[msg_tag] + 1;

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

                        // Clear the queue if it was L_PKT
                        if (frag_type == L_PKT || frag_type == SG_PKT) begin
                            queue_valid[current_queue_idx] <= 1'b0;
                            queue_state[current_queue_idx] <= 2'b00;
                            $display("[%0t] [SRAM_WR] Queue %0h cleared", $time, current_queue_idx);
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
        end
    end

endmodule

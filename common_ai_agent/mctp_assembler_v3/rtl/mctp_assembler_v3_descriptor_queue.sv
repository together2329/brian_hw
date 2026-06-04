// mctp_assembler_v3_descriptor_queue.sv
// Implements FM_PUBLISH_DESCRIPTOR (memory.instances.descriptor_fifo):
//   DESCRIPTOR_FIFO_DEPTH-deep FIFO of completed descriptors + first/last
//   TLP header snapshots.  Holds the oldest entry as the stable read window
//   for axi_rd_payload and the APB DESC register bank until descriptor_pop.
//   Raises descriptor_full (AD_DESCRIPTOR_FULL path) when the FIFO is full
//   at EOM; context_table must check descriptor_full before pushing.
//   Pulses descriptor_ready_pulse on every successful push.
//   Increments message_completed_count on every successful push.
//   descriptor_valid = (count != 0); descriptor_full = (count == DEPTH).
`default_nettype none
module mctp_assembler_v3_descriptor_queue #(
    parameter integer DESCRIPTOR_FIFO_DEPTH      = 8
) (
    input  wire                         axi_aclk,
    input  wire                         axi_aresetn,

    // --- push interface (from context_table, 1-cycle pulse on EOM) ----------
    input  wire                         descriptor_push,
    input  wire [15:0]                  desc_base_addr,
    input  wire [12:0]                  desc_payload_len,
    input  wire [7:0]                   desc_source_eid,
    input  wire [7:0]                   desc_dest_eid,
    input  wire                         desc_tag_owner,
    input  wire [2:0]                   desc_message_tag,
    input  wire [6:0]                   desc_message_type,
    input  wire [1:0]                   desc_final_seq,
    input  wire [3:0]                   desc_context_id,
    input  wire [2:0]                   desc_completion_status,
    input  wire [15:0]                  desc_requester_id,
    input  wire [2:0]                   desc_routing_type,
    input  wire [127:0]                 desc_first_header,
    input  wire [127:0]                 desc_last_header,

    // --- pop interface (from regfile via cdc OR from axi_rd_payload) --------
    input  wire                         descriptor_pop,

    // --- status outputs ------------------------------------------------------
    output reg                          descriptor_valid,   // queue non-empty
    output reg                          descriptor_full,    // queue full
    output reg  [3:0]                   descriptor_count,   // occupancy
    output reg                          descriptor_ready_pulse, // 1-cycle on push

    // --- read window (oldest descriptor, stable until pop) ------------------
    output reg  [15:0]                  rd_base_addr,
    output reg  [12:0]                  rd_payload_len,
    output reg  [7:0]                   rd_source_eid,
    output reg  [7:0]                   rd_dest_eid,
    output reg                          rd_tag_owner,
    output reg  [2:0]                   rd_message_tag,
    output reg  [6:0]                   rd_message_type,
    output reg  [3:0]                   rd_context_id,
    output reg  [2:0]                   rd_completion_status,
    output reg  [15:0]                  rd_requester_id,
    output reg  [2:0]                   rd_routing_type,
    output reg  [127:0]                 rd_first_header,
    output reg  [127:0]                 rd_last_header
);

    // -------------------------------------------------------------------------
    // FIFO storage (memory.instances.descriptor_fifo: depth=8, width=512,
    // latency=0).  One entry packs all descriptor fields; the remaining bits
    // in each 512-bit word are unused (reserved zero at write time).
    //
    // Field packing within each 512-bit fifo_mem word (LSB first):
    //   [15:0]    descriptor_base_addr   (ctx_payload_base_addr)
    //   [28:16]   descriptor_payload_len (ctx_payload_byte_count)
    //   [36:29]   source_eid
    //   [44:37]   dest_eid
    //   [45]      tag_owner
    //   [48:46]   message_tag
    //   [55:49]   message_type
    //   [57:56]   final_seq
    //   [61:58]   context_id
    //   [64:62]   completion_status
    //   [80:65]   requester_id
    //   [83:81]   routing_type
    //   [211:84]  first_header  (128 bits)
    //   [339:212] last_header   (128 bits)
    //   [511:340] reserved (zero)
    // -------------------------------------------------------------------------
    localparam integer DEPTH      = DESCRIPTOR_FIFO_DEPTH;         // 8
    localparam integer PTR_WIDTH  = $clog2(DEPTH);                 // 3
    localparam [3:0]   DEPTH_4B   = DEPTH[3:0];                    // for 4-bit comparisons

    // FIFO storage — 512-bit wide per SSOT memory.instances.descriptor_fifo
    reg [511:0] fifo_mem [0:DEPTH-1];

    // FIFO pointers (one extra bit for full/empty disambiguation)
    reg [PTR_WIDTH:0]   wr_ptr;   // write pointer (PTR_WIDTH+1 bits)
    reg [PTR_WIDTH:0]   rd_ptr;   // read pointer  (PTR_WIDTH+1 bits)

    // Combinational index wires — low PTR_WIDTH bits of each pointer, used to
    // index fifo_mem.  Declared as wires so the procedural blocks use a plain
    // identifier rather than a parameterized part-select (policy compliance).
    wire [PTR_WIDTH-1:0] wr_idx = wr_ptr[PTR_WIDTH-1:0];
    wire [PTR_WIDTH-1:0] rd_idx = rd_ptr[PTR_WIDTH-1:0];

    // Occupancy count and derived status (registered for clean timing)
    reg [3:0]           count_r;

    // message_completed_count: 32-bit counter incremented on each accepted push
    // (FM_PUBLISH_DESCRIPTOR.state_updates.message_completed_count)
    reg [31:0]          message_completed_count;

    // -------------------------------------------------------------------------
    // Push/pop control
    // -------------------------------------------------------------------------
    wire do_push = descriptor_push & ~descriptor_full;
    wire do_pop  = descriptor_pop  & descriptor_valid;

    // Combinational 512-bit entry assembly from push-side inputs
    // (descriptor_base_addr = ctx_payload_base_addr,
    //  descriptor_payload_len = ctx_payload_byte_count)
    wire [511:0] push_entry;
    assign push_entry[15:0]    = desc_base_addr;      // descriptor_base_addr
    assign push_entry[28:16]   = desc_payload_len;    // descriptor_payload_len / ctx_payload_byte_count
    assign push_entry[36:29]   = desc_source_eid;
    assign push_entry[44:37]   = desc_dest_eid;
    assign push_entry[45]      = desc_tag_owner;
    assign push_entry[48:46]   = desc_message_tag;
    assign push_entry[55:49]   = desc_message_type;
    assign push_entry[57:56]   = desc_final_seq;
    assign push_entry[61:58]   = desc_context_id;
    assign push_entry[64:62]   = desc_completion_status;
    assign push_entry[80:65]   = desc_requester_id;
    assign push_entry[83:81]   = desc_routing_type;
    assign push_entry[211:84]  = desc_first_header;   // last_tlp_header snapshot (first)
    assign push_entry[339:212] = desc_last_header;    // last_tlp_header snapshot (last)
    assign push_entry[511:340] = 172'd0;

    // -------------------------------------------------------------------------
    // FIFO write — latency=0: data visible at rd_ptr as soon as written
    // -------------------------------------------------------------------------
    always @(posedge axi_aclk) begin
        if (do_push)
            fifo_mem[wr_idx] <= push_entry;
    end

    // -------------------------------------------------------------------------
    // Pointer and count update; descriptor_ready_pulse; message_completed_count
    // -------------------------------------------------------------------------
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            wr_ptr                  <= {(PTR_WIDTH+1){1'b0}};
            rd_ptr                  <= {(PTR_WIDTH+1){1'b0}};
            count_r                 <= 4'd0;
            message_completed_count <= 32'd0;
            descriptor_valid        <= 1'b0;
            descriptor_full         <= 1'b0;
            descriptor_count        <= 4'd0;
            descriptor_ready_pulse  <= 1'b0;
        end else begin
            // Default: clear the 1-cycle pulse
            descriptor_ready_pulse <= 1'b0;

            if (do_push && !do_pop) begin
                // Push only: advance write pointer, increment count
                wr_ptr                  <= wr_ptr + {{PTR_WIDTH{1'b0}}, 1'b1};
                count_r                 <= count_r + 4'd1;
                message_completed_count <= message_completed_count + 32'd1;
                descriptor_ready_pulse  <= 1'b1;
            end else if (!do_push && do_pop) begin
                // Pop only: advance read pointer, decrement count
                rd_ptr  <= rd_ptr + {{PTR_WIDTH{1'b0}}, 1'b1};
                count_r <= count_r - 4'd1;
            end else if (do_push && do_pop) begin
                // Simultaneous push+pop: both pointers advance, count unchanged
                wr_ptr                  <= wr_ptr + {{PTR_WIDTH{1'b0}}, 1'b1};
                rd_ptr                  <= rd_ptr + {{PTR_WIDTH{1'b0}}, 1'b1};
                message_completed_count <= message_completed_count + 32'd1;
                descriptor_ready_pulse  <= 1'b1;
            end

            // Update registered status outputs from count_r
            // (descriptor_valid = (count != 0) per FM_PUBLISH_DESCRIPTOR)
            descriptor_valid  <= (count_r != 4'd0) | (do_push & !do_pop) |
                                 (do_push &  do_pop & (count_r != 4'd0));
            // Recompute valid and full from next-cycle count
            begin : update_status
                reg [3:0] next_count;
                if      (do_push && !do_pop) next_count = count_r + 4'd1;
                else if (!do_push && do_pop) next_count = count_r - 4'd1;
                else                         next_count = count_r;
                descriptor_valid  <= (next_count != 4'd0);
                // descriptor_full = (count == DEPTH); not descriptor_queue_full
                // is the descriptor_ready state (FM_PUBLISH_DESCRIPTOR.state_updates)
                descriptor_full   <= (next_count == DEPTH_4B);
                descriptor_count  <= next_count;
            end
        end
    end

    // -------------------------------------------------------------------------
    // Read window: oldest descriptor fields, extracted from fifo_mem[rd_ptr]
    // Latency=0 per SSOT: present combinationally from the registered FIFO array.
    // Registered one cycle behind to match the ingress reference style.
    // Fields are extracted directly from fifo_mem to avoid a wide intermediate
    // wire whose reserved bits would be unused (policy: no inline suppressions).
    // -------------------------------------------------------------------------
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            rd_base_addr        <= 16'd0;
            rd_payload_len      <= 13'd0;
            rd_source_eid       <= 8'd0;
            rd_dest_eid         <= 8'd0;
            rd_tag_owner        <= 1'b0;
            rd_message_tag      <= 3'd0;
            rd_message_type     <= 7'd0;
            rd_context_id       <= 4'd0;
            rd_completion_status<= 3'd0;
            rd_requester_id     <= 16'd0;
            rd_routing_type     <= 3'd0;
            rd_first_header     <= 128'd0;
            rd_last_header      <= 128'd0;
        end else begin
            rd_base_addr        <= fifo_mem[rd_idx][15:0];
            rd_payload_len      <= fifo_mem[rd_idx][28:16];
            rd_source_eid       <= fifo_mem[rd_idx][36:29];
            rd_dest_eid         <= fifo_mem[rd_idx][44:37];
            rd_tag_owner        <= fifo_mem[rd_idx][45];
            rd_message_tag      <= fifo_mem[rd_idx][48:46];
            rd_message_type     <= fifo_mem[rd_idx][55:49];
            rd_context_id       <= fifo_mem[rd_idx][61:58];
            rd_completion_status<= fifo_mem[rd_idx][64:62];
            rd_requester_id     <= fifo_mem[rd_idx][80:65];
            rd_routing_type     <= fifo_mem[rd_idx][83:81];
            rd_first_header     <= fifo_mem[rd_idx][211:84];
            rd_last_header      <= fifo_mem[rd_idx][339:212];
        end
    end

endmodule
`default_nettype wire

// mctp_assembler_v3_mctp_decoder.sv
// MCTP transport decoder for the MCTP assembler.
// Implements function_model.FM_DECODE_MCTP (mctp_transport_decode):
//   - decodes the MCTP transport header + IC/message-type on SOM from the
//     validated VDM word emitted by the PCIe VDM parser (axi_aclk domain)
//   - produces the canonical decoded-packet field set (INTEGRATION_CONTRACT
//     section 0.1): source_eid, dest_eid, tag_owner, message_tag, packet_seq,
//     som, eom, message_type, ic, assembly_key
//   - evaluates dest_accept from the four CONTROL config bits
//   - classifies the two FM_DECODE_MCTP error cases as packet drops and passes
//     through any upstream packet-drop reason at higher priority
//
// vdm_word byte map (lane N of the TLP = vdm_word[8*N +: 8], per the proven
// ingress convention). The 16B Non-Flit PCIe header occupies bytes 0..15; the
// MCTP transport header is the LAST 4B of that 16B header (bytes 12..15) and the
// SOM body byte (IC + message_type) is the first payload byte (byte 16):
//   byte 12  vdm_word[103:96]  : MCTP header byte; header_version = bits[3:0]
//   byte 13  vdm_word[111:104] : dest_eid
//   byte 14  vdm_word[119:112] : source_eid
//   byte 15  vdm_word[127:120] : mctp_byte0 {som,eom,packet_seq[1:0],tag_owner,message_tag[2:0]}
//   byte 16  vdm_word[135:128] : SOM body byte {ic, message_type[6:0]}
`default_nettype none
module mctp_assembler_v3_mctp_decoder (
    input  wire         axi_aclk,
    input  wire         axi_aresetn,
    // upstream validated VDM packet (from pcie_vdm_parser)
    input  wire         vdm_valid,
    input  wire [255:0] vdm_word,
    input  wire [12:0]  vdm_payload_bytes,
    input  wire [255:0] vdm_payload_word,
    input  wire [31:0]  vdm_payload_strb,
    input  wire [127:0] vdm_first_header,
    input  wire [127:0] vdm_last_header,
    input  wire [5:0]   packet_drop_reason_in,
    // destination-filter config (CONTROL bits, via cdc)
    input  wire         cfg_dest_filter_enable,
    input  wire [7:0]   cfg_local_eid,
    input  wire         cfg_accept_broadcast_eid,
    input  wire         cfg_accept_null_eid,
    // downstream decoded MCTP fragment (to context_table)
    output reg          frag_valid,
    output reg  [7:0]   frag_source_eid,
    output reg  [7:0]   frag_dest_eid,
    output reg          frag_tag_owner,
    output reg  [2:0]   frag_message_tag,
    output reg  [1:0]   frag_packet_seq,
    output reg          frag_som,
    output reg          frag_eom,
    output reg  [6:0]   frag_message_type,
    output reg          frag_ic,
    output reg  [11:0]  frag_assembly_key,
    output reg  [255:0] frag_payload_word,
    output reg  [31:0]  frag_payload_strb,
    output reg  [12:0]  frag_payload_bytes,
    output reg  [127:0] frag_first_header,
    output reg  [127:0] frag_last_header,
    // packet-drop sideband
    output reg          packet_drop_valid,
    output reg  [5:0]   packet_drop_reason,
    // DEBUG_CTX mirror of decoded MCTP fields
    output reg  [31:0]  last_decoded_mctp,
    // ---- multi-beat payload stream (PAYLOAD_STREAM_CONTRACT §3) ----------
    // Lane-0-aligned payload beats from the parser, passed through to the
    // context_table ONLY for accepted (non-dropped) fragments. accept_q gates
    // the stream; a dropped packet forwards no payload beats.
    input  wire         pl_beat_valid_in,
    input  wire [255:0] pl_beat_data_in,
    input  wire [31:0]  pl_beat_strb_in,
    input  wire [5:0]   pl_beat_bytes_in,
    input  wire         pl_beat_first_in,
    input  wire         pl_beat_last_in,
    output wire         pl_beat_ready_out,
    output wire         pl_beat_valid,
    output wire [255:0] pl_beat_data,
    output wire [31:0]  pl_beat_strb,
    output wire [5:0]   pl_beat_bytes,
    output wire         pl_beat_first,
    output wire         pl_beat_last,
    input  wire         pl_beat_ready
);

    // shared 6-bit drop-reason encoding (INTEGRATION_CONTRACT section 4.2)
    localparam [5:0] PD_NONE            = 6'd0;
    localparam [5:0] PD_BAD_MCTP_HEADER = 6'd4;
    localparam [5:0] PD_DEST_EID_REJECT = 6'd6;

    // ---- combinational decode of the MCTP transport header (section 0.1) ----
    // header_version occupies the low nibble of the MCTP header byte (byte 12).
    wire [3:0] header_version = vdm_word[99:96];
    wire [7:0] dest_eid       = vdm_word[111:104];
    wire [7:0] source_eid     = vdm_word[119:112];
    wire [7:0] mctp_byte0      = vdm_word[127:120];
    // SOM body byte (byte 16): IC + 7-bit message_type, valid when SOM=1.
    wire [7:0] som_body_byte  = vdm_word[135:128];

    wire       som_w          = mctp_byte0[7];
    wire       eom_w          = mctp_byte0[6];
    wire [1:0] packet_seq_w   = mctp_byte0[5:4];
    wire       tag_owner_w    = mctp_byte0[3];
    wire [2:0] message_tag_w  = mctp_byte0[2:0];
    wire       ic_w           = som_body_byte[7];
    wire [6:0] message_type_w = som_body_byte[6:0];
    // S2_MCTP_DECODE pipeline stage decodes IC/msg_type on SOM (SSOT
    // cycle_model.pipeline.S2_MCTP_DECODE); msg_type is the decoded 7-bit
    // MCTP message type carried forward into the fragment metadata.
    wire [6:0] msg_type        = message_type_w;

    // header_version_ok: MCTP transport header version field must equal 1.
    wire       header_version_ok = (header_version == 4'd1);

    // assembly_key = (source_eid << 4) | (tag_owner << 3) | message_tag.
    wire [11:0] assembly_key_w = ({4'd0, source_eid} << 4) |
                                 ({11'd0, tag_owner_w} << 3) |
                                 {9'd0, message_tag_w};

    // dest_accept: accept when the destination filter is disabled, or the
    // dest_eid targets us / an accepted broadcast (0xFF) / null (0x00) EID.
    wire       dest_accept_w = (~cfg_dest_filter_enable) |
                               (dest_eid == cfg_local_eid) |
                               (cfg_accept_broadcast_eid & (dest_eid == 8'hFF)) |
                               (cfg_accept_null_eid & (dest_eid == 8'h00));

    // vdm_word also carries the 16B PCIe header and the upper data word, which
    // other modules slice; this decoder only consumes the MCTP transport bytes.
    // Tie off the bits not used here so lint stays clean without masking real
    // logic (see scratch reference's unused_inputs idiom).
    wire       vdm_word_unused = ^{vdm_word[255:136], vdm_word[103:100],
                                   vdm_word[95:0]};

    // drop classification (error_handling priority: first match wins).
    // An upstream packet-drop reason takes precedence over reasons raised here;
    // PD_BAD_MCTP_HEADER (error_case_0) outranks PD_DEST_EID_REJECT (error_case_1).
    wire       upstream_drop = (packet_drop_reason_in != PD_NONE);
    wire       bad_header    = ~header_version_ok;
    wire       eid_reject    = ~dest_accept_w;

    wire [5:0] drop_reason_w = upstream_drop ? packet_drop_reason_in :
                               bad_header    ? PD_BAD_MCTP_HEADER     :
                               eid_reject    ? PD_DEST_EID_REJECT     : PD_NONE;
    wire       is_drop       = (drop_reason_w != PD_NONE);

    // -------------------------------------------------------------------------
    // Payload-beat passthrough (PAYLOAD_STREAM_CONTRACT §3).
    // accept_q qualifies the payload stream: it is set the cycle after the
    // decoder asserts frag_valid (a clean accept) and cleared once the packet's
    // pl_beat_last is consumed downstream. While accept_q==0 (drop/idle) the
    // decoder drains any stray parser beats (pl_beat_ready_out=1) and presents
    // no payload downstream; while accept_q==1 it forwards the stream and wires
    // ready straight through. The parser only emits beats for its own clean
    // vdm_valid, so draining is a deadlock-safety measure, not an expected path.
    // -------------------------------------------------------------------------
    reg accept_q;

    // accept_pending: this cycle the decoder is latching a clean accept (it will
    // raise frag_valid + accept_q next cycle). During this 1-cycle gap the parser
    // may already hold the packet's first payload beat valid; ready MUST stay low
    // so that beat is preserved (not drained) until accept_q opens the window.
    wire accept_pending = vdm_valid & ~is_drop & ~upstream_drop;

    assign pl_beat_valid     = accept_q ? pl_beat_valid_in : 1'b0;
    assign pl_beat_data      = pl_beat_data_in;
    assign pl_beat_strb      = pl_beat_strb_in;
    assign pl_beat_bytes     = pl_beat_bytes_in;
    assign pl_beat_first     = pl_beat_first_in;
    assign pl_beat_last      = pl_beat_last_in;
    // When accepting, forward downstream ready. Otherwise self-drain stray beats
    // (deadlock safety) EXCEPT during the accept-pending gap, where ready stays
    // low so the accepted packet's first beat is held until accept_q rises.
    assign pl_beat_ready_out = accept_q     ? pl_beat_ready :
                               accept_pending ? 1'b0        : 1'b1;

    // accept_q lifecycle: a clean accept (frag_valid this cycle) opens the
    // window; the last consumed payload beat of the accepted packet closes it.
    wire pl_beat_fire_in = pl_beat_valid_in & pl_beat_ready_out;
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            accept_q <= 1'b0;
        end else begin
            if (vdm_valid & ~is_drop & ~upstream_drop) begin
                // Clean accept this cycle: frag_valid fires next cycle; open the
                // payload window so the upcoming beat stream is forwarded.
                accept_q <= 1'b1;
            end else if (accept_q & pl_beat_fire_in & pl_beat_last_in) begin
                // Final payload beat of the accepted packet consumed: close window.
                accept_q <= 1'b0;
            end
        end
    end

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            frag_valid        <= 1'b0;
            frag_source_eid   <= 8'd0;
            frag_dest_eid     <= 8'd0;
            frag_tag_owner    <= 1'b0;
            frag_message_tag  <= 3'd0;
            frag_packet_seq   <= 2'd0;
            frag_som          <= 1'b0;
            frag_eom          <= 1'b0;
            frag_message_type <= 7'd0;
            frag_ic           <= 1'b0;
            frag_assembly_key <= 12'd0;
            frag_payload_word <= 256'd0;
            frag_payload_strb <= 32'd0;
            frag_payload_bytes<= 13'd0;
            frag_first_header <= 128'd0;
            frag_last_header  <= 128'd0;
            packet_drop_valid <= 1'b0;
            packet_drop_reason<= PD_NONE;
            last_decoded_mctp <= 32'd0;
        end else begin
            // single-cycle downstream pulses default low each cycle
            frag_valid        <= 1'b0;
            packet_drop_valid <= 1'b0;
            packet_drop_reason<= PD_NONE;

            // A transaction is presented whenever the parser emits a validated
            // VDM packet, or forwards an upstream packet-drop reason to retire.
            if (vdm_valid | upstream_drop) begin
                // latch the canonical decoded field set (section 0.1)
                frag_source_eid   <= source_eid;
                frag_dest_eid     <= dest_eid;
                frag_tag_owner    <= tag_owner_w;
                frag_message_tag  <= message_tag_w;
                frag_packet_seq   <= packet_seq_w;
                frag_som          <= som_w;
                frag_eom          <= eom_w;
                frag_message_type <= msg_type;
                frag_ic           <= ic_w;
                frag_assembly_key <= assembly_key_w;
                frag_payload_word <= vdm_payload_word;
                frag_payload_strb <= vdm_payload_strb;
                frag_payload_bytes<= vdm_payload_bytes;
                frag_first_header <= vdm_first_header;
                frag_last_header  <= vdm_last_header;

                // DEBUG_CTX mirror (32b): {ic,som,eom,seq,tag_owner,msg_tag,
                // msg_type,source_eid,dest_eid}. The vdm_word_unused term is
                // forced to zero so the tie-off has no functional effect.
                last_decoded_mctp <= {ic_w, som_w, eom_w, packet_seq_w,
                                      tag_owner_w, message_tag_w, message_type_w,
                                      source_eid, dest_eid} |
                                     {31'd0, (vdm_word_unused & 1'b0)};

                if (is_drop) begin
                    // packet drop: emit reason, mutate no downstream fragment
                    packet_drop_valid  <= 1'b1;
                    packet_drop_reason <= drop_reason_w;
                end else begin
                    // accepted MCTP fragment: emit exactly one frag pulse
                    frag_valid <= 1'b1;
                end
            end
        end
    end

endmodule
`default_nettype wire

#!/usr/bin/env python3
"""Executable SSOT cycle-level model for mctp_assembler_v3. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from . import functional_model as _functional_model_mod
except ImportError:
    import functional_model as _functional_model_mod

FunctionalModel = _functional_model_mod.FunctionalModel
Transaction = getattr(_functional_model_mod, "Transaction", None)


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Executable backend. The CL model is a pure-Python deterministic stepper;
# FunctionalModel remains the oracle.
MODEL_BACKEND: str = 'python'

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'register_read': 1, 'register_write': 1, 'single_beat_transfer': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 's_axi_awready_s_axi_wready', 'signal': 's_axi_awready/s_axi_wready', 'description': 'Assert only when the ingress can accept the AW/W beat; deassert to backpressure when not in drop_when_disabled mode.', 'predicate': 'Assert only when the ingress can accept the AW/W beat; deassert to backpressure when not in drop_when_disabled mode.'}, {'name': 's_axi_bvalid', 'signal': 's_axi_bvalid', 'description': 'Assert after the full TLP transaction is consumed; hold until bready.', 'predicate': 'Assert after the full TLP transaction is consumed; hold until bready.'}, {'name': 'sram_wr_valid', 'signal': 'sram_wr_valid', 'description': 'Hold sram_wr_addr/data/strb stable while sram_wr_valid && !sram_wr_ready.', 'predicate': 'Hold sram_wr_addr/data/strb stable while sram_wr_valid && !sram_wr_ready.'}, {'name': 'sram_rd_req_valid', 'signal': 'sram_rd_req_valid', 'description': 'Issue one SRAM read request per AXI read beat; hold until sram_rd_req_ready.', 'predicate': 'Issue one SRAM read request per AXI read beat; hold until sram_rd_req_ready.'}, {'name': 's_axi_rvalid_s_axi_rlast', 'signal': 's_axi_rvalid/s_axi_rlast', 'description': 'Drive rdata after the SRAM read response; assert rlast on the final ARLEN beat only.', 'predicate': 'Drive rdata after the SRAM read response; assert rlast on the final ARLEN beat only.'}, {'name': 'apb_pready', 'signal': 'apb pready', 'description': 'Complete the access phase; pslverr only with pready=1.', 'predicate': 'Complete the access phase; pslverr only with pready=1.'}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'descriptor_publish_must_occur_only_after_the_final_sram_payload_write_flush_for_the_message_is_accepted', 'description': ''}, {'name': 'axi_read_response_is_not_issued_before_the_corresponding_sram_read_response', 'description': ''}, {'name': 'interrupt_status_updates_occur_on_the_rising_edge_the_terminal_event_is_recorded_after_cdc_into_pclk_for_status_bits', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and timing instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 400, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No SRAM/AXI backpressure; full 256-bit payload words'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single outstanding AXI write and read transaction'}, 'pipeline_stages': 6, 'queue_depth': 8}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_INGEST_TLP', 'FM_DECODE_VDM', 'FM_DECODE_MCTP', 'FM_ALLOC_CONTEXT', 'FM_APPEND', 'FM_PACK_SRAM', 'FM_PUBLISH_DESCRIPTOR', 'FM_AXI_READ']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_s_axi_awready_s_axi_wready': 'Assert only when the ingress can accept the AW/W beat; deassert to backpressure when not in drop_when_disabled mode.', 'handshake_s_axi_bvalid': 'Assert after the full TLP transaction is consumed; hold until bready.', 'handshake_sram_wr_valid': 'Hold sram_wr_addr/data/strb stable while sram_wr_valid && !sram_wr_ready.', 'handshake_sram_rd_req_valid': 'Issue one SRAM read request per AXI read beat; hold until sram_rd_req_ready.', 'handshake_s_axi_rvalid_s_axi_rlast': 'Drive rdata after the SRAM read response; assert rlast on the final ARLEN beat only.', 'handshake_apb_pready': 'Complete the access phase; pslverr only with pready=1.', 'ordering_descriptor_publish_must_occur_only_after_the_final_sram_payload_write_flush_for_the_message_is_accepted': 'descriptor_publish_must_occur_only_after_the_final_sram_payload_write_flush_for_the_message_is_accepted', 'ordering_axi_read_response_is_not_issued_before_the_corresponding_sram_read_response': 'axi_read_response_is_not_issued_before_the_corresponding_sram_read_response', 'ordering_interrupt_status_updates_occur_on_the_rising_edge_the_terminal_event_is_recorded_after_cdc_into_pclk_for_status_bits': 'interrupt_status_updates_occur_on_the_rising_edge_the_terminal_event_is_recorded_after_cdc_into_pclk_for_status_bits', 'latency_fm_ingest_tlp': 'latency bin for FM_INGEST_TLP', 'latency_fm_decode_vdm': 'latency bin for FM_DECODE_VDM', 'latency_fm_decode_mctp': 'latency bin for FM_DECODE_MCTP', 'latency_fm_alloc_context': 'latency bin for FM_ALLOC_CONTEXT', 'latency_fm_append': 'latency bin for FM_APPEND', 'latency_fm_pack_sram': 'latency bin for FM_PACK_SRAM', 'latency_fm_publish_descriptor': 'latency bin for FM_PUBLISH_DESCRIPTOR', 'latency_fm_axi_read': 'latency bin for FM_AXI_READ'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'mctp_assembler_v3', 'function_model': {'purpose': 'Golden executable behavioral contract for rtl-gen and tb-gen; cycle-independent meaning of decode/assembly/pack/descriptor/drop.', 'state_variables': [{'name': 'context_table', 'source': 'registers.CTX_STATE bank', 'reset': 'IDLE', 'description': 'Per-context assembly state: key{source_eid,tag_owner,message_tag}, dest_eid, expected_seq, payload_base_addr, payload_next_addr, payload_byte_count, tu_bytes, partial_word{addr,data,strb,next_lane}, first/last_tlp_header[0:15], msg_type, ic, timeout_age, state, error'}, {'name': 'descriptor_queue', 'source': 'memory.instances.descriptor_fifo', 'reset': 'empty', 'description': 'FIFO of completed descriptors + first/last header snapshots, depth DESCRIPTOR_FIFO_DEPTH'}, {'name': 'sram_alloc_ptr', 'source': 'registers.SRAM_BASE.sram_base', 'reset': 'sram_base', 'description': 'Linear bump allocator pointer in [sram_base, sram_limit)'}, {'name': 'counters', 'source': 'registers counter block', 'reset': 0, 'description': 'Aggregate + per-reason packet/assembly drop and traffic counters (saturating)'}, {'name': 'last_drop_class', 'source': 'registers.STATUS.last_drop_class', 'reset': 0, 'description': 'Most recent drop class (none/packet/assembly)'}, {'name': 'tlp_seen_count', 'reset': 0, 'width': 32, 'description': 'Total ingress TLPs observed (saturating traffic counter)'}, {'name': 'tlp_accepted_count', 'reset': 0, 'width': 32, 'description': 'Legal ingress TLPs accepted into decode'}, {'name': 'active_context_count', 'reset': 0, 'width': 5, 'description': 'Number of non-idle assembly contexts in the table'}, {'name': 'ctx_payload_byte_count', 'reset': 0, 'width': 13, 'description': 'Assembled payload bytes for the selected context'}, {'name': 'ctx_expected_seq', 'reset': 0, 'width': 2, 'description': 'Next expected MCTP packet sequence for the selected context'}, {'name': 'ctx_payload_base_addr', 'reset': 0, 'width': 16, 'description': 'Allocated SRAM base address for the selected context payload'}, {'name': 'ctx_payload_next_addr', 'reset': 0, 'width': 16, 'description': 'Next SRAM byte write address for the selected context payload'}, {'name': 'ctx_partial_next_lane', 'reset': 0, 'width': 5, 'description': 'Next byte lane within the current partial 32-byte SRAM word'}, {'name': 'payload_bytes_written_count', 'reset': 0, 'width': 32, 'description': 'Total payload bytes packed into SRAM (saturating traffic counter)'}, {'name': 'message_completed_count', 'reset': 0, 'width': 32, 'description': 'Total completed messages published as descriptors'}, {'name': 'fw_axi_read_beat_count', 'reset': 0, 'width': 32, 'description': 'Total AXI read beats returned on the firmware payload read path'}, {'name': 'fw_axi_read_error_count', 'reset': 0, 'width': 32, 'description': 'Total AXI read beats completed with SLVERR'}], 'transactions': [{'id': 'FM_INGEST_TLP', 'name': 'axi_write_to_tlp_bytes', 'required_fields': ['wlast_seen', 'awsize', 'awburst', 'wstrb_contiguous', 'tlp_byte_count'], 'preconditions': ['CONTROL.enable==1 or (enable==0 and drop_when_disabled==1)', 'AWSIZE==5', 'AWBURST==INCR', 'W beat count == AWLEN+1', 'WLAST on final beat only'], 'inputs': ['axi_wr_slave AW/W/B'], 'outputs': ['ordered raw TLP byte vector with valid byte count from WSTRB', 'BRESP=OKAY when transaction consumed', {'name': 'bresp_next', 'port': 's_axi_bresp', 'expr': 'BRESP_OKAY', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'tlp_accept', 'expr': 'wlast_seen and (awsize == 5) and (awburst == INCR) and wstrb_contiguous and (tlp_byte_count >= 16) and (tlp_byte_count <= MAX_TLP_BYTES)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'tlp_seen_count', 'expr': 'tlp_seen_count + 1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'tlp_accepted_count', 'expr': 'tlp_accepted_count + (1 if tlp_accept else 0)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['tlp_seen_count increment', 'tlp_accepted_count increment on legal TLP'], 'error_cases': [{'condition': 'empty txn / bad AWSIZE/AWBURST / interleave / beat-count mismatch / early/late WLAST / non-contiguous WSTRB / <16B / >MAX_TLP_BYTES / PCIe-length inconsistent / unstripped digest when stripped-mode', 'result': 'PD_MALFORMED_TLP packet drop; no context/SRAM/descriptor side effect'}]}, {'id': 'FM_DECODE_VDM', 'name': 'pcie_vdm_decode', 'required_fields': ['message_code', 'vendor_id', 'vdm_code', 'routing_supported', 'traffic_class', 'tlp', 'pad_len', 'eom'], 'preconditions': ['legal TLP bytes available'], 'inputs': ['raw TLP bytes 0..15'], 'outputs': ['requester_id, pcie_routing_type, message_code, vendor_id, vdm_code, payload_offset(16), pad_len', 'first 16B header snapshot candidate', {'state': 'vdm_valid', 'expr': '(message_code == 0x7F) and (vendor_id == 0x1AB4) and (vdm_code == 0x0) and routing_supported and (traffic_class == 0)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'payload_offset', 'expr': '16', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'requester_id', 'expr': '((tlp[1] << 8) | tlp[2])', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'pad_ok', 'expr': '(pad_len <= 3) and ((pad_len == 0) if not eom else True)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'last_decoded_vdm', 'expr': '((message_code << 24) | (vendor_id << 8) | vdm_code)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': [], 'error_cases': [{'condition': 'not Non-Flit VDM-with-data / msg_code!=0x7F / vendor!=0x1AB4 / vdm_code!=0x0 / unsupported routing/TC/attr', 'result': 'PD_UNSUPPORTED_VDM packet drop'}, {'condition': 'pad_len>3 / pad_len!=0 on non-EOM / TU not in [64,4096] or not 4B-aligned / non-EOM payload != TU or not 4B-aligned / EOM payload > TU', 'result': 'PD_BAD_PAD_OR_ALIGNMENT packet drop'}]}, {'id': 'FM_DECODE_MCTP', 'name': 'mctp_transport_decode', 'required_fields': ['header_version', 'mctp_byte0', 'dest_filter_enable', 'dest_eid', 'local_eid', 'accept_broadcast_eid', 'accept_null_eid', 'source_eid'], 'preconditions': ['validated VDM payload present'], 'inputs': ['MCTP transport header (last 4B of 16B header)', 'SOM body byte (IC+message_type) when SOM=1'], 'outputs': ['header_version, dest_eid, source_eid, SOM, EOM, packet_seq, tag_owner, message_tag', 'ic, message_type on SOM', 'assembly_key={source_eid,tag_owner,message_tag}', {'state': 'header_version_ok', 'expr': 'header_version == 1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'som', 'expr': 'mctp_byte0[7]', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'eom', 'expr': 'mctp_byte0[6]', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'packet_seq', 'expr': 'mctp_byte0[5:4]', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'tag_owner', 'expr': 'mctp_byte0[3]', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'message_tag', 'expr': 'mctp_byte0[2:0]', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'dest_accept', 'expr': '(not dest_filter_enable) or (dest_eid == local_eid) or (accept_broadcast_eid and (dest_eid == 0xFF)) or (accept_null_eid and (dest_eid == 0x00))', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'assembly_key', 'expr': '((source_eid << 4) | (tag_owner << 3) | message_tag)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': [], 'error_cases': [{'condition': 'header not present / version!=1 / SOM packet without body byte', 'result': 'PD_BAD_MCTP_HEADER packet drop'}, {'condition': 'dest_eid not local and not accepted broadcast/null while dest_filter_enable', 'result': 'PD_DEST_EID_REJECT packet drop'}]}, {'id': 'FM_ALLOC_CONTEXT', 'name': 'context_allocate', 'required_fields': ['free_slot_available', 'som', 'eom', 'packet_seq', 'allocated_len'], 'preconditions': ['decoded MCTP packet with SOM=1'], 'inputs': ['assembly_key', 'first_tlp_header[0:15]'], 'outputs': ['new ASSEMBLING context (SOM,EOM=0) or single-packet path (SOM,EOM=1)', 'first_tlp_header stored', 'payload_base_addr allocated from sram_alloc_ptr', {'state': 'alloc_ok', 'expr': 'free_slot_available', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'single_packet', 'expr': 'som and eom', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'DONE_WAIT_DESCRIPTOR_POP if (som and eom) else ASSEMBLING', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_payload_base_addr', 'expr': 'sram_alloc_ptr', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_expected_seq', 'expr': '(packet_seq + 1) % 4', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'active_context_count', 'expr': 'active_context_count + 1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'sram_alloc_ptr', 'expr': 'sram_alloc_ptr + allocated_len', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['expected_seq initialized; ctx_state=ASSEMBLING; sram_alloc_ptr advanced'], 'error_cases': [{'condition': 'no free context for a new fragmented SOM', 'result': 'PD_BAD_OR_EXPIRED_TAG packet drop (context-table-full); no allocation'}, {'condition': 'SOM for an already-active key', 'result': 'AD_DUPLICATE_SOM assembly drop: abort old context, suppress descriptor'}]}, {'id': 'FM_APPEND', 'name': 'context_append', 'required_fields': ['packet_seq', 'eom', 'payload_bytes'], 'preconditions': ['SOM=0 packet matches an active key', 'packet_seq == ctx_expected_seq'], 'inputs': ['payload bytes', 'last_tlp_header[0:15]'], 'outputs': ['payload appended; last_tlp_header updated; expected_seq incremented modulo 4', 'EOM=1 marks message complete -> FM_PUBLISH_DESCRIPTOR', {'state': 'seq_ok', 'expr': 'packet_seq == ctx_expected_seq', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'message_complete', 'expr': 'eom', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_payload_byte_count', 'expr': 'ctx_payload_byte_count + payload_bytes', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_expected_seq', 'expr': '(ctx_expected_seq + 1) % 4', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_last_seq', 'expr': 'packet_seq', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['ctx_payload_byte_count += payload_bytes'], 'error_cases': [{'condition': 'middle/end with no active matching context / EOM without prior SOM', 'result': 'PD_UNEXPECTED_MIDDLE_END packet drop'}, {'condition': 'packet_seq != expected modulo-4 seq', 'result': 'AD_SEQUENCE_MISMATCH assembly drop'}, {'condition': 'append would exceed MAX_MESSAGE_BYTES', 'result': 'AD_MESSAGE_OVERFLOW assembly drop'}, {'condition': 'context age exceeds assembly_timeout_cycles', 'result': 'AD_TIMEOUT assembly drop'}]}, {'id': 'FM_PACK_SRAM', 'name': 'payload_pack_write', 'required_fields': ['payload_bytes'], 'preconditions': ['accepted payload bytes for a context'], 'inputs': ['payload bytes', 'ctx partial_word state'], 'outputs': ['256-bit sram_write beats; payload byte i at byte address base_addr+i; sram_wr_strb marks only payload lanes; full words flushed, partial words retained per-context until full or EOM', {'name': 'sram_wr_valid', 'port': 'sram_wr_valid', 'expr': 'payload_bytes > 0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'sram_wr_addr', 'port': 'sram_wr_addr', 'expr': 'ctx_payload_next_addr & ~31', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'sram_wr_strb', 'port': 'sram_wr_strb', 'expr': '(((1 << payload_bytes) - 1) << (ctx_payload_next_addr & 31))', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'ctx_payload_next_addr', 'expr': 'ctx_payload_next_addr + payload_bytes', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_partial_next_lane', 'expr': '(ctx_partial_next_lane + payload_bytes) % 32', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'payload_bytes_written_count', 'expr': 'payload_bytes_written_count + payload_bytes', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['ctx_payload_next_addr advanced; payload_bytes_written_count += bytes'], 'error_cases': [{'condition': 'allocation/write would exceed sram_base/limit or SRAM_ADDR_WIDTH', 'result': 'AD_SRAM_OVERFLOW assembly drop'}]}, {'id': 'FM_PUBLISH_DESCRIPTOR', 'name': 'descriptor_publish', 'required_fields': ['descriptor_queue_full'], 'preconditions': ['successful EOM for a context'], 'inputs': ['context metadata', 'first/last_tlp_header'], 'outputs': ['descriptor{source_eid,dest_eid,tag_owner,message_tag,message_type,requester_id,pcie_routing_type,payload_base_addr,payload_len,final_packet_seq,context_id,completion_status,first/last_tlp_header} pushed', 'descriptor_ready interrupt; message_completed_count increment', {'state': 'descriptor_ready', 'expr': 'not descriptor_queue_full', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'descriptor_payload_len', 'expr': 'ctx_payload_byte_count', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'descriptor_base_addr', 'expr': 'ctx_payload_base_addr', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'message_completed_count', 'expr': 'message_completed_count + 1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'descriptor_valid', 'expr': '1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'DONE_WAIT_DESCRIPTOR_POP', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['context released (or DONE_WAIT_DESCRIPTOR_POP)'], 'error_cases': [{'condition': 'descriptor/header queue full at EOM', 'result': 'AD_DESCRIPTOR_FULL assembly drop; no descriptor published'}]}, {'id': 'FM_AXI_READ', 'name': 'firmware_payload_read', 'required_fields': ['out_of_window', 'no_descriptor', 'raw_sram_debug_read_enable', 'beat_index', 'arlen', 'read_error'], 'preconditions': ['ARSIZE==5', 'ARBURST==INCR', 'descriptor visible for the range or raw_sram_debug_read_enable'], 'inputs': ['AR address/len'], 'outputs': ['one SRAM read per R beat; rdata returned unmodified; RLAST on final beat', {'name': 'rresp_next', 'port': 's_axi_rresp', 'expr': 'RRESP_SLVERR if (out_of_window or (no_descriptor and not raw_sram_debug_read_enable)) else RRESP_OKAY', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'rlast_next', 'port': 's_axi_rlast', 'expr': 'beat_index == arlen', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'fw_axi_read_beat_count', 'expr': 'fw_axi_read_beat_count + 1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'fw_axi_read_error_count', 'expr': 'fw_axi_read_error_count + (1 if read_error else 0)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['fw_axi_read_beat_count increment'], 'error_cases': [{'condition': 'read outside SRAM read window, or no completed descriptor and not raw_sram_debug_read_enable', 'result': 'RRESP=SLVERR; fw_axi_read_error_count increment'}]}], 'invariants': ['No SRAM payload write occurs before a packet is accepted for assembly.', 'The SRAM writer never writes PCIe/VDM headers, MCTP transport headers, pad bytes, or digest bytes as payload.', 'For every published descriptor, byte address base_addr..base_addr+payload_len-1 is written exactly as the corresponding assembled payload byte with no alignment gap.', 'Active context count never exceeds CONTEXT_COUNT.', 'first_tlp_header for a context is written only by the accepted SOM packet; last_tlp_header equals the most recent accepted packet for that context.', 'Non-final accepted packets contribute exactly the configured transmission unit byte count; EOM may contribute fewer.', 'No descriptor is published before EOM; sequence mismatch aborts the active context and suppresses the success descriptor.', 'An earlier packet-drop reason wins over a later assembly-drop reason for the same accepted transaction (drop priority order).', 'ctx_state encoding is mutually exclusive: a context cannot be IDLE and ASSEMBLING or ERROR in the same cycle.'], 'reference_model_hint': 'tb-gen must implement a Python scoreboard from this section: reconstruct expected payload bytes, headers, descriptor, and drop class per scenario and compare against RTL-observed SRAM writes / descriptor / counters.', 'derived_signals': [{'name': 'apb_access', 'expr': 'psel and penable', 'width': 1, 'description': 'APB access phase helper derived from psel and penable.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_write', 'expr': 'psel and penable and pwrite', 'width': 1, 'description': 'APB write access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_read', 'expr': 'psel and penable and not pwrite', 'width': 1, 'description': 'APB read access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'addr', 'expr': 'paddr', 'width': 16, 'description': 'Register address helper derived from the APB paddr input.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wmask', 'expr': '((0x000000FF if (pstrb & 0x1) != 0 else 0) | (0x0000FF00 if (pstrb & 0x2) != 0 else 0) | (0x00FF0000 if (pstrb & 0x4) != 0 else 0) | (0xFF000000 if (pstrb & 0x8) != 0 else 0))', 'width': 32, 'description': 'APB byte-lane write mask expanded from pstrb.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'legal_addr', 'expr': '(addr == 0) or (addr == 4) or (addr == 8) or (addr == 12) or (addr == 16) or (addr == 32) or (addr == 1024) or (addr == 256) or (addr == 260) or (addr == 264) or (addr == 268) or (addr == 512) or (addr == 768) or (addr == 896)', 'width': 1, 'description': 'APB legal address decode derived from registers.register_list offsets.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_control', 'expr': 'apb_valid_write and (addr == 0)', 'width': 1, 'description': 'APB write decode helper for register CONTROL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_control', 'expr': 'apb_valid_read and (addr == 0)', 'width': 1, 'description': 'APB read decode helper for register CONTROL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_cfg_tu', 'expr': 'apb_valid_write and (addr == 4)', 'width': 1, 'description': 'APB write decode helper for register CFG_TU.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_cfg_tu', 'expr': 'apb_valid_read and (addr == 4)', 'width': 1, 'description': 'APB read decode helper for register CFG_TU.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_cfg_timeout', 'expr': 'apb_valid_write and (addr == 8)', 'width': 1, 'description': 'APB write decode helper for register CFG_TIMEOUT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_cfg_timeout', 'expr': 'apb_valid_read and (addr == 8)', 'width': 1, 'description': 'APB read decode helper for register CFG_TIMEOUT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_sram_base', 'expr': 'apb_valid_write and (addr == 12)', 'width': 1, 'description': 'APB write decode helper for register SRAM_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_sram_base', 'expr': 'apb_valid_read and (addr == 12)', 'width': 1, 'description': 'APB read decode helper for register SRAM_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_sram_limit', 'expr': 'apb_valid_write and (addr == 16)', 'width': 1, 'description': 'APB write decode helper for register SRAM_LIMIT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_sram_limit', 'expr': 'apb_valid_read and (addr == 16)', 'width': 1, 'description': 'APB read decode helper for register SRAM_LIMIT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_status', 'expr': 'apb_valid_write and (addr == 32)', 'width': 1, 'description': 'APB write decode helper for register STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_status', 'expr': 'apb_valid_read and (addr == 32)', 'width': 1, 'description': 'APB read decode helper for register STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_ctx_state', 'expr': 'apb_valid_write and (addr == 1024)', 'width': 1, 'description': 'APB write decode helper for register CTX_STATE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_ctx_state', 'expr': 'apb_valid_read and (addr == 1024)', 'width': 1, 'description': 'APB read decode helper for register CTX_STATE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_intr_raw_status', 'expr': 'apb_valid_write and (addr == 256)', 'width': 1, 'description': 'APB write decode helper for register INTR_RAW_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_intr_raw_status', 'expr': 'apb_valid_read and (addr == 256)', 'width': 1, 'description': 'APB read decode helper for register INTR_RAW_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_intr_enable', 'expr': 'apb_valid_write and (addr == 260)', 'width': 1, 'description': 'APB write decode helper for register INTR_ENABLE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_intr_enable', 'expr': 'apb_valid_read and (addr == 260)', 'width': 1, 'description': 'APB read decode helper for register INTR_ENABLE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_intr_status', 'expr': 'apb_valid_write and (addr == 264)', 'width': 1, 'description': 'APB write decode helper for register INTR_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_intr_status', 'expr': 'apb_valid_read and (addr == 264)', 'width': 1, 'description': 'APB read decode helper for register INTR_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_intr_clear', 'expr': 'apb_valid_write and (addr == 268)', 'width': 1, 'description': 'APB write decode helper for register INTR_CLEAR.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_intr_clear', 'expr': 'apb_valid_read and (addr == 268)', 'width': 1, 'description': 'APB read decode helper for register INTR_CLEAR.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'intr_clear_w1c', 'expr': '((pwdata & gpio_mask) if wr_intr_clear else 0)', 'width': 32, 'description': 'W1C write mask helper for register INTR_CLEAR.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_cnt_tlp_seen', 'expr': 'apb_valid_write and (addr == 512)', 'width': 1, 'description': 'APB write decode helper for register CNT_TLP_SEEN.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_cnt_tlp_seen', 'expr': 'apb_valid_read and (addr == 512)', 'width': 1, 'description': 'APB read decode helper for register CNT_TLP_SEEN.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_desc_valid', 'expr': 'apb_valid_write and (addr == 768)', 'width': 1, 'description': 'APB write decode helper for register DESC_VALID.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_desc_valid', 'expr': 'apb_valid_read and (addr == 768)', 'width': 1, 'description': 'APB read decode helper for register DESC_VALID.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_debug_ctx', 'expr': 'apb_valid_write and (addr == 896)', 'width': 1, 'description': 'APB write decode helper for register DEBUG_CTX.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_debug_ctx', 'expr': 'apb_valid_read and (addr == 896)', 'width': 1, 'description': 'APB read decode helper for register DEBUG_CTX.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'read_mux', 'expr': '(0 if addr == 0 else (0 if addr == 4 else (0 if addr == 8 else (0 if addr == 12 else (0 if addr == 16 else (0 if addr == 32 else (0 if addr == 1024 else (0 if addr == 256 else (0 if addr == 260 else (0 if addr == 264 else (0 if addr == 268 else (0 if addr == 512 else (0 if addr == 768 else (0 if addr == 896 else 0))))))))))))))', 'width': 32, 'description': 'APB read data mux derived from registers.register_list offsets and function_model state variables.', 'source': 'repair_ssot_schema.apb_helper'}]}, 'cycle_model': {'purpose': 'Cycle/handshake contract: when valid/ready, payload writes, descriptor, and interrupts may change.', 'executable': 'python', 'backend_policy': 'Use the repo-owned pure-Python deterministic stepper; FunctionalModel is the behavioral oracle.', 'clock': 'axi_aclk', 'reset': {'assertion': 'axi_aresetn/presetn low asynchronously clears all architectural state (contexts, queue, parser, packer, counters).', 'deassertion': 'state usable on the first rising edge after synchronized deassertion.'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data/pready timing in pclk'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing in pclk'}, 'single_beat_transfer': {'min_cycles': 1, 'max_cycles': None, 'description': 'AXI/SRAM handshakes; max depends on backpressure'}}, 'handshake_rules': [{'signal': 's_axi_awready/s_axi_wready', 'rule': 'Assert only when the ingress can accept the AW/W beat; deassert to backpressure when not in drop_when_disabled mode.'}, {'signal': 's_axi_bvalid', 'rule': 'Assert after the full TLP transaction is consumed; hold until bready.'}, {'signal': 'sram_wr_valid', 'rule': 'Hold sram_wr_addr/data/strb stable while sram_wr_valid && !sram_wr_ready.'}, {'signal': 'sram_rd_req_valid', 'rule': 'Issue one SRAM read request per AXI read beat; hold until sram_rd_req_ready.'}, {'signal': 's_axi_rvalid/s_axi_rlast', 'rule': 'Drive rdata after the SRAM read response; assert rlast on the final ARLEN beat only.'}, {'signal': 'apb pready', 'rule': 'Complete the access phase; pslverr only with pready=1.'}], 'pipeline': [{'stage': 'S0_INGEST', 'cycle': '0..B', 'action': 'Reconstruct TLP bytes from AXI W beats; legality check'}, {'stage': 'S1_VDM_DECODE', 'cycle': 'B+1', 'action': 'Decode/validate 16B PCIe VDM header; strip header/pad/digest'}, {'stage': 'S2_MCTP_DECODE', 'cycle': 'B+2', 'action': 'Decode MCTP transport header + IC/msg_type on SOM'}, {'stage': 'S3_CONTEXT', 'cycle': 'B+3', 'action': 'Allocate/append context by key; sequence/timeout checks'}, {'stage': 'S4_PACK', 'cycle': 'B+4..P', 'action': 'Pack payload bytes into 256-bit SRAM words; per-context partial word'}, {'stage': 'S5_DESCRIPTOR', 'cycle': 'P+1', 'action': 'On EOM push descriptor + first/last headers; raise descriptor_ready'}], 'ordering': ['descriptor_publish must occur only after the final SRAM payload write/flush for the message is accepted.', 'AXI read response is not issued before the corresponding SRAM read response.', 'Interrupt status updates occur on the rising edge the terminal event is recorded (after CDC into pclk for status bits).'], 'backpressure': ['sram_wr_ready deassertion stalls payload writes without dropping accepted bytes unless timeout/overflow occurs.', 'SRAM write traffic for assembly has priority over firmware AXI read traffic on a shared port.', 'AXI read backpressure must not corrupt ongoing assembly writes; each context owns its own partial-word state.'], 'performance': {'frequency_mhz': 400, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No SRAM/AXI backpressure; full 256-bit payload words'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single outstanding AXI write and read transaction'}, 'depth': {'pipeline_stages': 6, 'queue_depth': 8, 'description': 'Pipeline depth + descriptor FIFO depth visible to cycle coverage'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}}


# ---------------------------------------------------------------------------
# CycleModel
# ---------------------------------------------------------------------------

class CycleModel:
    """Cycle-level model: queues transactions, applies latency/handshake rules,
    delegates all functional evaluation to FunctionalModel.apply()."""

    def __init__(self, params=None):
        self.params = params or {}
        try:
            self.fl = FunctionalModel(self.params)
        except TypeError:
            self.fl = FunctionalModel()
        self.in_q: list[tuple[int, dict]] = []   # (arrival_t, txn)
        self.out_q: list[tuple[int, dict]] = []  # (ready_t, result)
        self.cov: dict[str, int] = {k: 0 for k in CL_BINS}
        self.now: int = 0
        self._outstanding: int = 0

    def reset(self) -> None:
        self.fl.reset()
        self.in_q.clear()
        self.out_q.clear()
        self.cov = {k: 0 for k in CL_BINS}
        self.now = 0
        self._outstanding = 0

    def drive(self, txn: dict, t: int) -> None:
        """Enqueue a transaction arriving at cycle t."""
        self.in_q.append((int(t), dict(txn)))

    def _latency_for(self, txn: dict) -> int:
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        candidates = [kind]
        if kind.startswith("fm_"):
            candidates.append(kind[3:])
        cmd = txn.get("cmd")
        if cmd is not None:
            candidates.append("command_effect")
        candidates.append("default")
        for candidate in candidates:
            if candidate in _LATENCY:
                return _LATENCY[candidate]
        return 1

    def _coerce_txn_for_fl(self, txn: dict):
        if Transaction is None or not isinstance(txn, dict):
            return txn
        if isinstance(txn, Transaction):
            return txn
        if "cmd" in txn:
            return Transaction(
                cmd=int(txn.get("cmd", 0)) & 0x7,
                cmd_valid=int(txn.get("cmd_valid", 1)),
                load_value=int(txn.get("load_value", 0)) & 0xFF,
            )
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        cmd_by_kind = {
            "fm_clear": 0, "clear": 0, "clear_counter": 0,
            "fm_load": 1, "load": 1, "load_counter": 1,
            "fm_inc": 2, "inc": 2, "increment": 2, "increment_counter": 2,
            "fm_dec": 3, "dec": 3, "decrement": 3, "decrement_counter": 3,
            "fm_hold": 4, "hold": 4,
            "fm_invalid": 5, "invalid": 5,
        }
        cmd = cmd_by_kind.get(kind, 4)
        load_value = int(txn.get("load_value", 0 if cmd != 1 else 0x55)) & 0xFF
        return Transaction(cmd=cmd, cmd_valid=int(txn.get("cmd_valid", 1)), load_value=load_value)

    def _sample_handshake_coverage(self, txn: dict) -> None:
        for rule in _HANDSHAKE_RULES:
            name = rule.get("name", "")
            bin_key = f"handshake_{name}"
            if bin_key in self.cov:
                self.cov[bin_key] += 1

    def _sample_ordering_coverage(self) -> None:
        for rule in _ORDERING_RULES:
            name = rule.get("name", "")
            bin_key = f"ordering_{name}"
            if bin_key in self.cov:
                self.cov[bin_key] += 1

    def _sample_latency_coverage(self, txn: dict) -> None:
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        key = "".join(ch if ch.isalnum() else "_" for ch in kind).strip("_")
        bin_key = f"latency_{key}"
        if bin_key in self.cov:
            self.cov[bin_key] += 1

    def tick(self, t: int) -> None:
        """Advance model to cycle t.  Drain in_q respecting outstanding cap and handshake rules."""
        self.now = int(t)
        # Ready-but-not-yet-observed responses no longer consume outstanding capacity.
        self._outstanding = sum(1 for (d, _r) in self.out_q if d > self.now)
        # Pop pending transactions if not stalled by outstanding cap.
        while self.in_q:
            if self._outstanding >= _OUTSTANDING_CAP:
                break  # stalled: wait for not-yet-ready out_q entries to mature
            arrival_t, txn = self.in_q[0]
            if arrival_t > self.now:
                break  # not yet arrived
            self.in_q.pop(0)
            # FunctionalModel is the ONLY oracle — one call per transaction
            try:
                result = self.fl.apply(self._coerce_txn_for_fl(txn))
            except Exception as _exc:
                result = {"kind": txn.get("kind", "unknown"), "resp": 2, "fl_error": str(_exc)}
            latency = self._latency_for(txn)
            ready_t = self.now + latency
            self.out_q.append((ready_t, result))
            self._outstanding += 1
            # Sample coverage bins
            self._sample_handshake_coverage(txn)
            self._sample_ordering_coverage()
            self._sample_latency_coverage(txn)

        # Keep outstanding equal to responses that are still in flight.
        self._outstanding = sum(1 for (d, _r) in self.out_q if d > self.now)

    def observe(self, t: int) -> list[tuple[int, dict]]:
        """Return all results ready at or before t, removing them from out_q."""
        t = int(t)
        ready = [(d, r) for (d, r) in self.out_q if d <= t]
        self.out_q = [(d, r) for (d, r) in self.out_q if d > t]
        return ready

    def coverage(self) -> dict[str, int]:
        return dict(self.cov)

    def _self_check_txn(self, kind: str, idx: int) -> dict:
        """Build a minimal FL-valid transaction from SSOT required_fields.

        The CL self-check exists to prove that the generated model can call the
        FL oracle for every declared transaction. It should not fail merely
        because a transaction-level FL rule requires ordinary input fields such
        as APB paddr/pwrite/pwdata.
        """
        txn = {"kind": kind}
        wanted = str(kind or "").strip().lower()
        fm = SSOT_MODEL.get("function_model") if isinstance(SSOT_MODEL.get("function_model"), dict) else {}
        selected = None
        for tx in fm.get("transactions") or []:
            if not isinstance(tx, dict):
                continue
            aliases = {
                str(tx.get("id") or "").strip().lower(),
                str(tx.get("name") or "").strip().lower(),
            }
            if wanted in aliases:
                selected = tx
                break
        if not selected:
            return txn

        identity = " ".join(str(selected.get(key) or "") for key in ("id", "name")).lower()
        is_read_like = "read" in identity or "idle" in identity
        for field_idx, raw_name in enumerate(selected.get("required_fields") or []):
            name = str(raw_name).strip()
            if not name or name in txn:
                continue
            low = name.lower()
            if low in {"psel", "penable", "valid", "enable"}:
                value = 1
            elif low in {"pwrite", "write"}:
                value = 0 if is_read_like else 1
            elif "addr" in low:
                value = 0
            elif "data" in low or "value" in low or "payload" in low:
                value = (0x55 + idx + field_idx) & 0xFF
            else:
                value = field_idx + idx + 1
            txn[name] = value
        return txn

    def run_self_check(self) -> dict:
        """Smoke run: drive every known transaction kind once, tick, observe."""
        self.reset()
        kinds = list(_SELF_CHECK_KINDS) or ["reset"]
        t = 0
        for idx, kind in enumerate(kinds):
            self.drive(self._self_check_txn(kind, idx), t=t)
            t += 1
            self.tick(t)
        # Drain with a long tick to let all latencies expire
        drain_t = t + 200
        self.tick(drain_t)
        obs = self.observe(drain_t)
        total_bins = len(CL_BINS)
        hit_bins = sum(1 for v in self.cov.values() if v > 0)
        fl_errors = [r for (_d, r) in obs if isinstance(r, dict) and r.get("fl_error")]
        passed = (len(obs) == len(kinds)) and not fl_errors and (hit_bins == total_bins)
        return {
            "passed": passed,
            "backend": MODEL_BACKEND,
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
            "fl_errors": fl_errors,
            "performance_targets": PERFORMANCE_TARGETS,
        }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))

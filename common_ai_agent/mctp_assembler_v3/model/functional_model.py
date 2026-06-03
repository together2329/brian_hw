#!/usr/bin/env python3
"""Executable SSOT functional model for mctp_assembler_v3.

Generated from yaml/mctp_assembler_v3.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'mctp_assembler_v3', 'parameters': {'BRESP_OKAY': 0, 'RRESP_OKAY': 0, 'RRESP_SLVERR': 2, 'INCR': 1, 'ASSEMBLING': 1, 'DONE_WAIT_DESCRIPTOR_POP': 3, 'AXI_ADDR_WIDTH': 16, 'AXI_DATA_WIDTH': 256, 'AXI_STRB_WIDTH': 32, 'SRAM_ADDR_WIDTH': 16, 'SRAM_DATA_WIDTH': 256, 'CONTEXT_COUNT': 15, 'TLP_HEADER_SNAPSHOT_BYTES': 16, 'MIN_TRANSMISSION_UNIT_BYTES': 64, 'MAX_TRANSMISSION_UNIT_BYTES': 4096, 'TRANSMISSION_UNIT_ALIGN_BYTES': 4, 'MAX_TLP_BYTES': 4112, 'MAX_TLP_BEATS': 129, 'MAX_MESSAGE_BYTES': 4096, 'BASELINE_MTU_BYTES': 64, 'DESCRIPTOR_FIFO_DEPTH': 8, 'TIMEOUT_COUNTER_WIDTH': 24, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'mctp_assembler_v3', 'file': 'rtl/mctp_assembler_v3.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Bounded HW receiver that validates PCIe VDM MCTP TLPs from a 256-bit AXI4 write slave, assembles interleaved fragmented MCTP messages by {source_eid,tag_owner,message_tag}, packs payload-only bytes into a 256-bit SRAM, publishes completed-message descriptors with first/last TLP header snapshots, and exposes APB control/status plus an AXI4 read path for firmware payload access.', 'reference_spec': 'DMTF DSP0236 v1.3.3 + DSP0238 v1.4.0', 'target': {'technology': 'generic', 'clock_freq_mhz': 400, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'context_table', 'type': 'register_file', 'depth': 15, 'width': 512, 'read_ports': 2, 'write_ports': 1, 'latency': 0, 'description': 'Per-context assembly state incl. 16B first/last header snapshots and partial 256-bit pack buffer'}, {'name': 'descriptor_fifo', 'type': 'fifo', 'depth': 8, 'width': 512, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'Completed-message descriptor + first/last header snapshots until pop'}], 'note': 'Payload bytes live in EXTERNAL 256-bit SRAM via sram_write/sram_read; not stored inside this IP.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 16, 'byte_addressable': True, 'channel_stride': 64, 'channel_base': 1024, 'num_channels': 15}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'CONTROL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Global control/policy', 'write_side_effects': ['soft_reset clears contexts/queue/parser/packer/read state; does not rewrite persistent config', 'descriptor_pop retires the oldest descriptor', 'counter_clear clears non-sticky counters'], 'fields': [{'name': 'enable', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable AXI write ingress', 'description': 'Ingress enable'}, {'name': 'drop_when_disabled', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': 'Accept+packet-drop while disabled instead of backpressure', 'description': 'Disabled drop mode'}, {'name': 'soft_reset', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'write_effect': 'Self-clearing soft reset pulse', 'description': 'Soft reset'}, {'name': 'dest_filter_enable', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'write_effect': 'Enable destination EID filtering', 'description': 'Dest EID filter'}, {'name': 'accept_broadcast_eid', 'bits': [4, 4], 'access': 'rw', 'reset': 0, 'write_effect': 'Accept broadcast EID', 'description': 'Broadcast accept'}, {'name': 'accept_null_eid', 'bits': [5, 5], 'access': 'rw', 'reset': 0, 'write_effect': 'Accept null EID', 'description': 'Null EID accept'}, {'name': 'raw_sram_debug_read_enable', 'bits': [6, 6], 'access': 'rw', 'reset': 0, 'write_effect': 'Allow AXI reads outside completed descriptor ranges', 'description': 'Raw SRAM debug read'}, {'name': 'descriptor_pop', 'bits': [7, 7], 'access': 'rw', 'reset': 0, 'write_effect': '1=pop oldest descriptor (self-clearing)', 'description': 'Descriptor pop command'}, {'name': 'counter_clear', 'bits': [8, 8], 'access': 'rw', 'reset': 0, 'write_effect': '1=clear counters (self-clearing)', 'description': 'Counter clear command'}, {'name': 'local_eid', 'bits': [23, 16], 'access': 'rw', 'reset': 0, 'write_effect': 'Configured local endpoint ID', 'description': 'Local EID'}, {'name': 'debug_context_select', 'bits': [31, 24], 'access': 'rw', 'reset': 0, 'write_effect': 'Select context for DEBUG_CTX mirror', 'description': 'Debug context select'}]}, {'name': 'CFG_TU', 'offset': 4, 'width': 32, 'access': 'rw', 'reset': 268435520, 'category': 'control', 'description': 'Transmission unit / message size config', 'fields': [{'name': 'transmission_unit_bytes', 'bits': [12, 0], 'access': 'rw', 'reset': 64, 'write_effect': 'Configured TU 64..4096, 4-byte aligned', 'description': 'TU bytes'}, {'name': 'reserved_15_13', 'bits': [15, 13], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}, {'name': 'max_message_bytes', 'bits': [28, 16], 'access': 'rw', 'reset': 4096, 'write_effect': 'Max assembled message bytes', 'description': 'Max message bytes'}, {'name': 'reserved_31_29', 'bits': [31, 29], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'CFG_TIMEOUT', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Assembly timeout cycles', 'fields': [{'name': 'assembly_timeout_cycles', 'bits': [23, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Context age limit in axi_aclk cycles (0=disabled)', 'description': 'Timeout cycles'}, {'name': 'reserved_31_24', 'bits': [31, 24], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'SRAM_BASE', 'offset': 12, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Payload SRAM base byte address (bump allocator start)', 'fields': [{'name': 'sram_base', 'bits': [15, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Allocator start', 'description': 'SRAM base'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'SRAM_LIMIT', 'offset': 16, 'width': 32, 'access': 'rw', 'reset': 65535, 'category': 'control', 'description': 'Payload SRAM limit byte address (exclusive)', 'fields': [{'name': 'sram_limit', 'bits': [15, 0], 'access': 'rw', 'reset': 65535, 'write_effect': 'Allocator limit', 'description': 'SRAM limit'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'STATUS', 'offset': 32, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Global non-destructive status', 'fields': [{'name': 'ingress_busy', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'Ingress active'}, {'name': 'axi_read_busy', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': 'AXI read active'}, {'name': 'sram_write_busy', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'description': 'SRAM write active'}, {'name': 'sram_read_busy', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': 'SRAM read active'}, {'name': 'descriptor_available', 'bits': [4, 4], 'access': 'ro', 'reset': 0, 'description': 'Descriptor queue non-empty'}, {'name': 'descriptor_queue_full', 'bits': [5, 5], 'access': 'ro', 'reset': 0, 'description': 'Descriptor queue full'}, {'name': 'context_active_any', 'bits': [6, 6], 'access': 'ro', 'reset': 0, 'description': 'Any context active'}, {'name': 'context_error_any', 'bits': [7, 7], 'access': 'ro', 'reset': 0, 'description': 'Any context in error'}, {'name': 'packet_drop_seen', 'bits': [8, 8], 'access': 'ro', 'reset': 0, 'description': 'A packet drop occurred'}, {'name': 'assembly_drop_seen', 'bits': [9, 9], 'access': 'ro', 'reset': 0, 'description': 'An assembly drop occurred'}, {'name': 'active_context_count', 'bits': [15, 10], 'access': 'ro', 'reset': 0, 'description': 'Active context count'}, {'name': 'last_drop_class', 'bits': [17, 16], 'access': 'ro', 'reset': 0, 'description': '0=none,1=packet,2=assembly'}, {'name': 'last_drop_reason', 'bits': [23, 18], 'access': 'ro', 'reset': 0, 'description': 'Last drop reason code'}, {'name': 'last_error_context_id', 'bits': [27, 24], 'access': 'ro', 'reset': 0, 'description': 'Context id of last error'}, {'name': 'reserved_31_28', 'bits': [31, 28], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'CTX_STATE', 'offset': 1024, 'width': 32, 'access': 'ro', 'reset': 0, 'repeat': 15, 'stride': 64, 'category': 'channel', 'description': 'Per-context FSM/key snapshot (context[0..CONTEXT_COUNT-1]); full per-Q bank includes payload/header mirrors at +0x04..+0x3C', 'fields': [{'name': 'ctx_state', 'bits': [1, 0], 'access': 'ro', 'reset': 0, 'description': '0=IDLE,1=ASSEMBLING,2=ERROR,3=DONE_WAIT_DESCRIPTOR_POP'}, {'name': 'ctx_valid', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'description': 'Slot owns active/completed context'}, {'name': 'ctx_error', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': 'Slot in error'}, {'name': 'ctx_source_eid', 'bits': [11, 4], 'access': 'ro', 'reset': 0, 'description': 'Active source EID'}, {'name': 'ctx_message_tag', 'bits': [14, 12], 'access': 'ro', 'reset': 0, 'description': 'Active message tag'}, {'name': 'ctx_tag_owner', 'bits': [15, 15], 'access': 'ro', 'reset': 0, 'description': 'Active tag owner'}, {'name': 'ctx_expected_seq', 'bits': [17, 16], 'access': 'ro', 'reset': 0, 'description': 'Expected modulo-4 seq'}, {'name': 'ctx_last_seq', 'bits': [19, 18], 'access': 'ro', 'reset': 0, 'description': 'Last accepted seq'}, {'name': 'ctx_message_type', 'bits': [26, 20], 'access': 'ro', 'reset': 0, 'description': 'Recorded message type'}, {'name': 'ctx_last_drop_reason', 'bits': [31, 27], 'access': 'ro', 'reset': 0, 'description': 'Per-context last drop reason'}]}, {'name': 'INTR_RAW_STATUS', 'offset': 256, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'interrupt', 'description': 'Raw interrupt event state before masking', 'fields': [{'name': 'raw', 'bits': [8, 0], 'access': 'ro', 'reset': 0, 'description': 'Raw bits: descriptor_ready,packet_drop,assembly_drop,context_timeout,sram_overflow,descriptor_queue_full,axi_write_malformed,axi_read_error,fatal_internal_error'}, {'name': 'reserved_31_9', 'bits': [31, 9], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'INTR_ENABLE', 'offset': 260, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt mask', 'fields': [{'name': 'enable', 'bits': [8, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Per-bit interrupt enable', 'description': 'Interrupt enable mask'}, {'name': 'reserved_31_9', 'bits': [31, 9], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'INTR_STATUS', 'offset': 264, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'interrupt', 'description': 'Masked interrupt status (raw & enable)', 'fields': [{'name': 'status', 'bits': [8, 0], 'access': 'ro', 'reset': 0, 'description': 'Masked interrupt status'}, {'name': 'reserved_31_9', 'bits': [31, 9], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'INTR_CLEAR', 'offset': 268, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'interrupt', 'description': 'Write-one-to-clear interrupt bits', 'fields': [{'name': 'clear', 'bits': [8, 0], 'access': 'w1c', 'reset': 0, 'write_effect': 'Write 1 clears the matching raw/status bit', 'description': 'W1C clear'}, {'name': 'reserved_31_9', 'bits': [31, 9], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'CNT_TLP_SEEN', 'offset': 512, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'counter', 'description': 'Saturating traffic/drop counters block base (0x200..0x27C): tlp_seen, tlp_accepted, message_completed, payload_bytes_written, fw_axi_read_beat, fw_axi_read_error, packet_drop, assembly_drop, then 8 PD_* reason counters and 6 AD_* reason counters', 'fields': [{'name': 'count', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'tlp_seen_count (block base; see description for full layout)'}]}, {'name': 'DESC_VALID', 'offset': 768, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'descriptor', 'description': 'Oldest completed descriptor: valid + key + status (full descriptor body at 0x300..0x34C including payload_base_addr, payload_len, requester_id, pcie_routing_type, first/last_tlp_header[0:15])', 'fields': [{'name': 'descriptor_valid', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'Oldest descriptor valid'}, {'name': 'completion_status', 'bits': [3, 1], 'access': 'ro', 'reset': 0, 'description': 'Completion status code'}, {'name': 'source_eid', 'bits': [11, 4], 'access': 'ro', 'reset': 0, 'description': 'Source EID'}, {'name': 'destination_eid', 'bits': [19, 12], 'access': 'ro', 'reset': 0, 'description': 'Destination EID'}, {'name': 'message_tag', 'bits': [22, 20], 'access': 'ro', 'reset': 0, 'description': 'Message tag'}, {'name': 'tag_owner', 'bits': [23, 23], 'access': 'ro', 'reset': 0, 'description': 'Tag owner'}, {'name': 'message_type', 'bits': [30, 24], 'access': 'ro', 'reset': 0, 'description': 'Message type'}, {'name': 'context_id', 'bits': [31, 31], 'access': 'ro', 'reset': 0, 'description': 'Context id low bit (full id in DESC body)'}]}, {'name': 'DEBUG_CTX', 'offset': 896, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'debug', 'description': 'Selected-context mirror + FSM states (parser/axi-wr/axi-rd/sram-pack/sram-read) + last decoded VDM/MCTP fields', 'fields': [{'name': 'parser_state', 'bits': [3, 0], 'access': 'ro', 'reset': 0, 'description': 'Parser FSM state'}, {'name': 'axi_wr_state', 'bits': [7, 4], 'access': 'ro', 'reset': 0, 'description': 'AXI write ingress FSM state'}, {'name': 'axi_rd_state', 'bits': [11, 8], 'access': 'ro', 'reset': 0, 'description': 'AXI read FSM state'}, {'name': 'sram_pack_state', 'bits': [15, 12], 'access': 'ro', 'reset': 0, 'description': 'SRAM packer state'}, {'name': 'sram_read_state', 'bits': [19, 16], 'access': 'ro', 'reset': 0, 'description': 'SRAM read req/rsp state'}, {'name': 'selected_ctx', 'bits': [27, 20], 'access': 'ro', 'reset': 0, 'description': 'Mirrored debug_context_select'}, {'name': 'reserved_31_28', 'bits': [31, 28], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}]}, 'function_model': {'purpose': 'Golden executable behavioral contract for rtl-gen and tb-gen; cycle-independent meaning of decode/assembly/pack/descriptor/drop.', 'state_variables': [{'name': 'context_table', 'source': 'registers.CTX_STATE bank', 'reset': 'IDLE', 'description': 'Per-context assembly state: key{source_eid,tag_owner,message_tag}, dest_eid, expected_seq, payload_base_addr, payload_next_addr, payload_byte_count, tu_bytes, partial_word{addr,data,strb,next_lane}, first/last_tlp_header[0:15], msg_type, ic, timeout_age, state, error'}, {'name': 'descriptor_queue', 'source': 'memory.instances.descriptor_fifo', 'reset': 'empty', 'description': 'FIFO of completed descriptors + first/last header snapshots, depth DESCRIPTOR_FIFO_DEPTH'}, {'name': 'sram_alloc_ptr', 'source': 'registers.SRAM_BASE.sram_base', 'reset': 'sram_base', 'description': 'Linear bump allocator pointer in [sram_base, sram_limit)'}, {'name': 'counters', 'source': 'registers counter block', 'reset': 0, 'description': 'Aggregate + per-reason packet/assembly drop and traffic counters (saturating)'}, {'name': 'last_drop_class', 'source': 'registers.STATUS.last_drop_class', 'reset': 0, 'description': 'Most recent drop class (none/packet/assembly)'}, {'name': 'tlp_seen_count', 'reset': 0, 'width': 32, 'description': 'Total ingress TLPs observed (saturating traffic counter)'}, {'name': 'tlp_accepted_count', 'reset': 0, 'width': 32, 'description': 'Legal ingress TLPs accepted into decode'}, {'name': 'active_context_count', 'reset': 0, 'width': 5, 'description': 'Number of non-idle assembly contexts in the table'}, {'name': 'ctx_payload_byte_count', 'reset': 0, 'width': 13, 'description': 'Assembled payload bytes for the selected context'}, {'name': 'ctx_expected_seq', 'reset': 0, 'width': 2, 'description': 'Next expected MCTP packet sequence for the selected context'}, {'name': 'ctx_payload_base_addr', 'reset': 0, 'width': 16, 'description': 'Allocated SRAM base address for the selected context payload'}, {'name': 'ctx_payload_next_addr', 'reset': 0, 'width': 16, 'description': 'Next SRAM byte write address for the selected context payload'}, {'name': 'ctx_partial_next_lane', 'reset': 0, 'width': 5, 'description': 'Next byte lane within the current partial 32-byte SRAM word'}, {'name': 'payload_bytes_written_count', 'reset': 0, 'width': 32, 'description': 'Total payload bytes packed into SRAM (saturating traffic counter)'}, {'name': 'message_completed_count', 'reset': 0, 'width': 32, 'description': 'Total completed messages published as descriptors'}, {'name': 'fw_axi_read_beat_count', 'reset': 0, 'width': 32, 'description': 'Total AXI read beats returned on the firmware payload read path'}, {'name': 'fw_axi_read_error_count', 'reset': 0, 'width': 32, 'description': 'Total AXI read beats completed with SLVERR'}], 'transactions': [{'id': 'FM_INGEST_TLP', 'name': 'axi_write_to_tlp_bytes', 'required_fields': ['wlast_seen', 'awsize', 'awburst', 'wstrb_contiguous', 'tlp_byte_count'], 'output_rules': [{'name': 'bresp_next', 'expr': 'BRESP_OKAY', 'width': 2, 'port': 's_axi_bresp'}], 'state_updates': [{'name': 'tlp_accept', 'expr': 'wlast_seen and (awsize == 5) and (awburst == INCR) and wstrb_contiguous and (tlp_byte_count >= 16) and (tlp_byte_count <= MAX_TLP_BYTES)', 'width': 1}, {'name': 'tlp_seen_count', 'expr': 'tlp_seen_count + 1', 'width': 32}, {'name': 'tlp_accepted_count', 'expr': 'tlp_accepted_count + (1 if tlp_accept else 0)', 'width': 32}], 'preconditions': ['CONTROL.enable==1 or (enable==0 and drop_when_disabled==1)', 'AWSIZE==5', 'AWBURST==INCR', 'W beat count == AWLEN+1', 'WLAST on final beat only'], 'inputs': ['axi_wr_slave AW/W/B'], 'outputs': ['ordered raw TLP byte vector with valid byte count from WSTRB', 'BRESP=OKAY when transaction consumed', {'name': 'bresp_next', 'port': 's_axi_bresp', 'expr': 'BRESP_OKAY', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'tlp_accept', 'expr': 'wlast_seen and (awsize == 5) and (awburst == INCR) and wstrb_contiguous and (tlp_byte_count >= 16) and (tlp_byte_count <= MAX_TLP_BYTES)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'tlp_seen_count', 'expr': 'tlp_seen_count + 1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'tlp_accepted_count', 'expr': 'tlp_accepted_count + (1 if tlp_accept else 0)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['tlp_seen_count increment', 'tlp_accepted_count increment on legal TLP'], 'error_cases': [{'condition': 'empty txn / bad AWSIZE/AWBURST / interleave / beat-count mismatch / early/late WLAST / non-contiguous WSTRB / <16B / >MAX_TLP_BYTES / PCIe-length inconsistent / unstripped digest when stripped-mode', 'result': 'PD_MALFORMED_TLP packet drop; no context/SRAM/descriptor side effect'}]}, {'id': 'FM_DECODE_VDM', 'name': 'pcie_vdm_decode', 'required_fields': ['message_code', 'vendor_id', 'vdm_code', 'routing_supported', 'traffic_class', 'tlp', 'pad_len', 'eom'], 'state_updates': [{'name': 'vdm_valid', 'expr': '(message_code == 0x7F) and (vendor_id == 0x1AB4) and (vdm_code == 0x0) and routing_supported and (traffic_class == 0)', 'width': 1}, {'name': 'payload_offset', 'expr': '16', 'width': 5}, {'name': 'requester_id', 'expr': '((tlp[1] << 8) | tlp[2])', 'width': 16}, {'name': 'pad_ok', 'expr': '(pad_len <= 3) and ((pad_len == 0) if not eom else True)', 'width': 1}, {'name': 'last_decoded_vdm', 'expr': '((message_code << 24) | (vendor_id << 8) | vdm_code)', 'width': 32}], 'preconditions': ['legal TLP bytes available'], 'inputs': ['raw TLP bytes 0..15'], 'outputs': ['requester_id, pcie_routing_type, message_code, vendor_id, vdm_code, payload_offset(16), pad_len', 'first 16B header snapshot candidate', {'state': 'vdm_valid', 'expr': '(message_code == 0x7F) and (vendor_id == 0x1AB4) and (vdm_code == 0x0) and routing_supported and (traffic_class == 0)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'payload_offset', 'expr': '16', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'requester_id', 'expr': '((tlp[1] << 8) | tlp[2])', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'pad_ok', 'expr': '(pad_len <= 3) and ((pad_len == 0) if not eom else True)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'last_decoded_vdm', 'expr': '((message_code << 24) | (vendor_id << 8) | vdm_code)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': [], 'error_cases': [{'condition': 'not Non-Flit VDM-with-data / msg_code!=0x7F / vendor!=0x1AB4 / vdm_code!=0x0 / unsupported routing/TC/attr', 'result': 'PD_UNSUPPORTED_VDM packet drop'}, {'condition': 'pad_len>3 / pad_len!=0 on non-EOM / TU not in [64,4096] or not 4B-aligned / non-EOM payload != TU or not 4B-aligned / EOM payload > TU', 'result': 'PD_BAD_PAD_OR_ALIGNMENT packet drop'}], 'output_rules': []}, {'id': 'FM_DECODE_MCTP', 'name': 'mctp_transport_decode', 'required_fields': ['header_version', 'mctp_byte0', 'dest_filter_enable', 'dest_eid', 'local_eid', 'accept_broadcast_eid', 'accept_null_eid', 'source_eid'], 'state_updates': [{'name': 'header_version_ok', 'expr': 'header_version == 1', 'width': 1}, {'name': 'som', 'expr': 'mctp_byte0[7]', 'width': 1}, {'name': 'eom', 'expr': 'mctp_byte0[6]', 'width': 1}, {'name': 'packet_seq', 'expr': 'mctp_byte0[5:4]', 'width': 2}, {'name': 'tag_owner', 'expr': 'mctp_byte0[3]', 'width': 1}, {'name': 'message_tag', 'expr': 'mctp_byte0[2:0]', 'width': 3}, {'name': 'dest_accept', 'expr': '(not dest_filter_enable) or (dest_eid == local_eid) or (accept_broadcast_eid and (dest_eid == 0xFF)) or (accept_null_eid and (dest_eid == 0x00))', 'width': 1}, {'name': 'assembly_key', 'expr': '((source_eid << 4) | (tag_owner << 3) | message_tag)', 'width': 12}], 'preconditions': ['validated VDM payload present'], 'inputs': ['MCTP transport header (last 4B of 16B header)', 'SOM body byte (IC+message_type) when SOM=1'], 'outputs': ['header_version, dest_eid, source_eid, SOM, EOM, packet_seq, tag_owner, message_tag', 'ic, message_type on SOM', 'assembly_key={source_eid,tag_owner,message_tag}', {'state': 'header_version_ok', 'expr': 'header_version == 1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'som', 'expr': 'mctp_byte0[7]', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'eom', 'expr': 'mctp_byte0[6]', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'packet_seq', 'expr': 'mctp_byte0[5:4]', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'tag_owner', 'expr': 'mctp_byte0[3]', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'message_tag', 'expr': 'mctp_byte0[2:0]', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'dest_accept', 'expr': '(not dest_filter_enable) or (dest_eid == local_eid) or (accept_broadcast_eid and (dest_eid == 0xFF)) or (accept_null_eid and (dest_eid == 0x00))', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'assembly_key', 'expr': '((source_eid << 4) | (tag_owner << 3) | message_tag)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': [], 'error_cases': [{'condition': 'header not present / version!=1 / SOM packet without body byte', 'result': 'PD_BAD_MCTP_HEADER packet drop'}, {'condition': 'dest_eid not local and not accepted broadcast/null while dest_filter_enable', 'result': 'PD_DEST_EID_REJECT packet drop'}], 'output_rules': []}, {'id': 'FM_ALLOC_CONTEXT', 'name': 'context_allocate', 'required_fields': ['free_slot_available', 'som', 'eom', 'packet_seq', 'allocated_len'], 'state_updates': [{'name': 'alloc_ok', 'expr': 'free_slot_available', 'width': 1}, {'name': 'single_packet', 'expr': 'som and eom', 'width': 1}, {'name': 'ctx_state', 'expr': 'DONE_WAIT_DESCRIPTOR_POP if (som and eom) else ASSEMBLING', 'width': 2}, {'name': 'ctx_payload_base_addr', 'expr': 'sram_alloc_ptr', 'width': 16}, {'name': 'ctx_expected_seq', 'expr': '(packet_seq + 1) % 4', 'width': 2}, {'name': 'active_context_count', 'expr': 'active_context_count + 1', 'width': 5}, {'name': 'sram_alloc_ptr', 'expr': 'sram_alloc_ptr + allocated_len', 'width': 16}], 'preconditions': ['decoded MCTP packet with SOM=1'], 'inputs': ['assembly_key', 'first_tlp_header[0:15]'], 'outputs': ['new ASSEMBLING context (SOM,EOM=0) or single-packet path (SOM,EOM=1)', 'first_tlp_header stored', 'payload_base_addr allocated from sram_alloc_ptr', {'state': 'alloc_ok', 'expr': 'free_slot_available', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'single_packet', 'expr': 'som and eom', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'DONE_WAIT_DESCRIPTOR_POP if (som and eom) else ASSEMBLING', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_payload_base_addr', 'expr': 'sram_alloc_ptr', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_expected_seq', 'expr': '(packet_seq + 1) % 4', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'active_context_count', 'expr': 'active_context_count + 1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'sram_alloc_ptr', 'expr': 'sram_alloc_ptr + allocated_len', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['expected_seq initialized; ctx_state=ASSEMBLING; sram_alloc_ptr advanced'], 'error_cases': [{'condition': 'no free context for a new fragmented SOM', 'result': 'PD_BAD_OR_EXPIRED_TAG packet drop (context-table-full); no allocation'}, {'condition': 'SOM for an already-active key', 'result': 'AD_DUPLICATE_SOM assembly drop: abort old context, suppress descriptor'}], 'output_rules': []}, {'id': 'FM_APPEND', 'name': 'context_append', 'required_fields': ['packet_seq', 'eom', 'payload_bytes'], 'state_updates': [{'name': 'seq_ok', 'expr': 'packet_seq == ctx_expected_seq', 'width': 1}, {'name': 'message_complete', 'expr': 'eom', 'width': 1}, {'name': 'ctx_payload_byte_count', 'expr': 'ctx_payload_byte_count + payload_bytes', 'width': 13}, {'name': 'ctx_expected_seq', 'expr': '(ctx_expected_seq + 1) % 4', 'width': 2}, {'name': 'ctx_last_seq', 'expr': 'packet_seq', 'width': 2}], 'preconditions': ['SOM=0 packet matches an active key', 'packet_seq == ctx_expected_seq'], 'inputs': ['payload bytes', 'last_tlp_header[0:15]'], 'outputs': ['payload appended; last_tlp_header updated; expected_seq incremented modulo 4', 'EOM=1 marks message complete -> FM_PUBLISH_DESCRIPTOR', {'state': 'seq_ok', 'expr': 'packet_seq == ctx_expected_seq', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'message_complete', 'expr': 'eom', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_payload_byte_count', 'expr': 'ctx_payload_byte_count + payload_bytes', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_expected_seq', 'expr': '(ctx_expected_seq + 1) % 4', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_last_seq', 'expr': 'packet_seq', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['ctx_payload_byte_count += payload_bytes'], 'error_cases': [{'condition': 'middle/end with no active matching context / EOM without prior SOM', 'result': 'PD_UNEXPECTED_MIDDLE_END packet drop'}, {'condition': 'packet_seq != expected modulo-4 seq', 'result': 'AD_SEQUENCE_MISMATCH assembly drop'}, {'condition': 'append would exceed MAX_MESSAGE_BYTES', 'result': 'AD_MESSAGE_OVERFLOW assembly drop'}, {'condition': 'context age exceeds assembly_timeout_cycles', 'result': 'AD_TIMEOUT assembly drop'}], 'output_rules': []}, {'id': 'FM_PACK_SRAM', 'name': 'payload_pack_write', 'required_fields': ['payload_bytes'], 'output_rules': [{'name': 'sram_wr_valid', 'expr': 'payload_bytes > 0', 'width': 1, 'port': 'sram_wr_valid'}, {'name': 'sram_wr_addr', 'expr': 'ctx_payload_next_addr & ~31', 'width': 16, 'port': 'sram_wr_addr'}, {'name': 'sram_wr_strb', 'expr': '(((1 << payload_bytes) - 1) << (ctx_payload_next_addr & 31))', 'width': 32, 'port': 'sram_wr_strb'}], 'state_updates': [{'name': 'ctx_payload_next_addr', 'expr': 'ctx_payload_next_addr + payload_bytes', 'width': 16}, {'name': 'ctx_partial_next_lane', 'expr': '(ctx_partial_next_lane + payload_bytes) % 32', 'width': 5}, {'name': 'payload_bytes_written_count', 'expr': 'payload_bytes_written_count + payload_bytes', 'width': 32}], 'preconditions': ['accepted payload bytes for a context'], 'inputs': ['payload bytes', 'ctx partial_word state'], 'outputs': ['256-bit sram_write beats; payload byte i at byte address base_addr+i; sram_wr_strb marks only payload lanes; full words flushed, partial words retained per-context until full or EOM', {'name': 'sram_wr_valid', 'port': 'sram_wr_valid', 'expr': 'payload_bytes > 0', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'sram_wr_addr', 'port': 'sram_wr_addr', 'expr': 'ctx_payload_next_addr & ~31', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'sram_wr_strb', 'port': 'sram_wr_strb', 'expr': '(((1 << payload_bytes) - 1) << (ctx_payload_next_addr & 31))', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'ctx_payload_next_addr', 'expr': 'ctx_payload_next_addr + payload_bytes', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_partial_next_lane', 'expr': '(ctx_partial_next_lane + payload_bytes) % 32', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'payload_bytes_written_count', 'expr': 'payload_bytes_written_count + payload_bytes', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['ctx_payload_next_addr advanced; payload_bytes_written_count += bytes'], 'error_cases': [{'condition': 'allocation/write would exceed sram_base/limit or SRAM_ADDR_WIDTH', 'result': 'AD_SRAM_OVERFLOW assembly drop'}]}, {'id': 'FM_PUBLISH_DESCRIPTOR', 'name': 'descriptor_publish', 'required_fields': ['descriptor_queue_full'], 'state_updates': [{'name': 'descriptor_ready', 'expr': 'not descriptor_queue_full', 'width': 1}, {'name': 'descriptor_payload_len', 'expr': 'ctx_payload_byte_count', 'width': 13}, {'name': 'descriptor_base_addr', 'expr': 'ctx_payload_base_addr', 'width': 16}, {'name': 'message_completed_count', 'expr': 'message_completed_count + 1', 'width': 32}, {'name': 'descriptor_valid', 'expr': '1', 'width': 1}, {'name': 'ctx_state', 'expr': 'DONE_WAIT_DESCRIPTOR_POP', 'width': 2}], 'preconditions': ['successful EOM for a context'], 'inputs': ['context metadata', 'first/last_tlp_header'], 'outputs': ['descriptor{source_eid,dest_eid,tag_owner,message_tag,message_type,requester_id,pcie_routing_type,payload_base_addr,payload_len,final_packet_seq,context_id,completion_status,first/last_tlp_header} pushed', 'descriptor_ready interrupt; message_completed_count increment', {'state': 'descriptor_ready', 'expr': 'not descriptor_queue_full', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'descriptor_payload_len', 'expr': 'ctx_payload_byte_count', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'descriptor_base_addr', 'expr': 'ctx_payload_base_addr', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'message_completed_count', 'expr': 'message_completed_count + 1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'descriptor_valid', 'expr': '1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'DONE_WAIT_DESCRIPTOR_POP', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['context released (or DONE_WAIT_DESCRIPTOR_POP)'], 'error_cases': [{'condition': 'descriptor/header queue full at EOM', 'result': 'AD_DESCRIPTOR_FULL assembly drop; no descriptor published'}], 'output_rules': []}, {'id': 'FM_AXI_READ', 'name': 'firmware_payload_read', 'required_fields': ['out_of_window', 'no_descriptor', 'raw_sram_debug_read_enable', 'beat_index', 'arlen', 'read_error'], 'output_rules': [{'name': 'rresp_next', 'expr': 'RRESP_SLVERR if (out_of_window or (no_descriptor and not raw_sram_debug_read_enable)) else RRESP_OKAY', 'width': 2, 'port': 's_axi_rresp'}, {'name': 'rlast_next', 'expr': 'beat_index == arlen', 'width': 1, 'port': 's_axi_rlast'}], 'state_updates': [{'name': 'fw_axi_read_beat_count', 'expr': 'fw_axi_read_beat_count + 1', 'width': 32}, {'name': 'fw_axi_read_error_count', 'expr': 'fw_axi_read_error_count + (1 if read_error else 0)', 'width': 32}], 'preconditions': ['ARSIZE==5', 'ARBURST==INCR', 'descriptor visible for the range or raw_sram_debug_read_enable'], 'inputs': ['AR address/len'], 'outputs': ['one SRAM read per R beat; rdata returned unmodified; RLAST on final beat', {'name': 'rresp_next', 'port': 's_axi_rresp', 'expr': 'RRESP_SLVERR if (out_of_window or (no_descriptor and not raw_sram_debug_read_enable)) else RRESP_OKAY', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'rlast_next', 'port': 's_axi_rlast', 'expr': 'beat_index == arlen', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'fw_axi_read_beat_count', 'expr': 'fw_axi_read_beat_count + 1', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'fw_axi_read_error_count', 'expr': 'fw_axi_read_error_count + (1 if read_error else 0)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'side_effects': ['fw_axi_read_beat_count increment'], 'error_cases': [{'condition': 'read outside SRAM read window, or no completed descriptor and not raw_sram_debug_read_enable', 'result': 'RRESP=SLVERR; fw_axi_read_error_count increment'}]}], 'invariants': ['No SRAM payload write occurs before a packet is accepted for assembly.', 'The SRAM writer never writes PCIe/VDM headers, MCTP transport headers, pad bytes, or digest bytes as payload.', 'For every published descriptor, byte address base_addr..base_addr+payload_len-1 is written exactly as the corresponding assembled payload byte with no alignment gap.', 'Active context count never exceeds CONTEXT_COUNT.', 'first_tlp_header for a context is written only by the accepted SOM packet; last_tlp_header equals the most recent accepted packet for that context.', 'Non-final accepted packets contribute exactly the configured transmission unit byte count; EOM may contribute fewer.', 'No descriptor is published before EOM; sequence mismatch aborts the active context and suppresses the success descriptor.', 'An earlier packet-drop reason wins over a later assembly-drop reason for the same accepted transaction (drop priority order).', 'ctx_state encoding is mutually exclusive: a context cannot be IDLE and ASSEMBLING or ERROR in the same cycle.'], 'reference_model_hint': 'tb-gen must implement a Python scoreboard from this section: reconstruct expected payload bytes, headers, descriptor, and drop class per scenario and compare against RTL-observed SRAM writes / descriptor / counters.', 'derived_signals': [{'name': 'apb_access', 'expr': 'psel and penable', 'width': 1, 'description': 'APB access phase helper derived from psel and penable.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_write', 'expr': 'psel and penable and pwrite', 'width': 1, 'description': 'APB write access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_read', 'expr': 'psel and penable and not pwrite', 'width': 1, 'description': 'APB read access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'addr', 'expr': 'paddr', 'width': 16, 'description': 'Register address helper derived from the APB paddr input.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wmask', 'expr': '((0x000000FF if (pstrb & 0x1) != 0 else 0) | (0x0000FF00 if (pstrb & 0x2) != 0 else 0) | (0x00FF0000 if (pstrb & 0x4) != 0 else 0) | (0xFF000000 if (pstrb & 0x8) != 0 else 0))', 'width': 32, 'description': 'APB byte-lane write mask expanded from pstrb.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'legal_addr', 'expr': '(addr == 0) or (addr == 4) or (addr == 8) or (addr == 12) or (addr == 16) or (addr == 32) or (addr == 1024) or (addr == 256) or (addr == 260) or (addr == 264) or (addr == 268) or (addr == 512) or (addr == 768) or (addr == 896)', 'width': 1, 'description': 'APB legal address decode derived from registers.register_list offsets.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_control', 'expr': 'apb_valid_write and (addr == 0)', 'width': 1, 'description': 'APB write decode helper for register CONTROL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_control', 'expr': 'apb_valid_read and (addr == 0)', 'width': 1, 'description': 'APB read decode helper for register CONTROL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_cfg_tu', 'expr': 'apb_valid_write and (addr == 4)', 'width': 1, 'description': 'APB write decode helper for register CFG_TU.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_cfg_tu', 'expr': 'apb_valid_read and (addr == 4)', 'width': 1, 'description': 'APB read decode helper for register CFG_TU.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_cfg_timeout', 'expr': 'apb_valid_write and (addr == 8)', 'width': 1, 'description': 'APB write decode helper for register CFG_TIMEOUT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_cfg_timeout', 'expr': 'apb_valid_read and (addr == 8)', 'width': 1, 'description': 'APB read decode helper for register CFG_TIMEOUT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_sram_base', 'expr': 'apb_valid_write and (addr == 12)', 'width': 1, 'description': 'APB write decode helper for register SRAM_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_sram_base', 'expr': 'apb_valid_read and (addr == 12)', 'width': 1, 'description': 'APB read decode helper for register SRAM_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_sram_limit', 'expr': 'apb_valid_write and (addr == 16)', 'width': 1, 'description': 'APB write decode helper for register SRAM_LIMIT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_sram_limit', 'expr': 'apb_valid_read and (addr == 16)', 'width': 1, 'description': 'APB read decode helper for register SRAM_LIMIT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_status', 'expr': 'apb_valid_write and (addr == 32)', 'width': 1, 'description': 'APB write decode helper for register STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_status', 'expr': 'apb_valid_read and (addr == 32)', 'width': 1, 'description': 'APB read decode helper for register STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_ctx_state', 'expr': 'apb_valid_write and (addr == 1024)', 'width': 1, 'description': 'APB write decode helper for register CTX_STATE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_ctx_state', 'expr': 'apb_valid_read and (addr == 1024)', 'width': 1, 'description': 'APB read decode helper for register CTX_STATE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_intr_raw_status', 'expr': 'apb_valid_write and (addr == 256)', 'width': 1, 'description': 'APB write decode helper for register INTR_RAW_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_intr_raw_status', 'expr': 'apb_valid_read and (addr == 256)', 'width': 1, 'description': 'APB read decode helper for register INTR_RAW_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_intr_enable', 'expr': 'apb_valid_write and (addr == 260)', 'width': 1, 'description': 'APB write decode helper for register INTR_ENABLE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_intr_enable', 'expr': 'apb_valid_read and (addr == 260)', 'width': 1, 'description': 'APB read decode helper for register INTR_ENABLE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_intr_status', 'expr': 'apb_valid_write and (addr == 264)', 'width': 1, 'description': 'APB write decode helper for register INTR_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_intr_status', 'expr': 'apb_valid_read and (addr == 264)', 'width': 1, 'description': 'APB read decode helper for register INTR_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_intr_clear', 'expr': 'apb_valid_write and (addr == 268)', 'width': 1, 'description': 'APB write decode helper for register INTR_CLEAR.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_intr_clear', 'expr': 'apb_valid_read and (addr == 268)', 'width': 1, 'description': 'APB read decode helper for register INTR_CLEAR.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'intr_clear_w1c', 'expr': '((pwdata & gpio_mask) if wr_intr_clear else 0)', 'width': 32, 'description': 'W1C write mask helper for register INTR_CLEAR.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_cnt_tlp_seen', 'expr': 'apb_valid_write and (addr == 512)', 'width': 1, 'description': 'APB write decode helper for register CNT_TLP_SEEN.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_cnt_tlp_seen', 'expr': 'apb_valid_read and (addr == 512)', 'width': 1, 'description': 'APB read decode helper for register CNT_TLP_SEEN.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_desc_valid', 'expr': 'apb_valid_write and (addr == 768)', 'width': 1, 'description': 'APB write decode helper for register DESC_VALID.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_desc_valid', 'expr': 'apb_valid_read and (addr == 768)', 'width': 1, 'description': 'APB read decode helper for register DESC_VALID.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_debug_ctx', 'expr': 'apb_valid_write and (addr == 896)', 'width': 1, 'description': 'APB write decode helper for register DEBUG_CTX.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_debug_ctx', 'expr': 'apb_valid_read and (addr == 896)', 'width': 1, 'description': 'APB read decode helper for register DEBUG_CTX.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'read_mux', 'expr': '(0 if addr == 0 else (0 if addr == 4 else (0 if addr == 8 else (0 if addr == 12 else (0 if addr == 16 else (0 if addr == 32 else (0 if addr == 1024 else (0 if addr == 256 else (0 if addr == 260 else (0 if addr == 264 else (0 if addr == 268 else (0 if addr == 512 else (0 if addr == 768 else (0 if addr == 896 else 0))))))))))))))', 'width': 32, 'description': 'APB read data mux derived from registers.register_list offsets and function_model state variables.', 'source': 'repair_ssot_schema.apb_helper'}]}, 'cycle_model': {'purpose': 'Cycle/handshake contract: when valid/ready, payload writes, descriptor, and interrupts may change.', 'executable': 'python', 'backend_policy': 'Use the repo-owned pure-Python deterministic stepper; FunctionalModel is the behavioral oracle.', 'clock': 'axi_aclk', 'reset': {'assertion': 'axi_aresetn/presetn low asynchronously clears all architectural state (contexts, queue, parser, packer, counters).', 'deassertion': 'state usable on the first rising edge after synchronized deassertion.'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data/pready timing in pclk'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing in pclk'}, 'single_beat_transfer': {'min_cycles': 1, 'max_cycles': None, 'description': 'AXI/SRAM handshakes; max depends on backpressure'}}, 'handshake_rules': [{'signal': 's_axi_awready/s_axi_wready', 'rule': 'Assert only when the ingress can accept the AW/W beat; deassert to backpressure when not in drop_when_disabled mode.'}, {'signal': 's_axi_bvalid', 'rule': 'Assert after the full TLP transaction is consumed; hold until bready.'}, {'signal': 'sram_wr_valid', 'rule': 'Hold sram_wr_addr/data/strb stable while sram_wr_valid && !sram_wr_ready.'}, {'signal': 'sram_rd_req_valid', 'rule': 'Issue one SRAM read request per AXI read beat; hold until sram_rd_req_ready.'}, {'signal': 's_axi_rvalid/s_axi_rlast', 'rule': 'Drive rdata after the SRAM read response; assert rlast on the final ARLEN beat only.'}, {'signal': 'apb pready', 'rule': 'Complete the access phase; pslverr only with pready=1.'}], 'pipeline': [{'stage': 'S0_INGEST', 'cycle': '0..B', 'action': 'Reconstruct TLP bytes from AXI W beats; legality check'}, {'stage': 'S1_VDM_DECODE', 'cycle': 'B+1', 'action': 'Decode/validate 16B PCIe VDM header; strip header/pad/digest'}, {'stage': 'S2_MCTP_DECODE', 'cycle': 'B+2', 'action': 'Decode MCTP transport header + IC/msg_type on SOM'}, {'stage': 'S3_CONTEXT', 'cycle': 'B+3', 'action': 'Allocate/append context by key; sequence/timeout checks'}, {'stage': 'S4_PACK', 'cycle': 'B+4..P', 'action': 'Pack payload bytes into 256-bit SRAM words; per-context partial word'}, {'stage': 'S5_DESCRIPTOR', 'cycle': 'P+1', 'action': 'On EOM push descriptor + first/last headers; raise descriptor_ready'}], 'ordering': ['descriptor_publish must occur only after the final SRAM payload write/flush for the message is accepted.', 'AXI read response is not issued before the corresponding SRAM read response.', 'Interrupt status updates occur on the rising edge the terminal event is recorded (after CDC into pclk for status bits).'], 'backpressure': ['sram_wr_ready deassertion stalls payload writes without dropping accepted bytes unless timeout/overflow occurs.', 'SRAM write traffic for assembly has priority over firmware AXI read traffic on a shared port.', 'AXI read backpressure must not corrupt ongoing assembly writes; each context owns its own partial-word state.'], 'performance': {'frequency_mhz': 400, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No SRAM/AXI backpressure; full 256-bit payload words'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single outstanding AXI write and read transaction'}, 'depth': {'pipeline_stages': 6, 'queue_depth': 8, 'description': 'Pipeline depth + descriptor FIFO depth visible to cycle coverage'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC_SINGLE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_SINGLE', 'description': 'Valid single-packet message'}, {'id': 'SC_FRAG_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_FRAG', 'description': 'Fragmented message across TLPs'}, {'id': 'SC_INTERLEAVE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_INTERLEAVE', 'description': 'Interleaved messages distinct keys'}, {'id': 'SC_UNALIGNED_TU_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_UNALIGNED_TU', 'description': 'TU=68B unaligned 32B continuation'}, {'id': 'SC_MAX_TU_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_MAX_TU', 'description': 'Max TU 4096B over 129 beats'}, {'id': 'SC_PD_MALFORMED_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_PD_MALFORMED', 'description': 'Malformed AXI/TLP drops'}, {'id': 'SC_PD_VDM_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC_PD_VDM', 'description': 'Unsupported VDM constants'}, {'id': 'SC_PD_MCTP_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC_PD_MCTP', 'description': 'Bad MCTP header version'}, {'id': 'SC_PD_EID_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC_PD_EID', 'description': 'Dest EID reject'}, {'id': 'SC_PD_MIDDLE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC_PD_MIDDLE', 'description': 'Middle/EOM without SOM'}, {'id': 'SC_AD_DUP_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC_AD_DUP', 'description': 'Duplicate SOM'}, {'id': 'SC_AD_SEQ_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC_AD_SEQ', 'description': 'Sequence mismatch'}, {'id': 'SC_AD_CTXFULL_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[12]', 'scenario': 'SC_AD_CTXFULL', 'description': 'Context table full'}, {'id': 'SC_AD_SRAM_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[13]', 'scenario': 'SC_AD_SRAM', 'description': 'SRAM overflow'}, {'id': 'SC_AD_DESCFULL_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[14]', 'scenario': 'SC_AD_DESCFULL', 'description': 'Descriptor queue full'}, {'id': 'SC_AD_TIMEOUT_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[15]', 'scenario': 'SC_AD_TIMEOUT', 'description': 'Assembly timeout'}, {'id': 'SC_PRIORITY_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[16]', 'scenario': 'SC_PRIORITY', 'description': 'Drop priority'}, {'id': 'SC_FW_READ_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[17]', 'scenario': 'SC_FW_READ', 'description': 'Firmware payload read'}, {'id': 'SC_FW_READ_SLVERR_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[18]', 'scenario': 'SC_FW_READ_SLVERR', 'description': 'Read outside window'}, {'id': 'SC_REG_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[19]', 'scenario': 'SC_REG', 'description': 'APB register access'}, {'id': 'fcov_single', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_PUBLISH_DESCRIPTOR', 'source_ref': 'function_model.transactions.FM_PUBLISH_DESCRIPTOR', 'description': 'Single-packet message completes and publishes a descriptor'}, {'id': 'fcov_frag', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APPEND', 'source_ref': 'function_model.transactions.FM_APPEND', 'description': 'Fragmented append observed'}, {'id': 'fcov_pack', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_PACK_SRAM', 'source_ref': 'function_model.transactions.FM_PACK_SRAM', 'description': 'Payload-only SRAM pack observed (byte i at base+i)'}, {'id': 'fcov_pd_all', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DECODE_VDM', 'source_ref': 'function_model.transactions.FM_DECODE_VDM', 'description': 'Every PD_* packet-drop reason (error_cases of FM_DECODE_VDM/FM_DECODE_MCTP) observed with no side effect'}, {'id': 'fcov_ad_all', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_APPEND', 'source_ref': 'function_model.transactions.FM_APPEND', 'description': 'Every AD_* assembly-drop reason (error_cases of FM_ALLOC_CONTEXT/FM_APPEND) observed aborting exactly its context'}, {'id': 'ccov_ingest', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S0_INGEST', 'source_ref': 'cycle_model.pipeline.S0_INGEST', 'description': 'Ingest stage observed'}, {'id': 'ccov_sram_hold', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules', 'source_ref': 'cycle_model.handshake_rules', 'description': 'sram_wr hold-until-ready observed'}, {'id': 'ccov_desc_order', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering', 'source_ref': 'cycle_model.ordering', 'description': 'descriptor after final SRAM flush observed'}, {'id': 'ccov_ctx_fsm', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm', 'source_ref': 'fsm.context_fsm', 'description': 'context FSM legal transitions observed'}, {'id': 'ccov_outstanding', 'class': 'outstanding', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': 'single outstanding read/write exercised'}, {'id': 'function_axi_write_to_tlp_bytes', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_ingest_tlp', 'description': 'FM_INGEST_TLP axi_write_to_tlp_bytes'}, {'id': 'function_pcie_vdm_decode', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_decode_vdm', 'description': 'FM_DECODE_VDM pcie_vdm_decode'}, {'id': 'function_mctp_transport_decode', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_decode_mctp', 'description': 'FM_DECODE_MCTP mctp_transport_decode'}, {'id': 'function_context_allocate', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_alloc_context', 'description': 'FM_ALLOC_CONTEXT context_allocate'}, {'id': 'function_context_append', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_append', 'description': 'FM_APPEND context_append'}, {'id': 'function_payload_pack_write', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm_pack_sram', 'description': 'FM_PACK_SRAM payload_pack_write'}, {'id': 'function_descriptor_publish', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[6]', 'source_ref': 'function_model.transactions.fm_publish_descriptor', 'description': 'FM_PUBLISH_DESCRIPTOR descriptor_publish'}, {'id': 'function_firmware_payload_read', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[7]', 'source_ref': 'function_model.transactions.fm_axi_read', 'description': 'FM_AXI_READ firmware_payload_read'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 's_axi_awready/s_axi_wready', 'rule': 'Assert only when the ingress can accept the AW/W beat; deassert to backpressure when not in drop_when_disabled mode.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 's_axi_bvalid', 'rule': 'Assert after the full TLP transaction is consumed; hold until bready.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'sram_wr_valid', 'rule': 'Hold sram_wr_addr/data/strb stable while sram_wr_valid && !sram_wr_ready.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'sram_rd_req_valid', 'rule': 'Issue one SRAM read request per AXI read beat; hold until sram_rd_req_ready.'}"}, {'id': 'cycle_handshake_4', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[4]', 'source_ref': 'cycle_model.handshake_rules[4]', 'description': "{'signal': 's_axi_rvalid/s_axi_rlast', 'rule': 'Drive rdata after the SRAM read response; assert rlast on the final ARLEN beat only.'}"}, {'id': 'cycle_handshake_5', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[5]', 'source_ref': 'cycle_model.handshake_rules[5]', 'description': "{'signal': 'apb pready', 'rule': 'Complete the access phase; pslverr only with pready=1.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data/pready timing in pclk'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing in pclk'}"}, {'id': 'cycle_latency_single_beat_transfer', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.single_beat_transfer', 'source_ref': 'cycle_model.latency.single_beat_transfer', 'description': "{'min_cycles': 1, 'max_cycles': None, 'description': 'AXI/SRAM handshakes; max depends on backpressure'}"}, {'id': 'cycle_pipeline_s0_ingest', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Reconstruct TLP bytes from AXI W beats; legality check'}, {'id': 'cycle_pipeline_s1_vdm_decode', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Decode/validate 16B PCIe VDM header; strip header/pad/digest'}, {'id': 'cycle_pipeline_s2_mctp_decode', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Decode MCTP transport header + IC/msg_type on SOM'}, {'id': 'cycle_pipeline_s3_context', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Allocate/append context by key; sequence/timeout checks'}, {'id': 'cycle_pipeline_s4_pack', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Pack payload bytes into 256-bit SRAM words; per-context partial word'}, {'id': 'cycle_pipeline_s5_descriptor', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[5]', 'source_ref': 'cycle_model.pipeline[5]', 'description': 'On EOM push descriptor + first/last headers; raise descriptor_ready'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'descriptor_publish must occur only after the final SRAM payload write/flush for the message is accepted.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'AXI read response is not issued before the corresponding SRAM read response.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Interrupt status updates occur on the rising edge the terminal event is recorded (after CDC into pclk for status bits).'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'sram_wr_ready deassertion stalls payload writes without dropping accepted bytes unless timeout/overflow occurs.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'SRAM write traffic for assembly has priority over firmware AXI read traffic on a shared port.'}, {'id': 'cycle_backpressure_2', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[2]', 'source_ref': 'cycle_model.backpressure[2]', 'description': 'AXI read backpressure must not corrupt ongoing assembly writes; each context owns its own partial-word state.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 1, 'write_max': 1, 'description': 'Single outstanding AXI write and read transaction'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 6, 'queue_depth': 8, 'description': 'Pipeline depth + descriptor FIFO depth visible to cycle coverage'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '400'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_beats_per_cycle': 1, 'condition': 'No SRAM/AXI backpressure; full 256-bit payload words'}"}, {'id': 'fsm_ingress_fsm_idle_to_accept_aw_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ingress_fsm.transitions[0]', 'source_ref': 'fsm.ingress_fsm.transitions[0]', 'description': 'awvalid && awready'}, {'id': 'fsm_ingress_fsm_accept_aw_to_collect_w_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ingress_fsm.transitions[1]', 'source_ref': 'fsm.ingress_fsm.transitions[1]', 'description': 'AWSIZE==5 && AWBURST==INCR'}, {'id': 'fsm_ingress_fsm_accept_aw_to_resp_b_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ingress_fsm.transitions[2]', 'source_ref': 'fsm.ingress_fsm.transitions[2]', 'description': 'illegal AWSIZE/AWBURST (PD_MALFORMED_TLP)'}, {'id': 'fsm_ingress_fsm_collect_w_to_check_legal_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ingress_fsm.transitions[3]', 'source_ref': 'fsm.ingress_fsm.transitions[3]', 'description': 'wlast && wvalid && wready'}, {'id': 'fsm_ingress_fsm_check_legal_to_emit_tlp_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ingress_fsm.transitions[4]', 'source_ref': 'fsm.ingress_fsm.transitions[4]', 'description': 'beat-count/WSTRB/length legal'}, {'id': 'fsm_ingress_fsm_check_legal_to_resp_b_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ingress_fsm.transitions[5]', 'source_ref': 'fsm.ingress_fsm.transitions[5]', 'description': 'malformed (PD_MALFORMED_TLP)'}, {'id': 'fsm_ingress_fsm_emit_tlp_to_resp_b_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ingress_fsm.transitions[6]', 'source_ref': 'fsm.ingress_fsm.transitions[6]', 'description': 'TLP bytes emitted to parser'}, {'id': 'fsm_ingress_fsm_resp_b_to_idle_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.ingress_fsm.transitions[7]', 'source_ref': 'fsm.ingress_fsm.transitions[7]', 'description': 'bvalid && bready (OKAY)'}, {'id': 'fsm_context_fsm_idle_to_assembling_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[0]', 'source_ref': 'fsm.context_fsm.transitions[0]', 'description': 'accepted SOM=1,EOM=0 allocates slot'}, {'id': 'fsm_context_fsm_idle_to_done_wait_descriptor_pop_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[1]', 'source_ref': 'fsm.context_fsm.transitions[1]', 'description': 'accepted SOM=1,EOM=1 single-packet completes'}, {'id': 'fsm_context_fsm_assembling_to_assembling_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[2]', 'source_ref': 'fsm.context_fsm.transitions[2]', 'description': 'accepted SOM=0,EOM=0 append, seq ok'}, {'id': 'fsm_context_fsm_assembling_to_done_wait_descriptor_pop_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[3]', 'source_ref': 'fsm.context_fsm.transitions[3]', 'description': 'accepted SOM=0,EOM=1 completes; descriptor pushed'}, {'id': 'fsm_context_fsm_assembling_to_error_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[4]', 'source_ref': 'fsm.context_fsm.transitions[4]', 'description': 'AD_* assembly drop (dup SOM/seq/overflow/sram/timeout)'}, {'id': 'fsm_context_fsm_done_wait_descriptor_pop_to_idle_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[5]', 'source_ref': 'fsm.context_fsm.transitions[5]', 'description': 'descriptor copied/popped'}, {'id': 'fsm_context_fsm_error_to_idle_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[6]', 'source_ref': 'fsm.context_fsm.transitions[6]', 'description': 'clear policy releases the slot'}, {'id': 'fsm_axi_read_fsm_idle_to_accept_ar_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.axi_read_fsm.transitions[0]', 'source_ref': 'fsm.axi_read_fsm.transitions[0]', 'description': 'arvalid && arready'}, {'id': 'fsm_axi_read_fsm_accept_ar_to_issue_sram_rd_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.axi_read_fsm.transitions[1]', 'source_ref': 'fsm.axi_read_fsm.transitions[1]', 'description': 'ARSIZE==5 && in window && (descriptor present or raw_sram_debug_read_enable)'}, {'id': 'fsm_axi_read_fsm_accept_ar_to_drive_r_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.axi_read_fsm.transitions[2]', 'source_ref': 'fsm.axi_read_fsm.transitions[2]', 'description': 'out-of-window/no-descriptor -> SLVERR'}, {'id': 'fsm_axi_read_fsm_issue_sram_rd_to_wait_sram_rsp_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.axi_read_fsm.transitions[3]', 'source_ref': 'fsm.axi_read_fsm.transitions[3]', 'description': 'sram_rd_req accepted'}, {'id': 'fsm_axi_read_fsm_wait_sram_rsp_to_drive_r_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.axi_read_fsm.transitions[4]', 'source_ref': 'fsm.axi_read_fsm.transitions[4]', 'description': 'sram_rd_rsp_valid'}, {'id': 'fsm_axi_read_fsm_drive_r_to_issue_sram_rd_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.axi_read_fsm.transitions[5]', 'source_ref': 'fsm.axi_read_fsm.transitions[5]', 'description': 'rvalid && rready && !rlast'}, {'id': 'fsm_axi_read_fsm_drive_r_to_done_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.axi_read_fsm.transitions[6]', 'source_ref': 'fsm.axi_read_fsm.transitions[6]', 'description': 'rvalid && rready && rlast'}, {'id': 'fsm_axi_read_fsm_done_to_idle_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.axi_read_fsm.transitions[7]', 'source_ref': 'fsm.axi_read_fsm.transitions[7]', 'description': 'next'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'PD_DISABLED_DROP_MODE', 'condition': 'enable=0 and drop_when_disabled=1', 'architectural_effect': 'packet drop; pd_disabled_drop_mode_count++; last_drop_class=packet'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'PD_MALFORMED_TLP', 'condition': 'empty/bad AWSIZE/AWBURST/interleave/beat-count/WLAST/WSTRB/<16B/>MAX_TLP_BYTES/length-inconsistent/unstripped-digest', 'architectural_effect': 'packet drop; pd_malformed_tlp_count++; axi_write_malformed interrupt'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'PD_UNSUPPORTED_VDM', 'condition': 'not supported Non-Flit VDM / msg_code!=0x7F / vendor!=0x1AB4 / vdm_code!=0x0 / unsupported routing/TC/attr', 'architectural_effect': 'packet drop; pd_unsupported_vdm_count++'}"}, {'id': 'error_error_3', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': "{'id': 'PD_BAD_MCTP_HEADER', 'condition': 'header absent / version!=1 / SOM without body byte / IC policy reject', 'architectural_effect': 'packet drop; pd_bad_mctp_header_count++'}"}, {'id': 'error_error_4', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[4]', 'source_ref': 'error_handling.error_sources[4]', 'description': "{'id': 'PD_BAD_PAD_OR_ALIGNMENT', 'condition': 'pad>3 / pad!=0 on non-EOM / TU/payload alignment or size violations', 'architectural_effect': 'packet drop; pd_bad_pad_or_alignment_count++'}"}, {'id': 'error_error_5', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[5]', 'source_ref': 'error_handling.error_sources[5]', 'description': "{'id': 'PD_DEST_EID_REJECT', 'condition': 'dest EID fails filter', 'architectural_effect': 'packet drop; pd_dest_eid_reject_count++'}"}, {'id': 'error_error_6', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[6]', 'source_ref': 'error_handling.error_sources[6]', 'description': "{'id': 'PD_UNEXPECTED_MIDDLE_END', 'condition': 'middle/end with no active context / EOM without SOM', 'architectural_effect': 'packet drop; pd_unexpected_middle_end_count++'}"}, {'id': 'error_error_7', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[7]', 'source_ref': 'error_handling.error_sources[7]', 'description': "{'id': 'PD_BAD_OR_EXPIRED_TAG', 'condition': 'tag policy reject / context-table-full for new SOM', 'architectural_effect': 'packet drop; pd_bad_or_expired_tag_count++'}"}, {'id': 'error_error_8', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[8]', 'source_ref': 'error_handling.error_sources[8]', 'description': "{'id': 'AD_DUPLICATE_SOM', 'condition': 'SOM for an already-active key', 'architectural_effect': 'assembly drop; abort context; ad_duplicate_som_count++; assembly_drop interrupt'}"}, {'id': 'error_error_9', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[9]', 'source_ref': 'error_handling.error_sources[9]', 'description': "{'id': 'AD_SEQUENCE_MISMATCH', 'condition': 'seq != expected modulo-4', 'architectural_effect': 'assembly drop; abort context; ad_sequence_mismatch_count++'}"}, {'id': 'error_error_10', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[10]', 'source_ref': 'error_handling.error_sources[10]', 'description': "{'id': 'AD_MESSAGE_OVERFLOW', 'condition': 'append exceeds MAX_MESSAGE_BYTES', 'architectural_effect': 'assembly drop; ad_message_overflow_count++'}"}, {'id': 'error_error_11', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[11]', 'source_ref': 'error_handling.error_sources[11]', 'description': "{'id': 'AD_SRAM_OVERFLOW', 'condition': 'alloc/write exceeds sram_base/limit or SRAM_ADDR_WIDTH', 'architectural_effect': 'assembly drop; ad_sram_overflow_count++; sram_overflow interrupt'}"}, {'id': 'error_error_12', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[12]', 'source_ref': 'error_handling.error_sources[12]', 'description': "{'id': 'AD_DESCRIPTOR_FULL', 'condition': 'descriptor queue full at EOM', 'architectural_effect': 'assembly drop; ad_descriptor_full_count++; descriptor_queue_full interrupt'}"}, {'id': 'error_error_13', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[13]', 'source_ref': 'error_handling.error_sources[13]', 'description': "{'id': 'AD_TIMEOUT', 'condition': 'context age exceeds assembly_timeout_cycles', 'architectural_effect': 'assembly drop; ad_timeout_count++; context_timeout interrupt'}"}]}
RESP_OKAY = 0
RESP_SLVERR = 2


def _parse_int(value, default=0):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip().replace("_", "")
    if not text:
        return default
    literal = text.lower()
    if "'" in literal:
        try:
            base_tag = literal.split("'", 1)[1][0]
            digits = literal.split(base_tag, 1)[1]
            digits = digits.replace("x", "0").replace("z", "0")
            base = {"h": 16, "d": 10, "b": 2}.get(base_tag, 10)
            return int(digits, base)
        except Exception:
            return default
    if text.startswith("0x"):
        return int(text, 16)
    try:
        return int(text, 10)
    except ValueError:
        return default


_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Div: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.LShift: lambda a, b: a << b,
    ast.RShift: lambda a, b: a >> b,
    ast.BitAnd: lambda a, b: a & b,
    ast.BitOr: lambda a, b: a | b,
    ast.BitXor: lambda a, b: a ^ b,
}
_UNARYOPS = {
    ast.UAdd: lambda a: a,
    ast.USub: lambda a: -a,
    ast.Invert: lambda a: ~a,
    ast.Not: lambda a: 0 if a else 1,
}
_CMPOPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
}


def _normal_expr(text):
    text = str(text or "").strip()
    reduction_or = re.fullmatch(r"\|\s*\((.*)\)", text)
    if reduction_or:
        text = f"reduction_or({reduction_or.group(1)})"
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"(?<![=!<>])!(?!=)", " not ", text)
    return text


def _literal_int(text):
    text = str(text).strip().replace("_", "")
    return bool(re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+|[0-9]*'[hHdDbB][0-9a-fA-FxXzZ]+)", text))


def _h_bin_to_gray(value):
    v = _parse_int(value, 0)
    return v ^ (v >> 1)


def _h_gray_to_bin(value):
    g = _parse_int(value, 0)
    b = g
    s = g >> 1
    while s:
        b ^= s
        s >>= 1
    return b


def _h_popcount(value):
    return bin(_parse_int(value, 0) & ((1 << 256) - 1)).count("1")


def _h_parity(value):
    return _h_popcount(value) & 1


def _h_clog2(value):
    v = _parse_int(value, 0)
    if v <= 1:
        return 0
    return (v - 1).bit_length()


def _default_rule_helpers():
    return {
        "bin_to_gray": _h_bin_to_gray,
        "gray_to_bin": _h_gray_to_bin,
        "popcount": _h_popcount,
        "parity": _h_parity,
        "clog2": _h_clog2,
        "min": lambda a, b: min(_parse_int(a, 0), _parse_int(b, 0)),
        "max": lambda a, b: max(_parse_int(a, 0), _parse_int(b, 0)),
        "abs": lambda a: abs(_parse_int(a, 0)),
        "any": lambda *args: int(any(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "all": lambda *args: int(all(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "sum": lambda *args: int(sum(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "len": lambda *args: len(args[0]) if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else len(args),
    }


def _eval_ast(node, env):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, env)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return int(node.value)
        if isinstance(node.value, int):
            return node.value
        if isinstance(node.value, str):
            return _parse_int(node.value, 0)
        raise ValueError(f"unsupported constant {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in env:
            return _parse_int(env[node.id], 0)
        raise KeyError(f"unknown rule name {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval_ast(node.left, env), _eval_ast(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_ast(node.operand, env))
    if isinstance(node, ast.BoolOp):
        values = [_eval_ast(v, env) for v in node.values]
        if isinstance(node.op, ast.And):
            return int(all(values))
        if isinstance(node.op, ast.Or):
            return int(any(values))
    if isinstance(node, ast.Compare):
        left = _eval_ast(node.left, env)
        verdicts = []
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_ast(comparator, env)
            if type(op) not in _CMPOPS:
                raise ValueError(f"unsupported comparison {type(op).__name__}")
            verdicts.append(_CMPOPS[type(op)](left, right))
            left = right
        return int(all(verdicts))
    if isinstance(node, ast.IfExp):
        return _eval_ast(node.body if _eval_ast(node.test, env) else node.orelse, env)
    if isinstance(node, ast.Subscript):
        base = _eval_ast(node.value, env)
        sl = node.slice
        if isinstance(sl, ast.Index):
            sl = sl.value
        if isinstance(sl, ast.Slice):
            hi = _eval_ast(sl.lower, env) if sl.lower is not None else 0
            lo = _eval_ast(sl.upper, env) if sl.upper is not None else 0
            if hi < lo:
                hi, lo = lo, hi
            width = hi - lo + 1
            mask = (1 << width) - 1
            return (base >> lo) & mask
        idx = _eval_ast(sl, env)
        return (base >> idx) & 1
    if isinstance(node, ast.GeneratorExp):
        return _eval_comprehension(node, env, generator=True)
    if isinstance(node, ast.ListComp):
        return _eval_comprehension(node, env, generator=False)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError(f"unsupported rule call {ast.dump(node.func)}")
        func = env.get(node.func.id)
        if not callable(func):
            raise ValueError(f"unsupported rule helper {node.func.id}")
        if node.keywords:
            raise ValueError(f"unsupported keyword args for rule helper {node.func.id}")
        args = [_eval_ast(arg, env) for arg in node.args]
        return _parse_int(func(*args), 0)
    raise ValueError(f"unsupported rule expression node {type(node).__name__}")


def _eval_comprehension(node, env, generator=False):
    """Evaluate a generator expression or list comprehension.

    Supports single-clause ``for`` with optional ``if`` filter, e.g.:
        ``(x for x in range(8) if x > 0)``
    Nested comprehensions are not supported.
    """
    if not node.generators:
        raise ValueError("comprehension with no generators")
    comp = node.generators[0]
    if len(node.generators) > 1:
        raise ValueError("nested comprehensions are not supported in rule expressions")
    if not isinstance(comp.target, ast.Name):
        raise ValueError("comprehension target must be a simple name")
    var_name = comp.target.id
    iter_values = _eval_iter(comp.iter, env)
    results = []
    for val in iter_values:
        local_env = dict(env)
        local_env[var_name] = val
        # Apply if-filters
        skip = False
        for if_clause in comp.ifs:
            if not _eval_ast(if_clause, local_env):
                skip = True
                break
        if skip:
            continue
        results.append(_eval_ast(node.elt, local_env))
    return results if not generator else results


def _eval_iter(node, env):
    """Evaluate an iterable source (range call or name reference)."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "range":
            args = [_eval_ast(a, env) for a in node.args]
            if len(args) == 1:
                return list(range(args[0]))
            if len(args) == 2:
                return list(range(args[0], args[1]))
            if len(args) == 3:
                return list(range(args[0], args[1], args[2]))
            raise ValueError(f"range() expects 1-3 args, got {len(args)}")
        # Other callables: evaluate and treat result as iterable if possible
        func = env.get(node.func.id)
        if callable(func):
            call_args = [_eval_ast(a, env) for a in node.args]
            result = func(*call_args)
            if isinstance(result, (list, tuple, range)):
                return list(result)
            return [_parse_int(result, 0)]
    if isinstance(node, ast.Name):
        val = env.get(node.id)
        if isinstance(val, (list, tuple, range)):
            return list(val)
        return [_parse_int(val, 0)]
    raise ValueError(f"unsupported iterable in comprehension: {ast.dump(node)}")


def _eval_rule_expr(expr, env):
    if isinstance(expr, bool):
        return int(expr)
    if isinstance(expr, int):
        return expr
    text = _normal_expr(expr)
    if not text:
        return 0
    if _literal_int(text):
        return _parse_int(text, 0)
    return _eval_ast(ast.parse(text, mode="eval"), env)


def _expr_names(expr):
    try:
        node = ast.parse(_normal_expr(expr), mode="eval")
    except Exception:
        return set()
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


def _rule_items(value):
    if isinstance(value, dict):
        return [{"name": k, "expr": v} for k, v in value.items()]
    return [item for item in value or [] if isinstance(item, dict)]


class FunctionalModel:
    def __init__(self, params=None):
        self.params = dict(SSOT_MODEL.get("parameters") or {})
        if params:
            self.params.update(params)
        self.state_defaults = self._state_defaults()
        self.state = dict(self.state_defaults)
        self._declared_state_names = set(self.state_defaults)
        self.registers = self._register_defaults()
        self.trace = []

    @staticmethod
    def _norm(value):
        text = str(value or "").strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        return text.strip("_")

    def _state_defaults(self):
        defaults = {}
        fm = SSOT_MODEL.get("function_model") or {}
        for idx, item in enumerate(fm.get("state_variables") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"state_{idx}")
            defaults[name] = item.get("reset", 0)
        defaults.setdefault("busy", 0)
        defaults.setdefault("error", 0)
        return defaults

    def _register_defaults(self):
        defaults = {}
        regs = SSOT_MODEL.get("registers") or {}
        for idx, item in enumerate(regs.get("register_list") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"REG{idx}")
            defaults[name] = item.get("reset", 0)
            off = item.get("offset")
            if off is not None:
                defaults[str(off)] = item.get("reset", 0)
        return defaults

    @staticmethod
    def _field_bounds(field):
        bits = field.get("bits")
        if isinstance(bits, (list, tuple)) and len(bits) >= 2:
            hi = _parse_int(bits[0], 0)
            lo = _parse_int(bits[1], 0)
            return (max(hi, lo), min(hi, lo))
        if "msb" in field and "lsb" in field:
            hi = _parse_int(field.get("msb"), 0)
            lo = _parse_int(field.get("lsb"), 0)
            return (max(hi, lo), min(hi, lo))
        if "lsb" in field and ("width" in field or "bit_width" in field):
            lo = _parse_int(field.get("lsb"), 0)
            width = max(1, _parse_int(field.get("width", field.get("bit_width", 1)), 1))
            return (lo + width - 1, lo)
        return (0, 0)

    def _state_name_for_register(self, reg):
        name = str(reg.get("name") or "").strip()
        if not name:
            return ""
        fm = SSOT_MODEL.get("function_model") or {}
        for row in fm.get("state_variables") or []:
            if not isinstance(row, dict):
                continue
            source = str(row.get("source") or "").strip().lower()
            state_name = str(row.get("name") or "").strip()
            if state_name and source == f"registers.{name}".lower():
                return state_name
        norm = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        candidates = [
            norm,
            f"{norm}_reg",
            f"{norm}_q",
            f"{norm}_r",
            f"{norm}_value",
        ]
        for field in reg.get("fields") or []:
            if isinstance(field, dict):
                fname = re.sub(r"[^a-z0-9]+", "_", str(field.get("name") or "").lower()).strip("_")
                if fname:
                    candidates.extend([fname, f"{fname}_reg", f"{fname}_q", f"{fname}_r"])
        for candidate in candidates:
            if candidate in self.state:
                return candidate
        return ""

    def _register_read_value(self, reg):
        name = str(reg.get("name") or "")
        state_name = self._state_name_for_register(reg)
        if state_name:
            value = _parse_int(self.state.get(state_name), 0)
        else:
            value = _parse_int(self.registers.get(name, reg.get("reset", 0)), 0)
        for field in reg.get("fields") or []:
            if not isinstance(field, dict):
                continue
            fname = str(field.get("name") or "")
            if fname in self.state:
                fval = _parse_int(self.state.get(fname), 0)
            elif f"{fname}_q" in self.state:
                fval = _parse_int(self.state.get(f"{fname}_q"), 0)
            elif fname in self.registers:
                fval = _parse_int(self.registers.get(fname), 0)
            else:
                continue
            hi, lo = self._field_bounds(field)
            width = max(1, hi - lo + 1)
            mask = (1 << width) - 1
            value = (value & ~(mask << lo)) | ((fval & mask) << lo)
        return value

    def _read_mux(self, addr):
        addr_i = _parse_int(addr, 0)
        regs = SSOT_MODEL.get("registers") or {}
        for reg in regs.get("register_list") or []:
            if not isinstance(reg, dict):
                continue
            off = reg.get("offset")
            if off is not None and addr_i == _parse_int(off, 0):
                return self._register_read_value(reg)
        return 0

    def reset(self):
        self.state = dict(self.state_defaults)
        self.registers = self._register_defaults()
        self.trace.clear()

    def _looks_like_register_access(self, txn):
        kind = self._norm(txn.get("kind") or txn.get("transaction") or "")
        return (
            kind in {"csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr"}
            or "reg" in txn
            or "addr_or_name" in txn
        )

    def _transactions(self):
        fm = SSOT_MODEL.get("function_model") or {}
        return [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]

    def _find_transaction(self, kind):
        wanted = self._norm(kind)
        for tx in self._transactions():
            aliases = [
                tx.get("id"),
                tx.get("name"),
                self._norm(tx.get("id")),
                self._norm(tx.get("name")),
            ]
            if wanted in {self._norm(x) for x in aliases if x}:
                return tx
        if wanted in {"reset", "rst"}:
            return {"id": "RESET", "name": "reset", "outputs": ["state reset"], "side_effects": ["reset"]}
        return None

    def _record(self, kind, txn, result):
        entry = {
            "kind": kind,
            "scenario_id": txn.get("scenario_id", ""),
            "result": result,
            "state": dict(self.state),
        }
        self.trace.append(entry)
        return result

    def _derived_signal_items(self):
        fm = SSOT_MODEL.get("function_model") or {}
        return _rule_items(fm.get("derived_signals"))

    def _resolve_derived_signals(self, env):
        pending = []
        for idx, item in enumerate(self._derived_signal_items()):
            name = str(
                item.get("name")
                or item.get("signal")
                or item.get("output")
                or item.get("port")
                or f"derived_{idx}"
            )
            expr = item.get("expr", item.get("expression", item.get("value", "")))
            if name and expr not in (None, ""):
                pending.append((name, expr, item.get("width") or item.get("bits")))

        unresolved_errors = {}
        for _pass in range(max(len(pending), 1) + 1):
            progressed = False
            next_pending = []
            for name, expr, width in pending:
                try:
                    value = _eval_rule_expr(expr, env)
                except KeyError as exc:
                    unresolved_errors[name] = str(exc)
                    next_pending.append((name, expr, width))
                    continue
                if width is not None:
                    width_i = _parse_int(width, 0)
                    value &= (1 << max(width_i, 0)) - 1 if width_i > 0 else value
                env[name] = value
                unresolved_errors.pop(name, None)
                progressed = True
            pending = next_pending
            if not pending or not progressed:
                break
        return unresolved_errors

    @staticmethod
    def _norm_state_token(value):
        text = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
        for suffix in ("_reg", "_q", "_r", "_ff"):
            if text.endswith(suffix):
                text = text[: -len(suffix)]
                break
        return text

    def _state_update_target(self, update_name):
        name = str(update_name or "").strip()
        if name in self._declared_state_names:
            return name
        norm_name = self._norm_state_token(name)
        best = ""
        best_len = 0
        for state_name in self._declared_state_names:
            norm_state = self._norm_state_token(state_name)
            if not norm_state:
                continue
            if norm_name == norm_state or norm_name.endswith("_" + norm_state) or f"_{norm_state}_" in norm_name:
                if len(norm_state) > best_len:
                    best = state_name
                    best_len = len(norm_state)
        return best

    def _rule_env(self, txn):
        env = {}
        env.update(_default_rule_helpers())
        env.update(self.params)
        env.update(self.state)
        env.update(self.registers)
        env.update(txn)
        env["read_mux"] = self._read_mux
        env["reduction_or"] = lambda value: 1 if _parse_int(value, 0) != 0 else 0
        env.setdefault("true", 1)
        env.setdefault("false", 0)
        self._resolve_derived_signals(env)
        return env

    def _apply_structured_rules(self, tx, txn):
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        if not output_rules and not state_updates:
            return None

        env = self._rule_env(txn)
        result = {
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "sample_accepted": 0,
        }
        pending_outputs = []
        for idx, rule in enumerate(output_rules):
            name = str(rule.get("name") or rule.get("output") or rule.get("port") or f"output_{idx}")
            aliases = [
                str(v)
                for v in (rule.get("output"), rule.get("port"))
                if v is not None and str(v).strip() and str(v).strip() != name
            ]
            pending_outputs.append((
                name,
                rule.get("expr", rule.get("expression", rule.get("value", 0))),
                rule.get("width") or rule.get("bits"),
                aliases,
            ))

        def _resolve_pending_outputs(required_names=None):
            nonlocal pending_outputs
            required = set(required_names or [])
            unresolved_errors = {}
            for _pass in range(max(len(pending_outputs), 1) + 1):
                progressed = False
                next_pending = []
                for name, expr, width, aliases in pending_outputs:
                    try:
                        value = _eval_rule_expr(expr, env)
                    except KeyError as exc:
                        unresolved_errors[name] = str(exc)
                        next_pending.append((name, expr, width, aliases))
                        continue
                    if width is not None:
                        value &= (1 << max(_parse_int(width, 0), 0)) - 1 if _parse_int(width, 0) > 0 else value
                    result[name] = value
                    env[name] = value
                    for alias in aliases:
                        result.setdefault(alias, value)
                        env[alias] = value
                    unresolved_errors.pop(name, None)
                    progressed = True
                pending_outputs = next_pending
                if not pending_outputs:
                    break
                if required and required.issubset(env):
                    break
                if not progressed:
                    break
            if required:
                unresolved_required = sorted(name for name in required if name not in env)
                if unresolved_required:
                    detail = ", ".join(
                        f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}"
                        for name in unresolved_required
                    )
                    raise KeyError(f"unresolved sample condition dependencies: {detail}")
            return unresolved_errors

        output_names = set()
        for name, _expr, _width, aliases in pending_outputs:
            output_names.add(name)
            output_names.update(aliases)
        sample_expr = tx.get("sample_condition")
        sample_accepted = True
        if sample_expr not in (None, ""):
            needed_outputs = _expr_names(sample_expr) & output_names
            if needed_outputs:
                _resolve_pending_outputs(needed_outputs)
            sample_accepted = bool(_eval_rule_expr(sample_expr, env))
        result["sample_accepted"] = int(sample_accepted)

        unresolved_errors = _resolve_pending_outputs()
        if pending_outputs:
            missing = ", ".join(f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}" for name, _expr, _width, _aliases in pending_outputs)
            raise KeyError(f"unresolved output rule dependencies: {missing}")

        updates = {}
        pending_updates = []
        if sample_accepted:
            for idx, rule in enumerate(state_updates):
                pending_updates.append((
                    str(rule.get("name") or rule.get("state") or f"state_{idx}"),
                    rule.get("expr", rule.get("expression", rule.get("value", 0))),
                ))
        unresolved_errors = {}
        for _pass in range(max(len(pending_updates), 1) + 1):
            progressed = False
            next_pending = []
            for name, expr in pending_updates:
                try:
                    value = _eval_rule_expr(expr, env)
                except KeyError as exc:
                    unresolved_errors[name] = str(exc)
                    next_pending.append((name, expr))
                    continue
                updates[name] = value
                env[name] = value
                target = self._state_update_target(name)
                if target and target != name:
                    updates[target] = value
                    env[target] = value
                unresolved_errors.pop(name, None)
                progressed = True
            pending_updates = next_pending
            if not pending_updates:
                break
            if not progressed:
                break
        if pending_updates:
            missing = ", ".join(f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}" for name, _expr in pending_updates)
            raise KeyError(f"unresolved state update dependencies: {missing}")
        if updates:
            commit_updates = {}
            for update_name, value in updates.items():
                target = self._state_update_target(update_name)
                if target:
                    commit_updates[target] = value
                else:
                    commit_updates[update_name] = value
            self.state.update(commit_updates)
            result["state_updates"] = dict(updates)
        return result

    def _apply_register_access(self, txn):
        if not self._looks_like_register_access(txn):
            return None
        op = self._norm(txn.get("op") or txn.get("kind"))
        key = txn.get("reg", txn.get("addr", txn.get("name", "")))
        key = str(key)
        if op in {"write", "wr", "csr_write", "control_status_access"}:
            self.registers[key] = txn.get("data", txn.get("value", 0))
            return {"resp": RESP_OKAY, "write": True, "reg": key, "value": self.registers[key]}
        if op in {"read", "rd", "csr_read"}:
            return {"resp": RESP_OKAY, "read": True, "reg": key, "value": self.registers.get(key, 0)}
        return None

    def _apply_primary(self, tx, txn):
        structured = self._apply_structured_rules(tx, txn)
        if structured is not None:
            return structured
        # T1 #1 — Cardinal rule enforcement:
        # When SSOT does not declare structured output_rules/state_updates for
        # this transaction, do NOT fabricate state via name heuristics. Return
        # an SSOT-question-annotated result so the gap surfaces in the trace
        # and downstream validators can escalate to ssot-gen / human.
        return {
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "outputs_spec": tx.get("outputs") or [],
            "side_effects_spec": tx.get("side_effects") or [],
            "ssot_gap": (
                "structured output_rules/state_updates undefined for transaction "
                + str(tx.get("id") or tx.get("name") or "<unknown>")
            ),
            "synthetic_state": False,
        }

    def apply(self, txn):
        txn = dict(txn or {})
        kind = self._norm(txn.get("kind") or txn.get("op") or txn.get("transaction") or "")
        tx = self._find_transaction(kind)
        if tx is not None:
            if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {"reset", "fm_reset"}:
                self.reset()
                return self._record(kind or "reset", txn, {"kind": "reset", "resp": RESP_OKAY, "state": dict(self.state)})
            return self._record(kind, txn, self._apply_primary(tx, txn))
        reg_result = self._apply_register_access(txn)
        if reg_result is not None:
            return self._record(kind or "register_access", txn, reg_result)
        if tx is None:
            return self._record(kind or "unknown", txn, {"kind": kind or "unknown", "resp": RESP_SLVERR, "error": "unsupported_transaction"})

    def _eval_precondition(self, expr, env):
        """Evaluate a single precondition string against env.

        SSOT preconditions are mostly Python-evaluable but occasionally carry
        a trailing natural-language clause in parentheses (e.g.
        '(req_i & req_mask) != 0 (at least one unmasked active request)').
        Normalize SQL-style OR/AND/NOT to Python operators, strip trailing
        natural-language parentheticals, and try progressively shorter
        prefixes until ast.parse succeeds. Unparseable preconditions are
        treated as True so they don't block transaction matching.
        """
        text = str(expr or "").strip()
        if not text:
            return True
        # Normalize boolean operators (SSOT prose sometimes uses uppercase).
        text = re.sub(r"\bOR\b", " or ",  text)
        text = re.sub(r"\bAND\b", " and ", text)
        text = re.sub(r"\bNOT\b", " not ", text)
        # Drop trailing parenthesized natural-language comments
        # ('something words ...'). Detect by alpha-majority content.
        def _strip_nl_tail(s):
            # Find a trailing " (...)" where contents are mostly alphabetic.
            depth = 0
            best_end = len(s)
            i = len(s) - 1
            # Walk from the right, capture the last balanced "(...)" tail.
            while i >= 0:
                ch = s[i]
                if ch == ")":
                    depth += 1
                elif ch == "(":
                    depth -= 1
                    if depth == 0:
                        inner = s[i + 1:best_end - 1]
                        alpha = sum(1 for c in inner if c.isalpha())
                        if alpha >= max(3, len(inner) // 2) and " " in inner:
                            # Natural language tail.
                            return s[:i].rstrip()
                        break
                i -= 1
            return s
        text = _strip_nl_tail(text)
        # Try ast.parse on the full string, then on progressively shorter
        # prefixes ending at a comparison/logical operator.
        candidates = [text]
        for tok in (" and ", " or "):
            for piece in text.split(tok):
                candidates.append(piece.strip())
        for cand in candidates:
            if not cand:
                continue
            try:
                tree = ast.parse(cand, mode="eval")
            except Exception:
                continue
            try:
                return bool(eval(compile(tree, "<precond>", mode="eval"), {"__builtins__": {}}, dict(env)))
            except Exception:
                continue
        return True

    def _select_transaction(self, inputs):
        """Pick the transaction whose preconditions all hold given inputs.

        Mutually-exclusive preconditions (typical SSOT pattern) yield a single
        active transaction. If multiple match, the first declared wins.
        Returns (tx, txn_payload) or (None, None) if none match.
        """
        env = dict(self.state)
        env.update(self.registers)
        env.update(inputs or {})
        for tx in self._transactions():
            if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {"reset", "fm_reset"}:
                continue
            preconds = [p for p in (tx.get("preconditions") or []) if isinstance(p, str)]
            if all(self._eval_precondition(p, env) for p in preconds):
                txn = {"kind": tx.get("id") or tx.get("name")}
                txn.update(inputs or {})
                return tx, txn
        return None, None

    def step(self, inputs=None):
        """Cycle-accurate step: select active transaction from preconditions,
        apply its output_rules and state_updates against current state and
        inputs, register the result. Mirrors the RTL's per-cycle behaviour
        when cocotb drives the same inputs cycle-by-cycle.

        Returns the structured result dict (same shape as apply()).
        """
        inputs = inputs or {}
        tx, txn = self._select_transaction(inputs)
        if tx is None:
            # No transaction matched preconditions: hold state, emit zero outputs.
            return {"kind": "idle", "resp": RESP_OKAY, "state": dict(self.state)}
        try:
            return self._record(tx.get("id") or "", txn, self._apply_primary(tx, txn))
        except KeyError as exc:
            # output_rule references a signal that's neither SSOT state, FL
            # register, nor caller-provided input (e.g. decoded combinational
            # signals: branch_taken, is_store). Surface a partial idle result
            # rather than crash — the per-cycle co-sim path treats this as
            # 'no comparable expected at this cycle for this IP'.
            return {
                "kind": "step_unresolved",
                "resp": RESP_OKAY,
                "transaction_id": tx.get("id"),
                "transaction_name": tx.get("name"),
                "step_unresolved": str(exc),
            }

    def csr_write(self, offset, data):
        """Apply an APB-style CSR write via _apply_register_access. Drives
        the registers dict + any state_variables sourced from those register
        fields (e.g. arb_enabled <- CTRL.enable)."""
        result = self._apply_register_access({"kind": "csr_write", "op": "write", "addr": offset, "reg": offset, "data": data, "value": data})
        # Mirror register field reset/source mapping into state_variables when
        # state_variables.source is a register field path.
        regs = SSOT_MODEL.get("registers") or {}
        reg_list = regs.get("register_list") or []
        fm = SSOT_MODEL.get("function_model") or {}
        state_vars = fm.get("state_variables") or []
        # Find which register matched the offset.
        matched_reg = None
        for r in reg_list:
            if r.get("offset") == offset:
                matched_reg = r
                break
        if matched_reg is None:
            return result
        for sv in state_vars:
            src = str(sv.get("source") or "")
            if not src.startswith("registers."):
                continue
            parts = src.split(".")
            if len(parts) >= 2 and parts[1] != matched_reg.get("name"):
                continue
            if len(parts) >= 3:
                field_name = parts[2]
                for f in matched_reg.get("fields") or []:
                    if f.get("name") == field_name:
                        bits = f.get("bits") or [0, 0]
                        hi, lo = (int(bits[0]), int(bits[1])) if len(bits) >= 2 else (0, 0)
                        mask = (1 << (hi - lo + 1)) - 1
                        self.state[sv.get("name")] = (data >> lo) & mask
                        break
            else:
                self.state[sv.get("name")] = data
        return result

    def coverage_seed_bins(self):
        return {item["id"]: False for item in SSOT_MODEL.get("fcov_bins", [])}


def run_self_check():
    model = FunctionalModel()
    txs = SSOT_MODEL.get("function_model", {}).get("transactions", [])
    results = []
    for idx, tx in enumerate(txs):
        if not isinstance(tx, dict):
            continue
        kind = tx.get("id") or tx.get("name") or f"transaction_{idx}"
        txn = {"kind": kind, "scenario_id": f"self_{kind}"}
        for field_idx, field in enumerate(tx.get("required_fields") or []):
            name = str(field)
            if name and name not in txn:
                txn[name] = field_idx + idx + 1
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        derived_signals = _rule_items((SSOT_MODEL.get("function_model") or {}).get("derived_signals"))
        rule_names = set()
        rule_names.update(_expr_names(tx.get("sample_condition", "")))
        for rule in output_rules + state_updates:
            rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        for rule in derived_signals:
            rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        output_names = {
            str(rule.get("name") or rule.get("output") or rule.get("port"))
            for rule in output_rules
            if rule.get("name") or rule.get("output") or rule.get("port")
        }
        update_names = {
            str(rule.get("name") or rule.get("state"))
            for rule in state_updates
            if rule.get("name") or rule.get("state")
        }
        derived_names = {
            str(rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port"))
            for rule in derived_signals
            if rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port")
        }
        known_names = set(model.params) | set(model.state) | set(model.registers) | output_names | update_names
        known_names.update(derived_names)
        known_names.update({"true", "false", "True", "False", "and", "or", "not"})
        known_names.update(_default_rule_helpers().keys())
        known_names.update({"read_mux", "reduction_or", "range"})
        for name in sorted(rule_names - known_names):
            if name and name not in txn:
                txn[name] = idx + len(txn) + 1
        result = model.apply(txn)
        results.append({
            "id": tx.get("id"),
            "name": tx.get("name"),
            "kind": kind,
            "passed": result.get("resp") == RESP_OKAY,
            "result": result,
        })
    unsupported = model.apply({"kind": "__unsupported_self_check__"})
    checks = [item["passed"] for item in results]
    checks.append(unsupported.get("resp") == RESP_SLVERR)

    # T1 #5 — invariants / reset / error_case coverage
    fm_block = SSOT_MODEL.get("function_model", {}) or {}
    invariants_raw = fm_block.get("invariants") or []
    if isinstance(invariants_raw, dict):
        invariants_raw = [{"name": k, "expr": v} for k, v in invariants_raw.items()]
    invariants = []
    for inv in invariants_raw:
        if isinstance(inv, str):
            invariants.append({"name": inv[:40], "expr": inv})
        elif isinstance(inv, dict):
            expr = inv.get("expr") or inv.get("expression") or inv.get("rule") or inv.get("invariant")
            if expr is None and len(inv) == 1:
                k, v = next(iter(inv.items())); expr = v if isinstance(v, str) else None
                inv = {"name": str(k), "expr": expr}
            if expr is not None:
                invariants.append({"name": inv.get("name") or str(expr)[:40], "expr": expr})
    invariants_eval_env = {}
    invariants_eval_env.update(_default_rule_helpers())
    invariants_eval_env.update(model.params)
    invariants_eval_env.update(model.state)
    invariants_eval_env.update(model.registers)
    invariants_evaluated = 0
    invariants_failed = []
    invariants_skipped = []
    for inv in invariants:
        try:
            ok = bool(_eval_rule_expr(inv["expr"], invariants_eval_env))
            invariants_evaluated += 1
            if not ok:
                invariants_failed.append({"name": inv["name"], "expr": inv["expr"]})
        except Exception as exc:
            invariants_skipped.append({"name": inv["name"], "expr": inv["expr"], "reason": str(exc)[:80]})

    reset_consistency = True
    reset_diff = {}
    try:
        baseline_defaults = dict(model.state_defaults)
        snapshot_model = FunctionalModel()
        snapshot_model.reset()
        for k, v in baseline_defaults.items():
            actual = snapshot_model.state.get(k)
            if actual != v:
                reset_consistency = False
                reset_diff[k] = {"expected": v, "actual": actual}
    except Exception as exc:
        reset_consistency = False
        reset_diff["__error__"] = str(exc)[:80]

    error_cases_total = 0
    error_cases_planned = 0
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        cases = tx.get("error_cases") or []
        if isinstance(cases, list):
            error_cases_total += len(cases)
            error_cases_planned += sum(1 for c in cases if isinstance(c, dict) and c.get("condition"))

    overall_pass = all(checks) and not invariants_failed and reset_consistency

    return {
        "passed": overall_pass,
        "checks": len(checks),
        "failed": checks.count(False),
        "transactions": len(txs),
        "transaction_results": results,
        "unsupported_transaction_check": unsupported.get("resp") == RESP_SLVERR,
        "trace_entries": len(model.trace),
        "coverage_bins": len(SSOT_MODEL.get("fcov_bins", [])),
        "invariants_total": len(invariants),
        "invariants_evaluated": invariants_evaluated,
        "invariants_failed": invariants_failed,
        "invariants_skipped": invariants_skipped,
        "reset_consistency": reset_consistency,
        "reset_diff": reset_diff,
        "error_cases_total": error_cases_total,
        "error_cases_planned": error_cases_planned,
    }


if __name__ == "__main__":
    print(json.dumps(run_self_check(), indent=2))

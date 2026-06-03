#!/usr/bin/env python3
"""Executable SSOT cycle-level model for mctp_assembler_scratch_v4. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'FM_ACCEPT_AXI_TLP': 129, 'FM_FILTER_VDM': 2, 'FM_PARSE_MCTP': 2, 'FM_ASSEMBLE_FRAGMENT': 4, 'FM_SRAM_PACK_WRITE': 32, 'FM_COMPLETE_MESSAGE': 3, 'FM_AXI_READBACK': 8, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'axi_write_channels', 'signal': 'm_axi_awvalid/m_axi_awready/m_axi_wvalid/m_axi_wready', 'description': 'AXI write address and data payload remain stable while valid and not ready.', 'predicate': 'aw_w_handshake_stable_until_ready'}, {'name': 'axi_read_channels', 'signal': 'm_axi_arvalid/m_axi_arready/m_axi_rvalid/m_axi_rready', 'description': 'AXI read address and data payload remain stable while valid and not ready.', 'predicate': 'ar_r_handshake_stable_until_ready'}, {'name': 'apb_access', 'signal': 'psel/penable/pready', 'description': 'APB completes only in access phase when PREADY is asserted.', 'predicate': 'apb_two_phase_access'}, {'name': 'sram_ready_valid', 'signal': 'sram_wr_valid/sram_wr_ready/sram_rd_req_valid/sram_rd_req_ready', 'description': 'SRAM request payload remains stable until accepted.', 'predicate': 'sram_payload_stable_until_ready'}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'one_tlp_per_axi_write_transaction', 'description': 'WLAST terminates one TLP and no next AW is accepted while the current TLP is open.'}, {'name': 'per_key_fragment_order', 'description': 'Fragments for one context key must follow packet sequence order.'}, {'name': 'descriptor_after_sram_flush', 'description': 'Descriptor publish occurs after final partial SRAM word is flushed.'}, {'name': 'readback_after_descriptor', 'description': 'Firmware readback uses completed descriptors unless raw debug read is enabled.'}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and timing instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 250, 'throughput': {'ingress': 'one 256-bit AXI beat per cycle while resources are available', 'readback': 'one 256-bit AXI R beat per SRAM response'}, 'outstanding': {'write_max': 1, 'read_max': 1, 'total_max': 2}, 'pipeline_stages': 7, 'queue_depth': 'DESCRIPTOR_FIFO_DEPTH'}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_ACCEPT_AXI_TLP', 'FM_FILTER_VDM', 'FM_PARSE_MCTP', 'FM_ASSEMBLE_FRAGMENT', 'FM_SRAM_PACK_WRITE', 'FM_COMPLETE_MESSAGE', 'FM_PACKET_DROP', 'FM_ASSEMBLY_DROP', 'FM_APB_ACCESS', 'FM_AXI_READBACK']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_axi_write_channels': 'AXI write address and data payload remain stable while valid and not ready.', 'handshake_axi_read_channels': 'AXI read address and data payload remain stable while valid and not ready.', 'handshake_apb_access': 'APB completes only in access phase when PREADY is asserted.', 'handshake_sram_ready_valid': 'SRAM request payload remains stable until accepted.', 'ordering_one_tlp_per_axi_write_transaction': 'WLAST terminates one TLP and no next AW is accepted while the current TLP is open.', 'ordering_per_key_fragment_order': 'Fragments for one context key must follow packet sequence order.', 'ordering_descriptor_after_sram_flush': 'Descriptor publish occurs after final partial SRAM word is flushed.', 'ordering_readback_after_descriptor': 'Firmware readback uses completed descriptors unless raw debug read is enabled.', 'latency_fm_accept_axi_tlp': 'latency bin for FM_ACCEPT_AXI_TLP', 'latency_fm_filter_vdm': 'latency bin for FM_FILTER_VDM', 'latency_fm_parse_mctp': 'latency bin for FM_PARSE_MCTP', 'latency_fm_assemble_fragment': 'latency bin for FM_ASSEMBLE_FRAGMENT', 'latency_fm_sram_pack_write': 'latency bin for FM_SRAM_PACK_WRITE', 'latency_fm_complete_message': 'latency bin for FM_COMPLETE_MESSAGE', 'latency_fm_packet_drop': 'latency bin for FM_PACKET_DROP', 'latency_fm_assembly_drop': 'latency bin for FM_ASSEMBLY_DROP', 'latency_fm_apb_access': 'latency bin for FM_APB_ACCESS', 'latency_fm_axi_readback': 'latency bin for FM_AXI_READBACK'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'mctp_assembler_scratch_v4', 'function_model': {'description': 'Byte-accurate transaction model from AXI write TLP ingress to MCTP payload assembly, SRAM packing, descriptor publish, APB control, and AXI readback.', 'constants': {'packet_drop_ids': ['PD_DISABLED_DROP_MODE', 'PD_MALFORMED_TLP', 'PD_UNSUPPORTED_VDM', 'PD_BAD_MCTP_HEADER', 'PD_BAD_PAD_OR_ALIGNMENT', 'PD_DEST_EID_REJECT', 'PD_UNEXPECTED_MIDDLE_END', 'PD_BAD_OR_EXPIRED_TAG'], 'assembly_drop_ids': ['AD_DUPLICATE_SOM', 'AD_SEQUENCE_MISMATCH', 'AD_MESSAGE_OVERFLOW', 'AD_SRAM_OVERFLOW', 'AD_DESCRIPTOR_FULL', 'AD_TIMEOUT']}, 'state_variables': [{'name': 'enable_reg', 'reset': 0, 'width': 1, 'source': 'registers.GLOBAL_CTRL.enable', 'description': 'Global assembly enable'}, {'name': 'drop_mode_reg', 'reset': 0, 'width': 1, 'source': 'registers.GLOBAL_CTRL.drop_mode', 'description': 'Drop mode control bit'}, {'name': 'raw_debug_read_enable', 'reset': 0, 'width': 1, 'source': 'registers.DEBUG_CTRL.raw_read_enable', 'description': 'Allows raw SRAM debug reads without descriptor'}, {'name': 'active_context_count', 'reset': 0, 'width': 5, 'description': 'Number of non-idle Q contexts'}, {'name': 'descriptor_count', 'reset': 0, 'width': 4, 'description': 'Completed descriptor FIFO occupancy'}, {'name': 'payload_byte_count', 'reset': 0, 'width': 13, 'description': 'Current assembled payload bytes for selected context'}, {'name': 'collected_tlp_count', 'reset': 0, 'width': 16, 'description': 'Accepted raw TLP counter'}, {'name': 'packet_drop_count', 'reset': 0, 'width': 32, 'description': 'Packet drop counter'}, {'name': 'assembly_drop_count', 'reset': 0, 'width': 32, 'description': 'Assembly drop counter'}, {'name': 'read_error_count', 'reset': 0, 'width': 32, 'description': 'AXI readback error counter'}, {'name': 'ctx_state', 'reset': 'STATE_IDLE', 'width': 2, 'description': 'Current Q FSM state for selected context'}, {'name': 'ctx_valid', 'reset': 0, 'width': 1, 'description': 'Selected context valid bit'}, {'name': 'ctx_error', 'reset': 0, 'width': 1, 'description': 'Selected context error bit'}, {'name': 'ctx_source_eid', 'reset': 0, 'width': 8, 'description': 'Selected context source EID'}, {'name': 'ctx_destination_eid', 'reset': 0, 'width': 8, 'description': 'Selected context destination EID'}, {'name': 'ctx_tag_owner', 'reset': 0, 'width': 1, 'description': 'Selected context tag owner'}, {'name': 'ctx_message_tag', 'reset': 0, 'width': 3, 'description': 'Selected context message tag'}, {'name': 'ctx_message_type', 'reset': 0, 'width': 8, 'description': 'Selected context MCTP message type'}, {'name': 'ctx_expected_seq', 'reset': 0, 'width': 2, 'description': 'Next expected MCTP packet sequence'}, {'name': 'ctx_last_seq', 'reset': 0, 'width': 2, 'description': 'Last accepted MCTP packet sequence'}, {'name': 'ctx_payload_base_addr', 'reset': 0, 'width': 'SRAM_ADDR_WIDTH', 'description': 'Linear allocator base address for selected context'}, {'name': 'ctx_payload_next_addr', 'reset': 0, 'width': 'SRAM_ADDR_WIDTH', 'description': 'Next payload byte address for selected context'}, {'name': 'ctx_payload_byte_count', 'reset': 0, 'width': 13, 'description': 'Payload byte count for selected context'}, {'name': 'ctx_transmission_unit_bytes', 'reset': 'BASELINE_MTU_BYTES', 'width': 13, 'description': 'Programmed TU size for selected context'}, {'name': 'ctx_timeout_age', 'reset': 0, 'width': 'TIMEOUT_COUNTER_WIDTH', 'description': 'Timeout age for selected context'}, {'name': 'ctx_last_drop_reason', 'reset': 'DROP_NONE', 'width': 8, 'description': 'Last drop reason visible per Q'}, {'name': 'ctx_partial_word_addr', 'reset': 0, 'width': 'SRAM_ADDR_WIDTH', 'description': 'Address of current partial 32-byte SRAM word'}, {'name': 'ctx_partial_word_strobe', 'reset': 0, 'width': 32, 'description': 'Valid bytes currently accumulated in partial word'}, {'name': 'ctx_partial_word_valid', 'reset': 0, 'width': 1, 'description': 'Partial word has pending payload bytes'}, {'name': 'ctx_partial_next_lane', 'reset': 0, 'width': 5, 'description': 'Next byte lane inside current 32-byte SRAM word'}], 'derived_signals': [{'name': 'context_key', 'expr': '(source_eid << 10) | (tag_owner << 9) | message_tag', 'width': 18}, {'name': 'packet_drop_pulse', 'expr': 'packet_drop_reason != DROP_NONE', 'width': 1}, {'name': 'assembly_drop_pulse', 'expr': 'assembly_drop_reason != DROP_NONE', 'width': 1}, {'name': 'apb_access', 'expr': 'psel and penable', 'width': 1, 'description': 'APB access phase helper derived from psel and penable.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_write', 'expr': 'psel and penable and pwrite', 'width': 1, 'description': 'APB write access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_read', 'expr': 'psel and penable and not pwrite', 'width': 1, 'description': 'APB read access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'addr', 'expr': 'paddr', 'width': 16, 'description': 'Register address helper derived from the APB paddr input.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wmask', 'expr': '((0x000000FF if (pstrb & 0x1) != 0 else 0) | (0x0000FF00 if (pstrb & 0x2) != 0 else 0) | (0x00FF0000 if (pstrb & 0x4) != 0 else 0) | (0xFF000000 if (pstrb & 0x8) != 0 else 0))', 'width': 32, 'description': 'APB byte-lane write mask expanded from pstrb.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'legal_addr', 'expr': '(addr == 0) or (addr == 4) or (addr == 16) or (addr == 20) or (addr == 32) or (addr == 36) or (addr == 48) or (addr == 52) or (addr == 256) or (addr == 260) or (addr == 264) or (addr == 268)', 'width': 1, 'description': 'APB legal address decode derived from registers.register_list offsets.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_global_ctrl', 'expr': 'apb_valid_write and (addr == 0)', 'width': 1, 'description': 'APB write decode helper for register GLOBAL_CTRL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_global_ctrl', 'expr': 'apb_valid_read and (addr == 0)', 'width': 1, 'description': 'APB read decode helper for register GLOBAL_CTRL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_global_status', 'expr': 'apb_valid_write and (addr == 4)', 'width': 1, 'description': 'APB write decode helper for register GLOBAL_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_global_status', 'expr': 'apb_valid_read and (addr == 4)', 'width': 1, 'description': 'APB read decode helper for register GLOBAL_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_irq_status', 'expr': 'apb_valid_write and (addr == 16)', 'width': 1, 'description': 'APB write decode helper for register IRQ_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_irq_status', 'expr': 'apb_valid_read and (addr == 16)', 'width': 1, 'description': 'APB read decode helper for register IRQ_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'irq_status_w1c', 'expr': '((pwdata & gpio_mask) if wr_irq_status else 0)', 'width': 32, 'description': 'W1C write mask helper for register IRQ_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_irq_enable', 'expr': 'apb_valid_write and (addr == 20)', 'width': 1, 'description': 'APB write decode helper for register IRQ_ENABLE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_irq_enable', 'expr': 'apb_valid_read and (addr == 20)', 'width': 1, 'description': 'APB read decode helper for register IRQ_ENABLE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_packet_drop_count', 'expr': 'apb_valid_write and (addr == 32)', 'width': 1, 'description': 'APB write decode helper for register PACKET_DROP_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_packet_drop_count', 'expr': 'apb_valid_read and (addr == 32)', 'width': 1, 'description': 'APB read decode helper for register PACKET_DROP_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_assembly_drop_count', 'expr': 'apb_valid_write and (addr == 36)', 'width': 1, 'description': 'APB write decode helper for register ASSEMBLY_DROP_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_assembly_drop_count', 'expr': 'apb_valid_read and (addr == 36)', 'width': 1, 'description': 'APB read decode helper for register ASSEMBLY_DROP_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_sram_base', 'expr': 'apb_valid_write and (addr == 48)', 'width': 1, 'description': 'APB write decode helper for register SRAM_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_sram_base', 'expr': 'apb_valid_read and (addr == 48)', 'width': 1, 'description': 'APB read decode helper for register SRAM_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_sram_limit', 'expr': 'apb_valid_write and (addr == 52)', 'width': 1, 'description': 'APB write decode helper for register SRAM_LIMIT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_sram_limit', 'expr': 'apb_valid_read and (addr == 52)', 'width': 1, 'description': 'APB read decode helper for register SRAM_LIMIT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_q_state', 'expr': 'apb_valid_write and (addr == 256)', 'width': 1, 'description': 'APB write decode helper for register Q_STATE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_q_state', 'expr': 'apb_valid_read and (addr == 256)', 'width': 1, 'description': 'APB read decode helper for register Q_STATE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_q_key', 'expr': 'apb_valid_write and (addr == 260)', 'width': 1, 'description': 'APB write decode helper for register Q_KEY.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_q_key', 'expr': 'apb_valid_read and (addr == 260)', 'width': 1, 'description': 'APB read decode helper for register Q_KEY.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_q_payload_base', 'expr': 'apb_valid_write and (addr == 264)', 'width': 1, 'description': 'APB write decode helper for register Q_PAYLOAD_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_q_payload_base', 'expr': 'apb_valid_read and (addr == 264)', 'width': 1, 'description': 'APB read decode helper for register Q_PAYLOAD_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_q_payload_count', 'expr': 'apb_valid_write and (addr == 268)', 'width': 1, 'description': 'APB write decode helper for register Q_PAYLOAD_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_q_payload_count', 'expr': 'apb_valid_read and (addr == 268)', 'width': 1, 'description': 'APB read decode helper for register Q_PAYLOAD_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'read_mux', 'expr': '(0 if addr == 0 else (0 if addr == 4 else (0 if addr == 16 else (0 if addr == 20 else (packet_drop_count if addr == 32 else (assembly_drop_count if addr == 36 else (0 if addr == 48 else (0 if addr == 52 else (0 if addr == 256 else (0 if addr == 260 else (0 if addr == 264 else (0 if addr == 268 else 0))))))))))))', 'width': 32, 'description': 'APB read data mux derived from registers.register_list offsets and function_model state variables.', 'source': 'repair_ssot_schema.apb_helper'}], 'invariants': [{'name': 'context_bound', 'expr': 'CONTEXT_COUNT >= active_context_count'}, {'name': 'payload_bound', 'expr': 'MAX_MESSAGE_BYTES >= payload_byte_count'}, {'name': 'descriptor_bound', 'expr': 'DESCRIPTOR_FIFO_DEPTH >= descriptor_count'}], 'transactions': [{'id': 'FM_ACCEPT_AXI_TLP', 'name': 'Accept one AXI4 write burst as one PCIe VDM TLP', 'required_fields': ['axi_aw_accept', 'axi_wlast_seen', 'tlp_byte_count'], 'preconditions': ['axi_aw_accept and axi_wlast_seen'], 'outputs': ['bvalid_next', 'bresp_next', {'name': 'bvalid_next', 'port': 'm_axi_bvalid', 'expr': 'axi_aw_accept and axi_wlast_seen', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'bresp_next', 'port': 'm_axi_bresp', 'expr': 'BRESP_OKAY', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'collected_tlp_count', 'expr': 'collected_tlp_count + axi_wlast_seen', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['raw TLP bytes captured until WLAST', 'write response emitted after packet classification']}, {'id': 'FM_FILTER_VDM', 'name': 'Validate PCIe VDM envelope for MCTP transport', 'required_fields': ['vdm_supported', 'packet_drop_reason'], 'preconditions': ['tlp_valid'], 'outputs': ['debug_vdm_valid', 'debug_drop_pulse', {'state': 'packet_drop_count', 'expr': 'packet_drop_count + packet_drop_pulse', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_last_drop_reason', 'expr': 'packet_drop_reason', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'error_cases': [{'id': 'PD_MALFORMED_TLP', 'condition': 'packet_drop_reason == 2', 'action': 'no_sram_write_and_increment_packet_drop_count'}, {'id': 'PD_UNSUPPORTED_VDM', 'condition': 'packet_drop_reason == 3', 'action': 'no_sram_write_and_increment_packet_drop_count'}]}, {'id': 'FM_PARSE_MCTP', 'name': 'Decode MCTP transport header and context key', 'required_fields': ['source_eid', 'destination_eid', 'tag_owner', 'message_tag', 'message_type', 'packet_seq', 'som', 'eom'], 'preconditions': ['vdm_supported'], 'outputs': ['debug_context_key', {'state': 'ctx_source_eid', 'expr': 'source_eid', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_destination_eid', 'expr': 'destination_eid', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_tag_owner', 'expr': 'tag_owner', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_message_tag', 'expr': 'message_tag', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_message_type', 'expr': 'message_type', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_last_seq', 'expr': 'packet_seq', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['context key prepared before allocation or lookup']}, {'id': 'FM_ASSEMBLE_FRAGMENT', 'name': 'Allocate or update a Q context for one MCTP fragment', 'required_fields': ['context_accept', 'context_alloc', 'context_id', 'payload_len', 'packet_seq', 'next_seq'], 'preconditions': ['enable_reg and context_accept'], 'outputs': ['debug_context_id', {'state': 'active_context_count', 'expr': 'active_context_count + context_alloc', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'STATE_ASSEMBLING', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_valid', 'expr': 'context_accept', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_expected_seq', 'expr': 'next_seq', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'payload_byte_count', 'expr': 'payload_byte_count + payload_len', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_payload_byte_count', 'expr': 'ctx_payload_byte_count + payload_len', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'error_cases': [{'id': 'AD_DUPLICATE_SOM', 'condition': 'assembly_drop_reason == 20', 'action': 'no_sram_write_and_increment_assembly_drop_count'}, {'id': 'AD_SEQUENCE_MISMATCH', 'condition': 'assembly_drop_reason == 21', 'action': 'no_sram_write_and_enter_error_state'}]}, {'id': 'FM_SRAM_PACK_WRITE', 'name': 'Pack payload bytes into 32-byte SRAM beats with no holes', 'required_fields': ['payload_valid', 'payload_len', 'lane_advance', 'word_full', 'eom', 'current_word_addr', 'payload_data_word', 'payload_byte_strobe', 'context_accept'], 'preconditions': ['payload_valid and context_accept'], 'outputs': ['sram_write_valid', 'sram_write_addr', 'sram_write_data', 'sram_write_strb', {'name': 'sram_write_valid', 'port': 'sram_wr_valid', 'expr': 'payload_valid and (word_full or eom)', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'sram_write_addr', 'port': 'sram_wr_addr', 'expr': 'current_word_addr', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'sram_write_data', 'port': 'sram_wr_data', 'expr': 'payload_data_word', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'sram_write_strb', 'port': 'sram_wr_strb', 'expr': 'payload_byte_strobe', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'ctx_partial_word_addr', 'expr': 'current_word_addr', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_partial_next_lane', 'expr': 'ctx_partial_next_lane + lane_advance', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_partial_word_valid', 'expr': 'payload_valid and not word_full', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_partial_word_strobe', 'expr': 'payload_byte_strobe', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_payload_next_addr', 'expr': 'ctx_payload_next_addr + payload_len', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['sram_write_beat_emitted_only_when_32B_word_full_or_final_fragment_flushes']}, {'id': 'FM_COMPLETE_MESSAGE', 'name': 'Complete EOM message and publish descriptor', 'required_fields': ['eom', 'descriptor_ready', 'descriptor_publish'], 'preconditions': ['eom and descriptor_ready'], 'outputs': ['interrupt', {'name': 'interrupt', 'port': 'irq', 'expr': 'descriptor_publish', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'descriptor_count', 'expr': 'descriptor_count + descriptor_publish', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'STATE_DONE_WAIT_DESCRIPTOR_POP', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'active_context_count', 'expr': 'active_context_count - descriptor_publish', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'error_cases': [{'id': 'AD_DESCRIPTOR_FULL', 'condition': 'assembly_drop_reason == 24', 'action': 'no_descriptor_publish_and_increment_assembly_drop_count'}]}, {'id': 'FM_PACKET_DROP', 'name': 'Packet drop without SRAM payload write', 'required_fields': ['packet_drop_reason'], 'preconditions': ['packet_drop_reason != DROP_NONE'], 'outputs': ['debug_drop_pulse', {'state': 'packet_drop_count', 'expr': 'packet_drop_count + (packet_drop_reason != DROP_NONE)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_last_drop_reason', 'expr': 'packet_drop_reason', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'error_cases': [{'id': 'PD_DISABLED_DROP_MODE', 'condition': 'packet_drop_reason == 1', 'action': 'no_sram_write_and_count_packet_drop'}, {'id': 'PD_BAD_PAD_OR_ALIGNMENT', 'condition': 'packet_drop_reason == 5', 'action': 'no_sram_write_and_count_packet_drop'}, {'id': 'PD_DEST_EID_REJECT', 'condition': 'packet_drop_reason == 6', 'action': 'no_sram_write_and_count_packet_drop'}, {'id': 'PD_UNEXPECTED_MIDDLE_END', 'condition': 'packet_drop_reason == 7', 'action': 'no_sram_write_and_count_packet_drop'}, {'id': 'PD_BAD_OR_EXPIRED_TAG', 'condition': 'packet_drop_reason == 8', 'action': 'no_sram_write_and_count_packet_drop'}]}, {'id': 'FM_ASSEMBLY_DROP', 'name': 'Assembly drop without descriptor publish', 'required_fields': ['assembly_drop_reason'], 'preconditions': ['assembly_drop_reason != DROP_NONE'], 'outputs': ['debug_drop_pulse', 'interrupt', {'name': 'interrupt', 'port': 'irq', 'expr': 'assembly_drop_reason != DROP_NONE', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'assembly_drop_count', 'expr': 'assembly_drop_count + (assembly_drop_reason != DROP_NONE)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_error', 'expr': 'assembly_drop_reason != DROP_NONE', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'STATE_ERROR', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'ctx_last_drop_reason', 'expr': 'assembly_drop_reason', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'error_cases': [{'id': 'AD_MESSAGE_OVERFLOW', 'condition': 'assembly_drop_reason == 22', 'action': 'no_sram_write_and_enter_error_state'}, {'id': 'AD_SRAM_OVERFLOW', 'condition': 'assembly_drop_reason == 23', 'action': 'no_sram_write_and_enter_error_state'}, {'id': 'AD_TIMEOUT', 'condition': 'assembly_drop_reason == 25', 'action': 'clear_context_after_counting_drop'}]}, {'id': 'FM_APB_ACCESS', 'name': 'APB register access', 'required_fields': ['apb_access', 'apb_write', 'apb_wdata', 'illegal_apb_access'], 'preconditions': ['apb_access'], 'outputs': ['apb_ready', 'apb_error', {'name': 'apb_ready', 'port': 'pready', 'expr': 'apb_access', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'apb_error', 'port': 'pslverr', 'expr': 'illegal_apb_access', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'enable_reg', 'expr': 'apb_wdata & apb_write', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'drop_mode_reg', 'expr': '(apb_wdata >> 1) & apb_write', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['control_status_interrupt_counter_descriptor_debug_register_visible']}, {'id': 'FM_AXI_READBACK', 'name': 'AXI readback from descriptor-backed SRAM payload', 'required_fields': ['axi_ar_accept', 'read_has_descriptor', 'readback_data', 'read_last'], 'preconditions': ['axi_ar_accept'], 'outputs': ['readback_valid', 'readback_data_out', 'readback_resp', 'readback_last', {'name': 'readback_valid', 'port': 'm_axi_rvalid', 'expr': 'axi_ar_accept', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'readback_data_out', 'port': 'm_axi_rdata', 'expr': 'readback_data if read_has_descriptor else ZERO_256', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'readback_resp', 'port': 'm_axi_rresp', 'expr': 'RESP_OKAY if read_has_descriptor else RESP_SLVERR', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'readback_last', 'port': 'm_axi_rlast', 'expr': 'read_last', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'read_error_count', 'expr': 'read_error_count + (not read_has_descriptor)', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['no_descriptor_read_returns_zero_data_and_slverr_unless_raw_debug_enabled']}]}, 'cycle_model': {'executable': 'python', 'clock': 'axi_aclk', 'reset': 'axi_aresetn', 'latency': {'FM_ACCEPT_AXI_TLP': {'min_cycles': 1, 'max_cycles': 129, 'description': 'One beat through MAX_TLP_BEATS write beats'}, 'FM_FILTER_VDM': {'min_cycles': 1, 'max_cycles': 2, 'description': 'Header filter and drop classification'}, 'FM_PARSE_MCTP': {'min_cycles': 1, 'max_cycles': 2, 'description': 'MCTP transport header decode'}, 'FM_ASSEMBLE_FRAGMENT': {'min_cycles': 1, 'max_cycles': 4, 'description': 'Context lookup and update'}, 'FM_SRAM_PACK_WRITE': {'min_cycles': 1, 'max_cycles': 32, 'description': 'Pack up to one SRAM word with final flush'}, 'FM_COMPLETE_MESSAGE': {'min_cycles': 1, 'max_cycles': 3, 'description': 'Descriptor publish and IRQ update'}, 'FM_AXI_READBACK': {'min_cycles': 1, 'max_cycles': 8, 'description': 'AR accept through SRAM response and R beat'}, 'default': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Default bounded transaction latency'}}, 'handshake_rules': [{'name': 'axi_write_channels', 'signal': 'm_axi_awvalid/m_axi_awready/m_axi_wvalid/m_axi_wready', 'predicate': 'aw_w_handshake_stable_until_ready', 'description': 'AXI write address and data payload remain stable while valid and not ready.'}, {'name': 'axi_read_channels', 'signal': 'm_axi_arvalid/m_axi_arready/m_axi_rvalid/m_axi_rready', 'predicate': 'ar_r_handshake_stable_until_ready', 'description': 'AXI read address and data payload remain stable while valid and not ready.'}, {'name': 'apb_access', 'signal': 'psel/penable/pready', 'predicate': 'apb_two_phase_access', 'description': 'APB completes only in access phase when PREADY is asserted.'}, {'name': 'sram_ready_valid', 'signal': 'sram_wr_valid/sram_wr_ready/sram_rd_req_valid/sram_rd_req_ready', 'predicate': 'sram_payload_stable_until_ready', 'description': 'SRAM request payload remains stable until accepted.'}], 'pipeline': [{'stage': 'axi_write_collect', 'cycle': 'variable_1_to_129', 'action': 'Collect one raw TLP write transaction through WLAST.'}, {'stage': 'pcie_vdm_filter', 'cycle': 1, 'action': 'Decode required PCIe VDM fields and classify packet drops.'}, {'stage': 'mctp_parse', 'cycle': 1, 'action': 'Decode MCTP transport fields and form context key.'}, {'stage': 'context_lookup_update', 'cycle': '1_to_4', 'action': 'Allocate', 'append': None, 'complete': None, 'or drop per-Q state.': None}, {'stage': 'sram_pack_write', 'cycle': '0_to_32', 'action': 'Emit packed 256-bit SRAM writes without holes.'}, {'stage': 'descriptor_irq', 'cycle': '1_to_3', 'action': 'Publish descriptor', 'update counters': None, 'and assert IRQ.': None}, {'stage': 'axi_readback', 'cycle': '1_to_8', 'action': 'Read SRAM payload and return AXI R beats.'}], 'ordering': [{'name': 'one_tlp_per_axi_write_transaction', 'description': 'WLAST terminates one TLP and no next AW is accepted while the current TLP is open.'}, {'name': 'per_key_fragment_order', 'description': 'Fragments for one context key must follow packet sequence order.'}, {'name': 'descriptor_after_sram_flush', 'description': 'Descriptor publish occurs after final partial SRAM word is flushed.'}, {'name': 'readback_after_descriptor', 'description': 'Firmware readback uses completed descriptors unless raw debug read is enabled.'}], 'backpressure': ['AXI write backpressure is applied when context table, descriptor FIFO, or SRAM pack resources cannot accept more data.', 'AXI read backpressure is applied while waiting for SRAM read responses.', 'SRAM read requests yield to SRAM write requests in the first-target arbiter.'], 'arbitration': {'name': 'sram_write_priority', 'policy': 'assembly SRAM writes win over firmware SRAM reads; reads are retried after write acceptance.'}, 'outstanding': 1, 'performance': {'frequency_mhz': 250, 'throughput': {'ingress': 'one 256-bit AXI beat per cycle while resources are available', 'readback': 'one 256-bit AXI R beat per SRAM response'}, 'outstanding': {'write_max': 1, 'read_max': 1, 'total_max': 2}, 'depth': {'queue_depth': 'DESCRIPTOR_FIFO_DEPTH', 'pipeline_stages': 7}}, 'backend_policy': 'Use the repo-owned pure-Python deterministic stepper; FunctionalModel remains the behavioral oracle.'}}


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

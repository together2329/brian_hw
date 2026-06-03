#!/usr/bin/env python3
"""Executable SSOT functional model for mctp_assembler_scratch_v5.

Generated from yaml/mctp_assembler_scratch_v5.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'mctp_assembler_scratch_v5', 'parameters': {'AXI_ADDR_WIDTH': 16, 'AXI_DATA_WIDTH': 256, 'AXI_STRB_WIDTH': 32, 'SRAM_ADDR_WIDTH': 16, 'SRAM_DATA_WIDTH': 256, 'CONTEXT_COUNT': 15, 'TLP_HEADER_SNAPSHOT_BYTES': 16, 'MIN_TRANSMISSION_UNIT_BYTES': 64, 'MAX_TRANSMISSION_UNIT_BYTES': 4096, 'TRANSMISSION_UNIT_ALIGN_BYTES': 4, 'MAX_TLP_BYTES': 4112, 'MAX_TLP_BEATS': 129, 'MAX_MESSAGE_BYTES': 4096, 'BASELINE_MTU_BYTES': 64, 'DESCRIPTOR_FIFO_DEPTH': 8, 'TIMEOUT_COUNTER_WIDTH': 24, 'STATE_IDLE': 0, 'STATE_ASSEMBLING': 1, 'STATE_ERROR': 2, 'STATE_DONE_WAIT_DESCRIPTOR_POP': 3, 'RESP_OKAY': 0, 'RESP_SLVERR': 2, 'BRESP_OKAY': 0, 'DROP_NONE': 0, 'ZERO_256': 0}, 'top_module': {'name': 'mctp_assembler_scratch_v5', 'file': 'rtl/mctp_assembler_scratch_v5.sv', 'version': '0.1.0', 'type': 'peripheral', 'description': 'AXI4 write-slave ingress block that accepts one PCIe VDM TLP per write transaction, assembles interleaved MCTP payload bytes into a 256-bit external SRAM interface with no packing holes, and exposes APB control plus AXI4 readback for firmware.', 'reference_spec': 'req/mctp_assembler_scratch_v5_requirements.md; DMTF DSP0236 MCTP Base Specification; DMTF DSP0238 MCTP PCIe VDM Transport Binding', 'target': {'technology': 'generic', 'clock_freq_mhz': 250, 'area_um2': None, 'power_mw': None}}, 'memory': {'allocator': {'policy': 'linear_bump', 'base_register': 'SRAM_BASE', 'limit_register': 'SRAM_LIMIT', 'reclaim_policy': 'descriptor_pop_does_not_reclaim_first_target'}, 'instances': [{'name': 'context_table', 'kind': 'register_array', 'entries': 'CONTEXT_COUNT', 'width_bits': 256, 'description': 'Per-Q context state and metadata.'}, {'name': 'descriptor_fifo', 'kind': 'fifo', 'depth': 'DESCRIPTOR_FIFO_DEPTH', 'width_bits': 192, 'description': 'Completed message descriptor queue.'}, {'name': 'partial_word_buffer', 'kind': 'register_array', 'entries': 'CONTEXT_COUNT', 'width_bits': 288, 'description': 'Per-Q 256-bit data', '32-bit strobe': None, 'and lane tracking.': None}, {'name': 'payload_sram_window', 'kind': 'external_sram', 'width_bits': 'SRAM_DATA_WIDTH', 'addr_width': 'SRAM_ADDR_WIDTH', 'description': 'External SRAM payload storage accessed through declared SRAM ports.'}]}, 'registers': {'address_unit': 'byte', 'apb_data_width': 32, 'global_window': {'base': 0, 'description': 'Control, status, interrupt, counter, descriptor, and debug registers.'}, 'per_q_bank': {'base': 256, 'stride': 64, 'count': 'CONTEXT_COUNT', 'description': 'Each Q exposes state, key, SRAM base, byte count, first TLP header snapshot, last TLP header snapshot, partial pack state, timeout, and last drop reason.'}, 'descriptor_window': {'base': 2048, 'depth': 'DESCRIPTOR_FIFO_DEPTH', 'pop_rule': 'Descriptor pop does not reclaim SRAM space in the first target.'}, 'register_list': [{'name': 'GLOBAL_CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Global control register.', 'fields': [{'name': 'enable', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'Enable packet assembly', 'write_effect': 'Updates enable_reg through APB CDC.'}, {'name': 'drop_mode', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': 'Drop all accepted ingress packets when set', 'write_effect': 'Causes PD_DISABLED_DROP_MODE.'}, {'name': 'raw_debug_read_enable', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'Allows raw debug AXI read without descriptor', 'write_effect': 'Enables raw SRAM read path for debug.'}, {'name': 'reserved', 'bits': [31, 3], 'access': 'reserved', 'reset': 0, 'description': 'Reserved', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}, {'name': 'GLOBAL_STATUS', 'offset': 4, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Global status summary.', 'fields': [{'name': 'active_context_count', 'bits': [4, 0], 'access': 'ro', 'reset': 0, 'description': 'Number of active contexts.'}, {'name': 'descriptor_count', 'bits': [8, 5], 'access': 'ro', 'reset': 0, 'description': 'Completed descriptor FIFO occupancy.'}, {'name': 'any_error', 'bits': [9, 9], 'access': 'ro', 'reset': 0, 'description': 'Any Q is in error state.'}, {'name': 'reserved', 'bits': [31, 10], 'access': 'reserved', 'reset': 0, 'description': 'Reserved', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}, {'name': 'IRQ_STATUS', 'offset': 16, 'width': 32, 'access': 'rw1c', 'reset': 0, 'description': 'Interrupt pending bits.', 'fields': [{'name': 'desc_pending', 'bits': [0, 0], 'access': 'rw1c', 'reset': 0, 'description': 'Descriptor available interrupt', 'write_effect': 'Write one clears pending bit.'}, {'name': 'packet_drop_pending', 'bits': [1, 1], 'access': 'rw1c', 'reset': 0, 'description': 'Packet drop interrupt', 'write_effect': 'Write one clears pending bit.'}, {'name': 'assembly_drop_pending', 'bits': [2, 2], 'access': 'rw1c', 'reset': 0, 'description': 'Assembly drop interrupt', 'write_effect': 'Write one clears pending bit.'}, {'name': 'read_error_pending', 'bits': [3, 3], 'access': 'rw1c', 'reset': 0, 'description': 'AXI read error interrupt', 'write_effect': 'Write one clears pending bit.'}, {'name': 'reserved', 'bits': [31, 4], 'access': 'reserved', 'reset': 0, 'description': 'Reserved', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}, {'name': 'IRQ_ENABLE', 'offset': 20, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Interrupt enable bits.', 'fields': [{'name': 'desc_enable', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'description': 'Enable descriptor IRQ', 'write_effect': 'Controls IRQ mask.'}, {'name': 'packet_drop_enable', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'description': 'Enable packet drop IRQ', 'write_effect': 'Controls IRQ mask.'}, {'name': 'assembly_drop_enable', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'description': 'Enable assembly drop IRQ', 'write_effect': 'Controls IRQ mask.'}, {'name': 'read_error_enable', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'description': 'Enable read error IRQ', 'write_effect': 'Controls IRQ mask.'}, {'name': 'reserved', 'bits': [31, 4], 'access': 'reserved', 'reset': 0, 'description': 'Reserved', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}, {'name': 'PACKET_DROP_COUNT', 'offset': 32, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Total packet drops across all reasons.', 'fields': [{'name': 'value', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Packet drop counter.'}]}, {'name': 'ASSEMBLY_DROP_COUNT', 'offset': 36, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Total assembly drops across all reasons.', 'fields': [{'name': 'value', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Assembly drop counter.'}]}, {'name': 'SRAM_BASE', 'offset': 48, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Linear bump allocator base address.', 'fields': [{'name': 'base_addr', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'description': 'SRAM allocation base byte address', 'write_effect': 'Sets allocator base when idle.'}]}, {'name': 'SRAM_LIMIT', 'offset': 52, 'width': 32, 'access': 'rw', 'reset': 65536, 'description': 'Linear bump allocator limit address.', 'fields': [{'name': 'limit_addr', 'bits': [31, 0], 'access': 'rw', 'reset': 65536, 'description': 'SRAM allocation exclusive limit byte address', 'write_effect': 'Sets allocator limit when idle.'}]}, {'name': 'Q_STATE', 'offset': 256, 'width': 32, 'access': 'ro', 'reset': 0, 'bank': 'per_q', 'description': 'Per-Q state and error summary at base plus q stride.', 'fields': [{'name': 'ctx_state', 'bits': [1, 0], 'access': 'ro', 'reset': 0, 'description': 'IDLE', 'ASSEMBLING': None, 'ERROR': None, 'or DONE_WAIT_DESCRIPTOR_POP.': None}, {'name': 'ctx_valid', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'description': 'Context valid bit.'}, {'name': 'ctx_error', 'bits': [3, 3], 'access': 'ro', 'reset': 0, 'description': 'Context error bit.'}, {'name': 'ctx_last_drop_reason', 'bits': [15, 8], 'access': 'ro', 'reset': 0, 'description': 'Last packet or assembly drop reason for this Q.'}, {'name': 'reserved', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'description': 'Reserved', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}, {'name': 'Q_KEY', 'offset': 260, 'width': 32, 'access': 'ro', 'reset': 0, 'bank': 'per_q', 'description': 'Per-Q context key fields.', 'fields': [{'name': 'source_eid', 'bits': [7, 0], 'access': 'ro', 'reset': 0, 'description': 'Source EID.'}, {'name': 'destination_eid', 'bits': [15, 8], 'access': 'ro', 'reset': 0, 'description': 'Destination EID.'}, {'name': 'tag_owner', 'bits': [16, 16], 'access': 'ro', 'reset': 0, 'description': 'Tag owner bit.'}, {'name': 'message_tag', 'bits': [19, 17], 'access': 'ro', 'reset': 0, 'description': 'Message tag.'}, {'name': 'message_type', 'bits': [27, 20], 'access': 'ro', 'reset': 0, 'description': 'MCTP message type.'}, {'name': 'reserved', 'bits': [31, 28], 'access': 'reserved', 'reset': 0, 'description': 'Reserved', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}, {'name': 'Q_PAYLOAD_BASE', 'offset': 264, 'width': 32, 'access': 'ro', 'reset': 0, 'bank': 'per_q', 'description': 'Per-Q payload base address.', 'fields': [{'name': 'payload_base_addr', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'SRAM base byte address for this assembled message.'}]}, {'name': 'Q_PAYLOAD_COUNT', 'offset': 268, 'width': 32, 'access': 'ro', 'reset': 0, 'bank': 'per_q', 'description': 'Per-Q payload byte count and partial word lane.', 'fields': [{'name': 'payload_byte_count', 'bits': [12, 0], 'access': 'ro', 'reset': 0, 'description': 'Assembled payload byte count.'}, {'name': 'partial_next_lane', 'bits': [20, 16], 'access': 'ro', 'reset': 0, 'description': 'Next byte lane in partial 32-byte SRAM word.'}, {'name': 'partial_word_valid', 'bits': [21, 21], 'access': 'ro', 'reset': 0, 'description': 'Partial word valid bit.'}, {'name': 'reserved', 'bits': [31, 22], 'access': 'reserved', 'reset': 0, 'description': 'Reserved', 'read_value': 0, 'write_effect': 'Writes ignored.'}]}]}, 'function_model': {'description': 'Byte-accurate transaction model from AXI write TLP ingress to MCTP payload assembly, SRAM packing, descriptor publish, APB control, and AXI readback.', 'constants': {'packet_drop_ids': ['PD_DISABLED_DROP_MODE', 'PD_MALFORMED_TLP', 'PD_UNSUPPORTED_VDM', 'PD_BAD_MCTP_HEADER', 'PD_BAD_PAD_OR_ALIGNMENT', 'PD_DEST_EID_REJECT', 'PD_UNEXPECTED_MIDDLE_END', 'PD_BAD_OR_EXPIRED_TAG'], 'assembly_drop_ids': ['AD_DUPLICATE_SOM', 'AD_SEQUENCE_MISMATCH', 'AD_MESSAGE_OVERFLOW', 'AD_SRAM_OVERFLOW', 'AD_DESCRIPTOR_FULL', 'AD_TIMEOUT']}, 'state_variables': [{'name': 'enable_reg', 'reset': 0, 'width': 1, 'source': 'registers.GLOBAL_CTRL.enable', 'description': 'Global assembly enable'}, {'name': 'drop_mode_reg', 'reset': 0, 'width': 1, 'source': 'registers.GLOBAL_CTRL.drop_mode', 'description': 'Drop mode control bit'}, {'name': 'raw_debug_read_enable', 'reset': 0, 'width': 1, 'source': 'registers.DEBUG_CTRL.raw_read_enable', 'description': 'Allows raw SRAM debug reads without descriptor'}, {'name': 'active_context_count', 'reset': 0, 'width': 5, 'description': 'Number of non-idle Q contexts'}, {'name': 'descriptor_count', 'reset': 0, 'width': 4, 'description': 'Completed descriptor FIFO occupancy'}, {'name': 'payload_byte_count', 'reset': 0, 'width': 13, 'description': 'Current assembled payload bytes for selected context'}, {'name': 'collected_tlp_count', 'reset': 0, 'width': 16, 'description': 'Accepted raw TLP counter'}, {'name': 'packet_drop_count', 'reset': 0, 'width': 32, 'description': 'Packet drop counter'}, {'name': 'assembly_drop_count', 'reset': 0, 'width': 32, 'description': 'Assembly drop counter'}, {'name': 'read_error_count', 'reset': 0, 'width': 32, 'description': 'AXI readback error counter'}, {'name': 'ctx_state', 'reset': 'STATE_IDLE', 'width': 2, 'description': 'Current Q FSM state for selected context'}, {'name': 'ctx_valid', 'reset': 0, 'width': 1, 'description': 'Selected context valid bit'}, {'name': 'ctx_error', 'reset': 0, 'width': 1, 'description': 'Selected context error bit'}, {'name': 'ctx_source_eid', 'reset': 0, 'width': 8, 'description': 'Selected context source EID'}, {'name': 'ctx_destination_eid', 'reset': 0, 'width': 8, 'description': 'Selected context destination EID'}, {'name': 'ctx_tag_owner', 'reset': 0, 'width': 1, 'description': 'Selected context tag owner'}, {'name': 'ctx_message_tag', 'reset': 0, 'width': 3, 'description': 'Selected context message tag'}, {'name': 'ctx_message_type', 'reset': 0, 'width': 8, 'description': 'Selected context MCTP message type'}, {'name': 'ctx_expected_seq', 'reset': 0, 'width': 2, 'description': 'Next expected MCTP packet sequence'}, {'name': 'ctx_last_seq', 'reset': 0, 'width': 2, 'description': 'Last accepted MCTP packet sequence'}, {'name': 'ctx_payload_base_addr', 'reset': 0, 'width': 'SRAM_ADDR_WIDTH', 'description': 'Linear allocator base address for selected context'}, {'name': 'ctx_payload_next_addr', 'reset': 0, 'width': 'SRAM_ADDR_WIDTH', 'description': 'Next payload byte address for selected context'}, {'name': 'ctx_payload_byte_count', 'reset': 0, 'width': 13, 'description': 'Payload byte count for selected context'}, {'name': 'ctx_transmission_unit_bytes', 'reset': 'BASELINE_MTU_BYTES', 'width': 13, 'description': 'Programmed TU size for selected context'}, {'name': 'ctx_timeout_age', 'reset': 0, 'width': 'TIMEOUT_COUNTER_WIDTH', 'description': 'Timeout age for selected context'}, {'name': 'ctx_last_drop_reason', 'reset': 'DROP_NONE', 'width': 8, 'description': 'Last drop reason visible per Q'}, {'name': 'ctx_partial_word_addr', 'reset': 0, 'width': 'SRAM_ADDR_WIDTH', 'description': 'Address of current partial 32-byte SRAM word'}, {'name': 'ctx_partial_word_strobe', 'reset': 0, 'width': 32, 'description': 'Valid bytes currently accumulated in partial word'}, {'name': 'ctx_partial_word_valid', 'reset': 0, 'width': 1, 'description': 'Partial word has pending payload bytes'}, {'name': 'ctx_partial_next_lane', 'reset': 0, 'width': 5, 'description': 'Next byte lane inside current 32-byte SRAM word'}], 'derived_signals': [{'name': 'context_key', 'expr': '(source_eid << 10) | (tag_owner << 9) | message_tag', 'width': 18}, {'name': 'packet_drop_pulse', 'expr': 'packet_drop_reason != DROP_NONE', 'width': 1}, {'name': 'assembly_drop_pulse', 'expr': 'assembly_drop_reason != DROP_NONE', 'width': 1}, {'name': 'apb_access', 'expr': 'psel and penable', 'width': 1, 'description': 'APB access phase helper derived from psel and penable.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_write', 'expr': 'psel and penable and pwrite', 'width': 1, 'description': 'APB write access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'apb_valid_read', 'expr': 'psel and penable and not pwrite', 'width': 1, 'description': 'APB read access helper derived from psel, penable, and pwrite.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'addr', 'expr': 'paddr', 'width': 16, 'description': 'Register address helper derived from the APB paddr input.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wmask', 'expr': '((0x000000FF if (pstrb & 0x1) != 0 else 0) | (0x0000FF00 if (pstrb & 0x2) != 0 else 0) | (0x00FF0000 if (pstrb & 0x4) != 0 else 0) | (0xFF000000 if (pstrb & 0x8) != 0 else 0))', 'width': 32, 'description': 'APB byte-lane write mask expanded from pstrb.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'legal_addr', 'expr': '(addr == 0) or (addr == 4) or (addr == 16) or (addr == 20) or (addr == 32) or (addr == 36) or (addr == 48) or (addr == 52) or (addr == 256) or (addr == 260) or (addr == 264) or (addr == 268)', 'width': 1, 'description': 'APB legal address decode derived from registers.register_list offsets.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_global_ctrl', 'expr': 'apb_valid_write and (addr == 0)', 'width': 1, 'description': 'APB write decode helper for register GLOBAL_CTRL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_global_ctrl', 'expr': 'apb_valid_read and (addr == 0)', 'width': 1, 'description': 'APB read decode helper for register GLOBAL_CTRL.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_global_status', 'expr': 'apb_valid_write and (addr == 4)', 'width': 1, 'description': 'APB write decode helper for register GLOBAL_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_global_status', 'expr': 'apb_valid_read and (addr == 4)', 'width': 1, 'description': 'APB read decode helper for register GLOBAL_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_irq_status', 'expr': 'apb_valid_write and (addr == 16)', 'width': 1, 'description': 'APB write decode helper for register IRQ_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_irq_status', 'expr': 'apb_valid_read and (addr == 16)', 'width': 1, 'description': 'APB read decode helper for register IRQ_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'irq_status_w1c', 'expr': '((pwdata & gpio_mask) if wr_irq_status else 0)', 'width': 32, 'description': 'W1C write mask helper for register IRQ_STATUS.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_irq_enable', 'expr': 'apb_valid_write and (addr == 20)', 'width': 1, 'description': 'APB write decode helper for register IRQ_ENABLE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_irq_enable', 'expr': 'apb_valid_read and (addr == 20)', 'width': 1, 'description': 'APB read decode helper for register IRQ_ENABLE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_packet_drop_count', 'expr': 'apb_valid_write and (addr == 32)', 'width': 1, 'description': 'APB write decode helper for register PACKET_DROP_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_packet_drop_count', 'expr': 'apb_valid_read and (addr == 32)', 'width': 1, 'description': 'APB read decode helper for register PACKET_DROP_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_assembly_drop_count', 'expr': 'apb_valid_write and (addr == 36)', 'width': 1, 'description': 'APB write decode helper for register ASSEMBLY_DROP_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_assembly_drop_count', 'expr': 'apb_valid_read and (addr == 36)', 'width': 1, 'description': 'APB read decode helper for register ASSEMBLY_DROP_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_sram_base', 'expr': 'apb_valid_write and (addr == 48)', 'width': 1, 'description': 'APB write decode helper for register SRAM_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_sram_base', 'expr': 'apb_valid_read and (addr == 48)', 'width': 1, 'description': 'APB read decode helper for register SRAM_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_sram_limit', 'expr': 'apb_valid_write and (addr == 52)', 'width': 1, 'description': 'APB write decode helper for register SRAM_LIMIT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_sram_limit', 'expr': 'apb_valid_read and (addr == 52)', 'width': 1, 'description': 'APB read decode helper for register SRAM_LIMIT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_q_state', 'expr': 'apb_valid_write and (addr == 256)', 'width': 1, 'description': 'APB write decode helper for register Q_STATE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_q_state', 'expr': 'apb_valid_read and (addr == 256)', 'width': 1, 'description': 'APB read decode helper for register Q_STATE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_q_key', 'expr': 'apb_valid_write and (addr == 260)', 'width': 1, 'description': 'APB write decode helper for register Q_KEY.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_q_key', 'expr': 'apb_valid_read and (addr == 260)', 'width': 1, 'description': 'APB read decode helper for register Q_KEY.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_q_payload_base', 'expr': 'apb_valid_write and (addr == 264)', 'width': 1, 'description': 'APB write decode helper for register Q_PAYLOAD_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_q_payload_base', 'expr': 'apb_valid_read and (addr == 264)', 'width': 1, 'description': 'APB read decode helper for register Q_PAYLOAD_BASE.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'wr_q_payload_count', 'expr': 'apb_valid_write and (addr == 268)', 'width': 1, 'description': 'APB write decode helper for register Q_PAYLOAD_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'rd_q_payload_count', 'expr': 'apb_valid_read and (addr == 268)', 'width': 1, 'description': 'APB read decode helper for register Q_PAYLOAD_COUNT.', 'source': 'repair_ssot_schema.apb_helper'}, {'name': 'read_mux', 'expr': '(0 if addr == 0 else (0 if addr == 4 else (0 if addr == 16 else (0 if addr == 20 else (packet_drop_count if addr == 32 else (assembly_drop_count if addr == 36 else (0 if addr == 48 else (0 if addr == 52 else (0 if addr == 256 else (0 if addr == 260 else (0 if addr == 264 else (0 if addr == 268 else 0))))))))))))', 'width': 32, 'description': 'APB read data mux derived from registers.register_list offsets and function_model state variables.', 'source': 'repair_ssot_schema.apb_helper'}], 'invariants': [{'name': 'context_bound', 'expr': 'CONTEXT_COUNT >= active_context_count'}, {'name': 'payload_bound', 'expr': 'MAX_MESSAGE_BYTES >= payload_byte_count'}, {'name': 'descriptor_bound', 'expr': 'DESCRIPTOR_FIFO_DEPTH >= descriptor_count'}], 'transactions': [{'id': 'FM_ACCEPT_AXI_TLP', 'name': 'Accept one AXI4 write burst as one PCIe VDM TLP', 'required_fields': ['axi_aw_accept', 'axi_wlast_seen', 'tlp_byte_count'], 'preconditions': ['axi_aw_accept and axi_wlast_seen'], 'outputs': ['bvalid_next', 'bresp_next', {'name': 'bvalid_next', 'port': 'm_axi_bvalid', 'expr': 'axi_aw_accept and axi_wlast_seen', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'bresp_next', 'port': 'm_axi_bresp', 'expr': 'BRESP_OKAY', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'collected_tlp_count', 'expr': 'collected_tlp_count + axi_wlast_seen', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'bvalid_next', 'expr': 'axi_aw_accept and axi_wlast_seen', 'width': 1, 'port': 'm_axi_bvalid'}, {'name': 'bresp_next', 'expr': 'BRESP_OKAY', 'width': 2, 'port': 'm_axi_bresp'}], 'state_updates': [{'name': 'collected_tlp_count', 'expr': 'collected_tlp_count + axi_wlast_seen', 'width': 16}], 'side_effects': ['raw TLP bytes captured until WLAST', 'write response emitted after packet classification']}, {'id': 'FM_FILTER_VDM', 'name': 'Validate PCIe VDM envelope for MCTP transport', 'required_fields': ['vdm_supported', 'packet_drop_reason'], 'preconditions': ['tlp_valid'], 'outputs': ['debug_vdm_valid', 'debug_drop_pulse', {'state': 'packet_drop_count', 'expr': 'packet_drop_count + packet_drop_pulse', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_last_drop_reason', 'expr': 'packet_drop_reason', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'debug_vdm_valid', 'expr': 'vdm_supported', 'width': 1, 'port': 'debug_vdm_valid'}, {'name': 'debug_drop_pulse', 'expr': 'packet_drop_reason != DROP_NONE', 'width': 1, 'port': 'debug_drop_pulse'}], 'state_updates': [{'name': 'packet_drop_count', 'expr': 'packet_drop_count + packet_drop_pulse', 'width': 32}, {'name': 'ctx_last_drop_reason', 'expr': 'packet_drop_reason', 'width': 8}], 'error_cases': [{'id': 'PD_MALFORMED_TLP', 'condition': 'packet_drop_reason == 2', 'action': 'no_sram_write_and_increment_packet_drop_count'}, {'id': 'PD_UNSUPPORTED_VDM', 'condition': 'packet_drop_reason == 3', 'action': 'no_sram_write_and_increment_packet_drop_count'}]}, {'id': 'FM_PARSE_MCTP', 'name': 'Decode MCTP transport header and context key', 'required_fields': ['source_eid', 'destination_eid', 'tag_owner', 'message_tag', 'message_type', 'packet_seq', 'som', 'eom'], 'preconditions': ['vdm_supported'], 'outputs': ['debug_context_key', {'state': 'ctx_source_eid', 'expr': 'source_eid', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_destination_eid', 'expr': 'destination_eid', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_tag_owner', 'expr': 'tag_owner', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_message_tag', 'expr': 'message_tag', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_message_type', 'expr': 'message_type', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_last_seq', 'expr': 'packet_seq', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'debug_context_key', 'expr': 'context_key', 'width': 18, 'port': 'debug_context_key'}], 'state_updates': [{'name': 'ctx_source_eid', 'expr': 'source_eid', 'width': 8}, {'name': 'ctx_destination_eid', 'expr': 'destination_eid', 'width': 8}, {'name': 'ctx_tag_owner', 'expr': 'tag_owner', 'width': 1}, {'name': 'ctx_message_tag', 'expr': 'message_tag', 'width': 3}, {'name': 'ctx_message_type', 'expr': 'message_type', 'width': 8}, {'name': 'ctx_last_seq', 'expr': 'packet_seq', 'width': 2}], 'side_effects': ['context key prepared before allocation or lookup']}, {'id': 'FM_ASSEMBLE_FRAGMENT', 'name': 'Allocate or update a Q context for one MCTP fragment', 'required_fields': ['context_accept', 'context_alloc', 'context_id', 'payload_len', 'packet_seq', 'next_seq'], 'preconditions': ['enable_reg and context_accept'], 'outputs': ['debug_context_id', {'state': 'active_context_count', 'expr': 'active_context_count + context_alloc', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'STATE_ASSEMBLING', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_valid', 'expr': 'context_accept', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_expected_seq', 'expr': 'next_seq', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'payload_byte_count', 'expr': 'payload_byte_count + payload_len', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_payload_byte_count', 'expr': 'ctx_payload_byte_count + payload_len', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'debug_context_id', 'expr': 'context_id', 'width': 4, 'port': 'debug_context_id'}], 'state_updates': [{'name': 'active_context_count', 'expr': 'active_context_count + context_alloc', 'width': 5}, {'name': 'ctx_state', 'expr': 'STATE_ASSEMBLING', 'width': 2}, {'name': 'ctx_valid', 'expr': 'context_accept', 'width': 1}, {'name': 'ctx_expected_seq', 'expr': 'next_seq', 'width': 2}, {'name': 'payload_byte_count', 'expr': 'payload_byte_count + payload_len', 'width': 13}, {'name': 'ctx_payload_byte_count', 'expr': 'ctx_payload_byte_count + payload_len', 'width': 13}], 'error_cases': [{'id': 'AD_DUPLICATE_SOM', 'condition': 'assembly_drop_reason == 20', 'action': 'no_sram_write_and_increment_assembly_drop_count'}, {'id': 'AD_SEQUENCE_MISMATCH', 'condition': 'assembly_drop_reason == 21', 'action': 'no_sram_write_and_enter_error_state'}]}, {'id': 'FM_SRAM_PACK_WRITE', 'name': 'Pack payload bytes into 32-byte SRAM beats with no holes', 'required_fields': ['payload_valid', 'payload_len', 'lane_advance', 'word_full', 'eom', 'current_word_addr', 'payload_data_word', 'payload_byte_strobe', 'context_accept'], 'preconditions': ['payload_valid and context_accept'], 'outputs': ['sram_write_valid', 'sram_write_addr', 'sram_write_data', 'sram_write_strb', {'name': 'sram_write_valid', 'port': 'sram_wr_valid', 'expr': 'payload_valid and (word_full or eom)', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'sram_write_addr', 'port': 'sram_wr_addr', 'expr': 'current_word_addr', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'sram_write_data', 'port': 'sram_wr_data', 'expr': 'payload_data_word', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'sram_write_strb', 'port': 'sram_wr_strb', 'expr': 'payload_byte_strobe', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'ctx_partial_word_addr', 'expr': 'current_word_addr', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_partial_next_lane', 'expr': 'ctx_partial_next_lane + lane_advance', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_partial_word_valid', 'expr': 'payload_valid and not word_full', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_partial_word_strobe', 'expr': 'payload_byte_strobe', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_payload_next_addr', 'expr': 'ctx_payload_next_addr + payload_len', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'sram_write_valid', 'expr': 'payload_valid and (word_full or eom)', 'width': 1, 'port': 'sram_wr_valid'}, {'name': 'sram_write_addr', 'expr': 'current_word_addr', 'width': 'SRAM_ADDR_WIDTH', 'port': 'sram_wr_addr'}, {'name': 'sram_write_data', 'expr': 'payload_data_word', 'width': 256, 'port': 'sram_wr_data'}, {'name': 'sram_write_strb', 'expr': 'payload_byte_strobe', 'width': 32, 'port': 'sram_wr_strb'}], 'state_updates': [{'name': 'ctx_partial_word_addr', 'expr': 'current_word_addr', 'width': 'SRAM_ADDR_WIDTH'}, {'name': 'ctx_partial_next_lane', 'expr': 'ctx_partial_next_lane + lane_advance', 'width': 5}, {'name': 'ctx_partial_word_valid', 'expr': 'payload_valid and not word_full', 'width': 1}, {'name': 'ctx_partial_word_strobe', 'expr': 'payload_byte_strobe', 'width': 32}, {'name': 'ctx_payload_next_addr', 'expr': 'ctx_payload_next_addr + payload_len', 'width': 'SRAM_ADDR_WIDTH'}], 'side_effects': ['sram_write_beat_emitted_only_when_32B_word_full_or_final_fragment_flushes']}, {'id': 'FM_COMPLETE_MESSAGE', 'name': 'Complete EOM message and publish descriptor', 'required_fields': ['eom', 'descriptor_ready', 'descriptor_publish'], 'preconditions': ['eom and descriptor_ready'], 'outputs': ['interrupt', {'name': 'interrupt', 'port': 'irq', 'expr': 'descriptor_publish', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'descriptor_count', 'expr': 'descriptor_count + descriptor_publish', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'STATE_DONE_WAIT_DESCRIPTOR_POP', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'active_context_count', 'expr': 'active_context_count - descriptor_publish', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'interrupt', 'expr': 'descriptor_publish', 'width': 1, 'port': 'irq'}], 'state_updates': [{'name': 'descriptor_count', 'expr': 'descriptor_count + descriptor_publish', 'width': 4}, {'name': 'ctx_state', 'expr': 'STATE_DONE_WAIT_DESCRIPTOR_POP', 'width': 2}, {'name': 'active_context_count', 'expr': 'active_context_count - descriptor_publish', 'width': 5}], 'error_cases': [{'id': 'AD_DESCRIPTOR_FULL', 'condition': 'assembly_drop_reason == 24', 'action': 'no_descriptor_publish_and_increment_assembly_drop_count'}]}, {'id': 'FM_PACKET_DROP', 'name': 'Packet drop without SRAM payload write', 'required_fields': ['packet_drop_reason'], 'preconditions': ['packet_drop_reason != DROP_NONE'], 'outputs': ['debug_drop_pulse', {'state': 'packet_drop_count', 'expr': 'packet_drop_count + (packet_drop_reason != DROP_NONE)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_last_drop_reason', 'expr': 'packet_drop_reason', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'debug_drop_pulse', 'expr': 'packet_drop_reason != DROP_NONE', 'width': 1, 'port': 'debug_drop_pulse'}], 'state_updates': [{'name': 'packet_drop_count', 'expr': 'packet_drop_count + (packet_drop_reason != DROP_NONE)', 'width': 32}, {'name': 'ctx_last_drop_reason', 'expr': 'packet_drop_reason', 'width': 8}], 'error_cases': [{'id': 'PD_DISABLED_DROP_MODE', 'condition': 'packet_drop_reason == 1', 'action': 'no_sram_write_and_count_packet_drop'}, {'id': 'PD_BAD_PAD_OR_ALIGNMENT', 'condition': 'packet_drop_reason == 5', 'action': 'no_sram_write_and_count_packet_drop'}, {'id': 'PD_DEST_EID_REJECT', 'condition': 'packet_drop_reason == 6', 'action': 'no_sram_write_and_count_packet_drop'}, {'id': 'PD_UNEXPECTED_MIDDLE_END', 'condition': 'packet_drop_reason == 7', 'action': 'no_sram_write_and_count_packet_drop'}, {'id': 'PD_BAD_OR_EXPIRED_TAG', 'condition': 'packet_drop_reason == 8', 'action': 'no_sram_write_and_count_packet_drop'}]}, {'id': 'FM_ASSEMBLY_DROP', 'name': 'Assembly drop without descriptor publish', 'required_fields': ['assembly_drop_reason'], 'preconditions': ['assembly_drop_reason != DROP_NONE'], 'outputs': ['debug_drop_pulse', 'interrupt', {'name': 'interrupt', 'port': 'irq', 'expr': 'assembly_drop_reason != DROP_NONE', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'assembly_drop_count', 'expr': 'assembly_drop_count + (assembly_drop_reason != DROP_NONE)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_error', 'expr': 'assembly_drop_reason != DROP_NONE', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_state', 'expr': 'STATE_ERROR', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'ctx_last_drop_reason', 'expr': 'assembly_drop_reason', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'debug_drop_pulse', 'expr': 'assembly_drop_reason != DROP_NONE', 'width': 1, 'port': 'debug_drop_pulse'}, {'name': 'interrupt', 'expr': 'assembly_drop_reason != DROP_NONE', 'width': 1, 'port': 'irq'}], 'state_updates': [{'name': 'assembly_drop_count', 'expr': 'assembly_drop_count + (assembly_drop_reason != DROP_NONE)', 'width': 32}, {'name': 'ctx_error', 'expr': 'assembly_drop_reason != DROP_NONE', 'width': 1}, {'name': 'ctx_state', 'expr': 'STATE_ERROR', 'width': 2}, {'name': 'ctx_last_drop_reason', 'expr': 'assembly_drop_reason', 'width': 8}], 'error_cases': [{'id': 'AD_MESSAGE_OVERFLOW', 'condition': 'assembly_drop_reason == 22', 'action': 'no_sram_write_and_enter_error_state'}, {'id': 'AD_SRAM_OVERFLOW', 'condition': 'assembly_drop_reason == 23', 'action': 'no_sram_write_and_enter_error_state'}, {'id': 'AD_TIMEOUT', 'condition': 'assembly_drop_reason == 25', 'action': 'clear_context_after_counting_drop'}]}, {'id': 'FM_APB_ACCESS', 'name': 'APB register access', 'required_fields': ['apb_access', 'apb_write', 'apb_wdata', 'illegal_apb_access'], 'preconditions': ['apb_access'], 'outputs': ['apb_ready', 'apb_error', {'name': 'apb_ready', 'port': 'pready', 'expr': 'apb_access', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'apb_error', 'port': 'pslverr', 'expr': 'illegal_apb_access', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'enable_reg', 'expr': 'apb_wdata & apb_write', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}, {'state': 'drop_mode_reg', 'expr': '(apb_wdata >> 1) & apb_write', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'apb_ready', 'expr': 'apb_access', 'width': 1, 'port': 'pready'}, {'name': 'apb_error', 'expr': 'illegal_apb_access', 'width': 1, 'port': 'pslverr'}], 'state_updates': [{'name': 'enable_reg', 'expr': 'apb_wdata & apb_write', 'width': 1}, {'name': 'drop_mode_reg', 'expr': '(apb_wdata >> 1) & apb_write', 'width': 1}], 'side_effects': ['control_status_interrupt_counter_descriptor_debug_register_visible']}, {'id': 'FM_AXI_READBACK', 'name': 'AXI readback from descriptor-backed SRAM payload', 'required_fields': ['axi_ar_accept', 'read_has_descriptor', 'readback_data', 'read_last'], 'preconditions': ['axi_ar_accept'], 'outputs': ['readback_valid', 'readback_data_out', 'readback_resp', 'readback_last', {'name': 'readback_valid', 'port': 'm_axi_rvalid', 'expr': 'axi_ar_accept', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'readback_data_out', 'port': 'm_axi_rdata', 'expr': 'readback_data if read_has_descriptor else ZERO_256', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'readback_resp', 'port': 'm_axi_rresp', 'expr': 'RESP_OKAY if read_has_descriptor else RESP_SLVERR', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'name': 'readback_last', 'port': 'm_axi_rlast', 'expr': 'read_last', 'description': 'Mirrored from executable output_rules for SSOT validator completeness.'}, {'state': 'read_error_count', 'expr': 'read_error_count + (not read_has_descriptor)', 'description': 'Mirrored from executable state_updates for SSOT validator completeness.'}], 'output_rules': [{'name': 'readback_valid', 'expr': 'axi_ar_accept', 'width': 1, 'port': 'm_axi_rvalid'}, {'name': 'readback_data_out', 'expr': 'readback_data if read_has_descriptor else ZERO_256', 'width': 256, 'port': 'm_axi_rdata'}, {'name': 'readback_resp', 'expr': 'RESP_OKAY if read_has_descriptor else RESP_SLVERR', 'width': 2, 'port': 'm_axi_rresp'}, {'name': 'readback_last', 'expr': 'read_last', 'width': 1, 'port': 'm_axi_rlast'}], 'state_updates': [{'name': 'read_error_count', 'expr': 'read_error_count + (not read_has_descriptor)', 'width': 32}], 'side_effects': ['no_descriptor_read_returns_zero_data_and_slverr_unless_raw_debug_enabled']}]}, 'cycle_model': {'executable': 'python', 'clock': 'axi_aclk', 'reset': 'axi_aresetn', 'latency': {'FM_ACCEPT_AXI_TLP': {'min_cycles': 1, 'max_cycles': 129, 'description': 'One beat through MAX_TLP_BEATS write beats'}, 'FM_FILTER_VDM': {'min_cycles': 1, 'max_cycles': 2, 'description': 'Header filter and drop classification'}, 'FM_PARSE_MCTP': {'min_cycles': 1, 'max_cycles': 2, 'description': 'MCTP transport header decode'}, 'FM_ASSEMBLE_FRAGMENT': {'min_cycles': 1, 'max_cycles': 4, 'description': 'Context lookup and update'}, 'FM_SRAM_PACK_WRITE': {'min_cycles': 1, 'max_cycles': 32, 'description': 'Pack up to one SRAM word with final flush'}, 'FM_COMPLETE_MESSAGE': {'min_cycles': 1, 'max_cycles': 3, 'description': 'Descriptor publish and IRQ update'}, 'FM_AXI_READBACK': {'min_cycles': 1, 'max_cycles': 8, 'description': 'AR accept through SRAM response and R beat'}, 'default': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Default bounded transaction latency'}}, 'handshake_rules': [{'name': 'axi_write_channels', 'signal': 'm_axi_awvalid/m_axi_awready/m_axi_wvalid/m_axi_wready', 'predicate': 'aw_w_handshake_stable_until_ready', 'description': 'AXI write address and data payload remain stable while valid and not ready.'}, {'name': 'axi_read_channels', 'signal': 'm_axi_arvalid/m_axi_arready/m_axi_rvalid/m_axi_rready', 'predicate': 'ar_r_handshake_stable_until_ready', 'description': 'AXI read address and data payload remain stable while valid and not ready.'}, {'name': 'apb_access', 'signal': 'psel/penable/pready', 'predicate': 'apb_two_phase_access', 'description': 'APB completes only in access phase when PREADY is asserted.'}, {'name': 'sram_ready_valid', 'signal': 'sram_wr_valid/sram_wr_ready/sram_rd_req_valid/sram_rd_req_ready', 'predicate': 'sram_payload_stable_until_ready', 'description': 'SRAM request payload remains stable until accepted.'}], 'pipeline': [{'stage': 'axi_write_collect', 'cycle': 'variable_1_to_129', 'action': 'Collect one raw TLP write transaction through WLAST.'}, {'stage': 'pcie_vdm_filter', 'cycle': 1, 'action': 'Decode required PCIe VDM fields and classify packet drops.'}, {'stage': 'mctp_parse', 'cycle': 1, 'action': 'Decode MCTP transport fields and form context key.'}, {'stage': 'context_lookup_update', 'cycle': '1_to_4', 'action': 'Allocate', 'append': None, 'complete': None, 'or drop per-Q state.': None}, {'stage': 'sram_pack_write', 'cycle': '0_to_32', 'action': 'Emit packed 256-bit SRAM writes without holes.'}, {'stage': 'descriptor_irq', 'cycle': '1_to_3', 'action': 'Publish descriptor', 'update counters': None, 'and assert IRQ.': None}, {'stage': 'axi_readback', 'cycle': '1_to_8', 'action': 'Read SRAM payload and return AXI R beats.'}], 'ordering': [{'name': 'one_tlp_per_axi_write_transaction', 'description': 'WLAST terminates one TLP and no next AW is accepted while the current TLP is open.'}, {'name': 'per_key_fragment_order', 'description': 'Fragments for one context key must follow packet sequence order.'}, {'name': 'descriptor_after_sram_flush', 'description': 'Descriptor publish occurs after final partial SRAM word is flushed.'}, {'name': 'readback_after_descriptor', 'description': 'Firmware readback uses completed descriptors unless raw debug read is enabled.'}], 'backpressure': ['AXI write backpressure is applied when context table, descriptor FIFO, or SRAM pack resources cannot accept more data.', 'AXI read backpressure is applied while waiting for SRAM read responses.', 'SRAM read requests yield to SRAM write requests in the first-target arbiter.'], 'arbitration': {'name': 'sram_write_priority', 'policy': 'assembly SRAM writes win over firmware SRAM reads; reads are retried after write acceptance.'}, 'outstanding': 1, 'performance': {'frequency_mhz': 250, 'throughput': {'ingress': 'one 256-bit AXI beat per cycle while resources are available', 'readback': 'one 256-bit AXI R beat per SRAM response'}, 'outstanding': {'write_max': 1, 'read_max': 1, 'total_max': 2}, 'depth': {'queue_depth': 'DESCRIPTOR_FIFO_DEPTH', 'pipeline_stages': 7}}, 'backend_policy': 'Use the repo-owned pure-Python deterministic stepper; FunctionalModel remains the behavioral oracle.'}, 'fcov_bins': [{'id': 'SC_VALID_SINGLE_PACKET_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_VALID_SINGLE_PACKET', 'description': 'Valid single packet'}, {'id': 'SC_SINGLE_PACKET_32B_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_SINGLE_PACKET_32B', 'description': 'Single 32B packet with nonzero key'}, {'id': 'SC_MULTI_FRAGMENT_TU64_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_MULTI_FRAGMENT_TU64', 'description': 'Multi-fragment TU64'}, {'id': 'SC_MULTI_FRAGMENT_3PKT_SHORT_LAST_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_MULTI_FRAGMENT_3PKT_SHORT_LAST', 'description': 'Three-fragment message with short final payload'}, {'id': 'SC_MAX_TU_4096_129_BEATS_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_MAX_TU_4096_129_BEATS', 'description': 'Maximum 4096B transmission unit'}, {'id': 'SC_INTERLEAVE_TWO_KEYS_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_INTERLEAVE_TWO_KEYS', 'description': 'Interleaved two keys'}, {'id': 'SC_INTERLEAVE_TWO_Q_COMPLETE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC_INTERLEAVE_TWO_Q_COMPLETE', 'description': 'Interleaved two Q contexts complete'}, {'id': 'SC_UNALIGNED_SRAM_PACK_NO_HOLES_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC_UNALIGNED_SRAM_PACK_NO_HOLES', 'description': 'Unaligned SRAM pack without holes'}, {'id': 'SC_FIRST_LAST_TLP_HEADERS_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC_FIRST_LAST_TLP_HEADERS', 'description': 'First and last TLP headers stored'}, {'id': 'SC_AXI_READBACK_TRIM_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC_AXI_READBACK_TRIM', 'description': 'AXI readback trims final short packet'}, {'id': 'SC_READBACK_AFTER_MULTI_ASSEMBLE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC_READBACK_AFTER_MULTI_ASSEMBLE', 'description': 'AXI readback after multi-fragment assembly'}, {'id': 'SC_APB_REGS_PER_Q_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC_APB_REGS_PER_Q', 'description': 'APB per-Q visibility'}, {'id': 'PD_DISABLED_DROP_MODE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[12]', 'scenario': 'PD_DISABLED_DROP_MODE', 'description': 'Drop mode packet drop'}, {'id': 'PD_MALFORMED_TLP_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[13]', 'scenario': 'PD_MALFORMED_TLP', 'description': 'Malformed TLP packet drop'}, {'id': 'PD_UNSUPPORTED_VDM_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[14]', 'scenario': 'PD_UNSUPPORTED_VDM', 'description': 'Unsupported VDM packet drop'}, {'id': 'PD_BAD_MCTP_HEADER_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[15]', 'scenario': 'PD_BAD_MCTP_HEADER', 'description': 'Bad MCTP header packet drop'}, {'id': 'PD_BAD_PAD_OR_ALIGNMENT_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[16]', 'scenario': 'PD_BAD_PAD_OR_ALIGNMENT', 'description': 'Bad pad or alignment packet drop'}, {'id': 'PD_DEST_EID_REJECT_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[17]', 'scenario': 'PD_DEST_EID_REJECT', 'description': 'Destination EID reject packet drop'}, {'id': 'PD_UNEXPECTED_MIDDLE_END_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[18]', 'scenario': 'PD_UNEXPECTED_MIDDLE_END', 'description': 'Unexpected middle or end packet drop'}, {'id': 'PD_BAD_OR_EXPIRED_TAG_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[19]', 'scenario': 'PD_BAD_OR_EXPIRED_TAG', 'description': 'Bad or expired tag packet drop'}, {'id': 'AD_DUPLICATE_SOM_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[20]', 'scenario': 'AD_DUPLICATE_SOM', 'description': 'Duplicate SOM assembly drop'}, {'id': 'AD_SEQUENCE_MISMATCH_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[21]', 'scenario': 'AD_SEQUENCE_MISMATCH', 'description': 'Sequence mismatch assembly drop'}, {'id': 'AD_MESSAGE_OVERFLOW_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[22]', 'scenario': 'AD_MESSAGE_OVERFLOW', 'description': 'Message overflow assembly drop'}, {'id': 'AD_SRAM_OVERFLOW_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[23]', 'scenario': 'AD_SRAM_OVERFLOW', 'description': 'SRAM overflow assembly drop'}, {'id': 'AD_DESCRIPTOR_FULL_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[24]', 'scenario': 'AD_DESCRIPTOR_FULL', 'description': 'Descriptor full assembly drop'}, {'id': 'AD_TIMEOUT_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[25]', 'scenario': 'AD_TIMEOUT', 'description': 'Timeout assembly drop'}, {'id': 'fcov_accept_axi_tlp', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ACCEPT_AXI_TLP', 'source_ref': 'function_model.transactions.FM_ACCEPT_AXI_TLP', 'description': 'AXI write burst accepted as one TLP.'}, {'id': 'fcov_parse_mctp', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_PARSE_MCTP', 'source_ref': 'function_model.transactions.FM_PARSE_MCTP', 'description': 'MCTP key and transport fields decoded.'}, {'id': 'fcov_assemble_fragment', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ASSEMBLE_FRAGMENT', 'source_ref': 'function_model.transactions.FM_ASSEMBLE_FRAGMENT', 'description': 'Context allocation and append behavior exercised.'}, {'id': 'fcov_sram_pack_write', 'class': 'memory', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_SRAM_PACK_WRITE', 'source_ref': 'function_model.transactions.FM_SRAM_PACK_WRITE', 'description': 'SRAM no-hole packing exercised.'}, {'id': 'fcov_axi_readback', 'class': 'readback', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_AXI_READBACK', 'source_ref': 'function_model.transactions.FM_AXI_READBACK', 'description': 'Descriptor-backed and no-descriptor readback exercised.'}, {'id': 'fcov_packet_drops', 'class': 'error', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_PACKET_DROP', 'source_ref': 'function_model.transactions.FM_PACKET_DROP', 'description': 'Every PD_* packet drop reason is observed.'}, {'id': 'fcov_assembly_drops', 'class': 'error', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ASSEMBLY_DROP', 'source_ref': 'function_model.transactions.FM_ASSEMBLY_DROP', 'description': 'Every AD_* assembly drop reason is observed.'}, {'id': 'ccov_axi_handshakes', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.axi_write_channels', 'source_ref': 'cycle_model.handshake_rules.axi_write_channels', 'description': 'AXI write and read ready/valid hold rules exercised.'}, {'id': 'ccov_sram_arbitration', 'class': 'arbitration', 'coverage_domain': 'cycle', 'source': 'cycle_model.arbitration', 'source_ref': 'cycle_model.arbitration', 'description': 'SRAM write priority over firmware read exercised.'}, {'id': 'ccov_backpressure', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure', 'source_ref': 'cycle_model.backpressure', 'description': 'Input and output backpressure cases exercised.'}, {'id': 'ccov_context_fsm', 'class': 'fsm', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm', 'source_ref': 'fsm.context_fsm', 'description': 'IDLE'}, {'id': 'ccov_max_tlp_beats', 'class': 'max_latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': '129-beat 4096B plus header TLP path exercised.'}, {'id': 'function_accept_one_axi4_write_burst_as_one_pcie_vdm_tlp', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_accept_axi_tlp', 'description': 'FM_ACCEPT_AXI_TLP accept_one_axi4_write_burst_as_one_pcie_vdm_tlp'}, {'id': 'function_validate_pcie_vdm_envelope_for_mctp_transport', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_filter_vdm', 'description': 'FM_FILTER_VDM validate_pcie_vdm_envelope_for_mctp_transport'}, {'id': 'function_decode_mctp_transport_header_and_context_key', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_parse_mctp', 'description': 'FM_PARSE_MCTP decode_mctp_transport_header_and_context_key'}, {'id': 'function_allocate_or_update_a_q_context_for_one_mctp_fragment', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_assemble_fragment', 'description': 'FM_ASSEMBLE_FRAGMENT allocate_or_update_a_q_context_for_one_mctp_fragment'}, {'id': 'function_pack_payload_bytes_into_32_byte_sram_beats_with_no_holes', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_sram_pack_write', 'description': 'FM_SRAM_PACK_WRITE pack_payload_bytes_into_32_byte_sram_beats_with_no_holes'}, {'id': 'function_complete_eom_message_and_publish_descriptor', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm_complete_message', 'description': 'FM_COMPLETE_MESSAGE complete_eom_message_and_publish_descriptor'}, {'id': 'function_packet_drop_without_sram_payload_write', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[6]', 'source_ref': 'function_model.transactions.fm_packet_drop', 'description': 'FM_PACKET_DROP packet_drop_without_sram_payload_write'}, {'id': 'function_assembly_drop_without_descriptor_publish', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[7]', 'source_ref': 'function_model.transactions.fm_assembly_drop', 'description': 'FM_ASSEMBLY_DROP assembly_drop_without_descriptor_publish'}, {'id': 'function_apb_register_access', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[8]', 'source_ref': 'function_model.transactions.fm_apb_access', 'description': 'FM_APB_ACCESS apb_register_access'}, {'id': 'function_axi_readback_from_descriptor_backed_sram_payload', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[9]', 'source_ref': 'function_model.transactions.fm_axi_readback', 'description': 'FM_AXI_READBACK axi_readback_from_descriptor_backed_sram_payload'}, {'id': 'cycle_axi_write_channels', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': 'AXI write address and data payload remain stable while valid and not ready.'}, {'id': 'cycle_axi_read_channels', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': 'AXI read address and data payload remain stable while valid and not ready.'}, {'id': 'cycle_apb_access', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': 'APB completes only in access phase when PREADY is asserted.'}, {'id': 'cycle_sram_ready_valid', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': 'SRAM request payload remains stable until accepted.'}, {'id': 'cycle_latency_fm_accept_axi_tlp', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.FM_ACCEPT_AXI_TLP', 'source_ref': 'cycle_model.latency.FM_ACCEPT_AXI_TLP', 'description': "{'min_cycles': 1, 'max_cycles': 129, 'description': 'One beat through MAX_TLP_BEATS write beats'}"}, {'id': 'cycle_latency_fm_filter_vdm', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.FM_FILTER_VDM', 'source_ref': 'cycle_model.latency.FM_FILTER_VDM', 'description': "{'min_cycles': 1, 'max_cycles': 2, 'description': 'Header filter and drop classification'}"}, {'id': 'cycle_latency_fm_parse_mctp', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.FM_PARSE_MCTP', 'source_ref': 'cycle_model.latency.FM_PARSE_MCTP', 'description': "{'min_cycles': 1, 'max_cycles': 2, 'description': 'MCTP transport header decode'}"}, {'id': 'cycle_latency_fm_assemble_fragment', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.FM_ASSEMBLE_FRAGMENT', 'source_ref': 'cycle_model.latency.FM_ASSEMBLE_FRAGMENT', 'description': "{'min_cycles': 1, 'max_cycles': 4, 'description': 'Context lookup and update'}"}, {'id': 'cycle_latency_fm_sram_pack_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.FM_SRAM_PACK_WRITE', 'source_ref': 'cycle_model.latency.FM_SRAM_PACK_WRITE', 'description': "{'min_cycles': 1, 'max_cycles': 32, 'description': 'Pack up to one SRAM word with final flush'}"}, {'id': 'cycle_latency_fm_complete_message', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.FM_COMPLETE_MESSAGE', 'source_ref': 'cycle_model.latency.FM_COMPLETE_MESSAGE', 'description': "{'min_cycles': 1, 'max_cycles': 3, 'description': 'Descriptor publish and IRQ update'}"}, {'id': 'cycle_latency_fm_axi_readback', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.FM_AXI_READBACK', 'source_ref': 'cycle_model.latency.FM_AXI_READBACK', 'description': "{'min_cycles': 1, 'max_cycles': 8, 'description': 'AR accept through SRAM response and R beat'}"}, {'id': 'cycle_latency_default', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.default', 'source_ref': 'cycle_model.latency.default', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Default bounded transaction latency'}"}, {'id': 'cycle_pipeline_axi_write_collect', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Collect one raw TLP write transaction through WLAST.'}, {'id': 'cycle_pipeline_pcie_vdm_filter', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Decode required PCIe VDM fields and classify packet drops.'}, {'id': 'cycle_pipeline_mctp_parse', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Decode MCTP transport fields and form context key.'}, {'id': 'cycle_pipeline_context_lookup_update', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Allocate'}, {'id': 'cycle_pipeline_sram_pack_write', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Emit packed 256-bit SRAM writes without holes.'}, {'id': 'cycle_pipeline_descriptor_irq', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[5]', 'source_ref': 'cycle_model.pipeline[5]', 'description': 'Publish descriptor'}, {'id': 'cycle_pipeline_axi_readback', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[6]', 'source_ref': 'cycle_model.pipeline[6]', 'description': 'Read SRAM payload and return AXI R beats.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': "{'name': 'one_tlp_per_axi_write_transaction', 'description': 'WLAST terminates one TLP and no next AW is accepted while the current TLP is open.'}"}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': "{'name': 'per_key_fragment_order', 'description': 'Fragments for one context key must follow packet sequence order.'}"}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': "{'name': 'descriptor_after_sram_flush', 'description': 'Descriptor publish occurs after final partial SRAM word is flushed.'}"}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': "{'name': 'readback_after_descriptor', 'description': 'Firmware readback uses completed descriptors unless raw debug read is enabled.'}"}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'AXI write backpressure is applied when context table, descriptor FIFO, or SRAM pack resources cannot accept more data.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'AXI read backpressure is applied while waiting for SRAM read responses.'}, {'id': 'cycle_backpressure_2', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[2]', 'source_ref': 'cycle_model.backpressure[2]', 'description': 'SRAM read requests yield to SRAM write requests in the first-target arbiter.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'write_max': 1, 'read_max': 1, 'total_max': 2}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'queue_depth': 'DESCRIPTOR_FIFO_DEPTH', 'pipeline_stages': 7}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '250'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'ingress': 'one 256-bit AXI beat per cycle while resources are available', 'readback': 'one 256-bit AXI R beat per SRAM response'}"}, {'id': 'fsm_context_fsm_idle_to_assembling_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[0]', 'source_ref': 'fsm.context_fsm.transitions[0]', 'description': "{'from': 'IDLE', 'to': 'ASSEMBLING', 'when': 'valid_som_and_context_available', 'action': 'allocate_q_and_store_first_tlp_header'}"}, {'id': 'fsm_context_fsm_assembling_to_assembling_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[1]', 'source_ref': 'fsm.context_fsm.transitions[1]', 'description': "{'from': 'ASSEMBLING', 'to': 'ASSEMBLING', 'when': 'valid_middle_fragment', 'action': 'append_payload_and_update_last_tlp_header'}"}, {'id': 'fsm_context_fsm_assembling_to_done_wait_descriptor_pop_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[2]', 'source_ref': 'fsm.context_fsm.transitions[2]', 'description': "{'from': 'ASSEMBLING', 'to': 'DONE_WAIT_DESCRIPTOR_POP', 'when': 'valid_eom_and_descriptor_available', 'action': 'flush_partial_word_and_publish_descriptor'}"}, {'id': 'fsm_context_fsm_idle_to_error_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[3]', 'source_ref': 'fsm.context_fsm.transitions[3]', 'description': "{'from': 'IDLE', 'to': 'ERROR', 'when': 'unexpected_middle_or_eom', 'action': 'raise_PD_UNEXPECTED_MIDDLE_END'}"}, {'id': 'fsm_context_fsm_assembling_to_error_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[4]', 'source_ref': 'fsm.context_fsm.transitions[4]', 'description': "{'from': 'ASSEMBLING', 'to': 'ERROR', 'when': 'sequence_or_overflow_or_timeout', 'action': 'raise_AD_drop_reason'}"}, {'id': 'fsm_context_fsm_done_wait_descriptor_pop_to_idle_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[5]', 'source_ref': 'fsm.context_fsm.transitions[5]', 'description': "{'from': 'DONE_WAIT_DESCRIPTOR_POP', 'to': 'IDLE', 'when': 'descriptor_pop', 'action': 'release_context_without_reclaiming_sram_space'}"}, {'id': 'fsm_context_fsm_error_to_idle_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.context_fsm.transitions[6]', 'source_ref': 'fsm.context_fsm.transitions[6]', 'description': "{'from': 'ERROR', 'to': 'IDLE', 'when': 'software_clear_or_timeout_cleanup', 'action': 'clear_context_visible_error_state'}"}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'PD_DISABLED_DROP_MODE', 'condition': 'drop_mode_reg', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'PD_MALFORMED_TLP', 'condition': 'malformed_tlp_header_or_length', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'PD_UNSUPPORTED_VDM', 'condition': 'vendor_or_message_code_not_mctp_vdm', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_3', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': "{'id': 'PD_BAD_MCTP_HEADER', 'condition': 'invalid_mctp_transport_header', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_4', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[4]', 'source_ref': 'error_handling.error_sources[4]', 'description': "{'id': 'PD_BAD_PAD_OR_ALIGNMENT', 'condition': 'nonfinal_payload_not_tu_sized_or_not_4B_aligned', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_5', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[5]', 'source_ref': 'error_handling.error_sources[5]', 'description': "{'id': 'PD_DEST_EID_REJECT', 'condition': 'destination_eid_filter_miss', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_6', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[6]', 'source_ref': 'error_handling.error_sources[6]', 'description': "{'id': 'PD_UNEXPECTED_MIDDLE_END', 'condition': 'middle_or_eom_without_matching_context', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_7', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[7]', 'source_ref': 'error_handling.error_sources[7]', 'description': "{'id': 'PD_BAD_OR_EXPIRED_TAG', 'condition': 'tag_owner_message_tag_key_invalid_or_expired', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_8', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[8]', 'source_ref': 'error_handling.error_sources[8]', 'description': "{'id': 'AD_DUPLICATE_SOM', 'condition': 'som_matches_active_context', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_9', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[9]', 'source_ref': 'error_handling.error_sources[9]', 'description': "{'id': 'AD_SEQUENCE_MISMATCH', 'condition': 'packet_seq_not_expected', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_10', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[10]', 'source_ref': 'error_handling.error_sources[10]', 'description': "{'id': 'AD_MESSAGE_OVERFLOW', 'condition': 'payload_count_exceeds_MAX_MESSAGE_BYTES', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_11', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[11]', 'source_ref': 'error_handling.error_sources[11]', 'description': "{'id': 'AD_SRAM_OVERFLOW', 'condition': 'linear_allocator_exceeds_sram_limit', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_12', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[12]', 'source_ref': 'error_handling.error_sources[12]', 'description': "{'id': 'AD_DESCRIPTOR_FULL', 'condition': 'descriptor_fifo_full_at_eom', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_13', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[13]', 'source_ref': 'error_handling.error_sources[13]', 'description': "{'id': 'AD_TIMEOUT', 'condition': 'ctx_timeout_age_exceeds_timeout_limit', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}]}
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

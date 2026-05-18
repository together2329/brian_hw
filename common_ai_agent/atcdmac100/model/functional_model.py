#!/usr/bin/env python3
"""Executable SSOT functional model for atcdmac100.

Generated from yaml/atcdmac100.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'atcdmac100', 'parameters': {'ADDR_WIDTH': 32, 'DATA_WIDTH': 32, 'DMA_CH_NUM': 8, 'REQ_ACK_NUM': 16, 'FIFO_DEPTH': 8, 'CHAIN_TRANSFER_SUPPORT': 1}, 'top_module': {'name': 'atcdmac100', 'file': 'rtl/atcdmac100.sv', 'version': 'DS079_V1.2_doc_flow', 'type': 'rtl', 'description': 'AndeShape ATCDMAC100 DMA controller: AMBA 2 AHB slave register interface, AHB master data mover, up to 8 channels, up to 16 request/acknowledge pairs, round-robin arbitration with two priority levels, chain transfer hooks, interrupts, and configurable FIFO/address width.', 'target': 'synthesizable SystemVerilog validated through ATLAS full pipeline'}, 'memory': {'instances': [], 'addressing': {'policy': 'No internal memory array is architecturally required; external AHB memory supplies source/destination storage.'}, 'storage_policy': 'Only FIFO buffering is implementation detail bounded by FIFO_DEPTH; no firmware-visible memory.'}, 'registers': {'address_unit': 'byte', 'register_list': [{'name': 'IdRev', 'offset': '0x00', 'width': 32, 'access': 'RO', 'reset': '0x01021012', 'description': 'ID and revision register', 'fields': [{'name': 'ID', 'bits': [31, 12], 'access': 'RO', 'reset': '0x01021', 'description': 'ID number for DMAC', 'write_effect': 'none'}, {'name': 'RevMajor', 'bits': [11, 4], 'access': 'RO', 'reset': '0x1', 'description': 'Major revision', 'write_effect': 'none'}, {'name': 'RevMinor', 'bits': [3, 0], 'access': 'RO', 'reset': '0x2', 'description': 'Minor revision', 'write_effect': 'none'}]}, {'name': 'DMACfg', 'offset': '0x10', 'width': 32, 'access': 'RO', 'reset': 'CONFIG', 'description': 'Configuration register', 'fields': [{'name': 'ChainXfr', 'bits': [31, 31], 'access': 'RO', 'reset': 'CHAIN_TRANSFER_SUPPORT', 'description': 'Chain transfer configured', 'write_effect': 'none'}, {'name': 'ReqSync', 'bits': [30, 30], 'access': 'RO', 'reset': '0x0', 'description': 'DMA request synchronization configured', 'write_effect': 'none'}, {'name': 'ReqNum', 'bits': [14, 10], 'access': 'RO', 'reset': 'REQ_ACK_NUM', 'description': 'Request/acknowledge number', 'write_effect': 'none'}, {'name': 'FIFODepth', 'bits': [9, 4], 'access': 'RO', 'reset': 'FIFO_DEPTH', 'description': 'FIFO depth', 'write_effect': 'none'}, {'name': 'ChannelNum', 'bits': [3, 0], 'access': 'RO', 'reset': 'DMA_CH_NUM', 'description': 'Channel number', 'write_effect': 'none'}]}, {'name': 'DMACtrl', 'offset': '0x20', 'width': 32, 'access': 'WO', 'reset': '0x0', 'description': 'Software reset control', 'fields': [{'name': 'Reset', 'bits': [0, 0], 'access': 'WO', 'reset': '0x0', 'description': 'Set to 1 to reset DMA core and disable all channels', 'write_effect': 'software reset pulse'}]}, {'name': 'IntStatus', 'offset': '0x30', 'width': 32, 'access': 'R/W1C', 'reset': '0x0', 'description': 'Terminal count, abort, and error status', 'fields': [{'name': 'TC', 'bits': [23, 16], 'access': 'R/W1C', 'reset': '0x0', 'description': 'Terminal count status per channel', 'write_effect': 'write one clear'}, {'name': 'Abort', 'bits': [15, 8], 'access': 'R/W1C', 'reset': '0x0', 'description': 'Abort status per channel', 'write_effect': 'write one clear'}, {'name': 'Error', 'bits': [7, 0], 'access': 'R/W1C', 'reset': '0x0', 'description': 'Error status per channel', 'write_effect': 'write one clear'}]}, {'name': 'ChEN', 'offset': '0x34', 'width': 32, 'access': 'RO', 'reset': '0x0', 'description': 'Alias of channel enable fields', 'fields': [{'name': 'ChEN', 'bits': [7, 0], 'access': 'RO', 'reset': '0x0', 'description': 'Channel enable status', 'write_effect': 'none'}]}, {'name': 'ChAbort', 'offset': '0x40', 'width': 32, 'access': 'WO', 'reset': '0x0', 'description': 'Write-one channel abort control', 'fields': [{'name': 'ChAbort', 'bits': [7, 0], 'access': 'WO', 'reset': '0x0', 'description': 'Write 1 to stop current channel transfer; hardware clears when interrupt status cleared', 'write_effect': 'set abort request for enabled channel'}]}, {'name': 'ChnCtrl', 'offset': '0x44+n*0x14', 'width': 32, 'access': 'R/W', 'reset': '0x000A0000', 'description': 'Per-channel control register', 'fields': [{'name': 'Priority', 'bits': [29, 29], 'access': 'R/W', 'reset': '0x0', 'description': 'Priority level', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'SrcBurstSize', 'bits': [24, 22], 'access': 'R/W', 'reset': '0x0', 'description': 'Transfers before re-arbitration', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'SrcWidth', 'bits': [21, 20], 'access': 'R/W', 'reset': '0x2', 'description': 'Source transfer width', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'DstWidth', 'bits': [19, 18], 'access': 'R/W', 'reset': '0x2', 'description': 'Destination transfer width', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'SrcMode', 'bits': [17, 17], 'access': 'R/W', 'reset': '0x0', 'description': 'Source handshake mode', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'DstMode', 'bits': [16, 16], 'access': 'R/W', 'reset': '0x0', 'description': 'Destination handshake mode', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'SrcAddrCtrl', 'bits': [15, 14], 'access': 'R/W', 'reset': '0x0', 'description': 'Source address control', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'DstAddrCtrl', 'bits': [13, 12], 'access': 'R/W', 'reset': '0x0', 'description': 'Destination address control', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'SrcReqSel', 'bits': [11, 8], 'access': 'R/W', 'reset': '0x0', 'description': 'Source request select', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'DstReqSel', 'bits': [7, 4], 'access': 'R/W', 'reset': '0x0', 'description': 'Destination request select', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'IntAbtMask', 'bits': [3, 3], 'access': 'R/W', 'reset': '0x0', 'description': 'Abort interrupt mask', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'IntErrMask', 'bits': [2, 2], 'access': 'R/W', 'reset': '0x0', 'description': 'Error interrupt mask', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'IntTCMask', 'bits': [1, 1], 'access': 'R/W', 'reset': '0x0', 'description': 'Terminal count interrupt mask', 'write_effect': 'stores written field value when the register write is accepted'}, {'name': 'Enable', 'bits': [0, 0], 'access': 'R/W', 'reset': '0x0', 'description': 'Channel enable bit', 'write_effect': 'stores written field value when the register write is accepted'}]}, {'name': 'ChnSrcAddr', 'offset': '0x48+n*0x14', 'width': 32, 'access': 'R/W', 'reset': '0x0', 'description': 'Per-channel source address', 'fields': [{'name': 'SrcAddr', 'bits': [31, 0], 'access': 'R/W', 'reset': '0x0', 'description': 'Source starting address; updated as transfer progresses', 'write_effect': 'write source address'}]}, {'name': 'ChnDstAddr', 'offset': '0x4C+n*0x14', 'width': 32, 'access': 'R/W', 'reset': '0x0', 'description': 'Per-channel destination address', 'fields': [{'name': 'DstAddr', 'bits': [31, 0], 'access': 'R/W', 'reset': '0x0', 'description': 'Destination starting address; updated as transfer progresses', 'write_effect': 'write destination address'}]}, {'name': 'ChnTranSize', 'offset': '0x50+n*0x14', 'width': 32, 'access': 'R/W', 'reset': '0x0', 'description': 'Per-channel transfer size in source-width units', 'fields': [{'name': 'TranSize', 'bits': [21, 0], 'access': 'R/W', 'reset': '0x0', 'description': 'Total transfer size; zero at enable triggers error', 'write_effect': 'write transfer size'}]}, {'name': 'ChnLLPointer', 'offset': '0x54+n*0x14', 'width': 32, 'access': 'R/W', 'reset': '0x0', 'description': 'Per-channel linked list pointer', 'fields': [{'name': 'LLPointer', 'bits': [31, 2], 'access': 'R/W', 'reset': '0x0', 'description': 'Word-aligned pointer to next descriptor', 'write_effect': 'write linked list pointer'}, {'name': 'Reserved', 'bits': [1, 0], 'access': 'reserved', 'reset': '0x0', 'description': 'Reserved low alignment bits', 'write_effect': 'ignore writes', 'read_value': '0'}]}], 'decode_policy': 'AHB slave word-aligned register decode; unimplemented offsets read zero and return OKAY unless size/alignment is illegal.'}, 'function_model': {'state_variables': [{'name': 'dmac_reset_pulse', 'width': 1, 'reset': 0}, {'name': 'active_ch', 'width': 3, 'reset': 0}, {'name': 'busy', 'width': 1, 'reset': 0}, {'name': 'ch_enable', 'width': 8, 'reset': 0}, {'name': 'int_tc', 'width': 8, 'reset': 0}, {'name': 'int_abort', 'width': 8, 'reset': 0}, {'name': 'int_error', 'width': 8, 'reset': 0}, {'name': 'bytes_done', 'width': 22, 'reset': 0}, {'name': 'src_addr_cur', 'width': 'ADDR_WIDTH', 'reset': 0}, {'name': 'dst_addr_cur', 'width': 'ADDR_WIDTH', 'reset': 0}, {'name': 'read_data_hold', 'width': 32, 'reset': 0}, {'name': 'chain_pending', 'width': 1, 'reset': 0}], 'state': {'dmac_reset_pulse': {'width': 1, 'reset': 0}, 'active_ch': {'width': 3, 'reset': 0}, 'busy': {'width': 1, 'reset': 0}, 'ch_enable': {'width': 8, 'reset': 0}, 'int_tc': {'width': 8, 'reset': 0}, 'int_abort': {'width': 8, 'reset': 0}, 'int_error': {'width': 8, 'reset': 0}, 'bytes_done': {'width': 22, 'reset': 0}, 'src_addr_cur': {'width': 'ADDR_WIDTH', 'reset': 0}, 'dst_addr_cur': {'width': 'ADDR_WIDTH', 'reset': 0}, 'read_data_hold': {'width': 32, 'reset': 0}, 'chain_pending': {'width': 1, 'reset': 0}}, 'transactions': [{'id': 'FM_RESET', 'name': 'hardware or software reset', 'preconditions': ['hresetn == 0 or DMACtrl.Reset write is observed'], 'outputs': ['hready', 'hresp', 'hrdata', 'dma_int', 'dma_ack', 'hbusreq_mst', 'htrans_mst', 'haddr_mst', 'hwrite_mst', 'hsize_mst', 'hburst_mst', 'hwdata_mst'], 'side_effects': ['disable all channels, clear active state, clear interrupt status'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'hready_reset', 'port': 'hready', 'expr': '0', 'width': 1}, {'name': 'hresp_reset', 'port': 'hresp', 'expr': '0', 'width': 2}, {'name': 'dma_int_reset', 'port': 'dma_int', 'expr': '0', 'width': 1}, {'name': 'htrans_mst_reset', 'port': 'htrans_mst', 'expr': '0', 'width': 2}], 'state_updates': [{'state': 'dmac_reset_pulse', 'expr': '0', 'width': 1}, {'state': 'active_ch', 'expr': '0', 'width': 3}, {'state': 'busy', 'expr': '0', 'width': 1}, {'state': 'ch_enable', 'expr': '0', 'width': 8}, {'state': 'int_tc', 'expr': '0', 'width': 8}, {'state': 'int_abort', 'expr': '0', 'width': 8}, {'state': 'int_error', 'expr': '0', 'width': 8}, {'state': 'bytes_done', 'expr': '0', 'width': 22}, {'state': 'src_addr_cur', 'expr': '0', 'width': 'ADDR_WIDTH'}, {'state': 'dst_addr_cur', 'expr': '0', 'width': 'ADDR_WIDTH'}, {'state': 'read_data_hold', 'expr': '0', 'width': 32}, {'state': 'chain_pending', 'expr': '0', 'width': 1}]}, {'id': 'FM_AHB_WRITE', 'name': 'AHB slave register write', 'preconditions': ['hsel and hreadyin and htrans[1] and hwrite'], 'outputs': ['hready=1', 'hresp=OKAY for valid register writes'], 'side_effects': ['updates writable DMAC/channel registers; W1C clears IntStatus bits; ChAbort write-one aborts enabled channels'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'hready_write', 'port': 'hready', 'expr': '1', 'width': 1}, {'name': 'hresp_write', 'port': 'hresp', 'expr': '0', 'width': 2}, {'name': 'dma_int_after_write', 'port': 'dma_int', 'expr': 'reduction_or((int_tc | int_abort | int_error) & ch_enable)', 'width': 1}], 'state_updates': [{'state': 'dmac_reset_pulse', 'expr': '1 if haddr == 32 and (hwdata & 1) else 0', 'width': 1}, {'state': 'int_tc', 'expr': 'int_tc & ~((hwdata >> 16) & 255) if haddr == 48 else int_tc', 'width': 8}, {'state': 'int_abort', 'expr': 'int_abort & ~((hwdata >> 8) & 255) if haddr == 48 else int_abort', 'width': 8}, {'state': 'int_error', 'expr': 'int_error & ~(hwdata & 255) if haddr == 48 else int_error', 'width': 8}, {'state': 'ch_enable', 'expr': 'ch_enable & ~(hwdata & ch_enable) if haddr == 64 else ch_enable', 'width': 8}]}, {'id': 'FM_AHB_READ', 'name': 'AHB slave register read', 'preconditions': ['hsel and hreadyin and htrans[1] and not hwrite'], 'outputs': ['hrdata returns IdRev, DMACfg, IntStatus, ChEN, and channel windows'], 'side_effects': ['no architectural state changes'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'hready_read', 'port': 'hready', 'expr': '1', 'width': 1}, {'name': 'hresp_read', 'port': 'hresp', 'expr': '0', 'width': 2}, {'name': 'hrdata_id_cfg_status', 'port': 'hrdata', 'expr': '0x01021012 if haddr == 0 else ((CHAIN_TRANSFER_SUPPORT << 31) | (REQ_ACK_NUM << 10) | (FIFO_DEPTH << 4) | DMA_CH_NUM) if haddr == 16 else ((int_tc << 16) | (int_abort << 8) | int_error) if haddr == 48 else ch_enable if haddr == 52 else 0', 'width': 32}], 'state_updates': []}, {'id': 'FM_ARBITRATE', 'name': 'channel arbitration', 'preconditions': ['one or more ChnCtrl.Enable bits are set and DMA is not busy'], 'outputs': ['select high priority channel first; round-robin among same priority channels'], 'side_effects': ['sets busy and active_ch'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'hbusreq_on_start', 'port': 'hbusreq_mst', 'expr': '1', 'width': 1}, {'name': 'htrans_idle_on_start', 'port': 'htrans_mst', 'expr': '0', 'width': 2}], 'state_updates': [{'state': 'busy', 'expr': '1', 'width': 1}, {'state': 'active_ch', 'expr': 'active_ch', 'width': 3}, {'state': 'bytes_done', 'expr': '0', 'width': 22}]}, {'id': 'FM_MASTER_READ', 'name': 'AHB master read beat', 'preconditions': ['busy and hgrant_mst and hready_mst and not fifo full'], 'outputs': ['issues AHB master read from current source address'], 'side_effects': ['captures hrdata_mst for corresponding write beat'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'hbusreq_read', 'port': 'hbusreq_mst', 'expr': '1', 'width': 1}, {'name': 'htrans_read', 'port': 'htrans_mst', 'expr': '2', 'width': 2}, {'name': 'hwrite_read', 'port': 'hwrite_mst', 'expr': '0', 'width': 1}, {'name': 'haddr_read', 'port': 'haddr_mst', 'expr': 'src_addr_cur', 'width': 'ADDR_WIDTH'}, {'name': 'hsize_word', 'port': 'hsize_mst', 'expr': '2', 'width': 3}, {'name': 'hburst_incr', 'port': 'hburst_mst', 'expr': '1', 'width': 3}], 'state_updates': [{'state': 'read_data_hold', 'expr': 'hrdata_mst', 'width': 32}]}, {'id': 'FM_MASTER_WRITE', 'name': 'AHB master write beat', 'preconditions': ['busy and hgrant_mst and hready_mst and read data available'], 'outputs': ['issues AHB master write to current destination address'], 'side_effects': ['increments/decrements/fixes addresses according to control fields and updates bytes_done'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'hbusreq_write', 'port': 'hbusreq_mst', 'expr': '1', 'width': 1}, {'name': 'htrans_write', 'port': 'htrans_mst', 'expr': '3', 'width': 2}, {'name': 'hwrite_write', 'port': 'hwrite_mst', 'expr': '1', 'width': 1}, {'name': 'haddr_write', 'port': 'haddr_mst', 'expr': 'dst_addr_cur', 'width': 'ADDR_WIDTH'}, {'name': 'hwdata_write', 'port': 'hwdata_mst', 'expr': 'read_data_hold', 'width': 32}], 'state_updates': [{'state': 'bytes_done', 'expr': 'bytes_done + 4', 'width': 22}, {'state': 'src_addr_cur', 'expr': 'src_addr_cur + 4', 'width': 'ADDR_WIDTH'}, {'state': 'dst_addr_cur', 'expr': 'dst_addr_cur + 4', 'width': 'ADDR_WIDTH'}]}, {'id': 'FM_COMPLETE', 'name': 'terminal count completion', 'preconditions': ['bytes_done reaches ChnTranSize without error or abort'], 'outputs': ['updates IntStatus.TC and asserts dma_int if interrupt is unmasked'], 'side_effects': ['disables completed channel; chain pointer may preload next descriptor when enabled'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'hbusreq_complete', 'port': 'hbusreq_mst', 'expr': '0', 'width': 1}, {'name': 'htrans_complete', 'port': 'htrans_mst', 'expr': '0', 'width': 2}, {'name': 'dma_int_tc', 'port': 'dma_int', 'expr': 'reduction_or((int_tc | (1 << active_ch)) | int_abort | int_error)', 'width': 1}], 'state_updates': [{'state': 'busy', 'expr': '0', 'width': 1}, {'state': 'ch_enable', 'expr': 'ch_enable & ~(1 << active_ch)', 'width': 8}, {'state': 'int_tc', 'expr': 'int_tc | (1 << active_ch)', 'width': 8}, {'state': 'chain_pending', 'expr': '1 if CHAIN_TRANSFER_SUPPORT else 0', 'width': 1}]}, {'id': 'FM_ERROR_ABORT', 'name': 'error or software abort', 'preconditions': ['hresp_mst indicates error, unaligned address, reserved mode, zero transfer size, or ChAbort bit is written'], 'outputs': ['updates IntStatus.Error or Abort and asserts dma_int if unmasked'], 'side_effects': ['disables affected channel; no dma_ack on error'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'hbusreq_error', 'port': 'hbusreq_mst', 'expr': '0', 'width': 1}, {'name': 'htrans_error', 'port': 'htrans_mst', 'expr': '0', 'width': 2}, {'name': 'dma_int_error', 'port': 'dma_int', 'expr': '1', 'width': 1}, {'name': 'dma_ack_error', 'port': 'dma_ack', 'expr': '0', 'width': 'REQ_ACK_NUM'}], 'state_updates': [{'state': 'busy', 'expr': '0', 'width': 1}, {'state': 'ch_enable', 'expr': 'ch_enable & ~(1 << active_ch)', 'width': 8}, {'state': 'int_error', 'expr': 'int_error | (1 << active_ch)', 'width': 8}]}, {'id': 'FM_HANDSHAKE_ACK', 'name': 'hardware handshake acknowledge', 'preconditions': ['selected source or destination handshake mode is enabled and SrcBurstSize transfers complete'], 'outputs': ['asserts dma_ack for selected request pair until dma_req deasserts'], 'side_effects': ['does not assert ack when an error terminates the channel'], 'error_cases': ['illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel'], 'output_rules': [{'name': 'dma_ack_selected', 'port': 'dma_ack', 'expr': '1 << active_ch', 'width': 'REQ_ACK_NUM'}, {'name': 'dma_int_handshake', 'port': 'dma_int', 'expr': 'reduction_or(int_tc | int_abort | int_error)', 'width': 1}], 'state_updates': [{'state': 'active_ch', 'expr': 'active_ch', 'width': 3}]}], 'invariants': [{'name': 'one_channel_serviced', 'expr': 'busy == 0 or active_ch < DMA_CH_NUM', 'description': 'Controller services one channel at a time.'}, {'name': 'status_width', 'expr': '(int_tc | int_abort | int_error) < 256', 'description': 'Only configured channel status bits are used.'}]}, 'cycle_model': {'clock': 'hclk', 'reset': 'hresetn', 'latency': 'AHB slave register access is zero-wait; DMA data movement issues read/write beats while hgrant_mst and hready_mst are asserted.', 'handshake_rules': ['AHB slave access samples when hsel && hreadyin && htrans[1].', 'AHB master transfer completes when hgrant_mst && hready_mst && htrans_mst[1].', 'dma_ack is asserted after SrcBurstSize transfers for an enabled hardware request pair and is deasserted after dma_req deasserts.'], 'pipeline': ['IDLE selects a ready channel by priority/round-robin.', 'READ issues AHB read and captures hrdata_mst.', 'WRITE issues AHB write and advances counters.', 'DONE/ERROR updates status and interrupt.'], 'ordering': ['Only one channel is actively serviced at a time.', 'Same-priority channels are visited in round-robin order.', 'A write beat uses data captured from the preceding read beat.', 'Chain descriptor preload happens after head transfer completion when ChnLLPointer is nonzero.'], 'observability': ['active_ch', 'busy', 'htrans_mst', 'hbusreq_mst', 'dma_ack', 'dma_int'], 'performance': {'max_slave_wait_states': 0, 'bytes_per_master_read_write_pair': 4, 'arbitration_policy': 'two priority levels with round-robin within same priority'}}, 'fcov_bins': [{'id': 'SC_AHB_REG_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_AHB_REG', 'description': 'AHB register programming'}, {'id': 'SC_MEM_COPY_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_MEM_COPY', 'description': 'single-channel memory copy'}, {'id': 'SC_ARB_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_ARB', 'description': 'priority round-robin arbitration'}, {'id': 'SC_HANDSHAKE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_HANDSHAKE', 'description': 'hardware request acknowledge'}, {'id': 'SC_ERROR_ABORT_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_ERROR_ABORT', 'description': 'error and abort handling'}, {'id': 'SC_CHAIN_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_CHAIN', 'description': 'chain transfer continuation'}, {'id': 'fcov_reg_idcfg', 'class': 'register_access', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[0]', 'source_ref': 'function_model.transactions.FM_AHB_READ', 'description': 'IdRev/DMACfg/ChEN/IntStatus read paths are observed'}, {'id': 'fcov_int_w1c', 'class': 'register_access', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[1]', 'source_ref': 'function_model.transactions.FM_AHB_WRITE', 'description': 'IntStatus write-one-clear behavior is observed'}, {'id': 'fcov_dma_read_write', 'class': 'dma_datapath', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[2]', 'source_ref': 'function_model.transactions.FM_MASTER_READ', 'description': 'DMA master read beat is observed'}, {'id': 'fcov_dma_write', 'class': 'dma_datapath', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[3]', 'source_ref': 'function_model.transactions.FM_MASTER_WRITE', 'description': 'DMA master write beat is observed'}, {'id': 'fcov_tc_int', 'class': 'interrupt', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[4]', 'source_ref': 'function_model.transactions.FM_COMPLETE', 'description': 'Terminal count status and interrupt are observed'}, {'id': 'fcov_error_abort', 'class': 'error', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[5]', 'source_ref': 'function_model.transactions.FM_ERROR_ABORT', 'description': 'Error or abort handling is observed'}, {'id': 'fcov_req_ack', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'test_requirements.coverage_goals.planned_bins[6]', 'source_ref': 'function_model.transactions.FM_HANDSHAKE_ACK', 'description': 'dma_req/dma_ack service is observed'}, {'id': 'fcov_priority', 'class': 'arbitration', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[7]', 'source_ref': 'function_model.transactions.FM_ARBITRATE', 'description': 'priority round-robin arbitration is observed'}, {'id': 'ccov_ahb_slave_access', 'class': 'bus_handshake', 'coverage_domain': 'cycle', 'source': 'test_requirements.coverage_goals.planned_bins[8]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': 'AHB slave access handshake observed'}, {'id': 'ccov_master_read_write', 'class': 'pipeline', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[9]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'read/write pipeline states observed'}, {'id': 'ccov_wait_state', 'class': 'backpressure', 'coverage_domain': 'function', 'source': 'test_requirements.coverage_goals.planned_bins[10]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': 'AHB master ready/grant backpressure observed'}, {'id': 'ccov_handshake_wait', 'class': 'dma_handshake', 'coverage_domain': 'cycle', 'source': 'test_requirements.coverage_goals.planned_bins[11]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': 'dma_req wait and dma_ack sequence observed'}, {'id': 'ccov_error_response', 'class': 'fsm', 'coverage_domain': 'cycle', 'source': 'test_requirements.coverage_goals.planned_bins[12]', 'source_ref': 'fsm.transitions', 'description': 'error/abort FSM transition observed'}, {'id': 'function_hardware_or_software_reset', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_reset', 'description': 'hardware_or_software_reset'}, {'id': 'function_ahb_slave_register_write', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_ahb_write', 'description': 'ahb_slave_register_write'}, {'id': 'function_ahb_slave_register_read', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_ahb_read', 'description': 'ahb_slave_register_read'}, {'id': 'function_channel_arbitration', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_arbitrate', 'description': 'channel_arbitration'}, {'id': 'function_ahb_master_read_beat', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_master_read', 'description': 'ahb_master_read_beat'}, {'id': 'function_ahb_master_write_beat', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm_master_write', 'description': 'ahb_master_write_beat'}, {'id': 'function_terminal_count_completion', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[6]', 'source_ref': 'function_model.transactions.fm_complete', 'description': 'terminal_count_completion'}, {'id': 'function_error_or_software_abort', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[7]', 'source_ref': 'function_model.transactions.fm_error_abort', 'description': 'error_or_software_abort'}, {'id': 'function_hardware_handshake_acknowledge', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[8]', 'source_ref': 'function_model.transactions.fm_handshake_ack', 'description': 'hardware_handshake_acknowledge'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Only one channel is actively serviced at a time.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Same-priority channels are visited in round-robin order.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'A write beat uses data captured from the preceding read beat.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'Chain descriptor preload happens after head transfer completion when ChnLLPointer is nonzero.'}, {'id': 'fsm_name_idle_to_arbitrate_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[0]', 'source_ref': 'fsm.name.transitions[0]', 'description': 'ch_enable != 0'}, {'id': 'fsm_name_arbitrate_to_read_addr_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[1]', 'source_ref': 'fsm.name.transitions[1]', 'description': 'selected channel ready and handshake satisfied'}, {'id': 'fsm_name_read_addr_to_read_data_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[2]', 'source_ref': 'fsm.name.transitions[2]', 'description': 'hgrant_mst && hready_mst'}, {'id': 'fsm_name_read_data_to_write_addr_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[3]', 'source_ref': 'fsm.name.transitions[3]', 'description': 'read_data captured'}, {'id': 'fsm_name_write_addr_to_write_data_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[4]', 'source_ref': 'fsm.name.transitions[4]', 'description': 'hgrant_mst && hready_mst'}, {'id': 'fsm_name_write_data_to_complete_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[5]', 'source_ref': 'fsm.name.transitions[5]', 'description': 'last beat done'}, {'id': 'fsm_name_write_data_to_read_addr_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[6]', 'source_ref': 'fsm.name.transitions[6]', 'description': 'more beats remain'}, {'id': 'fsm_name_read_addr_to_error_abort_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[7]', 'source_ref': 'fsm.name.transitions[7]', 'description': 'hresp_mst error or alignment error'}, {'id': 'fsm_name_complete_to_chain_load_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[8]', 'source_ref': 'fsm.name.transitions[8]', 'description': 'CHAIN_TRANSFER_SUPPORT && ChnLLPointer != 0'}, {'id': 'fsm_name_complete_to_idle_9', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.name.transitions[9]', 'source_ref': 'fsm.name.transitions[9]', 'description': 'no chain continuation'}, {'id': 'error_ahb_hresp_mst_error', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': 'AHB hresp_mst error'}, {'id': 'error_unaligned_source_or_destination_address', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': 'unaligned source or destination address'}, {'id': 'error_reserved_width_or_address_control_mode', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': 'reserved width or address-control mode'}, {'id': 'error_zero_transfer_size_when_enabling_a_channel', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': 'zero transfer size when enabling a channel'}, {'id': 'error_software_chabort_for_enabled_channel', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[4]', 'source_ref': 'error_handling.error_sources[4]', 'description': 'software ChAbort for enabled channel'}]}
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
            "ssot_question": (
                "[SSOT QUESTION] structured output_rules/state_updates undefined "
                "for transaction " + str(tx.get("id") or tx.get("name") or "<unknown>")
            ),
            "fabricated_state": False,
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

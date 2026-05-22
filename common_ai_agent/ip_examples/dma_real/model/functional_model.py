#!/usr/bin/env python3
"""Executable SSOT functional model for dma_real.

Generated from yaml/dma_real.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'dma_real', 'parameters': {'ADDR_WIDTH': 32, 'DATA_WIDTH': 32, 'N_CHANNELS': 4, 'BURST_MAX': 16, 'FIFO_DEPTH': 16, 'TIMEOUT_DEFAULT': 1024}, 'top_module': {'name': 'dma_real_top', 'description': 'Production-grade multi-channel DMA controller with dual-clock architecture (pclk for APB configuration, hclk for AHB-Lite data transfer), CDC async FIFO bridge, full AHB-Lite master protocol with RETRY/SPLIT support, per-channel programmable stride, bus timeout detection, performance counters, and clock gating. N_CHANNELS parameterized via generate blocks.', 'file': 'rtl/dma_real_top.sv', 'owner': 'ssot-manual', 'quality_profile': 'standard'}, 'memory': {'internal': [{'name': 'ch_async_fifo', 'kind': 'async_fifo', 'width': 'DATA_WIDTH', 'depth': 'FIFO_DEPTH', 'per_instance': True, 'instances': ['ch0_fifo', 'ch1_fifo', 'ch2_fifo', 'ch3_fifo'], 'description': 'Per-channel dual-clock async FIFO with gray-code pointer sync. Read port in hclk domain, write port in pclk domain (via CDC config bridge). Pointer-based circular buffer with almost_full and almost_empty thresholds.', 'implementation': {'ptr_type': 'gray_code_binary', 'almost_full_threshold': 'FIFO_DEPTH - 2', 'almost_empty_threshold': 2, 'sync_stages': 2}}]}, 'registers': {'register_list': [{'name': 'GLOBAL_CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Global DMA control register', 'fields': [{'name': 'dma_en', 'lsb': 0, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Global DMA enable', 'write_effect': 'enables or disables DMA globally'}, {'name': 'reserved_31_1', 'lsb': 1, 'width': 31, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'INT_STATUS', 'offset': 4, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Per-channel interrupt status (bit per channel)', 'fields': [{'name': 'ch_status', 'lsb': 0, 'width': 4, 'access': 'ro', 'reset': 0, 'description': 'Bit[ch] is 1 when channel ch has pending interrupt', 'write_effect': 'read-only'}]}, {'name': 'INT_ENABLE', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Per-channel interrupt enable mask', 'fields': [{'name': 'ch_enable', 'lsb': 0, 'width': 4, 'access': 'rw', 'reset': 0, 'description': 'Bit[ch] = 1 enables interrupt for channel ch', 'write_effect': 'updates interrupt mask'}]}, {'name': 'INT_CLEAR', 'offset': 12, 'width': 32, 'access': 'wo', 'reset': 0, 'description': 'Write-1-to-clear per-channel interrupt', 'fields': [{'name': 'ch_clear', 'lsb': 0, 'width': 4, 'access': 'wo', 'reset': 0, 'description': 'Writing 1 to bit[ch] clears done_q and error_q for channel ch', 'write_effect': 'clears latched done and error status'}]}, {'name': 'GLOBAL_TIMEOUT', 'offset': 16, 'width': 32, 'access': 'rw', 'reset': 1024, 'description': 'Bus timeout threshold in hclk cycles. 0 disables timeout.', 'fields': [{'name': 'timeout_val', 'lsb': 0, 'width': 16, 'access': 'rw', 'reset': 1024, 'description': 'Max hclk cycles to wait for hready. 0 = disabled.', 'write_effect': 'updates timeout threshold for all channels'}, {'name': 'reserved_31_16', 'lsb': 16, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH0_CTRL', 'offset': 256, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 0 control register', 'fields': [{'name': 'ch_en', 'lsb': 0, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Channel enable', 'write_effect': 'enables or disables the channel'}, {'name': 'ch_start', 'lsb': 1, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Write 1 to start transfer (self-clearing)', 'write_effect': 'initiates DMA transfer if ch_en and dma_en are set'}, {'name': 'hsize', 'lsb': 2, 'width': 2, 'access': 'rw', 'reset': 0, 'description': 'Transfer size (00=byte, 01=halfword, 10=word)', 'write_effect': 'sets hsize for AHB transfers'}, {'name': 'burst_mode', 'lsb': 4, 'width': 2, 'access': 'rw', 'reset': 0, 'description': 'Burst mode (00=INCR, 01=INCR4, 10=INCR8, 11=INCR16)', 'write_effect': 'selects burst type for AHB'}, {'name': 'reserved_31_6', 'lsb': 6, 'width': 26, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH0_SRC_ADDR', 'offset': 260, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 0 source start address (must be word-aligned for word transfers)', 'fields': [{'name': 'src_addr', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Source address', 'write_effect': 'latches source address for transfer'}]}, {'name': 'CH0_DST_ADDR', 'offset': 264, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 0 destination start address', 'fields': [{'name': 'dst_addr', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Destination address', 'write_effect': 'latches destination address for transfer'}]}, {'name': 'CH0_LEN', 'offset': 268, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 0 transfer length in words (1..65536). 0 is invalid.', 'fields': [{'name': 'length', 'lsb': 0, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Transfer length in words', 'write_effect': 'sets number of words to transfer'}, {'name': 'reserved_31_16', 'lsb': 16, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH0_STATUS', 'offset': 272, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 0 status register', 'fields': [{'name': 'busy', 'lsb': 0, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Channel is actively transferring', 'write_effect': 'read-only'}, {'name': 'done', 'lsb': 1, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Transfer completed (sticky, cleared by INT_CLEAR)', 'write_effect': 'read-only'}, {'name': 'error', 'lsb': 2, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Error occurred (sticky, cleared by INT_CLEAR)', 'write_effect': 'read-only'}, {'name': 'err_code', 'lsb': 3, 'width': 3, 'access': 'ro', 'reset': 0, 'description': 'Error code (0=none, 1=align, 2=zero_len, 3=bus_err, 4=timeout, 5=fifo_overflow)', 'write_effect': 'read-only'}, {'name': 'reserved_31_6', 'lsb': 6, 'width': 26, 'access': 'ro', 'reset': 0, 'description': 'Reserved', 'write_effect': 'read-only'}]}, {'name': 'CH0_STRIDE', 'offset': 276, 'width': 32, 'access': 'rw', 'reset': 4, 'description': 'Channel 0 address stride per beat. Default 4 (word). Set 0 for fixed-address peripheral.', 'fields': [{'name': 'stride', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 4, 'description': 'Address increment per beat', 'write_effect': 'sets address stride for transfer'}]}, {'name': 'CH0_PERF_WORDS', 'offset': 284, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 0 total words transferred (saturating counter)', 'fields': [{'name': 'word_count', 'lsb': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Cumulative words transferred', 'write_effect': 'read-only'}]}, {'name': 'CH0_PERF_CYCLES', 'offset': 288, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 0 total active cycles (saturating counter)', 'fields': [{'name': 'cycle_count', 'lsb': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Cumulative active hclk cycles', 'write_effect': 'read-only'}]}, {'name': 'CH1_CTRL', 'offset': 320, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 1 control register', 'fields': [{'name': 'ch_en', 'lsb': 0, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Channel enable', 'write_effect': 'enables or disables the channel'}, {'name': 'ch_start', 'lsb': 1, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Write 1 to start transfer', 'write_effect': 'initiates DMA transfer'}, {'name': 'hsize', 'lsb': 2, 'width': 2, 'access': 'rw', 'reset': 0, 'description': 'Transfer size', 'write_effect': 'sets hsize for AHB transfers'}, {'name': 'burst_mode', 'lsb': 4, 'width': 2, 'access': 'rw', 'reset': 0, 'description': 'Burst mode', 'write_effect': 'selects burst type'}, {'name': 'reserved_31_6', 'lsb': 6, 'width': 26, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH1_SRC_ADDR', 'offset': 324, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 1 source start address', 'fields': [{'name': 'src_addr', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Source address', 'write_effect': 'latches source address'}]}, {'name': 'CH1_DST_ADDR', 'offset': 328, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 1 destination start address', 'fields': [{'name': 'dst_addr', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Destination address', 'write_effect': 'latches destination address'}]}, {'name': 'CH1_LEN', 'offset': 332, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 1 transfer length in words', 'fields': [{'name': 'length', 'lsb': 0, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Transfer length', 'write_effect': 'sets transfer length'}, {'name': 'reserved_31_16', 'lsb': 16, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH1_STATUS', 'offset': 336, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 1 status register', 'fields': [{'name': 'busy', 'lsb': 0, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Channel busy', 'write_effect': 'read-only'}, {'name': 'done', 'lsb': 1, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Transfer done', 'write_effect': 'read-only'}, {'name': 'error', 'lsb': 2, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Error flag', 'write_effect': 'read-only'}, {'name': 'err_code', 'lsb': 3, 'width': 3, 'access': 'ro', 'reset': 0, 'description': 'Error code', 'write_effect': 'read-only'}, {'name': 'reserved_31_6', 'lsb': 6, 'width': 26, 'access': 'ro', 'reset': 0, 'description': 'Reserved', 'write_effect': 'read-only'}]}, {'name': 'CH1_STRIDE', 'offset': 340, 'width': 32, 'access': 'rw', 'reset': 4, 'description': 'Channel 1 address stride per beat', 'fields': [{'name': 'stride', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 4, 'description': 'Address increment per beat', 'write_effect': 'sets address stride'}]}, {'name': 'CH1_PERF_WORDS', 'offset': 348, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 1 total words transferred', 'fields': [{'name': 'word_count', 'lsb': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Cumulative words transferred', 'write_effect': 'read-only'}]}, {'name': 'CH1_PERF_CYCLES', 'offset': 352, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 1 total active cycles', 'fields': [{'name': 'cycle_count', 'lsb': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Cumulative active hclk cycles', 'write_effect': 'read-only'}]}, {'name': 'CH2_CTRL', 'offset': 384, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 2 control register', 'fields': [{'name': 'ch_en', 'lsb': 0, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Channel enable', 'write_effect': 'enables or disables the channel'}, {'name': 'ch_start', 'lsb': 1, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Write 1 to start transfer', 'write_effect': 'initiates DMA transfer'}, {'name': 'hsize', 'lsb': 2, 'width': 2, 'access': 'rw', 'reset': 0, 'description': 'Transfer size', 'write_effect': 'sets hsize for AHB transfers'}, {'name': 'burst_mode', 'lsb': 4, 'width': 2, 'access': 'rw', 'reset': 0, 'description': 'Burst mode', 'write_effect': 'selects burst type'}, {'name': 'reserved_31_6', 'lsb': 6, 'width': 26, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH2_SRC_ADDR', 'offset': 388, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 2 source start address', 'fields': [{'name': 'src_addr', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Source address', 'write_effect': 'latches source address'}]}, {'name': 'CH2_DST_ADDR', 'offset': 392, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 2 destination start address', 'fields': [{'name': 'dst_addr', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Destination address', 'write_effect': 'latches destination address'}]}, {'name': 'CH2_LEN', 'offset': 396, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 2 transfer length', 'fields': [{'name': 'length', 'lsb': 0, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Transfer length', 'write_effect': 'sets transfer length'}, {'name': 'reserved_31_16', 'lsb': 16, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH2_STATUS', 'offset': 400, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 2 status register', 'fields': [{'name': 'busy', 'lsb': 0, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Channel busy', 'write_effect': 'read-only'}, {'name': 'done', 'lsb': 1, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Transfer done', 'write_effect': 'read-only'}, {'name': 'error', 'lsb': 2, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Error flag', 'write_effect': 'read-only'}, {'name': 'err_code', 'lsb': 3, 'width': 3, 'access': 'ro', 'reset': 0, 'description': 'Error code', 'write_effect': 'read-only'}, {'name': 'reserved_31_6', 'lsb': 6, 'width': 26, 'access': 'ro', 'reset': 0, 'description': 'Reserved', 'write_effect': 'read-only'}]}, {'name': 'CH2_STRIDE', 'offset': 404, 'width': 32, 'access': 'rw', 'reset': 4, 'description': 'Channel 2 address stride', 'fields': [{'name': 'stride', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 4, 'description': 'Address increment per beat', 'write_effect': 'sets address stride'}]}, {'name': 'CH2_PERF_WORDS', 'offset': 412, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 2 words transferred', 'fields': [{'name': 'word_count', 'lsb': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Cumulative words transferred', 'write_effect': 'read-only'}]}, {'name': 'CH2_PERF_CYCLES', 'offset': 416, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 2 active cycles', 'fields': [{'name': 'cycle_count', 'lsb': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Cumulative active hclk cycles', 'write_effect': 'read-only'}]}, {'name': 'CH3_CTRL', 'offset': 448, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 3 control register', 'fields': [{'name': 'ch_en', 'lsb': 0, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Channel enable', 'write_effect': 'enables or disables the channel'}, {'name': 'ch_start', 'lsb': 1, 'width': 1, 'access': 'rw', 'reset': 0, 'description': 'Write 1 to start transfer', 'write_effect': 'initiates DMA transfer'}, {'name': 'hsize', 'lsb': 2, 'width': 2, 'access': 'rw', 'reset': 0, 'description': 'Transfer size', 'write_effect': 'sets hsize for AHB transfers'}, {'name': 'burst_mode', 'lsb': 4, 'width': 2, 'access': 'rw', 'reset': 0, 'description': 'Burst mode', 'write_effect': 'selects burst type'}, {'name': 'reserved_31_6', 'lsb': 6, 'width': 26, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH3_SRC_ADDR', 'offset': 452, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 3 source start address', 'fields': [{'name': 'src_addr', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Source address', 'write_effect': 'latches source address'}]}, {'name': 'CH3_DST_ADDR', 'offset': 456, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 3 destination start address', 'fields': [{'name': 'dst_addr', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Destination address', 'write_effect': 'latches destination address'}]}, {'name': 'CH3_LEN', 'offset': 460, 'width': 32, 'access': 'rw', 'reset': 0, 'description': 'Channel 3 transfer length', 'fields': [{'name': 'length', 'lsb': 0, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Transfer length', 'write_effect': 'sets transfer length'}, {'name': 'reserved_31_16', 'lsb': 16, 'width': 16, 'access': 'rw', 'reset': 0, 'description': 'Reserved', 'write_effect': 'no side effect'}]}, {'name': 'CH3_STATUS', 'offset': 464, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 3 status register', 'fields': [{'name': 'busy', 'lsb': 0, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Channel busy', 'write_effect': 'read-only'}, {'name': 'done', 'lsb': 1, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Transfer done', 'write_effect': 'read-only'}, {'name': 'error', 'lsb': 2, 'width': 1, 'access': 'ro', 'reset': 0, 'description': 'Error flag', 'write_effect': 'read-only'}, {'name': 'err_code', 'lsb': 3, 'width': 3, 'access': 'ro', 'reset': 0, 'description': 'Error code', 'write_effect': 'read-only'}, {'name': 'reserved_31_6', 'lsb': 6, 'width': 26, 'access': 'ro', 'reset': 0, 'description': 'Reserved', 'write_effect': 'read-only'}]}, {'name': 'CH3_STRIDE', 'offset': 468, 'width': 32, 'access': 'rw', 'reset': 4, 'description': 'Channel 3 address stride', 'fields': [{'name': 'stride', 'lsb': 0, 'width': 32, 'access': 'rw', 'reset': 4, 'description': 'Address increment per beat', 'write_effect': 'sets address stride'}]}, {'name': 'CH3_PERF_WORDS', 'offset': 476, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 3 words transferred', 'fields': [{'name': 'word_count', 'lsb': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Cumulative words transferred', 'write_effect': 'read-only'}]}, {'name': 'CH3_PERF_CYCLES', 'offset': 480, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Channel 3 active cycles', 'fields': [{'name': 'cycle_count', 'lsb': 0, 'width': 32, 'access': 'ro', 'reset': 0, 'description': 'Cumulative active hclk cycles', 'write_effect': 'read-only'}]}]}, 'function_model': {'purpose': 'Behavioral DMA reference model independent of dual-clock microarchitecture. Models single-logical-cycle semantics; CDC and clock domain details are implementation concerns.', 'state_variables': [{'name': 'ch_busy_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel busy flag'}, {'name': 'ch_done_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel done sticky latch'}, {'name': 'ch_error_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel error sticky latch'}, {'name': 'ch_remaining_q', 'width': 32, 'reset': 0, 'description': 'Per-channel remaining word count'}, {'name': 'ch_src_addr_q', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Per-channel current source address'}, {'name': 'ch_dst_addr_q', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Per-channel current destination address'}, {'name': 'ch_stride_q', 'width': 'ADDR_WIDTH', 'reset': 4, 'description': 'Per-channel address increment per beat (default 4 for word)'}, {'name': 'dma_en_q', 'width': 1, 'reset': 0, 'description': 'Global DMA enable'}, {'name': 'int_enable_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel interrupt enable mask'}, {'name': 'arb_ptr_q', 'width': 3, 'reset': 0, 'description': 'Round-robin arbiter pointer'}, {'name': 'timeout_q', 'width': 16, 'reset': 0, 'description': 'Bus timeout threshold in hclk cycles'}, {'name': 'perf_words_q', 'width': 32, 'reset': 0, 'description': 'Per-channel total words transferred'}, {'name': 'perf_cycles_q', 'width': 32, 'reset': 0, 'description': 'Per-channel total active cycles'}], 'transactions': [{'id': 'FM_DMA_START', 'name': 'dma_start', 'required_fields': ['ch_id', 'src_addr', 'dst_addr', 'length', 'stride'], 'preconditions': ['presetn and hresetn are deasserted', 'dma_en_q == 1', 'ch_busy_q[ch_id] == 0'], 'outputs': ['ch_busy', 'ch_error', 'ch_err_code'], 'output_rules': [{'name': 'ch_busy_next', 'port': 'ch_busy', 'width': 1, 'expr': '1 if (dma_en_q and not ch_busy_q[ch_id] and length > 0 and (src_addr % 4 == 0) and (dst_addr % 4 == 0)) else 0'}, {'name': 'ch_error_flag', 'port': 'ch_error', 'width': 1, 'expr': '1 if (length == 0 or src_addr % 4 != 0 or dst_addr % 4 != 0) else 0'}, {'name': 'ch_err_code_val', 'port': 'ch_err_code', 'width': 3, 'expr': '2 if (length == 0) else 1 if (src_addr % 4 != 0 or dst_addr % 4 != 0) else 0'}], 'side_effects': ['ch_remaining_q[ch_id] set to length on valid start', 'ch_src_addr_q[ch_id] set to src_addr on valid start', 'ch_dst_addr_q[ch_id] set to dst_addr on valid start', 'ch_stride_q[ch_id] set to stride on valid start', 'perf_cycles_q[ch_id] reset to 0 on valid start', 'perf_words_q[ch_id] reset to 0 on valid start'], 'error_cases': ['zero length (length == 0, error code 2)', 'misaligned source address (src_addr % 4 != 0, error code 1)', 'misaligned destination address (dst_addr % 4 != 0, error code 1)', 'start while busy (ignored, preserves state)']}, {'id': 'FM_DMA_STEP', 'name': 'dma_step', 'required_fields': ['ch_id', 'burst_len'], 'preconditions': ['ch_busy_q[ch_id] == 1', 'arbiter has granted bus to ch_id'], 'outputs': ['ch_busy', 'ch_done'], 'output_rules': [{'name': 'busy_next', 'port': 'ch_busy', 'width': 1, 'expr': '1 if (ch_remaining_q[ch_id] > burst_len) else 0'}, {'name': 'done_pulse', 'port': 'ch_done', 'width': 1, 'expr': '1 if (ch_remaining_q[ch_id] <= burst_len and ch_remaining_q[ch_id] > 0) else 0'}], 'state_updates': [{'name': 'remaining_next', 'expr': 'ch_remaining_q[ch_id] - burst_len if ch_remaining_q[ch_id] > burst_len else 0', 'width': 32}, {'name': 'src_addr_next', 'expr': 'ch_src_addr_q[ch_id] + burst_len * ch_stride_q[ch_id]', 'width': 'ADDR_WIDTH'}, {'name': 'dst_addr_next', 'expr': 'ch_dst_addr_q[ch_id] + burst_len * ch_stride_q[ch_id]', 'width': 'ADDR_WIDTH'}, {'name': 'perf_words_next', 'expr': 'perf_words_q[ch_id] + burst_len', 'width': 32}, {'name': 'perf_cycles_next', 'expr': 'perf_cycles_q[ch_id] + burst_len + 4', 'width': 32}], 'side_effects': ['ch_remaining_q decrements by burst_len', 'ch_src_addr_q increments by burst_len * ch_stride_q[ch_id]', 'ch_dst_addr_q increments by burst_len * ch_stride_q[ch_id]', 'perf_words_q increments by burst_len', 'perf_cycles_q increments by burst_len plus pipeline overhead', 'done pulses on terminal step'], 'error_cases': ['bus error during AHB transfer (hresp == ERROR, code 3)', 'timeout waiting for hready (code 4)']}, {'id': 'FM_DMA_COMPLETE', 'name': 'dma_complete', 'required_fields': ['ch_id'], 'preconditions': ['ch_remaining_q[ch_id] == 0', 'ch_busy_q[ch_id] == 1'], 'outputs': ['ch_busy', 'ch_done', 'irq'], 'output_rules': [{'name': 'busy_clear', 'port': 'ch_busy', 'width': 1, 'expr': 0}, {'name': 'done_assert', 'port': 'ch_done', 'width': 1, 'expr': 1}, {'name': 'irq_assert', 'port': 'irq', 'width': 1, 'expr': '1 if (int_enable_q[ch_id]) else 0'}], 'side_effects': ['ch_done_q[ch_id] set to 1', 'ch_busy_q[ch_id] cleared', 'IRQ asserted if enabled'], 'error_cases': []}, {'id': 'FM_DMA_ERROR', 'name': 'dma_error', 'required_fields': ['ch_id', 'error_code'], 'preconditions': ['error condition detected (alignment, zero-length, bus error, timeout, or FIFO overflow)'], 'outputs': ['ch_error', 'ch_err_code', 'irq'], 'output_rules': [{'name': 'error_assert', 'port': 'ch_error', 'width': 1, 'expr': 1}, {'name': 'error_code_out', 'port': 'ch_err_code', 'width': 3, 'expr': 'error_code'}, {'name': 'irq_error', 'port': 'irq', 'width': 1, 'expr': '1 if (int_enable_q[ch_id]) else 0'}], 'side_effects': ['ch_error_q[ch_id] set to 1', 'ch_busy_q[ch_id] cleared', 'Error code latched in status register'], 'error_cases': ['alignment error (code 1)', 'zero length (code 2)', 'bus error (code 3)', 'timeout (code 4)', 'FIFO overflow (code 5)']}, {'id': 'FM_ARB_GRANT', 'name': 'arb_grant', 'required_fields': ['requester_mask'], 'preconditions': ['at least one channel is requesting bus access'], 'outputs': ['arb_grant'], 'output_rules': [{'name': 'grant_next', 'port': 'arb_grant', 'width': 3, 'expr': '(arb_ptr_q + 1) % N_CHANNELS if requester_mask[arb_ptr_q] == 0 else arb_ptr_q'}], 'state_updates': [{'name': 'arb_ptr_update', 'expr': '(grant_ch + 1) % N_CHANNELS', 'width': 3}], 'side_effects': ['arb_ptr_q updated to next channel after grant', 'granted channel gains AHB bus access'], 'error_cases': []}], 'invariants': ['ch_busy and ch_done are not asserted together for the same channel.', 'ch_error is asserted only for invalid requests, bus errors, timeouts, or FIFO overflows.', 'ch_remaining_q never underflows below zero.', 'irq[ch] reflects (done_q[ch] OR error_q[ch]) AND int_enable_q[ch].', 'irq_combined reflects OR of all per-channel irq outputs.', 'Each FIFO operates as circular buffer with gray-code synchronized pointers across clock domains.', 'htrans transitions IDLE only when no channel has an active grant.', "Performance counters saturate at 32'hFFFFFFFF and do not wrap."]}, 'cycle_model': {'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 shell for cycle behavior. FunctionalModel remains oracle.', 'clock': 'hclk', 'reset': 'hresetn', 'latency': 5, 'handshake_rules': [{'name': 'apb_access', 'description': 'APB accesses sample on pclk with psel and penable. No wait states. Config data crosses CDC to hclk domain via async FIFO.'}, {'name': 'cdc_config', 'description': 'APB write data pushed into pclk-side FIFO write port. hclk-side read port pops config. Gray-code pointer synchronization prevents metastability.'}, {'name': 'ahb_address_phase', 'description': 'AHB address phase drives haddr, htrans, hsize, hburst, hprot, hmaster, hmastlock for one hclk cycle.'}, {'name': 'ahb_data_phase', 'description': 'AHB data phase follows address phase by one hclk cycle with hwdata or hrdata.'}, {'name': 'ahb_1kb_boundary', 'description': 'Burst crossing 1KB address boundary starts new NONSEQ beat. hburst recalculated for remaining beats.'}, {'name': 'ahb_error_response', 'description': 'hresp=ERROR (01) completes current beat and aborts burst. hresp=RETRY (10) releases bus and re-requests. hresp=SPLIT (11) releases bus and waits.'}, {'name': 'arb_grant_rule', 'description': 'Arbiter evaluates requests every hclk cycle and grants to next round-robin contender.'}, {'name': 'start_accept', 'description': 'ch_start accepted only when ch_busy is low and dma_en is high and CDC config has arrived.'}, {'name': 'timeout_rule', 'description': 'Timeout counter increments each hclk cycle while waiting for hready. Resets on hready assertion. Error code 4 when counter reaches GLOBAL_TIMEOUT.'}], 'pipeline': [{'stage': 'IDLE', 'cycle': 0, 'action': 'wait for valid start/config from CDC bridge'}, {'stage': 'CFG', 'cycle': 1, 'action': 'latch src_addr, dst_addr, remaining, stride from CDC config registers'}, {'stage': 'REQUEST', 'cycle': 2, 'action': 'request AHB bus via arbiter, clock gating cell enables hclk to channel'}, {'stage': 'READ', 'cycle': 3, 'action': 'AHB read burst from source address into pointer-based FIFO, timeout counter active'}, {'stage': 'WRITE', 'cycle': 4, 'action': 'AHB write burst from FIFO to destination address, FIFO read pointer advances'}, {'stage': 'UPDATE', 'cycle': 5, 'action': 'update remaining count (decrement), src_addr (+= stride), dst_addr (+= stride), perf counters increment'}, {'stage': 'DONE', 'cycle': 6, 'action': 'assert done pulse, update status, trigger IRQ, clock gating cell may disable hclk'}, {'stage': 'ERROR', 'cycle': 2, 'action': 'assert error pulse, latch error code, return to IDLE, clock gating cell may disable hclk'}], 'ordering': ['Configuration (APB pclk) must cross CDC before hclk channel FSM reads it.', 'Read burst completion must precede write burst for same data.', 'Address update (UPDATE) must precede next burst request.', 'Transfer completion (DONE) precedes done pulse observation.', '1KB boundary crossing recalculates burst parameters before next address phase.'], 'backpressure': ['New starts blocked while channel busy.', 'AHB transfers stall when hready is low.', 'Arbiter queues requests when bus is occupied.', 'FIFO almost_full back-pressures read burst.', 'CDC FIFO full back-pressures APB writes (pslverr or pready deassert).'], 'performance': {'outstanding_limit': 'N_CHANNELS', 'throughput': 'one burst per channel per arbiter round', 'cdc_latency': '3 hclk cycles for config to cross from pclk domain', 'fifo_depth': 'FIFO_DEPTH words per channel'}}, 'fcov_bins': [{'id': 'SC_001_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_001', 'description': 'single_channel_transfer'}, {'id': 'SC_002_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_002', 'description': 'alignment_error'}, {'id': 'SC_003_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_003', 'description': 'zero_length_error'}, {'id': 'SC_004_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_004', 'description': 'busy_reject'}, {'id': 'SC_005_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_005', 'description': 'multi_channel_interleaved'}, {'id': 'SC_006_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_006', 'description': 'bus_error_during_transfer'}, {'id': 'SC_007_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC_007', 'description': 'global_enable_disable'}, {'id': 'SC_008_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC_008', 'description': 'interrupt_clear'}, {'id': 'SC_009_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC_009', 'description': 'apb_unmapped_address'}, {'id': 'SC_010_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC_010', 'description': 'stride_transfer'}, {'id': 'SC_011_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC_011', 'description': 'bus_timeout'}, {'id': 'SC_012_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC_012', 'description': 'performance_counters'}, {'id': 'SC_013_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[12]', 'scenario': 'SC_013', 'description': 'burst_wrap_boundary'}, {'id': 'SC_014_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[13]', 'scenario': 'SC_014', 'description': 'clock_gating'}, {'id': 'function_dma_step', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DMA_STEP', 'source_ref': 'function_model.transactions.FM_DMA_STEP', 'description': 'Valid DMA step with burst transfer'}, {'id': 'function_dma_error_align', 'class': 'error', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DMA_ERROR', 'source_ref': 'function_model.transactions.FM_DMA_ERROR', 'description': 'Alignment error path'}, {'id': 'function_dma_error_zero_len', 'class': 'error', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DMA_ERROR', 'source_ref': 'function_model.transactions.FM_DMA_ERROR', 'description': 'Zero-length error path'}, {'id': 'function_dma_error_bus', 'class': 'error', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DMA_ERROR', 'source_ref': 'function_model.transactions.FM_DMA_ERROR', 'description': 'Bus error during AHB transfer'}, {'id': 'function_dma_error_timeout', 'class': 'error', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DMA_ERROR', 'source_ref': 'function_model.transactions.FM_DMA_ERROR', 'description': 'Bus timeout error'}, {'id': 'function_dma_busy_reject', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DMA_START', 'source_ref': 'function_model.transactions.FM_DMA_START', 'description': 'Start while busy rejected'}, {'id': 'function_dma_multi_ch', 'class': 'arbitration', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ARB_GRANT', 'source_ref': 'function_model.transactions.FM_ARB_GRANT', 'description': 'Multiple channels active simultaneously'}, {'id': 'function_dma_global_enable', 'class': 'control', 'coverage_domain': 'function', 'source': 'function_model.state_variables.dma_en_q', 'source_ref': 'function_model.state_variables.dma_en_q', 'description': 'Global enable disable with in-progress transfer'}, {'id': 'function_dma_irq_clear', 'class': 'interrupt', 'coverage_domain': 'function', 'source': 'function_model.state_variables.int_enable_q', 'source_ref': 'function_model.state_variables.int_enable_q', 'description': 'Interrupt clear via INT_CLEAR register'}, {'id': 'function_dma_apb_err', 'class': 'protocol', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DMA_START', 'source_ref': 'function_model.transactions.FM_DMA_START', 'description': 'APB error on unmapped address access'}, {'id': 'function_dma_stride', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.state_variables.ch_stride_q', 'source_ref': 'function_model.state_variables.ch_stride_q', 'description': 'Non-default stride address increment'}, {'id': 'function_dma_timeout', 'class': 'error', 'coverage_domain': 'function', 'source': 'function_model.state_variables.timeout_q', 'source_ref': 'function_model.state_variables.timeout_q', 'description': 'Bus timeout detection'}, {'id': 'function_dma_perf_counters', 'class': 'status', 'coverage_domain': 'function', 'source': 'function_model.state_variables.perf_words_q', 'source_ref': 'function_model.state_variables.perf_words_q', 'description': 'Performance counter increment'}, {'id': 'function_dma_burst_boundary', 'class': 'protocol', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DMA_STEP', 'source_ref': 'function_model.transactions.FM_DMA_STEP', 'description': 'Burst split at 1KB boundary'}, {'id': 'function_dma_clock_gating', 'class': 'power', 'coverage_domain': 'function', 'source': 'function_model.state_variables.ch_busy_q', 'source_ref': 'function_model.state_variables.ch_busy_q', 'description': 'Clock gating enable/disable per channel'}, {'id': 'cycle_pipeline_idle', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Channel FSM IDLE state visited'}, {'id': 'cycle_pipeline_cfg', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Channel FSM CFG state visited'}, {'id': 'cycle_pipeline_request', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Channel FSM REQUEST state visited'}, {'id': 'cycle_pipeline_read', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Channel FSM READ state visited'}, {'id': 'cycle_pipeline_write', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Channel FSM WRITE state visited'}, {'id': 'cycle_pipeline_update', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[5]', 'source_ref': 'cycle_model.pipeline[5]', 'description': 'Channel FSM UPDATE state visited'}, {'id': 'cycle_pipeline_done', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[6]', 'source_ref': 'cycle_model.pipeline[6]', 'description': 'Channel FSM DONE state visited'}, {'id': 'cycle_pipeline_error', 'class': 'state', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[7]', 'source_ref': 'cycle_model.pipeline[7]', 'description': 'Channel FSM ERROR state visited'}, {'id': 'cycle_arb_round_robin', 'class': 'arbitration', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance', 'source_ref': 'cycle_model.performance', 'description': 'Round-robin arbitration switching between channels'}, {'id': 'cycle_burst_latency', 'class': 'timing', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.ahb_address_phase', 'source_ref': 'cycle_model.handshake_rules.ahb_address_phase', 'description': 'Burst completion latency measured'}, {'id': 'cycle_cdc_crossing', 'class': 'timing', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.cdc_config', 'source_ref': 'cycle_model.handshake_rules.cdc_config', 'description': 'CDC config crossing latency measured'}, {'id': 'cycle_timeout_path', 'class': 'timing', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.timeout_rule', 'source_ref': 'cycle_model.handshake_rules.timeout_rule', 'description': 'Timeout counter activation and expiry'}, {'id': 'function_dma_start', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_dma_start', 'description': 'dma_start'}, {'id': 'function_dma_complete', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_dma_complete', 'description': 'dma_complete'}, {'id': 'function_dma_error', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_dma_error', 'description': 'dma_error'}, {'id': 'function_arb_grant', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_arb_grant', 'description': 'arb_grant'}, {'id': 'cycle_apb_access', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': 'APB accesses sample on pclk with psel and penable. No wait states. Config data crosses CDC to hclk domain via async FIFO.'}, {'id': 'cycle_cdc_config', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': 'APB write data pushed into pclk-side FIFO write port. hclk-side read port pops config. Gray-code pointer synchronization prevents metastability.'}, {'id': 'cycle_ahb_address_phase', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': 'AHB address phase drives haddr, htrans, hsize, hburst, hprot, hmaster, hmastlock for one hclk cycle.'}, {'id': 'cycle_ahb_data_phase', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': 'AHB data phase follows address phase by one hclk cycle with hwdata or hrdata.'}, {'id': 'cycle_ahb_1kb_boundary', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[4]', 'source_ref': 'cycle_model.handshake_rules[4]', 'description': 'Burst crossing 1KB address boundary starts new NONSEQ beat. hburst recalculated for remaining beats.'}, {'id': 'cycle_ahb_error_response', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[5]', 'source_ref': 'cycle_model.handshake_rules[5]', 'description': 'hresp=ERROR (01) completes current beat and aborts burst. hresp=RETRY (10) releases bus and re-requests. hresp=SPLIT (11) releases bus and waits.'}, {'id': 'cycle_arb_grant_rule', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[6]', 'source_ref': 'cycle_model.handshake_rules[6]', 'description': 'Arbiter evaluates requests every hclk cycle and grants to next round-robin contender.'}, {'id': 'cycle_start_accept', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[7]', 'source_ref': 'cycle_model.handshake_rules[7]', 'description': 'ch_start accepted only when ch_busy is low and dma_en is high and CDC config has arrived.'}, {'id': 'cycle_timeout_rule', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[8]', 'source_ref': 'cycle_model.handshake_rules[8]', 'description': 'Timeout counter increments each hclk cycle while waiting for hready. Resets on hready assertion. Error code 4 when counter reaches GLOBAL_TIMEOUT.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Configuration (APB pclk) must cross CDC before hclk channel FSM reads it.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Read burst completion must precede write burst for same data.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Address update (UPDATE) must precede next burst request.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'Transfer completion (DONE) precedes done pulse observation.'}, {'id': 'cycle_ordering_4', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[4]', 'source_ref': 'cycle_model.ordering[4]', 'description': '1KB boundary crossing recalculates burst parameters before next address phase.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'New starts blocked while channel busy.'}, {'id': 'cycle_backpressure_1', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[1]', 'source_ref': 'cycle_model.backpressure[1]', 'description': 'AHB transfers stall when hready is low.'}, {'id': 'cycle_backpressure_2', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[2]', 'source_ref': 'cycle_model.backpressure[2]', 'description': 'Arbiter queues requests when bus is occupied.'}, {'id': 'cycle_backpressure_3', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[3]', 'source_ref': 'cycle_model.backpressure[3]', 'description': 'FIFO almost_full back-pressures read burst.'}, {'id': 'cycle_backpressure_4', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[4]', 'source_ref': 'cycle_model.backpressure[4]', 'description': 'CDC FIFO full back-pressures APB writes (pslverr or pready deassert).'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': 'one burst per channel per arbiter round'}, {'id': 'fsm_per_channel_idle_to_cfg_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[0]', 'source_ref': 'fsm.per_channel.transitions[0]', 'description': 'ch_start && ch_en && dma_en && valid_cfg && cdc_config_valid'}, {'id': 'fsm_per_channel_idle_to_error_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[1]', 'source_ref': 'fsm.per_channel.transitions[1]', 'description': 'ch_start && ch_en && !valid_cfg'}, {'id': 'fsm_per_channel_cfg_to_request_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[2]', 'source_ref': 'fsm.per_channel.transitions[2]', 'description': 'next_cycle'}, {'id': 'fsm_per_channel_request_to_read_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[3]', 'source_ref': 'fsm.per_channel.transitions[3]', 'description': 'arb_grant'}, {'id': 'fsm_per_channel_read_to_write_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[4]', 'source_ref': 'fsm.per_channel.transitions[4]', 'description': 'read_burst_complete && !fifo_full'}, {'id': 'fsm_per_channel_read_to_error_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[5]', 'source_ref': 'fsm.per_channel.transitions[5]', 'description': 'ahb_error || timeout_expired || fifo_overflow'}, {'id': 'fsm_per_channel_write_to_update_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[6]', 'source_ref': 'fsm.per_channel.transitions[6]', 'description': 'write_burst_complete'}, {'id': 'fsm_per_channel_write_to_error_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[7]', 'source_ref': 'fsm.per_channel.transitions[7]', 'description': 'ahb_error || timeout_expired'}, {'id': 'fsm_per_channel_update_to_request_8', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[8]', 'source_ref': 'fsm.per_channel.transitions[8]', 'description': 'remaining_gt_0'}, {'id': 'fsm_per_channel_update_to_done_9', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[9]', 'source_ref': 'fsm.per_channel.transitions[9]', 'description': 'remaining_eq_0'}, {'id': 'fsm_per_channel_done_to_idle_10', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[10]', 'source_ref': 'fsm.per_channel.transitions[10]', 'description': 'status_sampled'}, {'id': 'fsm_per_channel_error_to_idle_11', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.per_channel.transitions[11]', 'source_ref': 'fsm.per_channel.transitions[11]', 'description': 'status_sampled'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_ALIGN', 'source': 'channel_start', 'condition': 'src_addr[1:0] != 0 or dst_addr[1:0] != 0', 'code': 1, 'description': 'Misaligned source or destination address'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_ZERO_LEN', 'source': 'channel_start', 'condition': 'CHx_LEN == 0', 'code': 2, 'description': 'Zero-length transfer requested'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': '{\'id\': \'ERR_BUS\', \'source\': \'ahb_transfer\', \'condition\': "hresp == 2\'b01 (ERROR)", \'code\': 3, \'description\': \'AHB bus error during transfer\'}'}, {'id': 'error_error_3', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[3]', 'source_ref': 'error_handling.error_sources[3]', 'description': "{'id': 'ERR_TIMEOUT', 'source': 'bus_timeout', 'condition': 'hready==0 for GLOBAL_TIMEOUT consecutive hclk cycles', 'code': 4, 'description': 'Bus timeout waiting for slave response'}"}, {'id': 'error_error_4', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[4]', 'source_ref': 'error_handling.error_sources[4]', 'description': "{'id': 'ERR_FIFO_OVERFLOW', 'source': 'fifo_write', 'condition': 'fifo_write when fifo_full (CDC config path)', 'code': 5, 'description': 'FIFO overflow on config data path'}"}]}
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

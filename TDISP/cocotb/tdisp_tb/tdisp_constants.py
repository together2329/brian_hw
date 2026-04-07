"""
TDISP Constants and Enums u2014 Python mirror of tdisp_pkg.sv
Mirrors all enums, constants, structs from the TDISP RTL package.
Provides little-endian pack/unpack helpers for message construction.
"""

import struct
from enum import IntEnum, IntFlag
from dataclasses import dataclass
from typing import List


# ============================================================================
# Protocol Version (Section 11.3.3)
# ============================================================================
TDISP_VERSION_1_0 = 0x10  # Bits [7:4]=Major=1, [3:0]=Minor=0

# ============================================================================
# Design Parameters
# ============================================================================
MAX_NUM_TDI     = 16
MAX_P2P_STREAMS = 8
MAX_MMIO_RANGES = 32
MAX_REPORT_SIZE = 4096
TDI_INDEX_WIDTH = 4

# ============================================================================
# Message Header Constants (Table 11-6)
# ============================================================================
TDISP_MSG_HEADER_SIZE = 16   # bytes
INTERFACE_ID_WIDTH    = 96   # bits (12 bytes)
NONCE_WIDTH           = 256  # bits (32 bytes)

# Header field offsets (bytes)
TDISP_HDR_VER_OFFSET      = 0
TDISP_HDR_MSGTYPE_OFFSET  = 1
TDISP_HDR_RESERVED_OFFSET = 2
TDISP_HDR_IFACE_ID_OFFSET = 4
TDISP_HDR_PAYLOAD_OFFSET  = 16

# SPDM Protocol ID
SPDM_PROTOCOL_ID = 0x01


# ============================================================================
# TDI State Encoding (Section 11.3.13, Table 11-18)
# ============================================================================
class TdiState(IntEnum):
    CONFIG_UNLOCKED = 0x0
    CONFIG_LOCKED   = 0x1
    RUN             = 0x2
    ERROR           = 0x3


# ============================================================================
# TDISP Request Codes (Table 11-4)
# ============================================================================
class ReqCode(IntEnum):
    GET_TDISP_VERSION           = 0x81
    GET_TDISP_CAPABILITIES      = 0x82
    LOCK_INTERFACE              = 0x83
    GET_DEVICE_INTERFACE_REPORT = 0x84
    GET_DEVICE_INTERFACE_STATE  = 0x85
    START_INTERFACE             = 0x86
    STOP_INTERFACE              = 0x87
    BIND_P2P_STREAM             = 0x88
    UNBIND_P2P_STREAM           = 0x89
    SET_MMIO_ATTRIBUTE          = 0x8A
    VDM                         = 0x8B
    SET_TDISP_CONFIG            = 0x8C


# ============================================================================
# TDISP Response Codes (Table 11-5)
# ============================================================================
class RespCode(IntEnum):
    TDISP_VERSION           = 0x01
    TDISP_CAPABILITIES      = 0x02
    LOCK_INTERFACE          = 0x03
    DEVICE_INTERFACE_REPORT = 0x04
    DEVICE_INTERFACE_STATE  = 0x05
    START_INTERFACE         = 0x06
    STOP_INTERFACE          = 0x07
    BIND_P2P_STREAM         = 0x08
    UNBIND_P2P_STREAM       = 0x09
    SET_MMIO_ATTRIBUTE      = 0x0A
    VDM                     = 0x0B
    SET_TDISP_CONFIG        = 0x0C
    TDISP_ERROR             = 0x7F


# ============================================================================
# TDISP Error Codes (Table 11-28)
# ============================================================================
class ErrorCode(IntEnum):
    RESERVED                     = 0x0000
    INVALID_REQUEST              = 0x0001
    BUSY                         = 0x0003
    INVALID_INTERFACE_STATE      = 0x0004
    UNSPECIFIED                  = 0x0005
    UNSUPPORTED_REQUEST          = 0x0007
    VERSION_MISMATCH             = 0x0041
    VENDOR_SPECIFIC_ERROR        = 0x00FF
    INVALID_INTERFACE            = 0x0101
    INVALID_NONCE                = 0x0102
    INSUFFICIENT_ENTROPY         = 0x0103
    INVALID_DEVICE_CONFIGURATION = 0x0104


# ============================================================================
# Lock Interface Flags (Table 11-11 FLAGS field)
# Bit positions within the 16-bit flags word
# ============================================================================
class LockFlags:
    """Lock flags bit positions within the 16-bit flags word."""
    NO_FW_UPDATE         = 0
    SYS_CACHE_LINE_SIZE  = 1  # 0=64B, 1=128B
    LOCK_MSIX            = 2
    BIND_P2P             = 3
    ALL_REQUEST_REDIRECT = 4


# ============================================================================
# Interface Report Info bits (Table 11-16)
# ============================================================================
class InterfaceReportInfo:
    NO_FW_UPDATE      = 0
    DMA_WITHOUT_PASID = 1
    DMA_WITH_PASID    = 2
    ATS_ENABLED       = 3
    PRS_ENABLED       = 4
    XT_MODE_ENABLED   = 5


# ============================================================================
# Request-to-Response mapping (mirrors tdisp_resp_code_for_req)
# ============================================================================
REQ_TO_RESP = {
    ReqCode.GET_TDISP_VERSION:           RespCode.TDISP_VERSION,
    ReqCode.GET_TDISP_CAPABILITIES:      RespCode.TDISP_CAPABILITIES,
    ReqCode.LOCK_INTERFACE:              RespCode.LOCK_INTERFACE,
    ReqCode.GET_DEVICE_INTERFACE_REPORT: RespCode.DEVICE_INTERFACE_REPORT,
    ReqCode.GET_DEVICE_INTERFACE_STATE:  RespCode.DEVICE_INTERFACE_STATE,
    ReqCode.START_INTERFACE:             RespCode.START_INTERFACE,
    ReqCode.STOP_INTERFACE:              RespCode.STOP_INTERFACE,
    ReqCode.BIND_P2P_STREAM:             RespCode.BIND_P2P_STREAM,
    ReqCode.UNBIND_P2P_STREAM:           RespCode.UNBIND_P2P_STREAM,
    ReqCode.SET_MMIO_ATTRIBUTE:          RespCode.SET_MMIO_ATTRIBUTE,
    ReqCode.VDM:                         RespCode.VDM,
    ReqCode.SET_TDISP_CONFIG:            RespCode.SET_TDISP_CONFIG,
}


# ============================================================================
# Legal state-for-request mapping (mirrors tdisp_state_is_legal_for_req)
# ============================================================================
def is_legal_for_req(req_code: int, state: int) -> bool:
    """Check if a request is legal in the given TDI state per Table 11-4."""
    try:
        req = ReqCode(req_code)
    except ValueError:
        return False
    try:
        st = TdiState(state)
    except ValueError:
        return False

    _all_states = {TdiState.CONFIG_UNLOCKED, TdiState.CONFIG_LOCKED,
                   TdiState.RUN, TdiState.ERROR}
    _locked_or_run = {TdiState.CONFIG_LOCKED, TdiState.RUN}

    legal_map = {
        ReqCode.GET_TDISP_VERSION:           _all_states,
        ReqCode.GET_TDISP_CAPABILITIES:      _all_states,
        ReqCode.LOCK_INTERFACE:              {TdiState.CONFIG_UNLOCKED},
        ReqCode.GET_DEVICE_INTERFACE_REPORT: _locked_or_run,
        ReqCode.GET_DEVICE_INTERFACE_STATE:  _all_states,
        ReqCode.START_INTERFACE:             {TdiState.CONFIG_LOCKED},
        ReqCode.STOP_INTERFACE:              _all_states,
        ReqCode.BIND_P2P_STREAM:             {TdiState.RUN},
        ReqCode.UNBIND_P2P_STREAM:           {TdiState.RUN},
        ReqCode.SET_MMIO_ATTRIBUTE:          {TdiState.RUN},
        ReqCode.VDM:                         _all_states,
        ReqCode.SET_TDISP_CONFIG:            {TdiState.CONFIG_UNLOCKED},
    }
    return st in legal_map.get(req, set())


# ============================================================================
# Little-endian byte pack/unpack helpers
# ============================================================================

def pack_u8(val: int) -> bytes:
    """Pack a uint8 as 1 byte (little-endian)."""
    return struct.pack('<B', val & 0xFF)


def pack_u16(val: int) -> bytes:
    """Pack a uint16 as 2 bytes (little-endian)."""
    return struct.pack('<H', val & 0xFFFF)


def pack_u32(val: int) -> bytes:
    """Pack a uint32 as 4 bytes (little-endian)."""
    return struct.pack('<I', val & 0xFFFFFFFF)


def pack_u64(val: int) -> bytes:
    """Pack a uint64 as 8 bytes (little-endian)."""
    return struct.pack('<Q', val & 0xFFFFFFFFFFFFFFFF)


def unpack_u8(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from('<B', data, offset)[0]


def unpack_u16(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from('<H', data, offset)[0]


def unpack_u32(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from('<I', data, offset)[0]


def unpack_u64(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from('<Q', data, offset)[0]


# ============================================================================
# Interface ID helpers (96-bit = 12 bytes)
# ============================================================================

def pack_interface_id(iface_id: int) -> bytes:
    """Pack a 96-bit interface ID into 12 bytes (little-endian)."""
    result = bytearray(12)
    for i in range(12):
        result[i] = (iface_id >> (i * 8)) & 0xFF
    return bytes(result)


def unpack_interface_id(data: bytes, offset: int = 0) -> int:
    """Unpack 12 bytes into a 96-bit interface ID (little-endian)."""
    val = 0
    for i in range(12):
        val |= data[offset + i] << (i * 8)
    return val


# ============================================================================
# Nonce helpers (256-bit = 32 bytes)
# ============================================================================

def pack_nonce(nonce: int) -> bytes:
    """Pack a 256-bit nonce into 32 bytes (little-endian)."""
    result = bytearray(32)
    for i in range(32):
        result[i] = (nonce >> (i * 8)) & 0xFF
    return bytes(result)


def unpack_nonce(data: bytes, offset: int = 0) -> int:
    """Unpack 32 bytes into a 256-bit nonce (little-endian)."""
    val = 0
    for i in range(32):
        val |= data[offset + i] << (i * 8)
    return val


# ============================================================================
# Message Header pack/unpack (Table 11-6)
# ============================================================================

@dataclass
class TdispMsgHeader:
    version: int
    msg_type: int
    reserved: int = 0
    interface_id: int = 0

    def pack(self) -> bytes:
        """Pack header into 16 bytes (little-endian wire format)."""
        data = bytearray(16)
        data[0] = self.version & 0xFF
        data[1] = self.msg_type & 0xFF
        struct.pack_into('<H', data, 2, self.reserved & 0xFFFF)
        iface_bytes = pack_interface_id(self.interface_id)
        data[4:16] = iface_bytes
        return bytes(data)

    @staticmethod
    def unpack(data: bytes) -> 'TdispMsgHeader':
        """Unpack 16 bytes into a TdispMsgHeader."""
        version = data[0]
        msg_type = data[1]
        reserved = struct.unpack_from('<H', data, 2)[0]
        interface_id = unpack_interface_id(data, 4)
        return TdispMsgHeader(version, msg_type, reserved, interface_id)


def build_tdisp_message(msg_type: int, interface_id: int,
                        payload: bytes = b'') -> bytes:
    """Build a complete TDISP message (header + payload) as a byte array."""
    hdr = TdispMsgHeader(
        version=TDISP_VERSION_1_0,
        msg_type=msg_type,
        interface_id=interface_id
    )
    return hdr.pack() + payload


def parse_tdisp_message(data: bytes):
    """Parse a TDISP message into (header, payload_bytes)."""
    hdr = TdispMsgHeader.unpack(data[:TDISP_MSG_HEADER_SIZE])
    payload = data[TDISP_MSG_HEADER_SIZE:]
    return hdr, payload


# ============================================================================
# Lock Flags pack/unpack (Table 11-11)
# ============================================================================

def pack_lock_flags(no_fw_update: bool = False,
                    sys_cache_line_size: bool = False,
                    lock_msix: bool = False,
                    bind_p2p: bool = False,
                    all_request_redirect: bool = False) -> int:
    """Pack lock flags into a 16-bit word."""
    flags = 0
    if no_fw_update:
        flags |= (1 << LockFlags.NO_FW_UPDATE)
    if sys_cache_line_size:
        flags |= (1 << LockFlags.SYS_CACHE_LINE_SIZE)
    if lock_msix:
        flags |= (1 << LockFlags.LOCK_MSIX)
    if bind_p2p:
        flags |= (1 << LockFlags.BIND_P2P)
    if all_request_redirect:
        flags |= (1 << LockFlags.ALL_REQUEST_REDIRECT)
    return flags


def unpack_lock_flags(flags: int) -> dict:
    """Unpack a 16-bit flags word into a dict of flag names/bools."""
    return {
        'no_fw_update':         bool(flags & (1 << LockFlags.NO_FW_UPDATE)),
        'sys_cache_line_size':  bool(flags & (1 << LockFlags.SYS_CACHE_LINE_SIZE)),
        'lock_msix':            bool(flags & (1 << LockFlags.LOCK_MSIX)),
        'bind_p2p':             bool(flags & (1 << LockFlags.BIND_P2P)),
        'all_request_redirect': bool(flags & (1 << LockFlags.ALL_REQUEST_REDIRECT)),
    }


# ============================================================================
# LOCK_INTERFACE_REQUEST payload pack/unpack (Table 11-11)
# ============================================================================

def pack_lock_req_payload(flags: int = 0,
                          default_stream_id: int = 0,
                          mmio_reporting_offset: int = 0,
                          bind_p2p_addr_mask: int = 0) -> bytes:
    """Pack LOCK_INTERFACE_REQUEST payload (20 bytes)."""
    data = bytearray(20)
    struct.pack_into('<H', data, 0, flags & 0xFFFF)
    data[2] = default_stream_id & 0xFF
    data[3] = 0  # reserved
    struct.pack_into('<Q', data, 4, mmio_reporting_offset & 0xFFFFFFFFFFFFFFFF)
    struct.pack_into('<Q', data, 12, bind_p2p_addr_mask & 0xFFFFFFFFFFFFFFFF)
    return bytes(data)


def unpack_lock_req_payload(data: bytes) -> dict:
    """Unpack LOCK_INTERFACE_REQUEST payload (20 bytes)."""
    return {
        'flags':                unpack_u16(data, 0),
        'default_stream_id':    unpack_u8(data, 2),
        'reserved_byte':        unpack_u8(data, 3),
        'mmio_reporting_offset': unpack_u64(data, 4),
        'bind_p2p_addr_mask':   unpack_u64(data, 12),
    }


# ============================================================================
# GET_DEVICE_INTERFACE_REPORT request payload (Table 11-14)
# ============================================================================

def pack_get_report_req(offset: int = 0, length: int = 0) -> bytes:
    """Pack GET_DEVICE_INTERFACE_REPORT request payload (4 bytes)."""
    data = bytearray(4)
    struct.pack_into('<H', data, 0, offset & 0xFFFF)
    struct.pack_into('<H', data, 2, length & 0xFFFF)
    return bytes(data)


def unpack_get_report_req(data: bytes) -> dict:
    return {
        'offset': unpack_u16(data, 0),
        'length': unpack_u16(data, 2),
    }


# ============================================================================
# DEVICE_INTERFACE_REPORT response header (Table 11-15)
# ============================================================================

def unpack_report_resp_header(data: bytes) -> dict:
    """Unpack report response header (4 bytes at payload offset 0)."""
    return {
        'portion_length':   unpack_u16(data, 0),
        'remainder_length': unpack_u16(data, 2),
    }


# ============================================================================
# DEVICE_INTERFACE_STATE response payload (Table 11-18)
# ============================================================================

def unpack_iface_state_resp(data: bytes) -> dict:
    """Unpack interface state response (1 byte payload)."""
    return {'tdi_state': unpack_u8(data, 0)}


# ============================================================================
# TDISP_ERROR response payload (Table 11-27)
# ============================================================================

def unpack_error_resp(data: bytes) -> dict:
    """Unpack error response payload (8 bytes: error_code + error_data)."""
    return {
        'error_code': unpack_u32(data, 0),
        'error_data': unpack_u32(data, 4),
    }


# ============================================================================
# BIND_P2P_STREAM request payload (Section 11.3.18)
# ============================================================================

def pack_bind_p2p_req(stream_id: int = 0,
                      p2p_portion: int = 0) -> bytes:
    """Pack BIND_P2P_STREAM request payload (4 bytes)."""
    data = bytearray(4)
    data[0] = stream_id & 0xFF
    data[1] = 0  # reserved
    struct.pack_into('<H', data, 2, p2p_portion & 0xFFFF)
    return bytes(data)


def unpack_bind_p2p_req(data: bytes) -> dict:
    return {
        'stream_id':   unpack_u8(data, 0),
        'reserved':    unpack_u8(data, 1),
        'p2p_portion': unpack_u16(data, 2),
    }


# ============================================================================
# UNBIND_P2P_STREAM request payload (Section 11.3.20)
# ============================================================================

def pack_unbind_p2p_req(stream_id: int = 0) -> bytes:
    """Pack UNBIND_P2P_STREAM request payload (1 byte)."""
    return pack_u8(stream_id)


def unpack_unbind_p2p_req(data: bytes) -> dict:
    return {'stream_id': unpack_u8(data, 0)}


# ============================================================================
# SET_MMIO_ATTRIBUTE request payload (Section 11.3.22)
# ============================================================================

def pack_set_mmio_attr_req(start_addr: int = 0,
                           num_4k_pages: int = 0,
                           is_non_tee_mem: bool = False) -> bytes:
    """Pack SET_MMIO_ATTRIBUTE request payload (16 bytes)."""
    data = bytearray(16)
    struct.pack_into('<Q', data, 0, start_addr & 0xFFFFFFFFFFFFFFFF)
    struct.pack_into('<I', data, 8, num_4k_pages & 0xFFFFFFFF)
    attr_bit = 1 if is_non_tee_mem else 0
    struct.pack_into('<I', data, 12, attr_bit)
    return bytes(data)


def unpack_set_mmio_attr_req(data: bytes) -> dict:
    return {
        'start_addr':     unpack_u64(data, 0),
        'num_4k_pages':   unpack_u32(data, 8),
        'is_non_tee_mem': bool(data[12] & 1),
    }


# ============================================================================
# SET_TDISP_CONFIG request payload (Section 11.3.27)
# ============================================================================

def pack_set_config_req(xt_mode_enable: bool = False,
                        xt_bit_for_locked_msix: bool = False) -> bytes:
    """Pack SET_TDISP_CONFIG request payload (4 bytes)."""
    val = 0
    if xt_mode_enable:
        val |= (1 << 0)
    if xt_bit_for_locked_msix:
        val |= (1 << 1)
    return pack_u32(val)


def unpack_set_config_req(data: bytes) -> dict:
    val = unpack_u32(data, 0)
    return {
        'xt_mode_enable':         bool(val & (1 << 0)),
        'xt_bit_for_locked_msix': bool(val & (1 << 1)),
    }


# ============================================================================
# TDISP_CAPABILITIES struct pack/unpack (Table 11-10)
# Total: 1+30+128+16+24+8+8+8 = 223 bits = 27.875 bytes u2192 packed as 28 bytes
# Wire format is byte-aligned in the response payload:
#   DSM_CAPS (4 bytes) | req_msgs_supported (16 bytes) |
#   lock_iface_flags_supported (2 bytes) | caps_reserved (3 bytes) |
#   dev_addr_width (1 byte) | num_req_this (1 byte) | num_req_all (1 byte)
# Total = 28 bytes
# ============================================================================

def pack_caps(xt_mode_supported: bool = False,
              req_msgs_supported: int = 0,
              lock_iface_flags_supported: int = 0,
              dev_addr_width: int = 64,
              num_req_this: int = 1,
              num_req_all: int = 1) -> bytes:
    """Pack tdisp_caps_s as 28-byte wire-format payload."""
    data = bytearray(28)
    dsm_caps = 1 if xt_mode_supported else 0
    struct.pack_into('<I', data, 0, dsm_caps)
    # req_msgs_supported: 128-bit bitmask as 16 bytes LE
    for i in range(16):
        data[4 + i] = (req_msgs_supported >> (i * 8)) & 0xFF
    struct.pack_into('<H', data, 20, lock_iface_flags_supported & 0xFFFF)
    # caps_reserved: 3 bytes at offset 22 (zeros)
    data[25] = dev_addr_width & 0xFF
    data[26] = num_req_this & 0xFF
    data[27] = num_req_all & 0xFF
    return bytes(data)


def unpack_caps(data: bytes) -> dict:
    """Unpack tdisp_caps_s from 28-byte wire-format payload."""
    dsm_caps = unpack_u32(data, 0)
    req_msgs = 0
    for i in range(16):
        req_msgs |= data[4 + i] << (i * 8)
    return {
        'xt_mode_supported':            bool(dsm_caps & 1),
        'req_msgs_supported':           req_msgs,
        'lock_iface_flags_supported':   unpack_u16(data, 20),
        'dev_addr_width':               unpack_u8(data, 25),
        'num_req_this':                 unpack_u8(data, 26),
        'num_req_all':                  unpack_u8(data, 27),
    }


# ============================================================================
# Interface ID generation helpers for test TDI indices
# ============================================================================

def make_interface_id(tdi_index: int, base: int = 0) -> int:
    """Generate a unique 96-bit interface ID for a TDI index."""
    return base | (tdi_index + 1)


# ============================================================================
# TDI state name lookup (for logging)
# ============================================================================

TDI_STATE_NAMES = {
    TdiState.CONFIG_UNLOCKED: "CONFIG_UNLOCKED",
    TdiState.CONFIG_LOCKED:   "CONFIG_LOCKED",
    TdiState.RUN:             "RUN",
    TdiState.ERROR:           "ERROR",
}


def tdi_state_name(state: int) -> str:
    """Return human-readable state name."""
    return TDI_STATE_NAMES.get(TdiState(state), f"UNKNOWN({state})")


REQ_CODE_NAMES = {v: k.name for k, v in [(r, r) for r in ReqCode]}
RESP_CODE_NAMES = {v: k.name for k, v in [(r, r) for r in RespCode]}
ERROR_CODE_NAMES = {v: k.name for k, v in [(e, e) for e in ErrorCode]}

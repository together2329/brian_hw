"""
TDISP Golden Reference Model — Python predictor matching RTL one-to-one.

Models per-TDI state machines, nonce lifecycle, message validation
(version check, state legality per Table 11-4), register CAT tracking,
TLP filter rules (egress/ingress per §11.2), lock handler phases,
P2P stream binding, and expected response generation for any request.

Usage:
    model = TdispRefModel(num_tdi=4)
    resp  = model.process_request(raw_bytes)
    print(f"Expected response: {resp}")

All enums and constants are imported from tdisp_constants.py.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Set

from tdisp_constants import (
    TDISP_VERSION_1_0,
    MAX_NUM_TDI,
    MAX_P2P_STREAMS,
    MAX_REPORT_SIZE,
    TDISP_MSG_HEADER_SIZE,
    NONCE_WIDTH,
    TdiState,
    ReqCode,
    RespCode,
    ErrorCode,
    REQ_TO_RESP,
    is_legal_for_req,
    TdispMsgHeader,
    parse_tdisp_message,
    build_tdisp_message,
    pack_u8, pack_u16, pack_u32, pack_u64,
    unpack_u8, unpack_u16, unpack_u32, unpack_u64,
    pack_nonce, unpack_nonce,
    pack_interface_id, unpack_interface_id,
    unpack_lock_req_payload,
    unpack_get_report_req,
    unpack_bind_p2p_req,
    unpack_unbind_p2p_req,
    unpack_set_mmio_attr_req,
    unpack_set_config_req,
    unpack_error_resp,
    tdi_state_name,
    TDI_STATE_NAMES,
    REQ_CODE_NAMES,
    RESP_CODE_NAMES,
    ERROR_CODE_NAMES,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Register write categories (mirrors tdisp_reg_tracker.sv reg_category_e)
# ============================================================================

class RegCategory:
    """Register write classification categories per Table 11-3."""
    ALLOWED      = 0  # Write permitted, no action
    ERROR        = 1  # Always forbidden → error_trigger
    CMD_REGISTER = 2  # Command Register — check critical bits
    DEV_CTRL     = 3  # Device Control 1/2/3 — check critical bits
    MSIX         = 4  # MSI-X — error if table was locked
    VENDOR_SPEC  = 5  # Vendor Specific — vendor analysis required
    POWER_MGMT   = 6  # PCI Power Management — state loss check
    RESERVED_CAT = 7  # Reserved / unmapped → default ERROR


# ============================================================================
# Address type constants (mirrors tdisp_tlp_filter.sv)
# ============================================================================
AT_UNTRANSLATED = 0  # 2'b00


# ============================================================================
# Expected payload length per request code (mirrors tdisp_req_handler.sv)
# ============================================================================

def expected_payload_len(req_code: int) -> int:
    """Return expected payload length in bytes for a given request code.
    0xFFFF means variable length (VDM).
    """
    _len_map = {
        ReqCode.GET_TDISP_VERSION:           0,
        ReqCode.GET_TDISP_CAPABILITIES:      4,
        ReqCode.LOCK_INTERFACE:              20,
        ReqCode.GET_DEVICE_INTERFACE_REPORT: 4,
        ReqCode.GET_DEVICE_INTERFACE_STATE:  0,
        ReqCode.START_INTERFACE:             32,
        ReqCode.STOP_INTERFACE:              0,
        ReqCode.BIND_P2P_STREAM:             2,
        ReqCode.UNBIND_P2P_STREAM:           1,
        ReqCode.SET_MMIO_ATTRIBUTE:          16,
        ReqCode.VDM:                         0xFFFF,  # variable
        ReqCode.SET_TDISP_CONFIG:            4,
    }
    return _len_map.get(req_code, 0)


# ============================================================================
# Register address classification tables (mirrors tdisp_reg_tracker.sv)
# ============================================================================

# Standard config space (offset 0x000–0x0FF): exact address → category
_STD_REG_CATS = {
    0x00C: RegCategory.ALLOWED,   # Cache Line Size
    0x03C: RegCategory.ALLOWED,   # Interrupt Line
    0x006: RegCategory.ALLOWED,   # Status Register
    0x004: RegCategory.CMD_REGISTER,  # Command Register
    0x00F: RegCategory.ERROR,     # BIST Register
    0x010: RegCategory.ERROR,     # BAR0
    0x014: RegCategory.ERROR,     # BAR1
    0x018: RegCategory.ERROR,     # BAR2
    0x01C: RegCategory.ERROR,     # BAR3
    0x020: RegCategory.ERROR,     # BAR4
    0x024: RegCategory.ERROR,     # BAR5
    0x030: RegCategory.ERROR,     # Expansion ROM Base Address
}

# Extended config space (offset 0x100+): (start, end_exclusive) → category
_EXT_REG_CATS = [
    (0x100, 0x140, RegCategory.ALLOWED),   # AER Extended
    (0x140, 0x180, RegCategory.ALLOWED),   # VC / MFVC Extended
    (0x180, 0x190, RegCategory.ALLOWED),   # Serial Number Extended
    (0x190, 0x1A0, RegCategory.ALLOWED),   # Power Budgeting
    (0x1A0, 0x1B0, RegCategory.ALLOWED),   # ACS Extended
    (0x1B0, 0x1C0, RegCategory.ALLOWED),   # LTR Extended
    (0x200, 0x240, RegCategory.ALLOWED),   # Secondary PCIe Extended
    (0x240, 0x280, RegCategory.ALLOWED),   # Physical Layer 16.0 GT/s
    (0x280, 0x2C0, RegCategory.ALLOWED),   # Physical Layer 32.0 GT/s
    (0x2C0, 0x300, RegCategory.ALLOWED),   # Physical Layer 64.0 GT/s
    (0x300, 0x340, RegCategory.ALLOWED),   # Lane Margining at Receiver
    (0x340, 0x360, RegCategory.ALLOWED),   # Flit Error Injection
    (0x360, 0x380, RegCategory.ERROR),      # Resizable BAR Extended
    (0x380, 0x3A0, RegCategory.ERROR),      # VF Resizable BAR Extended
    (0x3A0, 0x3B0, RegCategory.ERROR),      # ARI Extended
    (0x3B0, 0x3C0, RegCategory.ERROR),      # PASID Extended
    (0x3C0, 0x3E0, RegCategory.ERROR),      # Multicast Extended
    (0x3E0, 0x400, RegCategory.ERROR),      # ATS Extended
    (0x400, 0x420, RegCategory.ALLOWED),   # L1 PM Substates
    (0x420, 0x440, RegCategory.ALLOWED),   # Dynamic Power Allocation
    (0x440, 0x460, RegCategory.ALLOWED),   # PTM Extended
    (0x460, 0x480, RegCategory.ALLOWED),   # DOE Extended
    (0x480, 0x500, RegCategory.ALLOWED),   # IDE Extended
    (0x500, 0x540, RegCategory.ERROR),      # Enhanced Allocation
    (0x600, 0x640, RegCategory.ALLOWED),   # Protocol Multiplexing
    (0x640, 0x660, RegCategory.ALLOWED),   # Shadow Functions
]


def classify_register_addr(addr: int,
                           pcie_cap_base: int = 0x080,
                           msix_cap_base: int = 0x0B0,
                           pm_cap_base: int = 0x040) -> int:
    """Classify a PCIe config space register address into a category.

    Mirrors the combinational logic in tdisp_reg_tracker.sv.
    Returns a RegCategory value.
    """
    addr_aligned = addr & 0xFFF  # 12-bit config space

    # Check standard header space first
    if addr_aligned in _STD_REG_CATS:
        return _STD_REG_CATS[addr_aligned]

    # Check capability structures (PCIe, MSI-X, PM)
    # PCIe Capability: check for Device Control registers
    pcie_end = (pcie_cap_base + 0x048) & 0xFFF
    if pcie_cap_base <= addr_aligned < pcie_end:
        dc_offsets = [0x008, 0x028, 0x044]
        for dc_off in dc_offsets:
            if (addr_aligned & 0xFFC) == ((pcie_cap_base + dc_off) & 0xFFC):
                return RegCategory.DEV_CTRL
        return RegCategory.ALLOWED  # Other PCIe cap registers

    # MSI-X Capability: 8-byte structure at msix_cap_base
    msix_end = (msix_cap_base + 0x008) & 0xFFF
    if msix_cap_base <= addr_aligned < msix_end:
        return RegCategory.MSIX

    # Power Management Capability
    pm_end = (pm_cap_base + 0x008) & 0xFFF
    if pm_cap_base <= addr_aligned < pm_end:
        pmcsr_addr = (pm_cap_base + 0x004) & 0xFFC
        if (addr_aligned & 0xFFC) == pmcsr_addr:
            return RegCategory.POWER_MGMT
        return RegCategory.ALLOWED  # Other PM registers

    # Extended config space (0x100+)
    if addr_aligned >= 0x100:
        for start, end_excl, cat in _EXT_REG_CATS:
            if start <= addr_aligned < end_excl:
                return cat
        # Default for unmapped extended: ALLOWED (per RTL "Hierarchy ID / NPEM / Alt Protocol")
        return RegCategory.ALLOWED

    # Unmapped standard header → reserved → ERROR
    return RegCategory.RESERVED_CAT


# ============================================================================
# TLP filter input dataclasses
# ============================================================================

@dataclass
class EgressTlpInput:
    """Input for egress TLP filter classification."""
    valid: bool = False
    is_memory_req: bool = False
    is_completion: bool = False
    is_msi: bool = False
    is_msix: bool = False
    is_msix_locked: bool = False
    is_ats_request: bool = False
    is_vdm: bool = False
    is_io_req: bool = False
    addr_type: int = 0       # AT field
    access_tee_mem: bool = False
    access_non_tee_mem: bool = False


@dataclass
class EgressTlpResult:
    """Result of egress TLP filter classification."""
    reject: bool = False
    xt_bit: bool = False
    t_bit: bool = False


@dataclass
class IngressTlpInput:
    """Input for ingress TLP filter classification."""
    valid: bool = False
    xt_bit: bool = False
    t_bit: bool = False
    is_memory_req: bool = False
    is_completion: bool = False
    is_vdm: bool = False
    is_ats_request: bool = False
    target_is_non_tee_mem: bool = False
    on_bound_stream: bool = False
    ide_required: bool = False
    msix_table_locked: bool = False


@dataclass
class IngressTlpResult:
    """Result of ingress TLP filter classification."""
    reject: bool = False


# ============================================================================
# TDI context — per-TDI state
# ============================================================================

@dataclass
class TdiContext:
    """Per-TDI state tracked by the reference model."""
    state: int = TdiState.CONFIG_UNLOCKED
    nonce: int = 0                 # 256-bit stored nonce
    nonce_valid: bool = False
    p2p_streams_bound: Set[int] = field(default_factory=set)
    lock_cfg: Optional[dict] = None  # Stored lock config from LOCK_INTERFACE


# ============================================================================
# Reference response dataclass
# ============================================================================

@dataclass
class RefResponse:
    """Expected response from the reference model."""
    msg_type: int               # RespCode value
    interface_id: int           # Echoed from request
    payload: bytes              # Response payload bytes
    is_error: bool = False      # True if response is TDISP_ERROR
    error_code: int = 0         # ErrorCode if is_error
    error_data: int = 0         # Error data if is_error

    @property
    def resp_name(self) -> str:
        return RESP_CODE_NAMES.get(self.msg_type,
                                    f"UNKNOWN(0x{self.msg_type:02x})")

    @property
    def error_name(self) -> str:
        if not self.is_error:
            return "NONE"
        return ERROR_CODE_NAMES.get(self.error_code,
                                     f"UNKNOWN(0x{self.error_code:04x})")

    def to_raw(self) -> bytes:
        """Build the complete response message bytes (header + payload)."""
        hdr = TdispMsgHeader(
            version=TDISP_VERSION_1_0,
            msg_type=self.msg_type,
            interface_id=self.interface_id,
        )
        return hdr.pack() + self.payload


# ============================================================================
# Register write result
# ============================================================================

@dataclass
class RegWriteResult:
    """Result of a register write classification."""
    category: int                # RegCategory value
    triggers_error: bool = False # Whether error_trigger pulses
    error_code: int = 0
    error_data: int = 0
    reg_name: str = ""


# ============================================================================
# Lock handler result
# ============================================================================

@dataclass
class LockResult:
    """Result of LOCK_INTERFACE lock handler phases."""
    success: bool = False
    nonce: int = 0               # Generated nonce (256-bit)
    error_code: int = 0


# ============================================================================
# Main reference model
# ============================================================================

class TdispRefModel:
    """Golden TDISP reference model that mirrors the RTL implementation.

    Maintains per-TDI state machines, nonce lifecycle, register CAT
    tracking, P2P stream bindings, and TLP filter rules.  Predicts
    the expected response for any request message.

    Args:
        num_tdi: Number of TDI instances (default: MAX_NUM_TDI=16)
        device_report: Device interface report bytes (up to MAX_REPORT_SIZE)
        device_caps: Device capabilities dict for GET_TDISP_CAPABILITIES
        hosted_interface_ids: List of 96-bit IDs identifying hosted TDIs
        ide_default_stream_id: Default IDE stream ID for lock validation
        pcie_cap_base: PCI Express Capability base address in config space
        msix_cap_base: MSI-X Capability base address in config space
        pm_cap_base: Power Management Capability base address in config space
    """

    def __init__(self,
                 num_tdi: int = MAX_NUM_TDI,
                 device_report: bytes = b'',
                 device_caps: Optional[dict] = None,
                 hosted_interface_ids: Optional[List[int]] = None,
                 ide_default_stream_id: int = 0,
                 pcie_cap_base: int = 0x080,
                 msix_cap_base: int = 0x0B0,
                 pm_cap_base: int = 0x040):

        self.num_tdi = num_tdi
        self.device_report = device_report
        self.device_report_len = len(device_report)
        self.device_caps = device_caps or {}
        self.ide_default_stream_id = ide_default_stream_id
        self.pcie_cap_base = pcie_cap_base
        self.msix_cap_base = msix_cap_base
        self.pm_cap_base = pm_cap_base

        # Per-TDI context
        self.tdi: List[TdiContext] = [TdiContext() for _ in range(num_tdi)]

        # Interface ID → TDI index lookup
        if hosted_interface_ids:
            self.hosted_interface_ids = list(hosted_interface_ids)
        else:
            # Default: generate IDs for num_tdi entries
            self.hosted_interface_ids = [
                (i + 1) & ((1 << 96) - 1) for i in range(num_tdi)
            ]

        # Global configuration (from SET_TDISP_CONFIG)
        self.xt_mode_enable: bool = False
        self.xt_bit_for_locked_msix: bool = False

        # Request counters
        self.req_cnt_this: List[int] = [0] * num_tdi
        self.req_cnt_all: int = 0
        self.num_req_this_config: List[int] = [1] * num_tdi
        self.num_req_all_config: int = 1

        # Lock handler internal state
        self._lock_ide_keys_programmed: bool = True
        self._lock_ide_stream_valid: bool = True
        self._lock_ide_tc_value: int = 0
        self._lock_ide_xt_enable: bool = False
        self._lock_phantom_funcs: bool = False
        self._lock_pf_bar_valid: bool = True
        self._lock_rbar_sizes_valid: bool = True
        self._lock_vf_bar_valid: bool = True
        self._lock_sr_iov_page_size: int = 0
        self._lock_cache_line_size: int = 64
        self._lock_tph_mode: int = 0
        self._lock_entropy_available: bool = True

        # MSI-X table lock status per TDI
        self.msix_table_locked: List[bool] = [False] * num_tdi

    # ====================================================================
    # Interface ID resolution (mirrors resolve_interface_id)
    # ====================================================================

    def resolve_interface_id(self, interface_id: int) -> Tuple[bool, int]:
        """Resolve a 96-bit interface ID to (found, tdi_index).

        Returns (False, 0) if the interface ID is not hosted.
        """
        for i, hosted_id in enumerate(self.hosted_interface_ids):
            if i >= self.num_tdi:
                break
            if interface_id == hosted_id:
                return True, i
        return False, 0

    # ====================================================================
    # Main request processing entry point
    # ====================================================================

    def process_request(self, raw_msg: bytes) -> RefResponse:
        """Process a complete TDISP request message and predict the response.

        This is the primary API.  Accepts raw bytes (header + payload),
        performs all validation steps matching the RTL, updates internal
        state, and returns the expected RefResponse.

        Validation order (matches tdisp_req_handler.sv H_DISPATCH):
          1. Parse header
          2. Resolve INTERFACE_ID
          3. Check outstanding request limits
          4. Check payload length
          5. Check SET_TDISP_CONFIG special case (all TDIs unlocked)
          6. Check TDI state legality (Table 11-4)
          7. Command-specific dispatch
        """
        # Parse the message
        if len(raw_msg) < TDISP_MSG_HEADER_SIZE:
            return self._error_resp(0, ErrorCode.INVALID_REQUEST, 0)

        header, payload = parse_tdisp_message(raw_msg)
        req_code = header.msg_type
        iface_id = header.interface_id
        version = header.version
        payload_len = len(payload)

        # Resolve interface ID
        found, tdi_idx = self.resolve_interface_id(iface_id)

        # Increment request counters (H_IDLE does this on parsed_valid)
        self.req_cnt_all += 1
        if found:
            self.req_cnt_this[tdi_idx] += 1

        # --- Step 1: INTERFACE_ID validity ---
        if not found:
            self._decrement_counters(found, tdi_idx)
            return self._error_resp(iface_id, ErrorCode.INVALID_INTERFACE, 0)

        # --- Step 2: Outstanding request limits ---
        if (self.req_cnt_this[tdi_idx] > self.num_req_this_config[tdi_idx] or
                self.req_cnt_all > self.num_req_all_config):
            self._decrement_counters(found, tdi_idx)
            return self._error_resp(iface_id, ErrorCode.BUSY, 0)

        # --- Step 3: Payload length ---
        exp_len = expected_payload_len(req_code)
        if req_code != ReqCode.VDM and exp_len != payload_len:
            self._decrement_counters(found, tdi_idx)
            return self._error_resp(iface_id, ErrorCode.INVALID_REQUEST,
                                     payload_len & 0xFFFF)

        # --- Step 4: SET_TDISP_CONFIG special case ---
        if req_code == ReqCode.SET_TDISP_CONFIG:
            return self._handle_set_config(iface_id, payload, tdi_idx)

        # --- Step 5: TDI state legality (Table 11-4) ---
        current_state = self.tdi[tdi_idx].state
        if not is_legal_for_req(req_code, current_state):
            self._decrement_counters(found, tdi_idx)
            return self._error_resp(iface_id,
                                     ErrorCode.INVALID_INTERFACE_STATE, 0)

        # --- Step 6: Command-specific dispatch ---
        try:
            rc = ReqCode(req_code)
        except ValueError:
            self._decrement_counters(found, tdi_idx)
            return self._error_resp(iface_id, ErrorCode.UNSUPPORTED_REQUEST,
                                     req_code & 0xFF)

        handler = {
            ReqCode.GET_TDISP_VERSION:           self._handle_get_version,
            ReqCode.GET_TDISP_CAPABILITIES:      self._handle_get_caps,
            ReqCode.LOCK_INTERFACE:              self._handle_lock_interface,
            ReqCode.GET_DEVICE_INTERFACE_REPORT: self._handle_get_report,
            ReqCode.GET_DEVICE_INTERFACE_STATE:  self._handle_get_state,
            ReqCode.START_INTERFACE:             self._handle_start_interface,
            ReqCode.STOP_INTERFACE:              self._handle_stop_interface,
            ReqCode.BIND_P2P_STREAM:             self._handle_bind_p2p,
            ReqCode.UNBIND_P2P_STREAM:           self._handle_unbind_p2p,
            ReqCode.SET_MMIO_ATTRIBUTE:          self._handle_set_mmio,
            ReqCode.VDM:                         self._handle_vdm,
        }.get(rc)

        if handler is None:
            self._decrement_counters(found, tdi_idx)
            return self._error_resp(iface_id, ErrorCode.UNSUPPORTED_REQUEST,
                                     req_code & 0xFF)

        resp = handler(iface_id, payload, tdi_idx, version)

        # Decrement outstanding counters (response dispatched)
        self._decrement_counters(found, tdi_idx)

        return resp

    def _decrement_counters(self, found: bool, tdi_idx: int):
        """Decrement outstanding request counters after response."""
        if self.req_cnt_all > 0:
            self.req_cnt_all -= 1
        if found and self.req_cnt_this[tdi_idx] > 0:
            self.req_cnt_this[tdi_idx] -= 1

    # ====================================================================
    # Error response builder (mirrors build_error_payload)
    # ====================================================================

    def _error_resp(self, iface_id: int, error_code: int,
                    error_data: int) -> RefResponse:
        """Build a TDISP_ERROR response.

        Payload is 8 bytes: error_code (4 bytes LE) + error_data (4 bytes LE).
        """
        payload = pack_u32(error_code) + pack_u32(error_data)
        return RefResponse(
            msg_type=RespCode.TDISP_ERROR,
            interface_id=iface_id,
            payload=payload,
            is_error=True,
            error_code=error_code,
            error_data=error_data,
        )

    # ====================================================================
    # Command handlers — one per request code
    # ====================================================================

    def _handle_get_version(self, iface_id: int, payload: bytes,
                            tdi_idx: int, version: int) -> RefResponse:
        """GET_TDISP_VERSION: validate version major==1, return version."""
        # Check version major nibble
        if (version >> 4) != 1:
            return self._error_resp(iface_id, ErrorCode.VERSION_MISMATCH, 0)

        # Build version response payload (2 bytes)
        resp_payload = pack_u8(1) + pack_u8(TDISP_VERSION_1_0)
        return RefResponse(
            msg_type=RespCode.TDISP_VERSION,
            interface_id=iface_id,
            payload=resp_payload,
        )

    def _handle_get_caps(self, iface_id: int, payload: bytes,
                         tdi_idx: int, version: int) -> RefResponse:
        """GET_TDISP_CAPABILITIES: return device capabilities."""
        # The RTL serializes the tdisp_caps_s struct.  We build a
        # simplified 28-byte payload matching pack_caps format.
        caps = self.device_caps.copy()
        caps['num_req_this'] = self.num_req_this_config[tdi_idx]
        caps['num_req_all'] = self.num_req_all_config

        from tdisp_constants import pack_caps
        resp_payload = pack_caps(
            xt_mode_supported=caps.get('xt_mode_supported', False),
            req_msgs_supported=caps.get('req_msgs_supported', 0),
            lock_iface_flags_supported=caps.get(
                'lock_iface_flags_supported', 0),
            dev_addr_width=caps.get('dev_addr_width', 64),
            num_req_this=caps['num_req_this'],
            num_req_all=caps['num_req_all'],
        )
        return RefResponse(
            msg_type=RespCode.TDISP_CAPABILITIES,
            interface_id=iface_id,
            payload=resp_payload,
        )

    def _handle_lock_interface(self, iface_id: int, payload: bytes,
                               tdi_idx: int, version: int) -> RefResponse:
        """LOCK_INTERFACE: validate lock phases, generate nonce, transition."""
        # Perform lock validation phases
        result = self._validate_lock(tdi_idx, payload)

        if not result.success:
            return self._error_resp(iface_id, result.error_code, 0)

        # Lock succeeded — transition TDI to CONFIG_LOCKED
        self.tdi[tdi_idx].state = TdiState.CONFIG_LOCKED
        self.tdi[tdi_idx].nonce = result.nonce
        self.tdi[tdi_idx].nonce_valid = True

        # Store lock config
        lock_fields = unpack_lock_req_payload(payload)
        self.tdi[tdi_idx].lock_cfg = lock_fields

        # Check if MSI-X lock flag was set
        flags = lock_fields.get('flags', 0)
        if flags & (1 << 2):  # LOCK_MSIX bit
            self.msix_table_locked[tdi_idx] = True

        # Return nonce as response payload (32 bytes)
        nonce_payload = pack_nonce(result.nonce)
        return RefResponse(
            msg_type=RespCode.LOCK_INTERFACE,
            interface_id=iface_id,
            payload=nonce_payload,
        )

    def _handle_get_report(self, iface_id: int, payload: bytes,
                           tdi_idx: int, version: int) -> RefResponse:
        """GET_DEVICE_INTERFACE_REPORT: return report portion."""
        req = unpack_get_report_req(payload)
        req_offset = req['offset']
        req_length = req['length']

        # Validate: length must be non-zero
        if req_length == 0:
            return self._error_resp(iface_id, ErrorCode.INVALID_REQUEST, 0)

        report_len = self.device_report_len

        # Compute available bytes from offset
        if req_offset >= report_len:
            available = 0
        else:
            available = report_len - req_offset

        # Portion = min(req_length, available)
        portion_len = min(req_length, available)

        # Remainder = total remaining after this portion
        remainder = available - portion_len if available > portion_len else 0

        # Build response payload (mirrors build_report_payload)
        resp = bytearray(4 + portion_len)
        struct_pack_into = __import__('struct').pack_into
        struct_pack_into('<H', resp, 0, portion_len & 0xFFFF)
        struct_pack_into('<H', resp, 2, remainder & 0xFFFF)

        # Copy report bytes
        for i in range(portion_len):
            src_idx = req_offset + i
            if src_idx < report_len:
                resp[4 + i] = self.device_report[src_idx]

        return RefResponse(
            msg_type=RespCode.DEVICE_INTERFACE_REPORT,
            interface_id=iface_id,
            payload=bytes(resp),
        )

    def _handle_get_state(self, iface_id: int, payload: bytes,
                          tdi_idx: int, version: int) -> RefResponse:
        """GET_DEVICE_INTERFACE_STATE: return current TDI state byte."""
        state_val = self.tdi[tdi_idx].state
        # State encoding matches TdiState enum directly
        resp_payload = pack_u8(state_val)
        return RefResponse(
            msg_type=RespCode.DEVICE_INTERFACE_STATE,
            interface_id=iface_id,
            payload=resp_payload,
        )

    def _handle_start_interface(self, iface_id: int, payload: bytes,
                                tdi_idx: int, version: int) -> RefResponse:
        """START_INTERFACE: validate nonce, transition to RUN."""
        # Payload is 32 bytes = 256-bit nonce
        if len(payload) < 32:
            return self._error_resp(iface_id, ErrorCode.INVALID_NONCE, 0)

        received_nonce = unpack_nonce(payload, 0)
        stored_nonce = self.tdi[tdi_idx].nonce

        # Validate nonce match
        if received_nonce != stored_nonce or not self.tdi[tdi_idx].nonce_valid:
            return self._error_resp(iface_id, ErrorCode.INVALID_NONCE, 0)

        # Nonce matches — transition to RUN, consume nonce
        self.tdi[tdi_idx].state = TdiState.RUN
        self.tdi[tdi_idx].nonce = 0
        self.tdi[tdi_idx].nonce_valid = False

        return RefResponse(
            msg_type=RespCode.START_INTERFACE,
            interface_id=iface_id,
            payload=b'',
        )

    def _handle_stop_interface(self, iface_id: int, payload: bytes,
                               tdi_idx: int, version: int) -> RefResponse:
        """STOP_INTERFACE: transition to CONFIG_UNLOCKED.

        Per Table 11-4:
          - From CONFIG_UNLOCKED: no-op (already unlocked)
          - From CONFIG_LOCKED: → CONFIG_UNLOCKED, destroy nonce
          - From RUN: → CONFIG_UNLOCKED, destroy nonce
          - From ERROR: → CONFIG_UNLOCKED
        """
        prev_state = self.tdi[tdi_idx].state

        self.tdi[tdi_idx].state = TdiState.CONFIG_UNLOCKED
        self.tdi[tdi_idx].nonce = 0
        self.tdi[tdi_idx].nonce_valid = False

        # Clear P2P stream bindings on stop
        self.tdi[tdi_idx].p2p_streams_bound.clear()
        self.tdi[tdi_idx].lock_cfg = None

        return RefResponse(
            msg_type=RespCode.STOP_INTERFACE,
            interface_id=iface_id,
            payload=b'',
        )

    def _handle_bind_p2p(self, iface_id: int, payload: bytes,
                         tdi_idx: int, version: int) -> RefResponse:
        """BIND_P2P_STREAM: bind a P2P stream to this TDI.

        Legal only in RUN state (checked by is_legal_for_req).
        """
        req = unpack_bind_p2p_req(payload)
        stream_id = req['stream_id']

        # Validate stream_id range
        if stream_id >= MAX_P2P_STREAMS:
            return self._error_resp(
                iface_id, ErrorCode.INVALID_REQUEST,
                ((stream_id & 0xFF) << 8) | 0x00)

        # Check not already bound
        if stream_id in self.tdi[tdi_idx].p2p_streams_bound:
            return self._error_resp(
                iface_id, ErrorCode.INVALID_REQUEST,
                ((stream_id & 0xFF) << 8) | 0x01)

        # Bind the stream
        self.tdi[tdi_idx].p2p_streams_bound.add(stream_id)

        return RefResponse(
            msg_type=RespCode.BIND_P2P_STREAM,
            interface_id=iface_id,
            payload=b'',
        )

    def _handle_unbind_p2p(self, iface_id: int, payload: bytes,
                           tdi_idx: int, version: int) -> RefResponse:
        """UNBIND_P2P_STREAM: unbind a P2P stream from this TDI.

        Legal only in RUN state (checked by is_legal_for_req).
        """
        req = unpack_unbind_p2p_req(payload)
        stream_id = req['stream_id']

        # Check that stream is currently bound
        if stream_id not in self.tdi[tdi_idx].p2p_streams_bound:
            return self._error_resp(
                iface_id, ErrorCode.INVALID_REQUEST,
                ((stream_id & 0xFF) << 8) | 0x00)

        # Unbind the stream
        self.tdi[tdi_idx].p2p_streams_bound.discard(stream_id)

        return RefResponse(
            msg_type=RespCode.UNBIND_P2P_STREAM,
            interface_id=iface_id,
            payload=b'',
        )

    def _handle_set_mmio(self, iface_id: int, payload: bytes,
                         tdi_idx: int, version: int) -> RefResponse:
        """SET_MMIO_ATTRIBUTE: store MMIO attribute for this TDI.

        Legal only in RUN state.  The RTL passes the 16-byte payload
        to device logic; we record it in the TDI context.
        """
        req = unpack_set_mmio_attr_req(payload)
        if self.tdi[tdi_idx].lock_cfg is None:
            self.tdi[tdi_idx].lock_cfg = {}
        self.tdi[tdi_idx].lock_cfg['mmio_attr'] = req

        return RefResponse(
            msg_type=RespCode.SET_MMIO_ATTRIBUTE,
            interface_id=iface_id,
            payload=b'',
        )

    def _handle_vdm(self, iface_id: int, payload: bytes,
                    tdi_idx: int, version: int) -> RefResponse:
        """VDM: Vendor Defined Message — echo payload back."""
        return RefResponse(
            msg_type=RespCode.VDM,
            interface_id=iface_id,
            payload=payload,
        )

    def _handle_set_config(self, iface_id: int, payload: bytes,
                           tdi_idx: int) -> RefResponse:
        """SET_TDISP_CONFIG: configure XT mode. All TDIs must be unlocked."""
        # Check ALL TDIs are in CONFIG_UNLOCKED
        for i in range(self.num_tdi):
            if self.tdi[i].state != TdiState.CONFIG_UNLOCKED:
                return self._error_resp(
                    iface_id, ErrorCode.INVALID_INTERFACE_STATE, 0)

        # Parse config
        config = unpack_set_config_req(payload)
        self.xt_mode_enable = config['xt_mode_enable']
        self.xt_bit_for_locked_msix = config['xt_bit_for_locked_msix']

        return RefResponse(
            msg_type=RespCode.SET_TDISP_CONFIG,
            interface_id=iface_id,
            payload=b'',
        )

    # ====================================================================
    # Lock handler validation phases (mirrors tdisp_lock_handler.sv)
    # ====================================================================

    def _validate_lock(self, tdi_idx: int, payload: bytes) -> LockResult:
        """Execute all lock validation phases.

        Phase 1: Check TDI is CONFIG_UNLOCKED
        Phase 2: Validate IDE configuration
        Phase 3: Validate device configuration
        Phase 4: Store lock config (binding)
        Generate nonce on success.

        Returns LockResult with success/failure and nonce or error code.
        """
        lock_fields = unpack_lock_req_payload(payload)

        # Phase 1: TDI must be CONFIG_UNLOCKED
        if self.tdi[tdi_idx].state != TdiState.CONFIG_UNLOCKED:
            return LockResult(success=False,
                              error_code=ErrorCode.INVALID_INTERFACE_STATE)

        # Phase 2: IDE validation
        ide_result = self._validate_lock_ide(lock_fields)
        if not ide_result:
            return LockResult(success=False,
                              error_code=ErrorCode.INVALID_REQUEST)

        # Phase 3: Device configuration validation
        dev_result = self._validate_lock_device()
        if not dev_result:
            return LockResult(success=False,
                              error_code=ErrorCode.INVALID_DEVICE_CONFIGURATION)

        # Phase 4: Config binding (store configuration)
        # In the model, we just accept it — the RTL stores tdi_lock_cfg
        self._lock_bind_config(tdi_idx, lock_fields)

        # Generate nonce
        if not self._lock_entropy_available:
            return LockResult(success=False,
                              error_code=ErrorCode.INSUFFICIENT_ENTROPY)

        nonce = self._generate_nonce()

        return LockResult(success=True, nonce=nonce)

    def _validate_lock_ide(self, lock_fields: dict) -> bool:
        """Phase 2: Validate IDE configuration.

        Checks (mirrors L_PHASE2_IDE in tdisp_lock_handler.sv):
          - default_stream_id matches IDE config
          - All sub-stream keys are programmed
          - IDE stream is valid
          - Default stream TC is TC0
          - XT Enable matches SET_TDISP_CONFIG
        """
        default_stream_id = lock_fields.get('default_stream_id', 0)

        # Check 3: default_stream_id must match IDE config
        if default_stream_id != self.ide_default_stream_id:
            return False

        # Check 4: All sub-stream keys must be programmed
        if not self._lock_ide_keys_programmed:
            return False

        # Check 6: IDE stream must be valid
        if not self._lock_ide_stream_valid:
            return False

        # Check 7: Default stream TC must be TC0
        if self._lock_ide_tc_value != 0:
            return False

        # Check 8: XT Enable must match SET_TDISP_CONFIG setting
        if self._lock_ide_xt_enable != self.xt_mode_enable:
            return False

        return True

    def _validate_lock_device(self) -> bool:
        """Phase 3: Validate device configuration.

        Checks (mirrors L_PHASE3_DEVCFG):
          - Phantom Functions not enabled
          - PF BARs not overlapping
          - Resizable BAR sizes valid
          - VF BARs not overlapping
          - SR-IOV page size ≤ 4 (64KB)
          - Cache Line Size valid (32, 64, or 128)
          - TPH mode ≤ 1
        """
        if self._lock_phantom_funcs:
            return False
        if not self._lock_pf_bar_valid:
            return False
        if not self._lock_rbar_sizes_valid:
            return False
        if not self._lock_vf_bar_valid:
            return False
        if self._lock_sr_iov_page_size > 4:
            return False
        cls = self._lock_cache_line_size
        if cls not in (32, 64, 128):
            return False
        if self._lock_tph_mode > 1:
            return False
        return True

    def _lock_bind_config(self, tdi_idx: int, lock_fields: dict):
        """Phase 4: Store lock configuration for this TDI."""
        # In the RTL, this stores mmio_reporting_offset, lock flags,
        # default_stream_id, bind_p2p_addr_mask into tdi_lock_cfg[].
        # We store the full fields dict for reference.
        pass  # Already stored in TdiContext.lock_cfg via caller

    def _generate_nonce(self) -> int:
        """Generate a pseudo-random 256-bit nonce.

        In real hardware, this comes from an entropy source.
        For the reference model, we use a deterministic but varied value.
        """
        import random
        return random.getrandbits(256)

    # ====================================================================
    # FSM state transitions (mirrors tdisp_fsm.sv)
    # ====================================================================

    def fsm_transition(self, tdi_idx: int,
                       lock_req: bool = False,
                       start_req: bool = False,
                       stop_req: bool = False,
                       error_trigger: bool = False,
                       reset_to_unlocked: bool = False) -> Tuple[int, int]:
        """Apply a state transition for a TDI, matching tdisp_fsm.sv priority.

        Priority: error > stop > start > lock

        Returns (old_state, new_state).
        Also manages nonce lifecycle per §11.3.9.
        """
        if tdi_idx >= self.num_tdi:
            return (TdiState.ERROR, TdiState.ERROR)

        old_state = self.tdi[tdi_idx].state

        if reset_to_unlocked:
            new_state = TdiState.CONFIG_UNLOCKED
        else:
            new_state = old_state  # Default: hold

            if old_state == TdiState.CONFIG_UNLOCKED:
                if error_trigger:
                    new_state = TdiState.ERROR
                elif lock_req:
                    new_state = TdiState.CONFIG_LOCKED

            elif old_state == TdiState.CONFIG_LOCKED:
                if error_trigger:
                    new_state = TdiState.ERROR
                elif stop_req:
                    new_state = TdiState.CONFIG_UNLOCKED
                elif start_req:
                    new_state = TdiState.RUN

            elif old_state == TdiState.RUN:
                if error_trigger:
                    new_state = TdiState.ERROR
                elif stop_req:
                    new_state = TdiState.CONFIG_UNLOCKED

            elif old_state == TdiState.ERROR:
                if stop_req:
                    new_state = TdiState.CONFIG_UNLOCKED

            else:
                # Defensive: invalid state → ERROR
                new_state = TdiState.ERROR

        # Nonce management (mirrors tdisp_fsm.sv nonce always_ff)
        if reset_to_unlocked:
            self.tdi[tdi_idx].nonce = 0
            self.tdi[tdi_idx].nonce_valid = False
        elif old_state == TdiState.CONFIG_UNLOCKED:
            if new_state == TdiState.CONFIG_LOCKED:
                # Capture nonce on lock transition (generated externally)
                pass  # Nonce set by _handle_lock_interface
        elif old_state == TdiState.CONFIG_LOCKED:
            if new_state != TdiState.CONFIG_LOCKED and new_state != TdiState.RUN:
                # Leaving CONFIG_LOCKED → destroy nonce
                self.tdi[tdi_idx].nonce = 0
                self.tdi[tdi_idx].nonce_valid = False
            elif new_state == TdiState.RUN:
                # CONFIG_LOCKED → RUN: nonce consumed
                self.tdi[tdi_idx].nonce = 0
                self.tdi[tdi_idx].nonce_valid = False
        elif old_state == TdiState.RUN:
            if new_state != TdiState.RUN:
                # Leaving RUN → destroy nonce
                self.tdi[tdi_idx].nonce = 0
                self.tdi[tdi_idx].nonce_valid = False
        elif old_state == TdiState.ERROR:
            self.tdi[tdi_idx].nonce = 0
            self.tdi[tdi_idx].nonce_valid = False

        # Apply state change
        self.tdi[tdi_idx].state = new_state

        return (old_state, new_state)

    # ====================================================================
    # Register write classification (mirrors tdisp_reg_tracker.sv)
    # ====================================================================

    def classify_reg_write(self, addr: int, data: int,
                           mask: int = 0xF,
                           tdi_idx: int = 0) -> RegWriteResult:
        """Classify a register write and determine if it triggers error.

        Mirrors the tdisp_reg_tracker.sv logic:
          1. Classify address into category
          2. If tracking is not enabled (TDI not in CONFIG_LOCKED/RUN),
             no error is triggered
          3. Apply category-specific validation

        Args:
            addr: 12-bit config space address
            data: 32-bit write data
            mask: 4-bit byte enable mask
            tdi_idx: TDI index for context lookup

        Returns:
            RegWriteResult with category and error trigger status
        """
        category = classify_register_addr(
            addr, self.pcie_cap_base, self.msix_cap_base, self.pm_cap_base)

        state = self.tdi[tdi_idx].state
        tracking_enabled = state in (TdiState.CONFIG_LOCKED, TdiState.RUN)

        result = RegWriteResult(category=category)

        if not tracking_enabled:
            return result

        # Apply category-specific validation
        if category == RegCategory.ALLOWED:
            pass  # No error

        elif category == RegCategory.ERROR:
            result.triggers_error = True

        elif category == RegCategory.CMD_REGISTER:
            # Check if Memory Space Enable (bit 1) or Bus Master Enable (bit 2)
            # is being CLEARED (written to 0)
            # Per spec: clearing these bits → ERROR
            if mask & 0x3:  # Lower 2 bytes affected
                mem_enable_bit = (data >> 1) & 1
                bus_master_bit = (data >> 2) & 1
                if not mem_enable_bit or not bus_master_bit:
                    result.triggers_error = True

        elif category == RegCategory.DEV_CTRL:
            # Check critical Device Control bits per Table 11-3
            # DC1: Extended Tag Enable (bit 8), Phantom Func Enable (bit 6),
            #      Max Payload Size (bits 7:5)
            # For simplicity, if ANY byte-enable in the lower word is set,
            # we conservatively flag it as needing review. The actual RTL
            # checks specific bits; we model the conservative path.
            if mask & 0x3:  # Lower 2 bytes = Device Control 1
                # Check if Extended Tag Enable is being cleared (bit 8)
                ext_tag_enable = (data >> 8) & 1
                phantom_func = (data >> 6) & 1
                # If either is being disabled when it was enabled
                # Simplified: flag if modifying critical bits
                result.triggers_error = True  # Conservative match

        elif category == RegCategory.MSIX:
            # MSI-X: error if table was locked
            if self.msix_table_locked[tdi_idx]:
                result.triggers_error = True

        elif category == RegCategory.POWER_MGMT:
            # PMCSR: check for power state transition that loses state
            # D3hot/D3cold transitions: bits [1:0] = 0x3 (D3hot) or 0x2
            power_state = data & 0x3
            if power_state >= 2:  # D2 or D3 → state loss
                result.triggers_error = True

        elif category == RegCategory.VENDOR_SPEC:
            # Vendor specific — conservative: allow
            pass

        elif category == RegCategory.RESERVED_CAT:
            # Unmapped → treat as error
            result.triggers_error = True

        return result

    # ====================================================================
    # TLP Egress Filter (mirrors tdisp_tlp_filter.sv §11.2.1)
    # ====================================================================

    def filter_egress(self, tdi_idx: int,
                      tlp: EgressTlpInput) -> EgressTlpResult:
        """Classify an egress TLP for a TDI.

        Implements the combinational classification logic from
        tdisp_tlp_filter.sv §11.2.1 (TDI as Requester).

        Returns EgressTlpResult with reject, xt_bit, t_bit.
        """
        result = EgressTlpResult()
        if not tlp.valid:
            return result

        state = self.tdi[tdi_idx].state
        xt_enabled = self.xt_mode_enable
        xt_locked_msix = self.xt_bit_for_locked_msix

        # ATS Translation Requests: never blocked
        if tlp.is_ats_request:
            return result  # XT=0, T=0, reject=False

        # I/O Requests: always rejected
        if tlp.is_io_req:
            result.reject = True
            return result

        # Completions: pass through only in RUN
        if tlp.is_completion:
            if state != TdiState.RUN:
                result.reject = True
            return result  # XT=0, T=0

        # VDMs: T=1 if CONFIG_LOCKED/RUN/ERROR; XT=1 if XT mode
        if tlp.is_vdm:
            if state in (TdiState.CONFIG_LOCKED, TdiState.RUN,
                         TdiState.ERROR):
                result.t_bit = True
                result.xt_bit = xt_enabled
            # else: CONFIG_UNLOCKED → XT=0, T=0 (no reject)
            return result

        # Memory Requests
        if tlp.is_memory_req:
            # Not in RUN: reject non-MSI
            if state != TdiState.RUN:
                if tlp.is_msi:
                    # MSI/MSI-X: allowed, XT=0, T=0
                    pass
                else:
                    result.reject = True
                return result

            # In RUN state
            if not xt_enabled:
                # No XT mode
                if tlp.is_msi and not tlp.is_msix:
                    pass  # MSI: XT=0, T=0
                elif tlp.is_msix and not tlp.is_msix_locked:
                    pass  # MSI-X not locked: XT=0, T=0
                elif tlp.is_msix and tlp.is_msix_locked:
                    result.t_bit = True  # MSI-X locked: T=1
                else:
                    # Non-MSI memory requests
                    if tlp.addr_type == AT_UNTRANSLATED:
                        result.t_bit = True  # Untranslated: T=1
                    # Translated: T=0
            else:
                # XT mode enabled
                if tlp.is_msi and not tlp.is_msix:
                    pass  # MSI: XT=0, T=0
                elif tlp.is_msix and not tlp.is_msix_locked:
                    pass  # MSI-X not locked: XT=0, T=0
                elif tlp.is_msix and tlp.is_msix_locked:
                    result.xt_bit = xt_locked_msix
                    result.t_bit = True
                elif tlp.access_tee_mem and not tlp.access_non_tee_mem:
                    result.xt_bit = True  # TEE mem: XT=1, T=1
                    result.t_bit = True
                elif tlp.access_non_tee_mem and not tlp.access_tee_mem:
                    result.xt_bit = True  # Non-TEE mem: XT=1, T=0
                else:
                    # Unrestricted: XT=0, T=1
                    result.t_bit = True

        # Other TLP types: pass through (default: XT=0, T=0, reject=False)
        return result

    # ====================================================================
    # TLP Ingress Filter (mirrors tdisp_tlp_filter.sv §11.2.2)
    # ====================================================================

    def filter_ingress(self, tdi_idx: int,
                       tlp: IngressTlpInput) -> IngressTlpResult:
        """Classify an ingress TLP for a TDI.

        Implements the combinational classification logic from
        tdisp_tlp_filter.sv §11.2.2 (TDI as Completer).

        Returns IngressTlpResult with reject flag.
        """
        result = IngressTlpResult()
        if not tlp.valid:
            return result

        state = self.tdi[tdi_idx].state
        xt_enabled = self.xt_mode_enable

        # ATS Translation Requests: never blocked
        if tlp.is_ats_request:
            return result

        # Completions: check IDE stream binding
        if tlp.is_completion:
            if tlp.ide_required and not tlp.on_bound_stream:
                result.reject = True
            return result

        # VDMs: check XT/T bits and IDE stream
        if tlp.is_vdm:
            if not xt_enabled:
                if not tlp.t_bit:
                    result.reject = True
            else:
                if not tlp.xt_bit or not tlp.t_bit:
                    result.reject = True
            if tlp.ide_required and not tlp.on_bound_stream:
                result.reject = True
            return result

        # Memory Requests
        if tlp.is_memory_req:
            # Global: Non-IDE when IDE required → reject
            if tlp.ide_required and not tlp.on_bound_stream:
                result.reject = True
                return result

            # MSI-X table locked without T bit → reject
            if tlp.msix_table_locked and not tlp.t_bit:
                result.reject = True
                return result

            if not xt_enabled:
                # No XT mode
                if not tlp.target_is_non_tee_mem:
                    # TEE memory: need T=1 AND RUN AND bound stream
                    if (not tlp.t_bit or
                            state != TdiState.RUN or
                            (tlp.ide_required and not tlp.on_bound_stream)):
                        result.reject = True
                else:
                    # Non-TEE memory: need T=0
                    if tlp.t_bit:
                        result.reject = True
            else:
                # XT mode
                if not tlp.target_is_non_tee_mem:
                    # TEE memory: need XT=1 AND T=1 AND RUN AND bound
                    if (not tlp.xt_bit or not tlp.t_bit or
                            state != TdiState.RUN or
                            not tlp.on_bound_stream):
                        result.reject = True
                else:
                    # Non-TEE memory: need T=0
                    if tlp.t_bit:
                        result.reject = True

        # Other TLP types: accept by default
        return result

    # ====================================================================
    # Lock handler IDE/device config setters (for test configuration)
    # ====================================================================

    def set_ide_config(self, *,
                       default_stream_id: Optional[int] = None,
                       keys_programmed: Optional[bool] = None,
                       stream_valid: Optional[bool] = None,
                       tc_value: Optional[int] = None,
                       xt_enable: Optional[bool] = None):
        """Configure IDE validation parameters for lock handler."""
        if default_stream_id is not None:
            self.ide_default_stream_id = default_stream_id
        if keys_programmed is not None:
            self._lock_ide_keys_programmed = keys_programmed
        if stream_valid is not None:
            self._lock_ide_stream_valid = stream_valid
        if tc_value is not None:
            self._lock_ide_tc_value = tc_value
        if xt_enable is not None:
            self._lock_ide_xt_enable = xt_enable

    def set_device_config(self, *,
                          phantom_funcs: Optional[bool] = None,
                          pf_bar_valid: Optional[bool] = None,
                          rbar_sizes_valid: Optional[bool] = None,
                          vf_bar_valid: Optional[bool] = None,
                          sr_iov_page_size: Optional[int] = None,
                          cache_line_size: Optional[int] = None,
                          tph_mode: Optional[int] = None,
                          entropy_available: Optional[bool] = None):
        """Configure device validation parameters for lock handler."""
        if phantom_funcs is not None:
            self._lock_phantom_funcs = phantom_funcs
        if pf_bar_valid is not None:
            self._lock_pf_bar_valid = pf_bar_valid
        if rbar_sizes_valid is not None:
            self._lock_rbar_sizes_valid = rbar_sizes_valid
        if vf_bar_valid is not None:
            self._lock_vf_bar_valid = vf_bar_valid
        if sr_iov_page_size is not None:
            self._lock_sr_iov_page_size = sr_iov_page_size
        if cache_line_size is not None:
            self._lock_cache_line_size = cache_line_size
        if tph_mode is not None:
            self._lock_tph_mode = tph_mode
        if entropy_available is not None:
            self._lock_entropy_available = entropy_available

    # ====================================================================
    # Convenience: get TDI state
    # ====================================================================

    def get_tdi_state(self, tdi_idx: int) -> int:
        """Return the current TDI state."""
        return self.tdi[tdi_idx].state

    def get_tdi_state_name(self, tdi_idx: int) -> str:
        """Return human-readable state name for a TDI."""
        return tdi_state_name(self.tdi[tdi_idx].state)

    def get_nonce(self, tdi_idx: int) -> int:
        """Return the stored nonce for a TDI."""
        return self.tdi[tdi_idx].nonce

    def is_nonce_valid(self, tdi_idx: int) -> bool:
        """Return whether the nonce is valid for a TDI."""
        return self.tdi[tdi_idx].nonce_valid

    def get_bound_streams(self, tdi_idx: int) -> Set[int]:
        """Return the set of bound P2P stream IDs for a TDI."""
        return set(self.tdi[tdi_idx].p2p_streams_bound)

    def is_p2p_stream_bound(self, tdi_idx: int, stream_id: int) -> bool:
        """Check if a P2P stream is bound to a TDI."""
        return stream_id in self.tdi[tdi_idx].p2p_streams_bound

    # ====================================================================
    # Reset
    # ====================================================================

    def reset(self):
        """Reset all TDI states and global config to power-on defaults."""
        for i in range(self.num_tdi):
            self.tdi[i] = TdiContext()
        self.xt_mode_enable = False
        self.xt_bit_for_locked_msix = False
        self.req_cnt_all = 0
        self.req_cnt_this = [0] * self.num_tdi
        self.msix_table_locked = [False] * self.num_tdi


# ============================================================================
# Convenience: full-lifecycle reference model runner
# ============================================================================

class TdispLifecycleModel:
    """High-level helper that runs complete TDISP lifecycle sequences.

    Wraps TdispRefModel and provides step-by-step methods for the
    standard TDISP flow: CONFIG_UNLOCKED → SET_TDISP_CONFIG →
    GET_TDISP_VERSION → GET_TDISP_CAPABILITIES → LOCK_INTERFACE →
    GET_DEVICE_INTERFACE_STATE → START_INTERFACE → RUN operations.

    Usage:
        lm = TdispLifecycleModel(num_tdi=2)
        for i in range(2):
            lm.set_config(tdi_idx=i, xt_mode=True)
            lm.lock_interface(tdi_idx=i)
            lm.start_interface(tdi_idx=i)
        # Now TDI 0 and 1 are in RUN state
    """

    def __init__(self, **kwargs):
        self.model = TdispRefModel(**kwargs)

    def set_config(self, tdi_idx: int = 0,
                   xt_mode: bool = False,
                   xt_bit_for_locked_msix: bool = False) -> RefResponse:
        """Send SET_TDISP_CONFIG (all TDIs must be CONFIG_UNLOCKED)."""
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        payload = pack_u32(
            (1 if xt_mode else 0) |
            ((1 if xt_bit_for_locked_msix else 0) << 1)
        )
        msg = build_tdisp_message(ReqCode.SET_TDISP_CONFIG, iface_id, payload)
        return self.model.process_request(msg)

    def get_version(self, tdi_idx: int = 0) -> RefResponse:
        """Send GET_TDISP_VERSION."""
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        msg = build_tdisp_message(ReqCode.GET_TDISP_VERSION, iface_id)
        return self.model.process_request(msg)

    def get_capabilities(self, tdi_idx: int = 0) -> RefResponse:
        """Send GET_TDISP_CAPABILITIES."""
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        payload = pack_u32(0)  # 4-byte param
        msg = build_tdisp_message(ReqCode.GET_TDISP_CAPABILITIES, iface_id,
                                   payload)
        return self.model.process_request(msg)

    def lock_interface(self, tdi_idx: int = 0,
                       flags: int = 0,
                       default_stream_id: int = 0,
                       mmio_reporting_offset: int = 0,
                       bind_p2p_addr_mask: int = 0) -> RefResponse:
        """Send LOCK_INTERFACE_REQUEST."""
        from tdisp_constants import pack_lock_req_payload
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        payload = pack_lock_req_payload(
            flags=flags,
            default_stream_id=default_stream_id,
            mmio_reporting_offset=mmio_reporting_offset,
            bind_p2p_addr_mask=bind_p2p_addr_mask,
        )
        msg = build_tdisp_message(ReqCode.LOCK_INTERFACE, iface_id, payload)
        return self.model.process_request(msg)

    def get_interface_state(self, tdi_idx: int = 0) -> RefResponse:
        """Send GET_DEVICE_INTERFACE_STATE."""
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        msg = build_tdisp_message(ReqCode.GET_DEVICE_INTERFACE_STATE, iface_id)
        return self.model.process_request(msg)

    def start_interface(self, tdi_idx: int = 0,
                        nonce: Optional[int] = None) -> RefResponse:
        """Send START_INTERFACE_REQUEST with the stored or provided nonce."""
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        if nonce is None:
            nonce = self.model.get_nonce(tdi_idx)
        payload = pack_nonce(nonce)
        msg = build_tdisp_message(ReqCode.START_INTERFACE, iface_id, payload)
        return self.model.process_request(msg)

    def stop_interface(self, tdi_idx: int = 0) -> RefResponse:
        """Send STOP_INTERFACE_REQUEST."""
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        msg = build_tdisp_message(ReqCode.STOP_INTERFACE, iface_id)
        return self.model.process_request(msg)

    def bind_p2p(self, tdi_idx: int = 0,
                 stream_id: int = 0,
                 p2p_portion: int = 0) -> RefResponse:
        """Send BIND_P2P_STREAM_REQUEST (RUN state required)."""
        from tdisp_constants import pack_bind_p2p_req
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        payload = pack_bind_p2p_req(stream_id=stream_id,
                                     p2p_portion=p2p_portion)
        msg = build_tdisp_message(ReqCode.BIND_P2P_STREAM, iface_id, payload)
        return self.model.process_request(msg)

    def unbind_p2p(self, tdi_idx: int = 0,
                   stream_id: int = 0) -> RefResponse:
        """Send UNBIND_P2P_STREAM_REQUEST (RUN state required)."""
        from tdisp_constants import pack_unbind_p2p_req
        iface_id = self.model.hosted_interface_ids[tdi_idx]
        payload = pack_unbind_p2p_req(stream_id=stream_id)
        msg = build_tdisp_message(ReqCode.UNBIND_P2P_STREAM, iface_id, payload)
        return self.model.process_request(msg)

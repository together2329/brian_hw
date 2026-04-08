"""Reference model for the TDISP DSM (TEE Device Interface Security Protocol
Device Security Manager) responder.

Cycle-accurate golden model matching tdisp_dsm.v RTL behavior exactly:
  - LFSR nonce generation (same polynomial)
  - TDI state machine (CONFIG_UNLOCKED → CONFIG_LOCKED → RUN)
  - Word-by-word request parsing with NBA timing
  - Combinational response data mux
  - Ready/valid handshake protocol

Usage:
    model = TdispDsmRefModel(
        configured_interface_id=0x00_00_00_00_00_00_00_00_00_00_00_01,
        ide_required=False,
        default_stream_id=0x00,
    )
    model.reset()
    resp = model.send_request_word(req_data=0x000081_10, req_valid=1)
    # ... or use send_request() for complete multi-word request
"""

# =====================================================================
# Constants — match RTL localparams
# =====================================================================

# TDI State Encoding (per RTL §11.3.13)
STATE_CONFIG_UNLOCKED = 0
STATE_CONFIG_LOCKED   = 1
STATE_RUN             = 2
STATE_ERROR           = 3

# TDISP Request Codes
REQ_GET_TDISP_VERSION          = 0x81
REQ_GET_TDISP_CAPABILITIES     = 0x82
REQ_LOCK_INTERFACE             = 0x83
REQ_GET_DEVICE_INTERFACE_REPORT = 0x84
REQ_GET_DEVICE_INTERFACE_STATE = 0x85
REQ_START_INTERFACE            = 0x86
REQ_STOP_INTERFACE             = 0x87

# TDISP Response Codes
RESP_TDISP_VERSION             = 0x01
RESP_TDISP_CAPABILITIES        = 0x02
RESP_LOCK_INTERFACE            = 0x03
RESP_DEVICE_INTERFACE_REPORT   = 0x04
RESP_DEVICE_INTERFACE_STATE    = 0x05
RESP_START_INTERFACE           = 0x06
RESP_STOP_INTERFACE            = 0x07
RESP_TDISP_ERROR               = 0x7F

# TDISP Error Codes
ERR_INVALID_REQUEST            = 0x0001
ERR_BUSY                       = 0x0003
ERR_INVALID_INTERFACE_STATE    = 0x0004
ERR_UNSPECIFIED                = 0x0005
ERR_UNSUPPORTED_REQUEST        = 0x0007
ERR_VERSION_MISMATCH           = 0x0041
ERR_INVALID_INTERFACE          = 0x0101
ERR_INVALID_NONCE              = 0x0102
ERR_INSUFFICIENT_ENTROPY       = 0x0103
ERR_INVALID_DEVICE_CONFIGURATION = 0x0104

# Default parameter values
TDISP_VERSION = 0x10   # V1.0 = Major 1, Minor 0
DATA_WIDTH    = 32
NONCE_WIDTH   = 256
INTERFACE_ID_WIDTH = 96
ADDR_WIDTH    = 64


def mask(width: int) -> int:
    """Return a bitmask of given width."""
    return (1 << width) - 1


def _byte(val: int, idx: int) -> int:
    """Extract byte at index from a 32-bit word (little-endian)."""
    return (val >> (8 * idx)) & 0xFF


# =====================================================================
# LFSR Nonce Generator — matches RTL polynomial exactly
# =====================================================================

def lfsr_next(state: int, width: int = NONCE_WIDTH) -> int:
    """Advance the LFSR one step.

    RTL feedback:
        lfsr_feedback = {nonce_lfsr[NONCE_WIDTH-2:0],
                         nonce_lfsr[NONCE_WIDTH-1] ^ nonce_lfsr[NONCE_WIDTH-4] ^
                         nonce_lfsr[NONCE_WIDTH-9] ^ nonce_lfsr[NONCE_WIDTH-12]}

    This is a left-rotate by 1 with XOR tap injection at bit 0.
    """
    m = mask(width)
    bit_0 = ((state >> (width - 1)) ^ (state >> (width - 4)) ^
             (state >> (width - 9)) ^ (state >> (width - 12))) & 1
    return ((state << 1) | bit_0) & m


# =====================================================================
# TDISP DSM Reference Model
# =====================================================================

class TdispDsmRefModel:
    """Cycle-accurate golden reference model matching tdisp_dsm.v RTL.

    Call step() once per clock cycle.  The model evaluates registered
    assignments (non-blocking) exactly like Verilog NBA semantics:
    compute next values from current state, then latch simultaneously.

    For convenience, higher-level methods are provided:
      - send_request(words_list): feed a complete multi-word request
      - collect_response():      drain all response words
    """

    def __init__(
        self,
        configured_interface_id: int = 0,
        ide_required: bool = False,
        default_stream_id: int = 0x00,
        data_width: int = DATA_WIDTH,
        nonce_width: int = NONCE_WIDTH,
        interface_id_width: int = INTERFACE_ID_WIDTH,
        addr_width: int = ADDR_WIDTH,
        tdisp_version: int = TDISP_VERSION,
    ):
        self.DATA_WIDTH = data_width
        self.NONCE_WIDTH = nonce_width
        self.INTERFACE_ID_WIDTH = interface_id_width
        self.ADDR_WIDTH = addr_width
        self.TDISP_VERSION = tdisp_version

        # Configuration (static inputs)
        self.configured_interface_id = configured_interface_id & mask(interface_id_width)
        self.ide_required = ide_required
        self.default_stream_id = default_stream_id & 0xFF

        # ---- Registered state (mirrors RTL registers) ----
        self._init_state()

    # -----------------------------------------------------------------
    # Internal state initialization
    # -----------------------------------------------------------------

    def _init_state(self):
        """Set all registers to their reset values."""
        # TDI state
        self.tdi_state = STATE_CONFIG_UNLOCKED

        # Output controls
        self.spdm_req_ready  = 1
        self.spdm_resp_valid = 0

        # Response construction
        self.resp_msg_type    = 0
        self.resp_word_idx    = 0
        self.resp_total_words = 0

        # Request parsing
        self.req_msg_type     = 0
        self.req_interface_id = 0
        self.req_parsed       = 0
        self.req_word_counter = 0
        self.received_nonce   = 0

        # Error tracking
        self.pending_error   = 0
        self.last_error_code = 0
        self.error_irq       = 0

        # Lock configuration
        self.lock_no_fw_update          = 0
        self.lock_msix_locked           = 0
        self.lock_bind_p2p              = 0
        self.lock_all_request_redirect  = 0
        self.lock_stream_id             = 0

        # Nonce / LFSR
        self.nonce_lfsr    = mask(self.NONCE_WIDTH)  # all-ones seed
        self.nonce_valid   = 0
        self.current_nonce = 0

        # MMIO
        self.mmio_reporting_offset = 0

    # -----------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------

    def reset(self):
        """Synchronous reset — matches RTL reset block exactly."""
        self._init_state()

    # -----------------------------------------------------------------
    # Combinational response data mux — matches RTL always @(*) block
    # -----------------------------------------------------------------

    def _resp_data(self) -> int:
        """Compute spdm_resp_data from current registered state (combinational).

        Matches RTL lines 458-550 exactly.
        Returns 0 when spdm_resp_valid is 0.
        """
        if not self.spdm_resp_valid:
            return 0

        w = self.resp_word_idx
        t = self.resp_msg_type

        if t == RESP_TDISP_VERSION:
            if   w == 0: return (self.TDISP_VERSION << 8) | RESP_TDISP_VERSION
            elif w == 1: return 0x00000001   # VERSION_NUM_COUNT = 1
            elif w == 2: return self.TDISP_VERSION  # Entry: V1.0
            else:        return 0

        elif t == RESP_TDISP_CAPABILITIES:
            if   w == 0:  return (self.TDISP_VERSION << 8) | RESP_TDISP_CAPABILITIES
            elif w == 1:  return 0x00000001   # DSM_CAPS
            elif w == 2:  return 0x0000007F   # REQ_MSGS_SUPPORTED [0-6]
            elif w == 3:  return 0x0000001F   # REQ_MSGS_SUPPORTED [7-12]
            elif w == 4:  return 0
            elif w == 5:  return 0
            elif w == 6:  return 0
            elif w == 7:  return 0
            elif w == 8:  return 0x0000001F   # LOCK_INTERFACE_FLAGS_SUPPORTED
            elif w == 9:  return 0
            elif w == 10: return 0x00000034   # DEV_ADDR_WIDTH = 52
            elif w == 11: return 0x00000001   # NUM_REQ_THIS = 1
            elif w == 12: return 0x00000001   # NUM_REQ_ALL = 1
            else:         return 0

        elif t == RESP_LOCK_INTERFACE:
            if   w == 0: return (self.TDISP_VERSION << 8) | RESP_LOCK_INTERFACE
            elif w == 1: return (self.current_nonce >> 0)   & mask(32)
            elif w == 2: return (self.current_nonce >> 32)  & mask(32)
            elif w == 3: return (self.current_nonce >> 64)  & mask(32)
            elif w == 4: return (self.current_nonce >> 96)  & mask(32)
            elif w == 5: return (self.current_nonce >> 128) & mask(32)
            elif w == 6: return (self.current_nonce >> 160) & mask(32)
            elif w == 7: return (self.current_nonce >> 192) & mask(32)
            elif w == 8: return (self.current_nonce >> 224) & mask(32)
            else:        return 0

        elif t == RESP_DEVICE_INTERFACE_REPORT:
            if   w == 0: return (self.TDISP_VERSION << 8) | RESP_DEVICE_INTERFACE_REPORT
            elif w == 1: return 0x00040000   # PORTION_LENGTH=4, REMAINDER_LENGTH=0
            elif w == 2: return 0            # INTERFACE_INFO
            elif w == 3: return 0            # Reserved
            elif w == 4: return 0            # MSI_X_MESSAGE_CONTROL
            elif w == 5: return 0            # LNR_CONTROL + TPH_CONTROL
            else:        return 0

        elif t == RESP_DEVICE_INTERFACE_STATE:
            if   w == 0: return (self.TDISP_VERSION << 8) | RESP_DEVICE_INTERFACE_STATE
            elif w == 1: return self.tdi_state & 0xFF   # TDI_STATE
            else:        return 0

        elif t == RESP_START_INTERFACE:
            return (self.TDISP_VERSION << 8) | RESP_START_INTERFACE

        elif t == RESP_STOP_INTERFACE:
            return (self.TDISP_VERSION << 8) | RESP_STOP_INTERFACE

        elif t == RESP_TDISP_ERROR:
            if   w == 0: return (self.TDISP_VERSION << 8) | RESP_TDISP_ERROR
            elif w == 1: return self.pending_error  # ERROR_CODE
            elif w == 2: return 0                   # ERROR_DATA
            else:        return 0

        else:
            return 0

    # -----------------------------------------------------------------
    # LFSR feedback computation — matches RTL wire
    # -----------------------------------------------------------------

    def _lfsr_feedback(self) -> int:
        """Compute next LFSR value from current nonce_lfsr."""
        return lfsr_next(self.nonce_lfsr, self.NONCE_WIDTH)

    # -----------------------------------------------------------------
    # Core cycle step — matches RTL always @(posedge clk)
    # -----------------------------------------------------------------

    def step(self, spdm_req_valid: int = 0, spdm_req_data: int = 0,
             spdm_resp_ready: int = 0, ide_keys_valid: int = 1,
             rst_n: int = 1) -> dict:
        """Advance one clock cycle (mirrors RTL NBA semantics exactly).

        All inputs are sampled at the current clock edge.
        Returns a dict of combinational outputs visible next cycle:
          spdm_resp_data, spdm_resp_len, spdm_resp_valid,
          spdm_req_ready, tdi_state, error_irq, last_error_code,
          current_nonce, mmio_reporting_offset

        The model updates internal state (register writes) to match
        what the RTL registers will hold after this clock edge.
        Output values reflect what the combinational logic will produce
        from those new register values.
        """
        if not rst_n:
            self._init_state()
            return self._snapshot()

        # ── Compute all next-values before latching (NBA semantics) ──
        # We read current state, compute next state, then latch.

        # Snapshot current state for reads
        cur = {
            'tdi_state':             self.tdi_state,
            'spdm_req_ready':        self.spdm_req_ready,
            'spdm_resp_valid':       self.spdm_resp_valid,
            'resp_msg_type':         self.resp_msg_type,
            'resp_word_idx':         self.resp_word_idx,
            'resp_total_words':      self.resp_total_words,
            'req_msg_type':          self.req_msg_type,
            'req_interface_id':      self.req_interface_id,
            'req_parsed':            self.req_parsed,
            'req_word_counter':      self.req_word_counter,
            'received_nonce':        self.received_nonce,
            'pending_error':         self.pending_error,
            'last_error_code':       self.last_error_code,
            'error_irq':             self.error_irq,
            'lock_no_fw_update':     self.lock_no_fw_update,
            'lock_msix_locked':      self.lock_msix_locked,
            'lock_bind_p2p':         self.lock_bind_p2p,
            'lock_all_request_redirect': self.lock_all_request_redirect,
            'lock_stream_id':        self.lock_stream_id,
            'mmio_reporting_offset': self.mmio_reporting_offset,
            'nonce_lfsr':            self.nonce_lfsr,
            'nonce_valid':           self.nonce_valid,
            'current_nonce':         self.current_nonce,
        }

        # ── Next-values (start from current, accumulate changes) ──
        nv = dict(cur)  # copy current as base

        # Default: deassert error_irq after 1 cycle
        nv['error_irq'] = 0

        # LFSR always advances
        nv['nonce_lfsr'] = self._lfsr_feedback()

        # Capture nonce when entering CONFIG_LOCKED (one-shot)
        if cur['tdi_state'] == STATE_CONFIG_LOCKED and not cur['nonce_valid']:
            nv['current_nonce'] = self._lfsr_feedback()
            nv['nonce_valid'] = 1

        # Invalidate nonce when in CONFIG_UNLOCKED
        if cur['tdi_state'] == STATE_CONFIG_UNLOCKED:
            nv['nonce_valid'] = 0
            nv['current_nonce'] = 0

        # ── Response transmission handshake ──
        if cur['spdm_resp_valid'] and spdm_resp_ready:
            if cur['resp_word_idx'] < cur['resp_total_words']:
                nv['resp_word_idx'] = cur['resp_word_idx'] + 1
            else:
                nv['spdm_resp_valid'] = 0
                nv['resp_word_idx'] = 0
                nv['spdm_req_ready'] = 1

        # ── Request reception and processing ──
        if spdm_req_valid and cur['spdm_req_ready'] and not cur['spdm_resp_valid']:
            if not cur['req_parsed']:
                # Word 0: Parse TDISP header
                msg_type = (spdm_req_data >> 8) & 0xFF

                nv['req_msg_type'] = msg_type
                nv['req_word_counter'] = 1
                nv['req_interface_id'] = 0
                nv['received_nonce'] = 0

                if msg_type != 0:
                    nv['req_parsed'] = 1

                # Route to handler
                if msg_type == REQ_GET_TDISP_VERSION:
                    nv['resp_msg_type'] = RESP_TDISP_VERSION
                    nv['resp_total_words'] = 5
                    nv['spdm_resp_valid'] = 1
                    nv['spdm_req_ready'] = 0

                elif msg_type == REQ_GET_TDISP_CAPABILITIES:
                    nv['resp_msg_type'] = RESP_TDISP_CAPABILITIES
                    nv['resp_total_words'] = 14
                    nv['spdm_resp_valid'] = 1
                    nv['spdm_req_ready'] = 0

                elif msg_type == REQ_LOCK_INTERFACE:
                    if cur['tdi_state'] != STATE_CONFIG_UNLOCKED:
                        nv['pending_error'] = ERR_INVALID_INTERFACE_STATE
                        nv['resp_msg_type'] = RESP_TDISP_ERROR
                        nv['resp_total_words'] = 8
                        nv['spdm_resp_valid'] = 1
                        nv['spdm_req_ready'] = 0
                        nv['error_irq'] = 1
                        nv['last_error_code'] = ERR_INVALID_INTERFACE_STATE
                    elif self.ide_required and not ide_keys_valid:
                        nv['pending_error'] = ERR_INVALID_REQUEST
                        nv['resp_msg_type'] = RESP_TDISP_ERROR
                        nv['resp_total_words'] = 8
                        nv['spdm_resp_valid'] = 1
                        nv['spdm_req_ready'] = 0
                        nv['error_irq'] = 1
                        nv['last_error_code'] = ERR_INVALID_REQUEST
                    # else: defer — no resp_valid set, wait for words 1-3

                elif msg_type == REQ_GET_DEVICE_INTERFACE_REPORT:
                    if (cur['tdi_state'] != STATE_CONFIG_LOCKED and
                            cur['tdi_state'] != STATE_RUN):
                        nv['pending_error'] = ERR_INVALID_INTERFACE_STATE
                        nv['resp_msg_type'] = RESP_TDISP_ERROR
                        nv['resp_total_words'] = 8
                        nv['spdm_resp_valid'] = 1
                        nv['spdm_req_ready'] = 0
                        nv['error_irq'] = 1
                        nv['last_error_code'] = ERR_INVALID_INTERFACE_STATE
                    else:
                        nv['resp_msg_type'] = RESP_DEVICE_INTERFACE_REPORT
                        nv['resp_total_words'] = 6
                        nv['spdm_resp_valid'] = 1
                        nv['spdm_req_ready'] = 0

                elif msg_type == REQ_GET_DEVICE_INTERFACE_STATE:
                    nv['resp_msg_type'] = RESP_DEVICE_INTERFACE_STATE
                    nv['resp_total_words'] = 5
                    nv['spdm_resp_valid'] = 1
                    nv['spdm_req_ready'] = 0

                elif msg_type == REQ_START_INTERFACE:
                    if cur['tdi_state'] != STATE_CONFIG_LOCKED:
                        nv['pending_error'] = ERR_INVALID_INTERFACE_STATE
                        nv['resp_msg_type'] = RESP_TDISP_ERROR
                        nv['resp_total_words'] = 8
                        nv['spdm_resp_valid'] = 1
                        nv['spdm_req_ready'] = 0
                        nv['error_irq'] = 1
                        nv['last_error_code'] = ERR_INVALID_INTERFACE_STATE
                    elif not cur['nonce_valid']:
                        nv['pending_error'] = ERR_INSUFFICIENT_ENTROPY
                        nv['resp_msg_type'] = RESP_TDISP_ERROR
                        nv['resp_total_words'] = 8
                        nv['spdm_resp_valid'] = 1
                        nv['spdm_req_ready'] = 0
                        nv['error_irq'] = 1
                        nv['last_error_code'] = ERR_INSUFFICIENT_ENTROPY
                    # else: defer — wait for words 4-11

                elif msg_type == REQ_STOP_INTERFACE:
                    nv['tdi_state'] = STATE_CONFIG_UNLOCKED
                    nv['nonce_valid'] = 0
                    nv['current_nonce'] = 0
                    nv['lock_no_fw_update'] = 0
                    nv['lock_msix_locked'] = 0
                    nv['lock_bind_p2p'] = 0
                    nv['lock_all_request_redirect'] = 0
                    nv['lock_stream_id'] = 0
                    nv['mmio_reporting_offset'] = 0

                    nv['resp_msg_type'] = RESP_STOP_INTERFACE
                    nv['resp_total_words'] = 1
                    nv['spdm_resp_valid'] = 1
                    nv['spdm_req_ready'] = 0

                else:
                    nv['pending_error'] = ERR_UNSUPPORTED_REQUEST
                    nv['resp_msg_type'] = RESP_TDISP_ERROR
                    nv['resp_total_words'] = 8
                    nv['spdm_resp_valid'] = 1
                    nv['spdm_req_ready'] = 0
                    nv['error_irq'] = 1
                    nv['last_error_code'] = ERR_UNSUPPORTED_REQUEST

            else:
                # Subsequent words (word 1+): Collect INTERFACE_ID and nonce
                wc = cur['req_word_counter']

                if wc == 1:
                    # RTL: req_interface_id[31:0] <= spdm_req_data
                    nv['req_interface_id'] = (
                        (cur['req_interface_id'] & ~mask(32)) |
                        (spdm_req_data & mask(32))
                    )
                elif wc == 2:
                    # RTL: req_interface_id[63:32] <= spdm_req_data
                    nv['req_interface_id'] = (
                        (cur['req_interface_id'] & ~(mask(32) << 32)) |
                        ((spdm_req_data & mask(32)) << 32)
                    )
                elif wc == 3:
                    # RTL: req_interface_id[95:64] <= spdm_req_data
                    nv['req_interface_id'] = (
                        (cur['req_interface_id'] & ~(mask(32) << 64)) |
                        ((spdm_req_data & mask(32)) << 64)
                    )
                    # LOCK_INTERFACE: INTERFACE_ID fully received
                    if cur['req_msg_type'] == REQ_LOCK_INTERFACE:
                        # NBA timing: [95:64] not yet latched, compare spdm_req_data
                        built_ifid = (
                            (cur['req_interface_id'] & mask(64)) |
                            ((spdm_req_data & mask(32)) << 64)
                        )
                        if built_ifid != self.configured_interface_id:
                            nv['pending_error'] = ERR_INVALID_INTERFACE
                            nv['resp_msg_type'] = RESP_TDISP_ERROR
                            nv['resp_total_words'] = 8
                            nv['spdm_resp_valid'] = 1
                            nv['spdm_req_ready'] = 0
                            nv['error_irq'] = 1
                            nv['last_error_code'] = ERR_INVALID_INTERFACE
                            nv['req_parsed'] = 0
                        else:
                            nv['tdi_state'] = STATE_CONFIG_LOCKED
                            nv['lock_stream_id'] = self.default_stream_id
                            nv['lock_no_fw_update'] = 0
                            nv['lock_msix_locked'] = 0
                            nv['lock_bind_p2p'] = 0
                            nv['lock_all_request_redirect'] = 0
                            nv['mmio_reporting_offset'] = 0

                            nv['resp_msg_type'] = RESP_LOCK_INTERFACE
                            nv['resp_total_words'] = 9
                            nv['spdm_resp_valid'] = 1
                            nv['spdm_req_ready'] = 0
                            nv['req_parsed'] = 0

                elif wc == 4:
                    nv['received_nonce'] = (
                        (cur['received_nonce'] & ~mask(32)) |
                        (spdm_req_data & mask(32))
                    )
                elif wc == 5:
                    nv['received_nonce'] = (
                        (cur['received_nonce'] & ~(mask(32) << 32)) |
                        ((spdm_req_data & mask(32)) << 32)
                    )
                elif wc == 6:
                    nv['received_nonce'] = (
                        (cur['received_nonce'] & ~(mask(32) << 64)) |
                        ((spdm_req_data & mask(32)) << 64)
                    )
                elif wc == 7:
                    nv['received_nonce'] = (
                        (cur['received_nonce'] & ~(mask(32) << 96)) |
                        ((spdm_req_data & mask(32)) << 96)
                    )
                elif wc == 8:
                    nv['received_nonce'] = (
                        (cur['received_nonce'] & ~(mask(32) << 128)) |
                        ((spdm_req_data & mask(32)) << 128)
                    )
                elif wc == 9:
                    nv['received_nonce'] = (
                        (cur['received_nonce'] & ~(mask(32) << 160)) |
                        ((spdm_req_data & mask(32)) << 160)
                    )
                elif wc == 10:
                    nv['received_nonce'] = (
                        (cur['received_nonce'] & ~(mask(32) << 192)) |
                        ((spdm_req_data & mask(32)) << 192)
                    )
                elif wc == 11:
                    nv['received_nonce'] = (
                        (cur['received_nonce'] & ~(mask(32) << 224)) |
                        ((spdm_req_data & mask(32)) << 224)
                    )
                    # Nonce validation — NBA timing: [255:224] not yet latched
                    built_nonce = (
                        (cur['received_nonce'] & mask(224)) |
                        ((spdm_req_data & mask(32)) << 224)
                    )
                    if built_nonce != cur['current_nonce']:
                        nv['pending_error'] = ERR_INVALID_NONCE
                        nv['resp_msg_type'] = RESP_TDISP_ERROR
                        nv['resp_total_words'] = 8
                        nv['spdm_resp_valid'] = 1
                        nv['spdm_req_ready'] = 0
                        nv['error_irq'] = 1
                        nv['last_error_code'] = ERR_INVALID_NONCE
                        nv['req_parsed'] = 0
                    else:
                        nv['tdi_state'] = STATE_RUN
                        nv['nonce_valid'] = 0
                        nv['resp_msg_type'] = RESP_START_INTERFACE
                        nv['resp_total_words'] = 1
                        nv['spdm_resp_valid'] = 1
                        nv['spdm_req_ready'] = 0
                        nv['req_parsed'] = 0
                else:
                    # Unexpected word — reset parser
                    nv['req_parsed'] = 0

                # Advance word counter
                if wc < 11:
                    nv['req_word_counter'] = wc + 1

        # ── Latch all next-values ──
        self.tdi_state             = nv['tdi_state']
        self.spdm_req_ready        = nv['spdm_req_ready']
        self.spdm_resp_valid       = nv['spdm_resp_valid']
        self.resp_msg_type         = nv['resp_msg_type']
        self.resp_word_idx         = nv['resp_word_idx']
        self.resp_total_words      = nv['resp_total_words']
        self.req_msg_type          = nv['req_msg_type']
        self.req_interface_id      = nv['req_interface_id']
        self.req_parsed            = nv['req_parsed']
        self.req_word_counter      = nv['req_word_counter']
        self.received_nonce        = nv['received_nonce']
        self.pending_error         = nv['pending_error']
        self.last_error_code       = nv['last_error_code']
        self.error_irq             = nv['error_irq']
        self.lock_no_fw_update     = nv['lock_no_fw_update']
        self.lock_msix_locked      = nv['lock_msix_locked']
        self.lock_bind_p2p         = nv['lock_bind_p2p']
        self.lock_all_request_redirect = nv['lock_all_request_redirect']
        self.lock_stream_id        = nv['lock_stream_id']
        self.mmio_reporting_offset = nv['mmio_reporting_offset']
        self.nonce_lfsr            = nv['nonce_lfsr']
        self.nonce_valid           = nv['nonce_valid']
        self.current_nonce         = nv['current_nonce']

        return self._snapshot()

    # -----------------------------------------------------------------
    # Snapshot current outputs
    # -----------------------------------------------------------------

    def _snapshot(self) -> dict:
        """Return current output state as a dict."""
        return {
            'spdm_resp_data':    self._resp_data(),
            'spdm_resp_len':     self.resp_total_words,
            'spdm_resp_valid':   self.spdm_resp_valid,
            'spdm_req_ready':    self.spdm_req_ready,
            'tdi_state':         self.tdi_state,
            'error_irq':         self.error_irq,
            'last_error_code':   self.last_error_code,
            'current_nonce':     self.current_nonce,
            'mmio_reporting_offset': self.mmio_reporting_offset,
        }

    # -----------------------------------------------------------------
    # High-level convenience methods
    # -----------------------------------------------------------------

    def send_request(self, words: list, resp_ready_every: bool = True,
                     ide_keys_valid: int = 1) -> list:
        """Feed a complete multi-word request and collect the response.

        Args:
            words: List of 32-bit word values (word 0 = header).
            resp_ready_every: If True, resp_ready=1 every cycle after
                              resp_valid is asserted.

        Returns:
            List of dicts, one per cycle, containing output snapshots.
        """
        results = []

        # Feed request words
        for i, w in enumerate(words):
            snap = self.step(
                spdm_req_valid=1,
                spdm_req_data=w,
                spdm_resp_ready=0,
                ide_keys_valid=ide_keys_valid,
            )
            results.append(snap)

        # Idle cycles with resp_ready=1 to drain response
        max_drain = 256
        for _ in range(max_drain):
            if self.spdm_resp_valid:
                resp_ready = 1 if resp_ready_every else 1
                snap = self.step(
                    spdm_req_valid=0,
                    spdm_req_data=0,
                    spdm_resp_ready=resp_ready,
                    ide_keys_valid=ide_keys_valid,
                )
                results.append(snap)
            else:
                break

        return results

    def collect_response(self, ide_keys_valid: int = 1) -> list:
        """Drain all response words by stepping with resp_ready=1.

        Returns list of response word values (integers).
        """
        words = []
        max_cycles = 256
        for _ in range(max_cycles):
            if not self.spdm_resp_valid:
                break
            data = self._resp_data()
            words.append(data)
            self.step(
                spdm_req_valid=0,
                spdm_req_data=0,
                spdm_resp_ready=1,
                ide_keys_valid=ide_keys_valid,
            )
        return words

    # -----------------------------------------------------------------
    # State query helpers
    # -----------------------------------------------------------------

    def get_tdi_state_name(self) -> str:
        """Return human-readable TDI state name."""
        names = {
            STATE_CONFIG_UNLOCKED: "CONFIG_UNLOCKED",
            STATE_CONFIG_LOCKED:   "CONFIG_LOCKED",
            STATE_RUN:             "RUN",
            STATE_ERROR:           "ERROR",
        }
        return names.get(self.tdi_state, f"UNKNOWN({self.tdi_state})")

    def get_resp_type_name(self) -> str:
        """Return human-readable response type name."""
        names = {
            RESP_TDISP_VERSION:           "TDISP_VERSION",
            RESP_TDISP_CAPABILITIES:      "TDISP_CAPABILITIES",
            RESP_LOCK_INTERFACE:          "LOCK_INTERFACE",
            RESP_DEVICE_INTERFACE_REPORT: "DEVICE_INTERFACE_REPORT",
            RESP_DEVICE_INTERFACE_STATE:  "DEVICE_INTERFACE_STATE",
            RESP_START_INTERFACE:         "START_INTERFACE",
            RESP_STOP_INTERFACE:          "STOP_INTERFACE",
            RESP_TDISP_ERROR:             "TDISP_ERROR",
        }
        return names.get(self.resp_msg_type, f"UNKNOWN(0x{self.resp_msg_type:02x})")

    def __repr__(self) -> str:
        return (f"TdispDsmRefModel(tdi_state={self.get_tdi_state_name()}, "
                f"resp_valid={self.spdm_resp_valid}, "
                f"resp_type={self.get_resp_type_name()}, "
                f"resp_word_idx={self.resp_word_idx}, "
                f"req_ready={self.spdm_req_ready})")

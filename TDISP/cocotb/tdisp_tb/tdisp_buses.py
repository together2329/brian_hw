"""
TDISP Bus Functional Models u2014 Python/cocotb wrappers for tdisp_top ports.

Provides high-level bus classes that wrap cocotb handle access for every
interface group on tdisp_top.  2-D unpacked arrays (per-TDI, per-PFu00d7BAR)
are accessed through indexed helpers that resolve to the correct cocotb
handle path at runtime.

Usage in a cocotb test:
    from tdisp_buses import (
        DoeBus, ConfigBus, RegWriteBus, EgressTlpBus,
        IngressTlpBus, VdmBus, StatusBus,
    )

    doe   = DoeBus(dut)
    cfg   = ConfigBus(dut, num_tdi=2, num_pf=1, num_bars=6)
    regs  = RegWriteBus(dut, num_tdi=2)
    eg    = EgressTlpBus(dut, num_tdi=2)
    ig    = IngressTlpBus(dut, num_tdi=2)
    vdm   = VdmBus(dut)
    stat  = StatusBus(dut, num_tdi=2)
"""

from __future__ import annotations

import cocotb
from cocotb.bus import Bus
from cocotb.handle import ModifiableObject, NonHierarchyIndexableObject
from typing import Optional, Dict, List


# ============================================================================
# Helper: safely resolve a cocotb handle by hierarchical path
# ============================================================================

def _sig(dut, name: str) -> ModifiableObject:
    """Return a cocotb signal handle, raising a clear error if missing."""
    try:
        return getattr(dut, name)
    except AttributeError:
        raise AttributeError(
            f"DUT has no signal '{name}'.  Check that the DUT is instantiated "
            f"and the signal name matches the RTL port."
        )


def _idx(dut, name: str, *indices: int) -> ModifiableObject:
    """Resolve an indexed signal: dut.name[i] or dut.name[i][j]."""
    handle = _sig(dut, name)
    for ix in indices:
        handle = handle[ix]
    return handle


# ============================================================================
# DOE Transport Bus (AXI-Stream-like, byte-serial)
#   RX: dut drives rx_data/rx_valid/rx_last, DUT returns rx_ready
#   TX: DUT drives tx_data/tx_valid/tx_last, dut drives tx_ready
# ============================================================================

class DoeRxBus(Bus):
    """DOE receive-side bus (testbench u2192 DUT)."""
    _signals = ["rx_valid", "rx_data", "rx_last", "rx_ready"]
    _optional_signals: List[str] = []

    def __init__(self, entity, *, signals=None, optional_signals=None,
                 bus_separator="_", prefix=""):
        # Use empty prefix u2014 signals live at DUT top level
        super().__init__(
            entity, self._signals, optional_signals or [],
            bus_separator=bus_separator, prefix=prefix,
        )


class DoeTxBus(Bus):
    """DOE transmit-side bus (DUT u2192 testbench)."""
    _signals = ["tx_valid", "tx_data", "tx_last", "tx_ready"]
    _optional_signals: List[str] = []

    def __init__(self, entity, *, signals=None, optional_signals=None,
                 bus_separator="_", prefix=""):
        super().__init__(
            entity, self._signals, optional_signals or [],
            bus_separator=bus_separator, prefix=prefix,
        )


class DoeBus:
    """Combined DOE transport wrapper (RX + TX)."""

    def __init__(self, dut):
        self.dut = dut
        self.rx = DoeRxBus(dut)
        self.tx = DoeTxBus(dut)

    # --- RX side (testbench sends bytes to DUT) ---------------------------

    @property
    def rx_valid(self):
        return self.rx.rx_valid

    @property
    def rx_data(self):
        return self.rx.rx_data

    @property
    def rx_last(self):
        return self.rx.rx_last

    @property
    def rx_ready(self):
        return self.rx.rx_ready

    # --- TX side (DUT sends bytes to testbench) ---------------------------

    @property
    def tx_valid(self):
        return self.tx.tx_valid

    @property
    def tx_data(self):
        return self.tx.tx_data

    @property
    def tx_last(self):
        return self.tx.tx_last

    @property
    def tx_ready(self):
        return self.tx.tx_ready


# ============================================================================
# ConfigBus u2014 static / slow-changing configuration inputs
#   Handles: version, caps, interface IDs, report, IDE, BARs, TRNG, misc
# ============================================================================

class ConfigBus:
    """Wraps all non-TLP, non-message configuration ports on tdisp_top.

    For 2-D unpacked arrays (BAR configs, interface IDs, etc.), provides
    indexed getter/setter helpers that resolve to the correct cocotb handle.
    """

    def __init__(self, dut, *,
                 num_tdi: int = 2,
                 num_pf: int = 1,
                 num_bars: int = 6,
                 report_buf_size: int = 4096):
        self.dut = dut
        self.num_tdi = num_tdi
        self.num_pf = num_pf
        self.num_bars = num_bars
        self.report_buf_size = report_buf_size

    # --- Version -----------------------------------------------------------

    def set_version(self, version: int, valid: bool = True):
        self.dut.negotiated_version.value = version & 0xFF
        self.dut.version_valid.value = int(valid)

    # --- Device Capabilities (struct) --------------------------------------

    def set_device_caps(self, caps_int: int):
        """Set device_caps as a single integer (packed struct)."""
        self.dut.device_caps.value = caps_int

    # --- Interface Report --------------------------------------------------

    def set_report(self, data: bytes, total_len: Optional[int] = None):
        """Load the report_data byte array and set report_total_len."""
        assert len(data) <= self.report_buf_size
        for i, b in enumerate(data):
            _idx(self.dut, "report_data", i).value = b
        if total_len is None:
            total_len = len(data)
        self.dut.report_total_len.value = total_len & 0xFFFF

    # --- Interface IDs (per TDI, 96-bit) -----------------------------------

    def set_interface_id(self, tdi_idx: int, iface_id: int):
        _idx(self.dut, "hosted_interface_ids", tdi_idx).value = iface_id

    def get_interface_id(self, tdi_idx: int) -> int:
        return int(_idx(self.dut, "hosted_interface_ids", tdi_idx).value)

    # --- Outstanding Request Counts ----------------------------------------

    def set_num_req_this(self, tdi_idx: int, count: int):
        _idx(self.dut, "num_req_this_config", tdi_idx).value = count & 0xFF

    def set_num_req_all(self, count: int):
        self.dut.num_req_all_config.value = count & 0xFF

    # --- IDE Stream Configuration ------------------------------------------

    def set_ide_config(self, *, stream_valid: bool = True,
                       keys_programmed: bool = True,
                       default_stream_id: int = 0,
                       xt_enable_setting: bool = False,
                       tc_value: int = 0):
        self.dut.ide_stream_valid.value = int(stream_valid)
        self.dut.ide_keys_programmed.value = int(keys_programmed)
        self.dut.ide_default_stream_id.value = default_stream_id & 0xFF
        self.dut.ide_xt_enable_setting.value = int(xt_enable_setting)
        self.dut.ide_tc_value.value = tc_value & 0x7

    # --- P2P Stream Bound Status (per TDI, bitmask) -----------------------

    def set_p2p_stream_bound(self, tdi_idx: int, mask: int):
        _idx(self.dut, "p2p_stream_bound", tdi_idx).value = mask

    def get_p2p_stream_bound(self, tdi_idx: int) -> int:
        return int(_idx(self.dut, "p2p_stream_bound", tdi_idx).value)

    # --- PF BAR Configuration (2-D: pf u00d7 bar) -----------------------------

    def set_pf_bar(self, pf: int, bar: int, *,
                   valid: bool = True,
                   addr: int = 0,
                   size: int = 0):
        _idx(self.dut, "pf_bar_config_valid", pf, bar).value = int(valid)
        _idx(self.dut, "pf_bar_addrs", pf, bar).value = addr & 0xFFFFFFFFFFFFFFFF
        _idx(self.dut, "pf_bar_sizes", pf, bar).value = size & 0xFFFFFFFFFFFFFFFF

    def get_pf_bar_addr(self, pf: int, bar: int) -> int:
        return int(_idx(self.dut, "pf_bar_addrs", pf, bar).value)

    def get_pf_bar_size(self, pf: int, bar: int) -> int:
        return int(_idx(self.dut, "pf_bar_sizes", pf, bar).value)

    # --- VF BAR Configuration (2-D: pf u00d7 bar) -----------------------------

    def set_vf_bar(self, pf: int, bar: int, *,
                   valid: bool = True,
                   addr: int = 0,
                   size: int = 0):
        _idx(self.dut, "vf_bar_config_valid", pf, bar).value = int(valid)
        _idx(self.dut, "vf_bar_addrs", pf, bar).value = addr & 0xFFFFFFFFFFFFFFFF
        _idx(self.dut, "vf_bar_sizes", pf, bar).value = size & 0xFFFFFFFFFFFFFFFF

    def get_vf_bar_addr(self, pf: int, bar: int) -> int:
        return int(_idx(self.dut, "vf_bar_addrs", pf, bar).value)

    # --- Miscellaneous Device Configuration --------------------------------

    def set_misc_config(self, *,
                        phantom_funcs_enabled: bool = False,
                        expansion_rom_valid: bool = False,
                        expansion_rom_addr: int = 0,
                        expansion_rom_size: int = 0,
                        resizable_bar_sizes_valid: bool = False,
                        sr_iov_page_size: int = 0,
                        cache_line_size: int = 64,
                        tph_mode: int = 0):
        self.dut.phantom_funcs_enabled.value = int(phantom_funcs_enabled)
        self.dut.expansion_rom_valid.value = int(expansion_rom_valid)
        self.dut.expansion_rom_addr.value = expansion_rom_addr & 0xFFFFFFFFFFFFFFFF
        self.dut.expansion_rom_size.value = expansion_rom_size & 0xFFFFFFFFFFFFFFFF
        self.dut.resizable_bar_sizes_valid.value = int(resizable_bar_sizes_valid)
        self.dut.sr_iov_page_size.value = sr_iov_page_size & 0x7
        self.dut.cache_line_size.value = cache_line_size & 0xFF
        self.dut.tph_mode.value = tph_mode & 0x3

    # --- TRNG / Entropy Source ---------------------------------------------

    def set_trng(self, *, valid: bool = False, data: int = 0):
        self.dut.trng_valid.value = int(valid)
        self.dut.trng_data.value = data

    # --- Capability Base Addresses (per TDI) -------------------------------

    def set_cap_bases(self, tdi_idx: int, *,
                      pcie_cap: int = 0,
                      msix_cap: int = 0,
                      pm_cap: int = 0):
        _idx(self.dut, "pcie_cap_base_per_tdi", tdi_idx).value = pcie_cap
        _idx(self.dut, "msix_cap_base_per_tdi", tdi_idx).value = msix_cap
        _idx(self.dut, "pm_cap_base_per_tdi", tdi_idx).value = pm_cap


# ============================================================================
# RegWriteBus u2014 per-TDI config-space register write events
# ============================================================================

class RegWriteBus:
    """Wraps the per-TDI register write event interface.

    Signals:
      reg_write_valid_per_tdi   [NUM_TDI-1:0]
      reg_write_addr_per_tdi    [NUM_TDI-1:0][REG_ADDR_WIDTH-1:0]
      reg_write_data_per_tdi    [NUM_TDI-1:0][REG_DATA_WIDTH-1:0]
      reg_write_mask_per_tdi    [NUM_TDI-1:0][REG_MASK_WIDTH-1:0]
    """

    def __init__(self, dut, *, num_tdi: int = 2):
        self.dut = dut
        self.num_tdi = num_tdi

    def drive_write(self, tdi_idx: int, *,
                    addr: int, data: int, mask: int = 0xF):
        """Drive a single register write event for one TDI."""
        self.clear_all()  # deassert all valid first
        _idx(self.dut, "reg_write_addr_per_tdi", tdi_idx).value = addr
        _idx(self.dut, "reg_write_data_per_tdi", tdi_idx).value = data
        _idx(self.dut, "reg_write_mask_per_tdi", tdi_idx).value = mask
        _idx(self.dut, "reg_write_valid_per_tdi", tdi_idx).value = 1

    def clear_all(self):
        """Deassert all reg_write_valid signals."""
        for i in range(self.num_tdi):
            _idx(self.dut, "reg_write_valid_per_tdi", i).value = 0


# ============================================================================
# EgressTlpBus u2014 per-TDI egress TLP interface (TDI as Requester)
# ============================================================================

class EgressTlpBus:
    """Wraps the per-TDI egress TLP input and output signals.

    Input signals (testbench u2192 DUT):
      eg_tlp_valid_per_tdi       eg_tlp_is_msix_locked_per_tdi
      eg_tlp_data_per_tdi        eg_tlp_is_ats_request_per_tdi
      eg_tlp_last_per_tdi        eg_tlp_is_vdm_per_tdi
      eg_tlp_is_memory_req_per_tdi  eg_tlp_is_io_req_per_tdi
      eg_tlp_is_completion_per_tdi  eg_tlp_addr_type_per_tdi
      eg_tlp_is_msi_per_tdi      eg_access_tee_mem_per_tdi
      eg_tlp_is_msix_per_tdi     eg_access_non_tee_mem_per_tdi

    Output signals (DUT u2192 testbench):
      eg_tlp_out_valid_per_tdi   eg_tlp_xt_bit_per_tdi
      eg_tlp_out_data_per_tdi    eg_tlp_t_bit_per_tdi
      eg_tlp_out_last_per_tdi    eg_tlp_reject_per_tdi
    """

    def __init__(self, dut, *, num_tdi: int = 2):
        self.dut = dut
        self.num_tdi = num_tdi

    # --- Input helpers (testbench drives) ----------------------------------

    def drive_input(self, tdi_idx: int, *,
                    valid: bool = False,
                    data: int = 0,
                    last: bool = False,
                    is_memory_req: bool = False,
                    is_completion: bool = False,
                    is_msi: bool = False,
                    is_msix: bool = False,
                    is_msix_locked: bool = False,
                    is_ats_request: bool = False,
                    is_vdm: bool = False,
                    is_io_req: bool = False,
                    addr_type: int = 0,
                    access_tee_mem: bool = False,
                    access_non_tee_mem: bool = False):
        """Drive all egress TLP input signals for one TDI."""
        d = self.dut
        i = tdi_idx
        _idx(d, "eg_tlp_valid_per_tdi", i).value = int(valid)
        _idx(d, "eg_tlp_data_per_tdi", i).value = data
        _idx(d, "eg_tlp_last_per_tdi", i).value = int(last)
        _idx(d, "eg_tlp_is_memory_req_per_tdi", i).value = int(is_memory_req)
        _idx(d, "eg_tlp_is_completion_per_tdi", i).value = int(is_completion)
        _idx(d, "eg_tlp_is_msi_per_tdi", i).value = int(is_msi)
        _idx(d, "eg_tlp_is_msix_per_tdi", i).value = int(is_msix)
        _idx(d, "eg_tlp_is_msix_locked_per_tdi", i).value = int(is_msix_locked)
        _idx(d, "eg_tlp_is_ats_request_per_tdi", i).value = int(is_ats_request)
        _idx(d, "eg_tlp_is_vdm_per_tdi", i).value = int(is_vdm)
        _idx(d, "eg_tlp_is_io_req_per_tdi", i).value = int(is_io_req)
        _idx(d, "eg_tlp_addr_type_per_tdi", i).value = addr_type
        _idx(d, "eg_access_tee_mem_per_tdi", i).value = int(access_tee_mem)
        _idx(d, "eg_access_non_tee_mem_per_tdi", i).value = int(access_non_tee_mem)

    def clear_input(self, tdi_idx: int):
        """Clear all egress inputs for a TDI (valid=0, data=0)."""
        self.drive_input(tdi_idx)

    def clear_all_inputs(self):
        """Clear egress inputs for all TDIs."""
        for i in range(self.num_tdi):
            self.clear_input(i)

    # --- Output sample helpers (testbench reads) ---------------------------

    def sample_output(self, tdi_idx: int) -> Dict:
        """Read all egress TLP output signals for one TDI."""
        d = self.dut
        i = tdi_idx
        return {
            "out_valid":   int(_idx(d, "eg_tlp_out_valid_per_tdi", i).value),
            "out_data":    int(_idx(d, "eg_tlp_out_data_per_tdi", i).value),
            "out_last":    int(_idx(d, "eg_tlp_out_last_per_tdi", i).value),
            "xt_bit":      int(_idx(d, "eg_tlp_xt_bit_per_tdi", i).value),
            "t_bit":       int(_idx(d, "eg_tlp_t_bit_per_tdi", i).value),
            "reject":      int(_idx(d, "eg_tlp_reject_per_tdi", i).value),
        }

    def is_rejected(self, tdi_idx: int) -> bool:
        return bool(int(_idx(self.dut, "eg_tlp_reject_per_tdi", tdi_idx).value))


# ============================================================================
# IngressTlpBus u2014 per-TDI ingress TLP interface (TDI as Completer)
# ============================================================================

class IngressTlpBus:
    """Wraps the per-TDI ingress TLP input and output signals.

    Input signals (testbench u2192 DUT):
      ig_tlp_valid_per_tdi             ig_tlp_is_vdm_per_tdi
      ig_tlp_data_per_tdi              ig_tlp_is_ats_request_per_tdi
      ig_tlp_last_per_tdi              ig_tlp_target_is_non_tee_mem_per_tdi
      ig_tlp_xt_bit_in_per_tdi         ig_tlp_on_bound_stream_per_tdi
      ig_tlp_t_bit_in_per_tdi          ig_ide_required_per_tdi
      ig_tlp_is_memory_req_per_tdi     ig_msix_table_locked_per_tdi
      ig_tlp_is_completion_per_tdi

    Output signals (DUT u2192 testbench):
      ig_tlp_out_valid_per_tdi
      ig_tlp_out_data_per_tdi
      ig_tlp_out_last_per_tdi
      ig_tlp_reject_per_tdi
    """

    def __init__(self, dut, *, num_tdi: int = 2):
        self.dut = dut
        self.num_tdi = num_tdi

    # --- Input helpers (testbench drives) ----------------------------------

    def drive_input(self, tdi_idx: int, *,
                    valid: bool = False,
                    data: int = 0,
                    last: bool = False,
                    xt_bit_in: bool = False,
                    t_bit_in: bool = False,
                    is_memory_req: bool = False,
                    is_completion: bool = False,
                    is_vdm: bool = False,
                    is_ats_request: bool = False,
                    target_is_non_tee_mem: bool = False,
                    on_bound_stream: bool = False,
                    ide_required: bool = False,
                    msix_table_locked: bool = False):
        """Drive all ingress TLP input signals for one TDI."""
        d = self.dut
        i = tdi_idx
        _idx(d, "ig_tlp_valid_per_tdi", i).value = int(valid)
        _idx(d, "ig_tlp_data_per_tdi", i).value = data
        _idx(d, "ig_tlp_last_per_tdi", i).value = int(last)
        _idx(d, "ig_tlp_xt_bit_in_per_tdi", i).value = int(xt_bit_in)
        _idx(d, "ig_tlp_t_bit_in_per_tdi", i).value = int(t_bit_in)
        _idx(d, "ig_tlp_is_memory_req_per_tdi", i).value = int(is_memory_req)
        _idx(d, "ig_tlp_is_completion_per_tdi", i).value = int(is_completion)
        _idx(d, "ig_tlp_is_vdm_per_tdi", i).value = int(is_vdm)
        _idx(d, "ig_tlp_is_ats_request_per_tdi", i).value = int(is_ats_request)
        _idx(d, "ig_tlp_target_is_non_tee_mem_per_tdi", i).value = int(target_is_non_tee_mem)
        _idx(d, "ig_tlp_on_bound_stream_per_tdi", i).value = int(on_bound_stream)
        _idx(d, "ig_ide_required_per_tdi", i).value = int(ide_required)
        _idx(d, "ig_msix_table_locked_per_tdi", i).value = int(msix_table_locked)

    def clear_input(self, tdi_idx: int):
        """Clear all ingress inputs for a TDI."""
        self.drive_input(tdi_idx)

    def clear_all_inputs(self):
        """Clear ingress inputs for all TDIs."""
        for i in range(self.num_tdi):
            self.clear_input(i)

    # --- Output sample helpers (testbench reads) ---------------------------

    def sample_output(self, tdi_idx: int) -> Dict:
        """Read all ingress TLP output signals for one TDI."""
        d = self.dut
        i = tdi_idx
        return {
            "out_valid":   int(_idx(d, "ig_tlp_out_valid_per_tdi", i).value),
            "out_data":    int(_idx(d, "ig_tlp_out_data_per_tdi", i).value),
            "out_last":    int(_idx(d, "ig_tlp_out_last_per_tdi", i).value),
            "reject":      int(_idx(d, "ig_tlp_reject_per_tdi", i).value),
        }

    def is_rejected(self, tdi_idx: int) -> bool:
        return bool(int(_idx(self.dut, "ig_tlp_reject_per_tdi", tdi_idx).value))


# ============================================================================
# VdmBus u2014 VDM pass-through interface
# ============================================================================

class VdmBus:
    """Wraps the VDM request output and response-ready input.

    Output signals (DUT u2192 testbench):
      vdm_req_valid
      vdm_req_interface_id
      vdm_req_payload          [REPORT_BUF_SIZE-1:0]
      vdm_req_payload_len

    Input signal (testbench u2192 DUT):
      vdm_resp_ready
    """

    def __init__(self, dut, *, report_buf_size: int = 4096):
        self.dut = dut
        self.report_buf_size = report_buf_size

    def set_resp_ready(self, ready: bool = True):
        self.dut.vdm_resp_ready.value = int(ready)

    def get_req_valid(self) -> bool:
        return bool(int(self.dut.vdm_req_valid.value))

    def get_req_interface_id(self) -> int:
        return int(self.dut.vdm_req_interface_id.value)

    def get_req_payload_len(self) -> int:
        return int(self.dut.vdm_req_payload_len.value)

    def get_req_payload(self, length: Optional[int] = None) -> bytes:
        """Read VDM payload bytes from DUT."""
        if length is None:
            length = self.get_req_payload_len()
        result = bytearray(length)
        for i in range(length):
            result[i] = int(_idx(self.dut, "vdm_req_payload", i).value) & 0xFF
        return bytes(result)


# ============================================================================
# P2pBindBus u2014 P2P stream bind/unbind outputs
# ============================================================================

class P2pBindBus:
    """Wraps P2P stream bind/unbind pulse outputs and stream_id.

    Output signals (DUT u2192 testbench):
      bind_stream_id
      bind_pulse       [NUM_TDI-1:0]
      unbind_pulse     [NUM_TDI-1:0]
    """

    def __init__(self, dut, *, num_tdi: int = 2):
        self.dut = dut
        self.num_tdi = num_tdi

    def get_bind_stream_id(self) -> int:
        return int(self.dut.bind_stream_id.value)

    def get_bind_pulse(self, tdi_idx: int) -> bool:
        return bool(int(_idx(self.dut, "bind_pulse", tdi_idx).value))

    def get_unbind_pulse(self, tdi_idx: int) -> bool:
        return bool(int(_idx(self.dut, "unbind_pulse", tdi_idx).value))


# ============================================================================
# MmioAttrBus u2014 MMIO attribute update outputs
# ============================================================================

class MmioAttrBus:
    """Wraps the MMIO attribute update interface.

    Output signals (DUT u2192 testbench):
      mmio_attr_update_valid
      mmio_attr_tdi_idx
      mmio_attr_update_data  (tdisp_set_mmio_attr_req_s struct)
    """

    def __init__(self, dut):
        self.dut = dut

    def get_valid(self) -> bool:
        return bool(int(self.dut.mmio_attr_update_valid.value))

    def get_tdi_idx(self) -> int:
        return int(self.dut.mmio_attr_tdi_idx.value)

    def get_update_data(self) -> Dict:
        """Read the MMIO attribute update struct fields."""
        raw = self.dut.mmio_attr_update_data
        return {
            "start_addr":     int(raw.start_addr.value),
            "num_4k_pages":   int(raw.num_4k_pages.value),
            "is_non_tee_mem": bool(int(raw.is_non_tee_mem.value)),
        }


# ============================================================================
# StatusBus u2014 output status / interrupt monitoring
# ============================================================================

class StatusBus:
    """Wraps status outputs: TDI state, error IRQ, reset input.

    Output signals (DUT u2192 testbench):
      tdi_error_irq        [NUM_TDI-1:0]
      tdi_state_out        [NUM_TDI-1:0]  (tdisp_tdi_state_e)

    Input signal (testbench u2192 DUT):
      reset_to_unlocked
    """

    def __init__(self, dut, *, num_tdi: int = 2):
        self.dut = dut
        self.num_tdi = num_tdi

    # --- TDI state monitoring ----------------------------------------------

    def get_tdi_state(self, tdi_idx: int) -> int:
        """Return the current TDI state as an integer."""
        return int(_idx(self.dut, "tdi_state_out", tdi_idx).value)

    def get_all_tdi_states(self) -> List[int]:
        """Return TDI states for all TDI instances."""
        return [self.get_tdi_state(i) for i in range(self.num_tdi)]

    # --- Error IRQ monitoring ----------------------------------------------

    def get_error_irq(self, tdi_idx: int) -> bool:
        return bool(int(_idx(self.dut, "tdi_error_irq", tdi_idx).value))

    def get_all_error_irqs(self) -> List[bool]:
        return [self.get_error_irq(i) for i in range(self.num_tdi)]

    # --- Reset control -----------------------------------------------------

    def assert_reset_to_unlocked(self):
        self.dut.reset_to_unlocked.value = 1

    def deassert_reset_to_unlocked(self):
        self.dut.reset_to_unlocked.value = 0

    def pulse_reset_to_unlocked(self, cycles: int = 5):
        """Pulse reset_to_unlocked for a number of clock cycles."""
        import cocotb
        self.assert_reset_to_unlocked()
        for _ in range(cycles):
            yield cocotb.triggers.RisingEdge(self.dut.clk)
        self.deassert_reset_to_unlocked()


# ============================================================================
# Convenience: all-in-one wrapper
# ============================================================================

class TdispBuses:
    """Instantiates all bus functional models at once.

    Usage:
        buses = TdispBuses(dut, num_tdi=2, num_pf=1, num_bars=6)
        buses.cfg.set_version(0x10)
        buses.doe.rx.rx_valid.value = 1
    """

    def __init__(self, dut, *,
                 num_tdi: int = 2,
                 num_pf: int = 1,
                 num_bars: int = 6,
                 report_buf_size: int = 4096):
        self.doe = DoeBus(dut)
        self.cfg = ConfigBus(dut, num_tdi=num_tdi, num_pf=num_pf,
                             num_bars=num_bars,
                             report_buf_size=report_buf_size)
        self.regs = RegWriteBus(dut, num_tdi=num_tdi)
        self.egress = EgressTlpBus(dut, num_tdi=num_tdi)
        self.ingress = IngressTlpBus(dut, num_tdi=num_tdi)
        self.vdm = VdmBus(dut, report_buf_size=report_buf_size)
        self.p2p = P2pBindBus(dut, num_tdi=num_tdi)
        self.mmio = MmioAttrBus(dut)
        self.status = StatusBus(dut, num_tdi=num_tdi)

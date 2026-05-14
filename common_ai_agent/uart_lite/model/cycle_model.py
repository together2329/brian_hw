#!/usr/bin/env python3
"""Executable SSOT cycle-level model for uart_lite. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from .functional_model import FunctionalModel
except ImportError:
    from functional_model import FunctionalModel

try:
    from pymtl3 import Bits1, Bits32, Component, InPort, OutPort, update_ff
    HAS_PYMTL3 = True
except Exception:
    Bits1 = Bits32 = Component = InPort = OutPort = update_ff = None
    HAS_PYMTL3 = False


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Requested executable backend.  PyMTL3 is the default CL shell; FunctionalModel remains the oracle.
MODEL_BACKEND: str = 'pymtl3'

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'register_read': 1, 'register_write': 1, 'tx_byte': 1, 'rx_byte': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}, {'name': 'handshake_3', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'tx_fsm_does_not_start_a_new_frame_until_the_current_frame_completes_no_pipelining_across_bytes', 'description': ''}, {'name': 'rx_fsm_does_not_start_a_new_frame_until_the_current_frame_completes', 'description': ''}, {'name': 'interrupt_pending_bits_update_on_the_same_pclk_edge_as_the_condition_fifo_threshold_crossing_error_detection_frame_completion', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 50, 'throughput': {'max_baud': 'PCLK / (OVERSAMPLE * 1) = 3.125 Mbaud at baud_div=0', 'sustained_bytes_per_second': 'baud_rate / (1 + DATA_WIDTH + parity_en + stop_bits)'}, 'outstanding': {'description': 'FIFO depth bounds maximum queued TX/RX bytes'}, 'pipeline_stages': None, 'queue_depth': None}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_TX_BYTE', 'FM_RX_BYTE', 'FM_BREAK_SEND', 'FM_LOOPBACK']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'handshake_handshake_3': 'handshake_3', 'ordering_tx_fsm_does_not_start_a_new_frame_until_the_current_frame_completes_no_pipelining_across_bytes': 'tx_fsm_does_not_start_a_new_frame_until_the_current_frame_completes_no_pipelining_across_bytes', 'ordering_rx_fsm_does_not_start_a_new_frame_until_the_current_frame_completes': 'rx_fsm_does_not_start_a_new_frame_until_the_current_frame_completes', 'ordering_interrupt_pending_bits_update_on_the_same_pclk_edge_as_the_condition_fifo_threshold_crossing_error_detection_frame_completion': 'interrupt_pending_bits_update_on_the_same_pclk_edge_as_the_condition_fifo_threshold_crossing_error_detection_frame_completion', 'latency_fm_tx_byte': 'latency bin for FM_TX_BYTE', 'latency_fm_rx_byte': 'latency bin for FM_RX_BYTE', 'latency_fm_break_send': 'latency bin for FM_BREAK_SEND', 'latency_fm_loopback': 'latency bin for FM_LOOPBACK'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'uart_lite', 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the UART computes independent of cycle timing.', 'state_variables': [{'name': 'tx_fifo', 'source': 'memory.instances.tx_fifo', 'reset': 'empty', 'description': 'TX FIFO queue of bytes to transmit'}, {'name': 'rx_fifo', 'source': 'memory.instances.rx_fifo', 'reset': 'empty', 'description': 'RX FIFO queue of received bytes'}, {'name': 'tx_active', 'source': 'internal', 'reset': False, 'description': 'True while TX FSM is not IDLE'}, {'name': 'rx_active', 'source': 'internal', 'reset': False, 'description': 'True while RX FSM is not IDLE'}, {'name': 'baud_div', 'source': 'registers.BAUD.baud_div', 'reset': 324, 'description': 'Baud divisor register value'}, {'name': 'parity_en', 'source': 'registers.CTRL.parity_en', 'reset': False, 'description': 'Parity enable'}, {'name': 'parity_odd', 'source': 'registers.CTRL.parity_odd', 'reset': False, 'description': 'Parity odd/even select'}, {'name': 'stop_bits', 'source': 'registers.CTRL.stop_bits', 'reset': False, 'description': '0=1 stop, 1=2 stop'}, {'name': 'loopback', 'source': 'registers.CTRL.loopback', 'reset': False, 'description': 'Loopback mode active'}, {'name': 'break_send', 'source': 'registers.CTRL.break_send', 'reset': False, 'description': 'Break send active; self-clears'}], 'transactions': [{'id': 'FM_TX_BYTE', 'name': 'transmit_byte', 'preconditions': ['tx_enable == 1', 'tx_fifo not empty', 'tx_active == false', 'break_send == false'], 'inputs': ['byte d popped from tx_fifo'], 'outputs': ['tx line: start bit (0), d[0]..d[DATA_WIDTH-1] LSB-first, parity bit (if parity_en), 1 or 2 stop bits (1)', 'tx_active transitions true → false across the frame'], 'side_effects': ['debug counter bytes_tx increments by 1', 'tx_fifo level decreases by 1', 'STAT.tx_empty updates when FIFO becomes empty'], 'error_cases': [{'condition': 'tx_fifo empty when TX FSM requests byte', 'result': 'underrun_err sticky flag set; frame aborted with tx returning to idle (mark)'}]}, {'id': 'FM_RX_BYTE', 'name': 'receive_byte', 'preconditions': ['rx_enable == 1', 'rx_active == false', 'rx_fifo not full'], 'inputs': ['rx line serial stream after 2-FF synchronizer'], 'outputs': ['byte d reconstructed from sampled bits pushed to rx_fifo', 'STAT.rx_not_empty set'], 'side_effects': ['debug counter bytes_rx increments by 1', 'rx_fifo level increases by 1', 'If parity_en and parity mismatch: parity_err sticky set, parities_errored incremented', 'If stop bit(s) not high: frame_err sticky set, frames_errored incremented'], 'error_cases': [{'condition': 'rx_fifo full when new byte ready', 'result': 'overrun_err sticky flag set; received byte discarded'}, {'condition': 'spurious start bit (mid-bit sample high)', 'result': 'rx_active returns false; no byte pushed'}, {'condition': 'frame_err: stop bit sampled low', 'result': 'frame_err sticky set; byte still pushed to rx_fifo if space available'}, {'condition': 'parity_err: computed parity != received parity bit', 'result': 'parity_err sticky set; byte still pushed to rx_fifo if space available'}]}, {'id': 'FM_BREAK_SEND', 'name': 'send_break', 'preconditions': ['break_send written to 1 via CTRL register'], 'inputs': ['none'], 'outputs': ['tx line forced low for duration of one full frame (start+data+parity+stop bits)'], 'side_effects': ['break_send self-clears to 0 after break completes', 'TX FSM held in IDLE during break']}, {'id': 'FM_LOOPBACK', 'name': 'loopback_mode', 'preconditions': ['loopback == 1'], 'inputs': ['tx line output'], 'outputs': ['rx synchronizer input connected to tx output (after 2-FF synchronizer stage)'], 'side_effects': ['External rx pin ignored', 'All TX bytes appear as received bytes when rx_enable == 1']}], 'invariants': ['TX FIFO never underflows during a valid frame — underrun terminates frame early.', 'RX FIFO never overflows without sticky overrun_err flag.', 'Register read side effects are exactly those listed in registers.register_list.', 'Sticky status flags remain set until explicitly cleared via CLR_STAT W1C.', 'Debug counters are free-running, read-only, and wrap at 0xFFFFFFFF.'], 'reference_model_hint': 'tb-gen should implement a Python scoreboard that feeds TX bytes and checks RX bytes match in loopback mode, and checks error flags trigger per scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when TX/RX state, baud ticks, sampling, and interrupts may change.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; keep FunctionalModel as the behavioral oracle and run direct Python smoke checks instead of relying on pytest-pymtl3.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'baud_generator': {'oversample_factor': 16, 'parameter': 'OVERSAMPLE', 'tick_formula': 'baud_tick asserted when internal counter == (baud_div * OVERSAMPLE) - 1; counter resets to 0', 'counter_width': 'ceil(log2(max_baud_div * OVERSAMPLE))', 'mid_sample_point': 7, 'description': 'RX samples data/parity/stop bits at the centre of each bit period (oversample count 7 of 16). Start-bit confirmation also at count 7.'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}, 'tx_byte': {'min_cycles': 'baud_tick_period * (1 + DATA_WIDTH + parity_en + stop_bits)', 'max_cycles': None, 'description': 'TX frame duration; max unbounded if TX FIFO is empty and no new data'}, 'rx_byte': {'min_cycles': 'baud_tick_period * (1 + DATA_WIDTH + parity_en + stop_bits)', 'max_cycles': None, 'description': 'RX frame duration; max unbounded waiting for start bit'}}, 'handshake_rules': [{'signal': 'tx', 'rule': 'Driven synchronously to PCLK; changes only on baud_tick boundaries at TX FSM state transitions. Idle state is high (mark).'}, {'signal': 'rx', 'rule': 'External async input. Passed through 2-FF synchronizer. Synchronizer output sampled on every PCLK edge by RX FSM start-bit detector.'}, {'signal': 'PREADY', 'rule': 'Asserted in the access phase (PSEL=1, PENABLE=1) for all valid register addresses. Deasserted otherwise.'}, {'signal': 'PSLVERR', 'rule': 'Asserted only with PREADY=1 for accesses to unimplemented address ranges.'}], 'pipeline': [{'stage': 'TX_IDLE', 'cycle': 0, 'action': 'Wait for TX FIFO not empty; assert tx_active=false'}, {'stage': 'TX_START', 'cycle': 1, 'action': 'Drive tx=0 for one baud tick period; assert tx_active'}, {'stage': 'TX_DATA', 'cycle': '2..1+DATA_WIDTH', 'action': 'Shift LSB of tx_shift_reg to tx each baud tick; repeat DATA_WIDTH times. tx_shift_reg loaded from TX FIFO on entry.'}, {'stage': 'TX_PARITY', 'cycle': '2+DATA_WIDTH', 'action': 'Drive computed parity bit to tx for one baud tick (present only if parity_en=1)'}, {'stage': 'TX_STOP1', 'cycle': '3+DATA_WIDTH', 'action': 'Drive tx=1 for one baud tick'}, {'stage': 'TX_STOP2', 'cycle': '4+DATA_WIDTH', 'action': 'Drive tx=1 for one baud tick (present only if stop_bits=1)'}, {'stage': 'RX_IDLE', 'cycle': 0, 'action': 'Monitor synchronized rx for falling edge; assert rx_active=false'}, {'stage': 'RX_START_DETECT', 'cycle': 1, 'action': 'On falling edge, wait until oversample count 7'}, {'stage': 'RX_START_CONFIRM', 'cycle': 2, 'action': 'At oversample count 7, sample synchronized rx. If low → confirmed start, advance. If high → spurious, return to RX_IDLE.'}, {'stage': 'RX_DATA', 'cycle': '3..2+DATA_WIDTH', 'action': 'At oversample count 7 of each subsequent bit period, sample rx into rx_shift_reg LSB-first; repeat DATA_WIDTH times'}, {'stage': 'RX_PARITY', 'cycle': '3+DATA_WIDTH', 'action': 'At oversample count 7, sample parity bit; compute expected parity; compare. (present only if parity_en=1)'}, {'stage': 'RX_STOP1', 'cycle': '4+DATA_WIDTH', 'action': 'At oversample count 7, sample stop bit. If high → valid. If low → frame_err.'}, {'stage': 'RX_STOP2', 'cycle': '5+DATA_WIDTH', 'action': 'At oversample count 7, sample second stop bit. (present only if stop_bits=1)'}], 'ordering': ['TX FSM does not start a new frame until the current frame completes (no pipelining across bytes).', 'RX FSM does not start a new frame until the current frame completes.', 'Interrupt pending bits update on the same PCLK edge as the condition (FIFO threshold crossing, error detection, frame completion).'], 'backpressure': ['TX backpressure: TX FSM waits in TX_IDLE when TX FIFO is empty.', 'RX backpressure: If RX FIFO is full when a new byte would be pushed, overrun_err is set and the byte is discarded; RX FSM returns to RX_IDLE.'], 'performance': {'frequency_mhz': 50, 'throughput': {'max_baud': 'PCLK / (OVERSAMPLE * 1) = 3.125 Mbaud at baud_div=0', 'sustained_bytes_per_second': 'baud_rate / (1 + DATA_WIDTH + parity_en + stop_bits)'}, 'outstanding': {'tx_max': 16, 'rx_max': 16, 'description': 'FIFO depth bounds maximum queued TX/RX bytes'}, 'depth': {'fifo_depth': 16, 'oversample_stages': 16, 'description': 'FIFO depth and oversample counter depth'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model TX or RX stage.', 'Baud tick, oversample counter, TX/RX shift registers, and FIFO pointers are observable in waveform.']}}


# ---------------------------------------------------------------------------
# CycleModel
# ---------------------------------------------------------------------------

class CycleModel:
    """Cycle-level model: queues transactions, applies latency/handshake rules,
    delegates all functional evaluation to FunctionalModel.apply()."""

    def __init__(self, params=None):
        self.fl = FunctionalModel(params)
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
        return _LATENCY.get(kind, _LATENCY.get("default", 1))

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
        # Pop one pending transaction if not stalled by outstanding cap
        while self.in_q:
            if self._outstanding >= _OUTSTANDING_CAP:
                break  # stalled: wait for out_q drain
            arrival_t, txn = self.in_q[0]
            if arrival_t > self.now:
                break  # not yet arrived
            self.in_q.pop(0)
            # FunctionalModel is the ONLY oracle — one call per transaction
            try:
                result = self.fl.apply(txn)
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

        # Release completed transactions from outstanding count
        completed = [r for (d, r) in self.out_q if d <= self.now]
        self._outstanding = max(0, self._outstanding - len(completed))

    def observe(self, t: int) -> list[tuple[int, dict]]:
        """Return all results ready at or before t, removing them from out_q."""
        t = int(t)
        ready = [(d, r) for (d, r) in self.out_q if d <= t]
        self.out_q = [(d, r) for (d, r) in self.out_q if d > t]
        return ready

    def coverage(self) -> dict[str, int]:
        return dict(self.cov)

    def run_self_check(self) -> dict:
        """Smoke run: drive every known transaction kind once, tick, observe."""
        self.reset()
        kinds = list(_SELF_CHECK_KINDS) or ["reset"]
        t = 0
        for kind in kinds:
            self.drive({"kind": kind}, t=t)
            t += 1
            self.tick(t)
        # Drain with a long tick to let all latencies expire
        drain_t = t + 200
        self.tick(drain_t)
        obs = self.observe(drain_t)
        total_bins = len(CL_BINS)
        hit_bins = sum(1 for v in self.cov.values() if v > 0)
        return {
            "passed": bool(obs),
            "backend": MODEL_BACKEND,
            "pymtl3_available": HAS_PYMTL3,
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
            "performance_targets": PERFORMANCE_TARGETS,
        }


if HAS_PYMTL3:
    class CycleModelPyMTL(Component):
        """PyMTL3 cycle shell around CycleModel for cycle/performance validation.

        The wrapper intentionally delegates behavioral results to CycleModel,
        which delegates function evaluation to FunctionalModel.  PyMTL owns the
        clocked shell and observable counters used by CL coverage.
        """

        def construct(s):
            s.reset_in = InPort(Bits1)
            s.valid = InPort(Bits1)
            s.ready = OutPort(Bits1)
            s.cycle_count = OutPort(Bits32)
            s.outstanding = OutPort(Bits32)
            s.queue_depth = OutPort(Bits32)
            s._model = CycleModel()

            @update_ff
            def cl_tick():
                if s.reset_in:
                    s._model.reset()
                    s.ready <<= 1
                    s.cycle_count <<= 0
                    s.outstanding <<= 0
                    s.queue_depth <<= 0
                else:
                    next_cycle = s._model.now + 1
                    s._model.tick(next_cycle)
                    s.ready <<= int(s._model._outstanding < _OUTSTANDING_CAP)
                    s.cycle_count <<= next_cycle
                    s.outstanding <<= s._model._outstanding
                    s.queue_depth <<= len(s._model.in_q)
else:
    CycleModelPyMTL = None


def make_pymtl_cycle_model():
    """Return the PyMTL3 cycle shell.  Use direct Python smoke, not pytest-pymtl3."""
    if not HAS_PYMTL3:
        raise RuntimeError("pymtl3 is not importable in this Python environment")
    return CycleModelPyMTL()


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))

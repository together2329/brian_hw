#!/usr/bin/env python3
"""
SSOT-derived executable FunctionalModel for dma_scratch_ui_20260519b.

Semantic authority: dma_scratch_ui_20260519b/yaml/dma_scratch_ui_20260519b.ssot.yaml
Generated/maintained by fl-model-gen from function_model, registers, cycle_model,
error_handling, interrupts, dataflow, and test_requirements sections only.

This module intentionally avoids dataclasses so it remains importable through
importlib.util.module_from_spec(...); spec.loader.exec_module(mod) without
pre-registering sys.modules.
"""

IP_NAME = "dma_scratch_ui_20260519b"
SSOT_PATH = "dma_scratch_ui_20260519b/yaml/dma_scratch_ui_20260519b.ssot.yaml"
MODEL_SOURCE_SECTIONS = [
    "function_model",
    "registers.register_list",
    "cycle_model",
    "dataflow",
    "interrupts",
    "error_handling",
    "test_requirements",
]

TRANSACTION_IDS = [
    "FM_RESET",
    "FM_APB_WRITE",
    "FM_APB_READ",
    "FM_START",
    "FM_READ_ACCEPT",
    "FM_READ_DATA",
    "FM_WRITE_ACCEPT",
]

STATE_VARIABLES = {
    "src_addr": {"width": 32, "reset": 0, "source": "function_model.state_variables.src_addr"},
    "dst_addr": {"width": 32, "reset": 0, "source": "function_model.state_variables.dst_addr"},
    "length_bytes": {"width": 32, "reset": 0, "source": "function_model.state_variables.length_bytes"},
    "irq_enable": {"width": 1, "reset": 0, "source": "function_model.state_variables.irq_enable"},
    "busy": {"width": 1, "reset": 0, "source": "function_model.state_variables.busy"},
    "done": {"width": 1, "reset": 0, "source": "function_model.state_variables.done"},
    "error": {"width": 1, "reset": 0, "source": "function_model.state_variables.error"},
    "irq_status": {"width": 1, "reset": 0, "source": "function_model.state_variables.irq_status"},
    "current_src": {"width": 32, "reset": 0, "source": "function_model.state_variables.current_src"},
    "current_dst": {"width": 32, "reset": 0, "source": "function_model.state_variables.current_dst"},
    "byte_index": {"width": 32, "reset": 0, "source": "function_model.state_variables.byte_index"},
    "captured_rdata": {"width": 32, "reset": 0, "source": "function_model.state_variables.captured_rdata"},
}

LEGAL_ADDRS = (0, 4, 8, 12, 16, 20)
REG_CTRL = 0
REG_SRC_ADDR = 4
REG_DST_ADDR = 8
REG_LENGTH_BYTES = 12
REG_STATUS = 16
REG_IRQ_STATUS = 20
MASK32 = (1 << 32) - 1
MASK4 = 0xF


def _u32(value):
    return int(value or 0) & MASK32


def _bit(value, bit):
    return (_u32(value) >> bit) & 1


def _b(value):
    return 1 if bool(value) else 0


def _txn_get(txn, key, default=0):
    if txn is None:
        return default
    if hasattr(txn, "get"):
        return txn.get(key, default)
    return getattr(txn, key, default)


def _txn_id(txn):
    for key in ("id", "txn_id", "transaction", "name", "op"):
        val = _txn_get(txn, key, None)
        if val is not None:
            return str(val)
    raise ValueError("Transaction missing id/txn_id/transaction/name/op; SSOT transactions are " + ", ".join(TRANSACTION_IDS))


class FunctionalModel(object):
    """Executable SSOT functional oracle.

    apply(txn) accepts a dict-like or attribute-like transaction containing one
    of the SSOT transaction IDs and optional input fields. It returns a dict
    with keys: transaction_id, source_ref, accepted, outputs, state_updates,
    state, trace, and questions.
    """

    def __init__(self):
        self.reset_state()
        self.trace = []

    def reset_state(self):
        self.state = {}
        for name, meta in STATE_VARIABLES.items():
            self.state[name] = int(meta["reset"])
        return dict(self.state)

    def state_traceability(self):
        return {name: dict(meta) for name, meta in STATE_VARIABLES.items()}

    def snapshot(self):
        return dict(self.state)

    def irq_level(self):
        # SSOT invariant: irq equals irq_enable && irq_status.
        return _b(self.state["irq_enable"] and self.state["irq_status"])

    def status_value(self):
        # SSOT FM_APB_READ: {0,error,done,busy} mapped to bits [2:0].
        return ((_b(self.state["error"]) << 2) |
                (_b(self.state["done"]) << 1) |
                _b(self.state["busy"])) & MASK32

    def ctrl_value(self):
        # SSOT FM_APB_READ expression {0,irq_enable,0}: observable irq_enable at bit 1.
        return (_b(self.state["irq_enable"]) << 1) & MASK32

    def irq_status_value(self):
        return _b(self.state["irq_status"])

    def read_data_for_addr(self, paddr):
        paddr = _u32(paddr)
        if paddr == REG_CTRL:
            return self.ctrl_value()
        if paddr == REG_SRC_ADDR:
            return _u32(self.state["src_addr"])
        if paddr == REG_DST_ADDR:
            return _u32(self.state["dst_addr"])
        if paddr == REG_LENGTH_BYTES:
            return _u32(self.state["length_bytes"])
        if paddr == REG_STATUS:
            return self.status_value()
        if paddr == REG_IRQ_STATUS:
            return self.irq_status_value()
        return 0

    def bytes_this_beat(self):
        remaining = max(0, _u32(self.state["length_bytes"]) - _u32(self.state["byte_index"]))
        return 4 if remaining >= 4 else remaining

    def write_strobe_for_current_beat(self):
        b = self.bytes_this_beat()
        if b >= 4:
            return MASK4
        if b <= 0:
            return 0
        return ((1 << b) - 1) & MASK4

    def _result(self, tid, source_ref, outputs=None, state_before=None, state_updates=None, accepted=True, note=None, questions=None):
        if outputs is None:
            outputs = {}
        if state_before is None:
            state_before = {}
        if state_updates is None:
            state_updates = {}
        if questions is None:
            questions = []
        event = {
            "transaction_id": tid,
            "source_ref": source_ref,
            "accepted": bool(accepted),
            "outputs": dict(outputs),
            "state_updates": dict(state_updates),
            "state_before": dict(state_before),
            "state": self.snapshot(),
            "questions": list(questions),
        }
        if note:
            event["note"] = note
        self.trace.append(event)
        return event

    def apply(self, txn):
        tid = _txn_id(txn)
        if tid == "FM_RESET" or tid == "reset":
            return self._fm_reset(txn)
        if tid == "FM_APB_WRITE" or tid == "apb_programming_and_clear":
            return self._fm_apb_write(txn)
        if tid == "FM_APB_READ" or tid == "apb_status_readback":
            return self._fm_apb_read(txn)
        if tid == "FM_START" or tid == "start_transfer":
            return self._fm_start(txn)
        if tid == "FM_READ_ACCEPT" or tid == "memory_read_request_accept":
            return self._fm_read_accept(txn)
        if tid == "FM_READ_DATA" or tid == "memory_read_data_capture":
            return self._fm_read_data(txn)
        if tid == "FM_WRITE_ACCEPT" or tid == "memory_write_accept_and_advance":
            return self._fm_write_accept(txn)
        return {
            "transaction_id": tid,
            "accepted": False,
            "outputs": {},
            "state_updates": {},
            "state": self.snapshot(),
            "questions": [{
                "kind": "SSOT QUESTION",
                "owner": "ssot-gen",
                "yaml_path": "function_model.transactions",
                "message": "Unsupported transaction; SSOT declares only: " + ", ".join(TRANSACTION_IDS),
            }],
        }

    def _fm_reset(self, txn):
        before = self.snapshot()
        self.reset_state()
        outputs = {"pready": 1, "irq": 0}
        return self._result("FM_RESET", "function_model.transactions.FM_RESET", outputs, before, dict(self.state), True,
                            "rstn == 0 clears all architectural state to function_model reset values")

    def _fm_apb_write(self, txn):
        before = self.snapshot()
        paddr = _u32(_txn_get(txn, "paddr", 0))
        pwdata = _u32(_txn_get(txn, "pwdata", 0))
        busy = _b(_txn_get(txn, "busy", self.state["busy"]))
        updates = {}

        # SSOT: Update selected CSR when idle; clear done/irq on CTRL.clear_done.
        if not busy:
            if paddr == REG_SRC_ADDR:
                self.state["src_addr"] = pwdata
                updates["src_addr"] = pwdata
            elif paddr == REG_DST_ADDR:
                self.state["dst_addr"] = pwdata
                updates["dst_addr"] = pwdata
            elif paddr == REG_LENGTH_BYTES:
                self.state["length_bytes"] = pwdata
                updates["length_bytes"] = pwdata
            elif paddr == REG_CTRL:
                self.state["irq_enable"] = _bit(pwdata, 1)
                updates["irq_enable"] = self.state["irq_enable"]

        if paddr == REG_CTRL and _bit(pwdata, 2):
            self.state["done"] = 0
            self.state["irq_status"] = 0
            updates["done"] = 0
            updates["irq_status"] = 0

        if busy and paddr == REG_CTRL and _bit(pwdata, 0):
            self.state["error"] = 1
            updates["error"] = 1

        outputs = {"pready": 1, "pslverr": _b(paddr not in LEGAL_ADDRS), "irq": self.irq_level()}
        return self._result("FM_APB_WRITE", "function_model.transactions.FM_APB_WRITE", outputs, before, updates, True)

    def _fm_apb_read(self, txn):
        before = self.snapshot()
        paddr = _u32(_txn_get(txn, "paddr", 0))
        outputs = {
            "prdata": self.read_data_for_addr(paddr),
            "pready": 1,
            "pslverr": _b(paddr not in LEGAL_ADDRS),
            "irq": self.irq_level(),
        }
        return self._result("FM_APB_READ", "function_model.transactions.FM_APB_READ", outputs, before, {}, True,
                            "APB reads have no state update")

    def _fm_start(self, txn):
        before = self.snapshot()
        length = _u32(self.state["length_bytes"])
        updates = {
            "done": 0,
            "current_src": _u32(self.state["src_addr"]),
            "current_dst": _u32(self.state["dst_addr"]),
            "byte_index": 0,
        }
        self.state["done"] = 0
        self.state["current_src"] = updates["current_src"]
        self.state["current_dst"] = updates["current_dst"]
        self.state["byte_index"] = 0
        if length != 0:
            self.state["busy"] = 1
            updates["busy"] = 1
        else:
            self.state["busy"] = 0
            self.state["error"] = 1
            updates["busy"] = 0
            updates["error"] = 1
        outputs = {
            "mem_rd_valid": _b(length != 0),
            "mem_rd_addr": _u32(self.state["src_addr"]),
            "irq": self.irq_level(),
        }
        return self._result("FM_START", "function_model.transactions.FM_START", outputs, before, updates, True,
                            "Start latches programmed fields; zero length sets error and starts no memory traffic")

    def _fm_read_accept(self, txn):
        before = self.snapshot()
        outputs = {
            "mem_rd_addr": _u32(self.state["current_src"]),
            "mem_rd_valid": _b(self.state["busy"]),
            "irq": self.irq_level(),
        }
        return self._result("FM_READ_ACCEPT", "function_model.transactions.FM_READ_ACCEPT", outputs, before, {}, True,
                            "Accepted read request remains outstanding until mem_rdata_valid")

    def _fm_read_data(self, txn):
        before = self.snapshot()
        mem_rdata = _u32(_txn_get(txn, "mem_rdata", 0))
        self.state["captured_rdata"] = mem_rdata
        updates = {"captured_rdata": mem_rdata}
        outputs = {
            "mem_wr_valid": 1,
            "mem_wr_data": mem_rdata,
            "mem_wr_addr": _u32(self.state["current_dst"]),
            "mem_wr_strb": self.write_strobe_for_current_beat(),
            "irq": self.irq_level(),
        }
        return self._result("FM_READ_DATA", "function_model.transactions.FM_READ_DATA", outputs, before, updates, True,
                            "Read data captured and presented as the immediately following write beat")

    def _fm_write_accept(self, txn):
        before = self.snapshot()
        beat = self.bytes_this_beat()
        next_index = _u32(self.state["byte_index"] + beat)
        next_src = _u32(self.state["current_src"] + beat)
        next_dst = _u32(self.state["current_dst"] + beat)
        complete = next_index >= _u32(self.state["length_bytes"])

        self.state["byte_index"] = next_index
        self.state["current_src"] = next_src
        self.state["current_dst"] = next_dst
        updates = {"byte_index": next_index, "current_src": next_src, "current_dst": next_dst}
        if complete:
            self.state["busy"] = 0
            self.state["done"] = 1
            self.state["irq_status"] = 1
            updates.update({"busy": 0, "done": 1, "irq_status": 1})
        else:
            # SSOT expression says busy remains busy when not complete.
            updates["busy"] = self.state["busy"]

        outputs = {
            "mem_rd_valid": _b(not complete),
            "mem_rd_addr": next_src,
            "irq": self.irq_level(),
        }
        return self._result("FM_WRITE_ACCEPT", "function_model.transactions.FM_WRITE_ACCEPT", outputs, before, updates, True,
                            "Write accept advances pointers; final beat commits done and irq_status")

    def check_invariants(self):
        failures = []
        if self.state["irq_enable"] not in (0, 1):
            failures.append("irq_enable must be 0/1")
        for name in ("busy", "done", "error", "irq_status"):
            if self.state[name] not in (0, 1):
                failures.append(name + " must be 0/1")
        if self.irq_level() != _b(self.state["irq_enable"] and self.state["irq_status"]):
            failures.append("irq equals irq_enable && irq_status invariant failed")
        return failures


def _assert_equal(got, exp, msg):
    if got != exp:
        raise AssertionError("%s: got %r expected %r" % (msg, got, exp))


def run_self_check():
    fm = FunctionalModel()
    results = []

    r = fm.apply({"id": "FM_RESET", "rstn": 0})
    _assert_equal(r["outputs"]["pready"], 1, "reset pready")
    _assert_equal(r["outputs"]["irq"], 0, "reset irq")
    results.append({"id": "FM_RESET", "passed": True, "source_ref": "function_model.transactions.FM_RESET"})

    r = fm.apply({"id": "FM_APB_WRITE", "paddr": 4, "pwdata": 0x1000})
    _assert_equal(fm.state["src_addr"], 0x1000, "src write")
    r = fm.apply({"id": "FM_APB_WRITE", "paddr": 8, "pwdata": 0x2000})
    _assert_equal(fm.state["dst_addr"], 0x2000, "dst write")
    r = fm.apply({"id": "FM_APB_WRITE", "paddr": 12, "pwdata": 5})
    _assert_equal(fm.state["length_bytes"], 5, "length write")
    r = fm.apply({"id": "FM_APB_WRITE", "paddr": 0, "pwdata": 0x2})
    _assert_equal(fm.state["irq_enable"], 1, "irq enable write")
    results.append({"id": "FM_APB_WRITE", "passed": True, "source_ref": "function_model.transactions.FM_APB_WRITE"})

    r = fm.apply({"id": "FM_APB_READ", "paddr": 4})
    _assert_equal(r["outputs"]["prdata"], 0x1000, "src read")
    r = fm.apply({"id": "FM_APB_READ", "paddr": 16})
    _assert_equal(r["outputs"]["prdata"], 0, "status initial read")
    results.append({"id": "FM_APB_READ", "passed": True, "source_ref": "function_model.transactions.FM_APB_READ"})

    r = fm.apply({"id": "FM_START"})
    _assert_equal(fm.state["busy"], 1, "start busy")
    _assert_equal(r["outputs"]["mem_rd_valid"], 1, "start read valid")
    _assert_equal(r["outputs"]["mem_rd_addr"], 0x1000, "start read addr")
    results.append({"id": "FM_START", "passed": True, "source_ref": "function_model.transactions.FM_START"})

    r = fm.apply({"id": "FM_READ_ACCEPT"})
    _assert_equal(r["outputs"]["mem_rd_addr"], 0x1000, "read accept addr")
    results.append({"id": "FM_READ_ACCEPT", "passed": True, "source_ref": "function_model.transactions.FM_READ_ACCEPT"})

    r = fm.apply({"id": "FM_READ_DATA", "mem_rdata": 0xAABBCCDD})
    _assert_equal(r["outputs"]["mem_wr_valid"], 1, "read data write valid")
    _assert_equal(r["outputs"]["mem_wr_data"], 0xAABBCCDD, "read data payload")
    _assert_equal(r["outputs"]["mem_wr_addr"], 0x2000, "read data write addr")
    _assert_equal(r["outputs"]["mem_wr_strb"], 0xF, "first strobe full")
    results.append({"id": "FM_READ_DATA", "passed": True, "source_ref": "function_model.transactions.FM_READ_DATA"})

    r = fm.apply({"id": "FM_WRITE_ACCEPT"})
    _assert_equal(fm.state["byte_index"], 4, "first write index")
    _assert_equal(r["outputs"]["mem_rd_valid"], 1, "next read valid")
    _assert_equal(r["outputs"]["mem_rd_addr"], 0x1004, "next read addr")
    fm.apply({"id": "FM_READ_ACCEPT"})
    r = fm.apply({"id": "FM_READ_DATA", "mem_rdata": 0x11223344})
    _assert_equal(r["outputs"]["mem_wr_strb"], 0x1, "final partial strobe")
    r = fm.apply({"id": "FM_WRITE_ACCEPT"})
    _assert_equal(fm.state["busy"], 0, "complete busy clear")
    _assert_equal(fm.state["done"], 1, "complete done")
    _assert_equal(fm.state["irq_status"], 1, "complete irq status")
    _assert_equal(r["outputs"]["irq"], 1, "completion irq")
    results.append({"id": "FM_WRITE_ACCEPT", "passed": True, "source_ref": "function_model.transactions.FM_WRITE_ACCEPT"})

    # Error and clear paths from SSOT error_handling/FM_APB_WRITE.
    fm2 = FunctionalModel()
    fm2.apply({"id": "FM_APB_WRITE", "paddr": 12, "pwdata": 0})
    fm2.apply({"id": "FM_START"})
    _assert_equal(fm2.state["error"], 1, "zero length sets error")
    fm.apply({"id": "FM_APB_WRITE", "paddr": 0, "pwdata": 0x4})
    _assert_equal(fm.state["done"], 0, "clear done")
    _assert_equal(fm.state["irq_status"], 0, "clear irq_status")

    inv = fm.check_invariants() + fm2.check_invariants()
    if inv:
        raise AssertionError("Invariant failures: " + "; ".join(inv))

    represented = sorted(set(item["id"] for item in results))
    missing = [tid for tid in TRANSACTION_IDS if tid not in represented]
    if missing:
        raise AssertionError("Missing self-check coverage for " + ", ".join(missing))
    return {
        "passed": True,
        "ip": IP_NAME,
        "ssot_path": SSOT_PATH,
        "model_path": "dma_scratch_ui_20260519b/model/functional_model.py",
        "transaction_results": results,
        "represented_transactions": represented,
        "missing_transactions": missing,
        "state_variables": fm.state_traceability(),
        "invariant_failures": inv,
        "trace_event_count": len(fm.trace) + len(fm2.trace),
        "ssot_tbd_report": "none",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_self_check(), indent=2, sort_keys=True))

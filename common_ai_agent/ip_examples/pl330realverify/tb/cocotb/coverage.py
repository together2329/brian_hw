#!/usr/bin/env python3
"""Functional and cycle coverage collector for pl330realverify."""

import json
from pathlib import Path


class CoverageCollector:
    def __init__(self, ip: str = "pl330realverify", root: str = "."):
        self.ip = ip
        self.root = Path(root)
        self.bins: dict[str, bool] = {}
        self._load_bins()

    def _load_bins(self):
        # Derive bins from SSOT functional_model coverage seed
        try:
            spec = (
                self.root / self.ip / "model" / "functional_model.py"
            ).read_text(encoding="utf-8")
            # Extract SSOT_MODEL fcov_bins via a simple parse
            import ast
            tree = ast.parse(spec)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "SSOT_MODEL":
                            # Try compile-time eval (risky); safer: exec in safe env
                            try:
                                env = {}
                                exec(compile(ast.Module([node], type_ignores=[]), "<string>", "exec"), env)
                                model = env.get("SSOT_MODEL", {})
                                for b in model.get("fcov_bins", []):
                                    if isinstance(b, dict) and "id" in b:
                                        self.bins[b["id"]] = False
                            except Exception:
                                pass
        except Exception:
            pass
        # Fallback: use scenario IDs + transaction IDs from SSOT yaml if model parse fails
        if not self.bins:
            for sid in [
                "SC_RESET_APB_executed", "SC_SINGLE_BEAT_COPY_executed",
                "SC_MULTI_BEAT_COPY_executed", "SC_AXI_BACKPRESSURE_executed",
                "SC_WFP_EVENT_executed", "SC_AXI_READ_FAULT_executed",
                "SC_AXI_WRITE_FAULT_executed", "SC_W1C_IRQ_CLEAR_executed",
                "SC_DEBUG_COMMAND_executed",
                "fcov_reset", "fcov_apb_read", "fcov_apb_write",
                "fcov_transfer", "fcov_wfp", "fcov_fault_rd", "fcov_fault_wr",
                "fcov_irq_clear",
                "ccov_apb_access", "ccov_axi_ar_hold", "ccov_axi_r_capture",
                "ccov_axi_aw_w", "ccov_axi_b", "ccov_irq_level",
                "ccov_pipeline_all_stages", "ccov_channel_fsm",
                "ccov_performance_outstanding", "ccov_performance_depth",
                "ccov_performance_throughput",
            ]:
                self.bins[sid] = False

    def hit(self, bin_id: str):
        if bin_id in self.bins:
            self.bins[bin_id] = True

    def dump(self, path: str = "") -> Path:
        out = Path(path) if path else self.root / self.ip / "cov" / "coverage_functional.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "ip": self.ip,
            "functional_bins": self.bins,
            "hit_count": sum(1 for v in self.bins.values() if v),
            "total": len(self.bins),
        }, indent=2))
        return out

    def summary_md(self, path: str = "") -> Path:
        out = Path(path) if path else self.root / self.ip / "sim" / "coverage_report.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        hit = sum(1 for v in self.bins.values() if v)
        total = len(self.bins)
        lines = [
            f"# Coverage Report: {self.ip}",
            f"- Functional bins: {hit}/{total}",
            "## Bin Status",
        ]
        for bid, val in sorted(self.bins.items()):
            lines.append(f"- {'[HIT]' if val else '[MISS]'} {bid}")
        out.write_text("\n".join(lines))
        return out

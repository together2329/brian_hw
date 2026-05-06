#!/usr/bin/env python3
"""Generate SSOT YAML for simple_gpio3."""
from pathlib import Path
import yaml

ip = "simple_gpio3"

ssot = {
    "top_module": ip,
    "parameters": [
        {"name": "WIDTH", "value": 16},
        {"name": "HAS_IRQ", "value": 1},
    ],
    "clocks": [
        {"name": "clk", "period_ns": 10.0, "source_port": "clk"},
    ],
    "resets": [
        {"name": "rst_n", "polarity": "active_low", "source_port": "rst_n"},
    ],
    "ports": [
        {"name": "clk",     "dir": "input",  "width": 1,  "kind": "clock"},
        {"name": "rst_n",   "dir": "input",  "width": 1,  "kind": "reset"},
        {"name": "psel",    "dir": "input",  "width": 1,  "bus": "S_APB"},
        {"name": "penable", "dir": "input",  "width": 1,  "bus": "S_APB"},
        {"name": "pwrite",  "dir": "input",  "width": 1,  "bus": "S_APB"},
        {"name": "paddr",   "dir": "input",  "width": 12, "bus": "S_APB"},
        {"name": "pwdata",  "dir": "input",  "width": 32, "bus": "S_APB"},
        {"name": "prdata",  "dir": "output", "width": 32, "bus": "S_APB"},
        {"name": "pready",  "dir": "output", "width": 1,  "bus": "S_APB"},
        {"name": "pslverr", "dir": "output", "width": 1,  "bus": "S_APB"},
        {"name": "gpio_i",  "dir": "input",  "width": 16, "bus": "GPIO"},
        {"name": "gpio_o",  "dir": "output", "width": 16, "bus": "GPIO"},
        {"name": "gpio_oe", "dir": "output", "width": 16, "bus": "GPIO"},
        {"name": "irq",     "dir": "output", "width": 1,  "bus": "IRQ"},
    ],
    "busInterfaces": [
        {"name": "S_APB", "proto": "APB",  "role": "slave",  "side": "left",  "width": 32},
        {"name": "IRQ",   "proto": "IRQ",  "role": "master", "side": "right", "width": 1},
        {"name": "GPIO",  "proto": "GPIO", "role": "master", "side": "right", "width": 16},
    ],
    "memoryMap": [
        {"name": "regs", "base": "0x4000_5000", "range": "0x1000"},
    ],
    "sub_modules": [
        {
            "name": "simple_gpio3_regs",
            "file": "rtl/simple_gpio3_regs.sv",
            "ownership": "manifest",
            "role": "apb_register_bank",
        },
        {
            "name": "simple_gpio3_pins",
            "file": "rtl/simple_gpio3_pins.sv",
            "ownership": "manifest",
            "role": "pin_direction_data_path",
        },
        {
            "name": "simple_gpio3_irq",
            "file": "rtl/simple_gpio3_irq.sv",
            "ownership": "manifest",
            "role": "edge_interrupt_controller",
        },
    ],
}

p = Path(ip) / "yaml" / (ip + ".ssot.yaml")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(yaml.dump(ssot, default_flow_style=False, sort_keys=False), encoding="utf-8")

# Validate round-trip
d = yaml.safe_load(p.read_text())
assert d["top_module"] == ip
n_bus = len(d.get("busInterfaces", []))
n_sub = len(d.get("sub_modules", []))
assert n_bus >= 3
assert n_sub >= 3

print("SSOT_PARSE_OK " + str(p) + " busInterfaces=" + str(n_bus) + " sub_modules=" + str(n_sub))
print("METRICS: ssot.complete=1, ssot.files=1)

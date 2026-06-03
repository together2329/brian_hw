# Bus protocol whitelist

The Architect only accepts these `proto` values in `connections[].proto`
and in any `busInterfaces[].proto`:

| proto  | Description              | Carries          |
| ------ | ------------------------ | ---------------- |
| AXI4   | AMBA AXI4 full           | data + control   |
| AXI4L  | AMBA AXI4-Lite           | register access  |
| ACE    | AXI Coherency Extensions | coherent traffic |
| AHB    | AMBA AHB                 | bus master       |
| APB    | AMBA APB                 | peripheral regs  |
| AXIS   | AXI-Stream               | streaming        |
| IRQ    | Interrupt line           | level/edge       |
| CLK    | Clock                    | clk-in           |
| RST    | Reset                    | rst-in           |

## Rejection rules

- Anything else → reject the edit with a one-liner naming the offending
  field. Do not silently coerce.
- Vendor-specific protocols (e.g. "TileLink", "OCP") must be wrapped
  by an adapter IP first; the architect view only sees the AMBA edge.
- Custom-named ports without a `proto` default to `AXI4`. The architect
  flags this as a warning and recommends explicit annotation.

## Master/slave check

Every connection must have exactly one master and one slave end:

- `from: A/iface_a` must be `role: master` in A's leaf SSOT.
- `to:   B/iface_b` must be `role: slave`  in B's leaf SSOT.

A mismatch (master→master or slave→slave) is a hard error. If the user
intended a system-level bus (e.g. APB into a bridge), the bridge IP
needs an explicit slave-side `busInterface` entry.

CLK and RST connections are exempt from the role check (they are always
broadcast: 1 source → N sinks).

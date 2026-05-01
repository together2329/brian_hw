"""IP-XACT (IEEE 1685) → SSOT YAML importer.

Reads an IP-XACT XML file and converts it into the SSOT-lite shape this
project consumes:

    top_module: <name>
    parameters: [{ name, value }, …]
    clocks:     [{ name, period_ns, source_port }, …]
    resets:     [{ name, polarity, source_port }, …]
    busInterfaces:
      - { name, proto, role, side, width }
    memoryMap:
      - { name, base, range, addressBlocks: [{ name, offset, size, access }] }

Stdlib only — handles IEEE 1685-2014 and 1685-2022 (`ipxact:` prefix) plus
the older 1685-2009 (`spirit:` prefix). Unknown / vendor-specific elements
are silently ignored.

Usage (Python):
    from core.ipxact_import import import_ipxact_file
    ssot = import_ipxact_file("foo.xml")           # → dict
    import_ipxact_file("foo.xml", out_path="...")  # writes YAML

Usage (agent tool, see core/tools.py): `ipxact_import(xml_path=…, ip_name=…)`
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple


# IP-XACT element names appear under one of these namespaces depending on
# the spec version. We strip the namespace at parse time to keep the rest
# of the code version-agnostic.
_NAMESPACES = (
    "{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}",
    "{http://www.accellera.org/XMLSchema/IPXACT/1685-2014}",
    "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009}",
    "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5}",
    "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4}",
)


def _local(tag: str) -> str:
    """Strip XML namespace; return bare local-name."""
    if tag and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _findall(elem, name: str):
    """Return direct children whose local-name matches `name`."""
    return [c for c in list(elem) if _local(c.tag) == name]


def _find(elem, name: str):
    for c in list(elem):
        if _local(c.tag) == name:
            return c
    return None


def _text(elem, name: str, default: str = "") -> str:
    c = _find(elem, name)
    if c is None or c.text is None:
        return default
    return c.text.strip()


def _path_text(elem, *names: str, default: str = "") -> str:
    cur = elem
    for n in names:
        cur = _find(cur, n) if cur is not None else None
        if cur is None:
            return default
    if cur.text is None:
        return default
    return cur.text.strip()


def _parse_int(s: str) -> Optional[int]:
    if not s:
        return None
    s = s.strip().replace("_", "").replace("'", "")
    try:
        if s.lower().startswith("0x"): return int(s, 16)
        if s.lower().startswith("0b"): return int(s, 2)
        if s.lower().startswith("0o"): return int(s, 8)
        return int(s, 10)
    except (ValueError, TypeError):
        return None


def _hexlit(n: int, pad_to_4=True) -> str:
    """Pretty hex: 0x4000_2000."""
    h = f"{n:x}"
    if pad_to_4 and len(h) % 4 != 0:
        h = h.zfill(((len(h) // 4) + 1) * 4)
    if len(h) > 4:
        # group every 4 hex digits with underscore from the right
        rev = h[::-1]
        groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
        h = "_".join(groups)[::-1]
    return f"0x{h}"


# ── busType → our short proto label ─────────────────────────────────
_PROTO_MAP = {
    "AXI": "AXI4", "AXI4": "AXI4", "AXI3": "AXI4",
    "AXI4LITE": "AXI4L", "AXI4-LITE": "AXI4L", "AXI_LITE": "AXI4L", "AXIL": "AXI4L",
    "ACE": "ACE", "ACE_LITE": "ACE", "ACELITE": "ACE",
    "AHB": "AHB", "AHB3": "AHB", "AHB5": "AHB", "AHBLITE": "AHB",
    "APB": "APB", "APB3": "APB", "APB4": "APB",
    "AXIS": "AXIS", "AXISTREAM": "AXIS", "AXI4STREAM": "AXIS", "AXI-STREAM": "AXIS",
    "IRQ": "IRQ", "INTERRUPT": "IRQ",
    "CLOCK": "CLK", "CLK": "CLK",
    "RESET": "RST", "RST": "RST",
}


def _normalize_proto(s: str) -> str:
    if not s: return "AXI4"
    key = re.sub(r"[^A-Z0-9]", "", s.upper())
    if key in _PROTO_MAP: return _PROTO_MAP[key]
    # heuristic substring fallbacks
    for k, v in _PROTO_MAP.items():
        if k in key: return v
    return s.upper()


def _bus_role(busif_elem) -> str:
    """IP-XACT busInterface contains exactly one of <slave>, <master>,
    <system>, <mirroredSlave>, etc. Map to slave/master/system."""
    for c in list(busif_elem):
        ln = _local(c.tag).lower()
        if ln in ("slave", "target"):           return "slave"
        if ln in ("master", "initiator"):       return "master"
        if ln == "mirroredslave":               return "master"  # mirror = role flip
        if ln == "mirroredmaster":              return "slave"
        if ln == "system":                       return "system"
        if ln == "monitor":                      return "monitor"
    return "slave"


def _side_for(role: str, hint: str = "") -> str:
    """Pick a default side for the diagram."""
    h = (hint or "").lower()
    if h in ("left", "right", "top", "bottom"): return h
    if role == "master": return "right"
    if role == "slave":  return "left"
    return "left"


# ── per-section converters ──────────────────────────────────────────
def _parse_parameters(component) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for sect_name in ("parameters", "modelParameters"):
        sect = _find(component, sect_name)
        if sect is None:
            # `model/modelParameters` is one level deeper
            mdl = _find(component, "model")
            if mdl is not None:
                sect = _find(mdl, sect_name)
        if sect is None: continue
        for p in _findall(sect, "parameter") + _findall(sect, "modelParameter"):
            name = _text(p, "name")
            value = _text(p, "value")
            if not name: continue
            n = _parse_int(value)
            out.append({"name": name, "value": n if n is not None else (value or "")})
    return out


def _parse_ports_for_clkrst(component) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Look at <model><ports> for ports whose name matches clk/rst patterns
    and emit clocks: / resets: entries (the canonical SSOT shape used by
    syn/sim workflows)."""
    clocks: List[Dict[str, Any]] = []
    resets: List[Dict[str, Any]] = []
    mdl = _find(component, "model")
    if mdl is None: return clocks, resets
    ports = _find(mdl, "ports")
    if ports is None: return clocks, resets
    for prt in _findall(ports, "port"):
        name = _text(prt, "name")
        if not name: continue
        wire = _find(prt, "wire")
        direction = _path_text(prt, "wire", "direction", default="in")
        if direction != "in": continue
        ln = name.lower()
        if "clk" in ln or "clock" in ln:
            clocks.append({
                "name": name,
                "period_ns": 10.0,
                "source_port": name,
            })
        elif "rst" in ln or "reset" in ln:
            # ARM-ish naming: aresetn / rstn / rst_n / xxx_resetn → active_low.
            # Catch any name ending in 'n' since rst+n is the universal
            # active-low marker; also catch the rare "_n_xxx" mid-name form.
            polarity = "active_low" if (ln.endswith("n") or "_n_" in ln) else "active_high"
            resets.append({
                "name": name,
                "polarity": polarity,
                "sync_async": "async_assert_sync_deassert",
                "source_port": name,
            })
    return clocks, resets


def _parse_bus_interfaces(component) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    sect = _find(component, "busInterfaces")
    if sect is None: return out
    for bif in _findall(sect, "busInterface"):
        name = _text(bif, "name")
        if not name: continue
        bt = _find(bif, "busType")
        proto_raw = ""
        if bt is not None:
            # busType has attributes (vendor/library/name/version) — no body
            for k, v in bt.attrib.items():
                if _local(k) == "name":
                    proto_raw = v; break
        proto = _normalize_proto(proto_raw)
        role = _bus_role(bif)
        # Width: AXI buses carry a "BUSWIDTH" parameter (or DATA_WIDTH).
        width = None
        for sect_name in ("parameters",):
            psect = _find(bif, sect_name)
            if psect is None: continue
            for p in _findall(psect, "parameter"):
                pname = _text(p, "name").upper()
                if any(k in pname for k in ("BUSWIDTH", "DATA_WIDTH", "WIDTH")):
                    width = _parse_int(_text(p, "value"))
                    break
        out.append({
            "name": name,
            "proto": proto,
            "role": role,
            "side": _side_for(role),
            **({"width": width} if width is not None else {}),
        })
    return out


def _parse_memory_maps(component) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    sect = _find(component, "memoryMaps")
    if sect is None: return out
    for mm in _findall(sect, "memoryMap"):
        mm_name = _text(mm, "name", "regs")
        addr_blocks: List[Dict[str, Any]] = []
        first_base: Optional[int] = None
        first_range: Optional[int] = None
        for ab in _findall(mm, "addressBlock"):
            ab_name = _text(ab, "name")
            base = _parse_int(_text(ab, "baseAddress"))
            rng = _parse_int(_text(ab, "range"))
            width = _parse_int(_text(ab, "width")) or 32
            usage = _text(ab, "usage", "register")
            if first_base is None and base is not None:
                first_base = base
                first_range = rng
            addr_blocks.append({
                "name": ab_name,
                "offset": _hexlit(base) if base is not None else "0x0",
                "size":   width,
                "access": "rw",
                **({"range": _hexlit(rng)} if rng is not None else {}),
                **({"usage": usage} if usage and usage != "register" else {}),
            })
        out.append({
            "name": mm_name,
            "base": _hexlit(first_base) if first_base is not None else "0x0",
            "range": _hexlit(first_range) if first_range is not None else "0x1000",
            "addressBlocks": addr_blocks,
        })
    return out


# ── public entry point ─────────────────────────────────────────────
def import_ipxact(xml_text: str, ip_name: Optional[str] = None) -> Dict[str, Any]:
    """Parse an IP-XACT XML *string* into our SSOT-lite dict.

    Args:
        xml_text: full XML payload as text.
        ip_name:  override for top_module (default: pulled from <name>).
    """
    root = ET.fromstring(xml_text)
    # Handle two layouts: <component> as root (our usual case) OR
    # <designConfiguration>/<design>/etc. with a <component> child.
    if _local(root.tag) == "component":
        component = root
    else:
        component = _find(root, "component") or root

    name = ip_name or _text(component, "name") or "unnamed_ip"
    vendor  = _text(component, "vendor")
    library = _text(component, "library")
    version = _text(component, "version")

    parameters = _parse_parameters(component)
    clocks, resets = _parse_ports_for_clkrst(component)
    bus_ifs   = _parse_bus_interfaces(component)
    mem_maps  = _parse_memory_maps(component)

    ssot: Dict[str, Any] = {
        "top_module": name,
        "rtl_files":  [f"{name}/rtl/{name}.sv"],
    }
    if clocks: ssot["clocks"] = clocks
    if resets: ssot["resets"] = resets
    if parameters: ssot["parameters"] = parameters
    if bus_ifs:    ssot["busInterfaces"] = bus_ifs
    if mem_maps:   ssot["memoryMap"] = mem_maps
    ssot["io_delay"] = {"input_pct": 0.20, "output_pct": 0.20}
    ssot["_ipxact_origin"] = {
        "vendor": vendor, "library": library, "name": name, "version": version,
    }
    return ssot


def import_ipxact_file(xml_path: str,
                       ip_name: Optional[str] = None,
                       out_path: Optional[str] = None) -> Dict[str, Any]:
    """Read an IP-XACT XML file → SSOT dict (and optionally write YAML).

    Args:
        xml_path: source XML path.
        ip_name:  override for top_module.
        out_path: if given, write YAML there. Otherwise return dict only.
    """
    if not os.path.isfile(xml_path):
        raise FileNotFoundError(xml_path)
    with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
        xml_text = f.read()
    ssot = import_ipxact(xml_text, ip_name=ip_name)
    if out_path:
        try: import yaml as _yaml
        except ImportError as e:
            raise RuntimeError(
                "PyYAML is required to write SSOT YAML. "
                "Install with `pip install pyyaml`."
            ) from e
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("# Auto-imported from IP-XACT — review and edit as needed.\n")
            _yaml.safe_dump(ssot, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return ssot

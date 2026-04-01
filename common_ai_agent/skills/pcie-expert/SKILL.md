---
name: pcie-expert
description: >
  PCIe 7.0 spec expert. Covers TLP/DLLP packet structure, LTSSM state machine, Flow Control,
  Lane Equalization, Power Management, AER, ACS, TDISP, IDE, ATS, IOV,
  Physical/Data Link/Transaction Layer, Flit Mode, Link Training, Virtual Channel,
  Root Complex, Endpoint, and all PCIe registers/capabilities.
  Trigger on: pcie, pci express, tlp, dllp, ltssm, tdisp, ide, ats, aer, acs, flit,
  equalization, power management, link training, physical layer, data link, transaction layer.
priority: 85
activation:
  keywords: [pcie, "pci express", tlp, dllp, ltssm, "state machine", "flow control",
             equalization, aer, acs, ide, tdisp, "root complex", endpoint, completion,
             "power management", "physical layer", "data link layer", "transaction layer",
             "address translation", ats, iov, "virtual channel", flit, "lane equalization",
             "link training", register, config, specification, spec]
  file_patterns: ["*.md", "*.pdf", "*.txt", "*.rst"]
  auto_detect: true
requires_tools: [spec_navigate, grep_file, read_lines]
related_skills: [verilog-expert, protocol-spec-expert]
---

# ⚠️ MANDATORY: Use spec_navigate to look up the spec

**All PCIe spec questions MUST be answered by navigating the spec with `spec_navigate`.
Never answer from general knowledge alone.**

## How to navigate

```
# 1. Get the table of contents
Action: spec_navigate(spec="pcie", node_id="root")

# 2. Drill into the relevant chapter — leaf nodes contain the full content
Action: spec_navigate(spec="pcie", node_id="<section_id>")

# 3. If deeper search is needed — grep under the path, then read specific lines
Action: grep_file(pattern="<keyword>", path="<directory from navigate path>")
Action: read_lines(path="<file_path>", start_line=<N>, end_line=<N+80>)
```

## Rules
- **Never guess acronyms or terms** — do not assume anything before seeing navigate results
- If a leaf node's `content` is sufficient, no further read is needed
- grep paths must be derived from `spec_navigate`'s returned `path` — no arbitrary paths
- Do not use `spec_search`

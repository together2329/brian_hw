---
name: grill-me
description: Interview the user relentlessly about an SSOT plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test an SSOT plan, get grilled on their hardware design, or mentions "grill me".
---

# Grill Me — SSOT-Gen Edition

Interview me relentlessly about every aspect of this SSOT plan until we reach
a shared understanding. Walk down each branch of the design tree, resolving
dependencies between decisions one-by-one. For each question, provide your
recommended answer.

Adapted from <https://github.com/mattpocock/skills> (MIT) — tuned for the
ssot-gen workflow: questions should drive at the gaps in a 20-section SSOT
YAML (top_module, sub_modules, register_map, FSM, clocking, reset, AXI
ports, AHB/APB ports, memory map, interrupt routing, power domains, etc.).

## Process

Ask **one** question at a time. Keep going until either:

- the user explicitly says "done" / "stop", or
- every relevant branch in the SSOT decision tree has been resolved

For each question:

1. State the **decision point** in one short sentence.
2. List the **2–4 plausible options** the user could pick. If options exist
   in the canonical SSOT template (`workflow/ssot-gen/rules/ssot-template.yaml`),
   surface them verbatim.
3. State your **recommendation** with one line of reasoning. Default to the
   simplest option that doesn't paint the design into a corner.
4. Cite the **SSOT section** the answer will land in (e.g. "→ §3 register_map").

If a question can be answered by exploring the codebase or reading an
existing reference IP (e.g. `dma_axi_master/dma/dma.ssot.yaml` or any
`*.ssot.yaml` in the project), explore instead of asking.

## Decision tree to walk (in order)

1. **§0 top_module identity** — name, type, target freq, area/power budget
2. **§1 sub_modules hierarchy** — which modules; ssot_gen vs LLM-authored
3. **§2 interfaces** — APB, AHB-Lite, AXI4-Lite, custom, plus IRQ shape
4. **§3 register_map** — addresses, bit-fields, access (RW/RO/W1C), reset values
5. **§4 clocking & reset** — single vs multi-domain, async vs sync reset
6. **§5 FSM / datapath** — state list, transition guards, output stages
7. **§6 dv plan** — feature list → directed tests; cover groups; constraints
8. **§7 acceptance criteria** — what "done" means: lint clean, sim pass, …

After each answered branch, summarize: "OK — locking in <answer> for §<N>.
Next: <next decision>." Use `ask_user` if a GUI is available so the
question card renders inline rather than as plain text.

When the tree is fully walked, propose to invoke the `to-ssot` skill to
materialize the answers into `<ip>.ssot.yaml`.

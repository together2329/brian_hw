# Deterministic Emit Stages (fl-model-gen, cl-model-gen)

Some pipeline stages do **not** call an LLM. They are mechanical
translators that read SSOT and write a Python or JSON artifact whose
content is fully determined by the SSOT input. This page explains why
that design choice exists, which stages it applies to today, and what
the failure modes look like.

Related: [[full-flow-pipeline]] · [[workflow-ownership-and-boundaries]]
· [[rtl-gen-ssot-contract]] · [[golden-todo-evidence]]
· [[provider-and-llm-call-accounting]]

## Stages and their scripts

| Stage | Slash | Script (under `workflow/`) | Output |
|---|---|---|---|
| **fl-model-gen** | `/ssot-fl-model <ip>` | `fl-model-gen/scripts/emit_fl_model.py` | `<ip>/model/functional_model.py`, `<ip>/model/decomposition.json`, `<ip>/model/fl_model_check.json`, `<ip>/model/manifest.json`, `<ip>/cov/fcov_plan.json` |
| **cl-model-gen** | `/ssot-cycle-model <ip>` | `fl-model-gen/scripts/emit_cycle_model.py` | `<ip>/model/cycle_model.py`, `<ip>/cov/cycle_cov_plan.json` (and cl-side artifacts) |
| equiv-goals | `/ssot-equiv-goals <ip>` | script-driven combination of fl + cl | `<ip>/verify/equivalence_goals.json` |
| dual-fcov | `/ssot-dual-fcov <ip>` | script-driven coverage emit | dual coverage plan |

(`cl-model-gen` lives **inside the fl-model-gen workspace** — same
`-w fl-model-gen` agent process hosts both slashes. There is no
separate `workflow/cl-model-gen/` directory.)

## Why these stages must stay LLM-free

### 1. fl_model and cycle_model are ground truth for the scoreboard

`sim` runs `EquivalenceScoreboard` which compares per-cycle DUT state
against `functional_model.py` (and `cycle_model.py` for latency /
handshake / ordering rules). If the ground truth is non-deterministic
(LLM rewrites the same SSOT differently across runs), the equivalence
verdict means nothing.

SSOT is the **single source of truth**. fl_model and cycle_model are
its mechanical projection. Adding a second source (LLM "judgement")
breaks the contract.

### 2. evidence_required approval policy

Per [[golden-todo-evidence]]:

```
LLM        = worker
TodoTracker = state machine
validator   = judge
human review = product/spec authority
```

The model files sit beside the validator (they ARE part of how
validators read truth). A worker (LLM) cannot manufacture the truth a
judge will later use to grade workers. That is circular.

### 3. SSOT defects must be exposed, not hidden

`emit_fl_model.py` parses every `expr` and `precondition` string with
Python's `ast.parse(text, mode="eval")`. If the SSOT author (`ssot-gen`
LLM) wrote a non-Python form, the script crashes loudly:

```
SyntaxError: invalid syntax
    branch_taken ? branch_target : (pc + 2)
                 ^
```

That stack trace is exactly the desired UX: the SSOT has a defect
(C/Verilog ternary inside an expr field) and the workflow refuses to
continue. An LLM-driven fl-model-gen would silently "fix" the
expression and the defect would only surface later (or never) as
mysterious RTL ↔ FL mismatches.

**Real example** ([[arm-m0-min-pipeline-run]] 2026-05-15): SSOT
`arm_m0_min.ssot.yaml:198-219` had three Verilog ternaries
(`cond ? a : b`) and three Verilog bit literals (`32'h0`, `1'b1`).
`emit_fl_model.py` crashed at the first one with `SyntaxError`. We
patched the SSOT to Python ternary (`a if cond else b`) and decimal
literals, re-ran the script, and it succeeded in 5 seconds. The
defect was a **ssot-gen** authoring error; surfacing it at
fl-model-gen kept it from corrupting RTL or sim downstream.

### 4. cost and speed

`emit_fl_model.py` and `emit_cycle_model.py` run in seconds with 0 LLM
calls. The arm_m0_min run took **5 s** for fl-model-gen. Adding an LLM
would cost minutes and dollars per stage for no semantic gain.

### 5. The contract this places on the upstream ssot-gen LLM

Because the emit scripts only accept Python forms, the SSOT author
**must** write expressions in Python syntax:

- ternary: `a if cond else b` (not `cond ? a : b`)
- numeric literal: `0`, `1`, `0xCAFE` (not `32'h0`, `1'b1`,
  `4'b0010`)
- helper names from a fixed whitelist: `gray_to_bin`, `bin_to_gray`,
  `popcount`, `parity`, `clog2`, `min`, `max`, `abs` (see
  `workflow/fl-model-gen/scripts/emit_fl_model.py` `_default_rule_helpers()`)
- bit operations use Python operators (`>>`, `<<`, `&`, `|`, `^`)

`workflow/ssot-gen/system_prompt.md` "DOWNSTREAM READINESS" section
already names some of these constraints; the C-style ternary trap is
the next obvious extension (open improvement in [[log]] 2026-05-16).

## LLM-vs-deterministic across the pipeline

| Stage | LLM | Notes |
|---|---|---|
| ssot-gen | ✅ heavy | natural-language requirement → canonical YAML; meaning inference required |
| **fl-model-gen** | ❌ | SSOT → `functional_model.py` mechanical emit |
| **cl-model-gen** | ❌ | SSOT → `cycle_model.py` mechanical emit |
| **equiv-goals** | ❌ | script combines fl + cl |
| **dual-fcov** | ❌ | script emits coverage plans |
| rtl-gen | ✅ heavy | free-form SV authoring |
| tb-gen | ✅ medium | cocotb sequences and scoreboard authoring |
| sim | ❌ (tool) | cocotb runner |
| sim-debug | ✅ light | mismatch owner classification |
| lint | ❌ (tool) | pyslang + verilator |
| coverage | ❌ (tool) | accounting |
| syn / sta / pnr / sta-post | ❌ (EDA tools) | — |

LLMs enter only where the value-add is **interpretation, generation,
or classification**. Where the right answer is fully derived from
SSOT and a deterministic procedure exists, the workflow uses that
procedure. This keeps the audit trail meaningful.

## Failure mode taxonomy

When a deterministic emit stage fails, the failure is always one of:

| Failure | Owner | Action |
|---|---|---|
| `SyntaxError` parsing an `expr` or `precondition` | ssot-gen | Fix SSOT to Python syntax |
| Helper name unknown | ssot-gen | Use a whitelisted helper, or add a new one to `_default_rule_helpers()` |
| `cycle_model.pipeline` references stage not in `decomposition` | ssot-gen | Reconcile pipeline stages with the decomposition tree |
| `sub_module` referenced from `cycle_model.handshake` with no `function_model_refs` | ssot-gen | Add ownership refs in `sub_modules[].function_model_refs` |
| Script crash (Python bug) | workflow author | Open issue, never patch SSOT to "make it pass" |

The "make it pass by patching SSOT" anti-pattern is the one
[[workflow-ownership-and-boundaries]] explicitly forbids.

## Running cl-model-gen on arm_m0_min

`arm_m0_min` is the only reference IP without `cycle_model.py` yet —
the plan scope stopped at fl-model-gen. To close RTL-0023 (open
ledger item, see [[arm-m0-min-pipeline-run]]):

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
python3 src/main.py \
  -s arm_m0_min/arm_m0_min/cl-model-gen \
  -w fl-model-gen \
  --model gpt-5.3-codex --effort low \
  < <(echo -e "/mode pipeline\n/ssot-cycle-model arm_m0_min\n")
```

Expected runtime: < 10 s, 0 LLM calls. Output:
`arm_m0_min/model/cycle_model.py` plus a `cl_model_check.json`. The
cycle_model script reads `cycle_model.pipeline`, `cycle_model.latency`,
`cycle_model.handshake`, `cycle_model.ordering`, and
`cycle_model.backpressure` from the SSOT and emits a step-by-step CL
trace.

## Bottom line

> **fl-model-gen and cl-model-gen are not lazy stages. They are
> verifier-friendly translators. Their value is being **predictable**,
> which is exactly what an evidence-based approval pipeline needs as
> its mid-flight ground truth.**

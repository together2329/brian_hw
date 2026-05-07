# ATLAS SSOT Detailed Guide

This guide is the operating runbook for SSOT-driven IP generation in this
workspace.

Workspace:

```text
/Users/brian/Desktop/Project/NEW_ATLAS
```

Reference workflow source:

```text
/Users/brian/Desktop/Project/brian_hw/common_ai_agent
```

Current active IP:

```text
sqa_cmux_import_0506
```

Current active IP kind:

```text
APB4 queue peripheral
```

## 1. Big Picture

SSOT means Single Source of Truth. In ATLAS, the SSOT is the YAML contract for
one hardware IP block.

The SSOT must describe what the IP is, what it does, how it connects, how it is
configured, how it is verified, and which downstream stages are allowed to
generate or repair artifacts.

The full flow is:

```text
requirements/spec
  -> ssot-gen
  -> fl-model-gen
  -> rtl-gen
  -> tb-gen
  -> sim
  -> sim-debug
  -> goal-audit/signoff
```

The short command sequence is:

```text
/new-ip <ip> <kind>
/import <doc_or_rtl_path>
/grill-me
approve <ip>
/to-ssot <ip>
/golden-all <ip>
/ssot-rtl <ip>
/ssot-tb <ip>
/sim <ip>
/sim-debug <ip>
/goal-audit <ip>
```

## 2. Source Of Truth Rules

Use this authority order:

```text
Human-approved requirement/spec
  > approved SSOT YAML
  > generated FL/golden model
  > RTL implementation
  > TB implementation
  > sim/debug reports
```

Hard rules:

- SSOT owns behavior, interfaces, registers, coverage goals, waivers, timing
  targets, and signoff criteria.
- FL/golden model is the executable oracle derived from SSOT.
- RTL must be repaired to match SSOT and FL.
- TB must compare RTL observations against FL/golden expectations.
- Sim-debug classifies failures; it does not silently change the spec.
- Do not edit FL, coverage goals, interface rules, or performance targets just
  to make RTL pass.
- If behavior is undefined, ambiguous, or contradictory, stop that branch and
  route back to SSOT/human approval.

## 3. Canonical IP Layout

Every IP lives directly under the workspace root:

```text
<ip>/
  yaml/
    <ip>.ssot.yaml
  docs/
    spec.md
  req/
    <ip>_requirements.md
  model/
    functional_model.py
    cycle_model.py
    decomposition.json
    fl_model_check.json
    cl_model_check.json
    model_signature.json
  cov/
    fl_fcov_plan.json
    cl_fcov_plan.json
    fcov_plan.json
  verify/
    equivalence_goals.json
    cocotb_harness.py
    scoreboard_bindings.sv
  golden/
    golden_todos.json
    golden_todos_tracker.json
  governance/
    authority.json
    authority.md
  rtl/
    *.sv or *.v
  list/
    <ip>.f
  tb/
    testbench files
  tc/
    test cases
  sim/
    logs, waves, scoreboard output, reports
  lint/
    lint reports
  sdc/
    <ip>.sdc
  doc/
    <ip>_mas.md
```

Do not create ad-hoc layouts such as `workflow/<ip>/`. The IP directory is
`<workspace>/<ip>/`.

## 4. Current Workspace Files

Useful local files:

```text
aes_gcm/yaml/aes_gcm.ssot.yaml
sqa_cmux_import_0506/docs/spec.md
sqa_cmux_import_0506/yaml/sqa_cmux_import_0506.ssot.yaml
.session/<ip>/ssot-gen/
```

The AES-GCM SSOT is a fuller canonical-style example. The current
`sqa_cmux_import_0506` YAML is only a draft scaffold.

Current draft YAML:

```text
sqa_cmux_import_0506/yaml/sqa_cmux_import_0506.ssot.yaml
```

Current evidence document:

```text
sqa_cmux_import_0506/docs/spec.md
```

The current YAML has `custom.atlas_decisions: {}`. Import the spec before trying
to generate downstream artifacts.

## 5. Stage 1: SSOT Gen

Stage owner:

```text
ssot-gen
```

Purpose:

```text
Turn requirements, imported evidence, and Q&A answers into <ip>/yaml/<ip>.ssot.yaml.
```

Primary commands:

```text
/new-ip <ip> <kind>
/import <doc_or_rtl_path>
/grill-me
approve <ip>
/to-ssot <ip>
```

Inputs:

```text
<ip>/docs/*.md
<ip>/req/<ip>_requirements.md
existing RTL, if importing legacy behavior
existing YAML, if refreshing prior SSOT
human Q&A answers
```

Output:

```text
<ip>/yaml/<ip>.ssot.yaml
```

Required decisions:

```text
purpose
bus_interface
register_map
clock_reset
interrupt
memory_map
parameters
submodule_structure
test_expectation
```

Production SSOT sections should also cover:

```text
top_module
sub_modules
decomposition
parameters
io_list
features
dataflow
function_model
cycle_model
clock_reset_domains
cdc_requirements
rdc_requirements
registers
memory
interrupts
fsm
timing
power
security
error_handling
debug_observability
integration
dft
synthesis
coding_rules
reuse_modules
custom
dir_structure
filelist
test_requirements
quality_gates
traceability
workflow_todos
generation_flow
```

Entry criteria:

```text
An IP name and kind are known.
Evidence exists, or Q&A can fill missing decisions.
```

Exit criteria:

```text
<ip>/yaml/<ip>.ssot.yaml exists.
All required decisions are concrete or explicitly none/not applicable.
No unresolved TBD blocks remain in required fields.
The YAML can be parsed.
```

Validation command from the workflow source:

```bash
bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh <ip>
```

Notes:

- `ssot-gen` must not generate RTL, TB, sim files, firmware, or docs.
- It may write downstream instructions under `workflow_todos.<stage>[]`.
- For `workflow_todos.rtl-gen[]`, include `content`, `detail`, `criteria`,
  `source_refs`, and an owner when known.
- Missing semantics should produce a Q&A/human gate, not guessed RTL behavior.

## 6. Stage 2: FL Gen / Golden Model

Stage owner:

```text
fl-model-gen
```

Purpose:

```text
Generate executable golden artifacts from SSOT.
```

The FL stage creates the reference behavior that RTL and TB must match.

Composite command:

```text
/golden-all <ip>
```

Alias:

```text
/ga <ip>
```

The composite chain includes:

```text
/ssot-fl-model <ip>
/ssot-cycle-model <ip>
/ssot-dual-fcov <ip>
/ssot-equiv-goals <ip>
/ssot-verification-rtl <ip>
/ssot-golden-todos <ip>
/ssot-protocol-assertions <ip>
/ssot-authority <ip>
/ssot-loop-map <ip>
/ssot-submodule-fl <ip>
/ssot-module-harness <ip>
```

Individual command reference:

```text
/ssot-fl-model <ip>          # FunctionalModel, decomposition, FL checks
/ssot-cycle-model <ip>       # CycleModel when cycle behavior needs execution
/ssot-dual-fcov <ip>         # FL and CL coverage plans
/ssot-equiv-goals <ip>       # FL-vs-RTL equivalence goals
/ssot-verification-rtl <ip>  # cocotb harness and scoreboard hooks
/ssot-golden-todos <ip>      # golden todo tracker files
/ssot-protocol-assertions <ip>
/ssot-authority <ip>
/ssot-loop-map <ip>
/ssot-submodule-fl <ip>
/ssot-module-harness <ip>
```

Inputs:

```text
<ip>/yaml/<ip>.ssot.yaml
```

Typical outputs:

```text
<ip>/model/functional_model.py
<ip>/model/cycle_model.py
<ip>/model/decomposition.json
<ip>/model/fl_model_check.json
<ip>/model/cl_model_check.json
<ip>/model/model_signature.json
<ip>/cov/fl_fcov_plan.json
<ip>/cov/cl_fcov_plan.json
<ip>/cov/fcov_plan.json
<ip>/verify/equivalence_goals.json
<ip>/verify/cocotb_harness.py
<ip>/verify/scoreboard_bindings.sv
<ip>/golden/golden_todos.json
<ip>/golden/golden_todos_tracker.json
<ip>/governance/authority.json
<ip>/governance/authority.md
```

Cycle model trigger:

```text
Create cycle_model.py when the SSOT has non-trivial handshake, ordering,
arbitration, outstanding transaction, unbounded latency, or performance target
behavior that needs executable checking.
```

Entry criteria:

```text
SSOT exists and parses.
SSOT required behavior fields are filled.
```

Exit criteria:

```text
FunctionalModel exists.
FL self-check passes or has explicit failure evidence.
model_signature.json is current.
equivalence_goals.json exists before RTL/TB signoff.
```

Golden rule:

```text
If RTL does not match FL, repair RTL or escalate SSOT. Do not change FL to make RTL pass.
```

Drift guard:

```text
If SSOT changes after FL generation, rerun /golden-all <ip> before rtl-gen, tb-gen, sim, or audit.
```

## 7. Stage 3: RTL Gen

Stage owner:

```text
rtl-gen
```

Purpose:

```text
Generate or repair RTL that satisfies the SSOT and FL/golden goals.
```

Primary command:

```text
/ssot-rtl <ip>
```

Alias:

```text
/sr <ip>
```

Useful checks:

```text
/lint <file.sv>
/syn-check <file.sv>
```

Inputs:

```text
<ip>/yaml/<ip>.ssot.yaml
<ip>/model/functional_model.py
<ip>/model/cycle_model.py, when present
<ip>/verify/equivalence_goals.json
SSOT workflow_todos.rtl-gen[], when present
```

Typical outputs:

```text
<ip>/rtl/*.sv
<ip>/rtl/*.v
<ip>/list/<ip>.f
<ip>/rtl/rtl_todo_plan.json
<ip>/rtl/rtl_traceability.json
<ip>/rtl/rtl_contract.json
<ip>/rtl/rtl_compile.json
<ip>/lint/dut_lint.json
<ip>/doc/<ip>_mas.md
```

Entry criteria:

```text
SSOT is approved.
FL/golden artifacts are current.
Equivalence goals exist.
No golden drift is detected.
```

Exit criteria:

```text
RTL files exist.
Filelist is complete.
DUT-only compile passes.
Lint has zero unwaived errors.
Every required rtl-gen TODO has pass evidence or an explicit escalation.
RTL traceability maps generated RTL back to SSOT sections.
```

### Verilog-2001 Dialect Rule

If the target RTL should feel like pure Verilog-2001, the SSOT must say that
explicitly. Do not rely on rtl-gen to infer it from taste or file naming.

Project policy for this workspace:

```text
Default RTL dialect: verilog_2001
Default RTL extension: .v
Scaffold output: .v
RTL-gen fallback output: .v
Filelist RTL entries: rtl/*.v
SystemVerilog is opt-in only.
```

Required SSOT entries:

```yaml
synthesis:
  dialect: "verilog_2001"

coding_rules:
  verilog_style: "verilog_2001"
  file_extension: ".v"
  allowed_constructs:
    - "module / endmodule"
    - "parameter / localparam"
    - "wire / reg"
    - "assign"
    - "always @(posedge clk or negedge rst_n)"
    - "always @(*)"
    - "case / if / else"
  banned_constructs:
    - "typedef"
    - "enum"
    - "logic"
    - "bit / byte / int / longint / shortint"
    - "always_ff"
    - "always_comb"
    - "always_latch"
    - "package / import"
    - "interface / modport"
    - "'0 / '1 SystemVerilog literals"
  fsm_style:
    state_encoding: "localparam"
    state_register_type: "reg"
    next_state_type: "reg"
  reset_style:
    polarity: "active_low"
    assertion: "async"
    template: "always @(posedge pclk or negedge presetn)"
```

RTL-gen must then emit patterns like this:

```verilog
localparam [1:0] ST_IDLE = 2'd0,
                 ST_RUN  = 2'd1,
                 ST_DONE = 2'd2;

reg [1:0] state;
reg [1:0] next_state;

always @(posedge pclk or negedge presetn) begin
    if (!presetn)
        state <= ST_IDLE;
    else
        state <= next_state;
end

always @(*) begin
    next_state = state;
    case (state)
        ST_IDLE: next_state = start ? ST_RUN : ST_IDLE;
        ST_RUN:  next_state = done  ? ST_DONE : ST_RUN;
        ST_DONE: next_state = ST_IDLE;
        default: next_state = ST_IDLE;
    endcase
end
```

And it must not emit:

```systemverilog
typedef enum logic [1:0] { ST_IDLE, ST_RUN, ST_DONE } state_t;
state_t state, next_state;

always_ff @(posedge pclk or negedge presetn) begin
    ...
end
```

Why SystemVerilog keeps appearing:

```text
The canonical SSOT template still contains many .sv example paths.
Some legacy rtl-gen todo templates explicitly say "use logic" and "enum".
TB commands often compile with iverilog -g2012, which accepts SV syntax.
If coding_rules.verilog_style is missing or weak, the model follows those examples.
```

Prevent it at the gate:

```text
Fail rtl-gen if any synthesizable RTL under <ip>/rtl/ contains:
typedef
enum
logic
always_ff
always_comb
always_latch
interface
modport
package
import ...::*
```

Implementation cleanup needed in the workflow source:

```text
scaffold_ip already follows RTL_DIALECT and emits .v by default.
The remaining problem is hardcoded .sv fallbacks in SSOT templates, rtl-gen
preflight, derive_rtl_todos, workflow_stage_engine, and some legacy docs.
Those must use the selected RTL file extension instead of literal .sv.
```

Concrete places to check:

```text
src/config.py:
  RTL_DIALECT defaults to verilog_2001.
  RTL_FILE_EXT is .v for verilog_2001 and .sv for systemverilog_2012.

core/tools.py:
  scaffold_ip already uses RTL_DIALECT to choose .v or .sv.

workflow/ssot-gen/rules/ssot-template.yaml:
  filelist and sub_modules examples still show rtl/<ip>_*.sv.

workflow/ssot-gen/system_prompt.md:
  copied template examples still show rtl/<ip>_*.sv.

workflow/rtl-gen/scripts/ssot_to_rtl.py:
  fallback expected file and generic seed output still use rtl/<top>.sv.

workflow/rtl-gen/scripts/derive_rtl_todos.py:
  fallback owner files still use rtl/<module>.sv.

src/workflow_stage_engine.py:
  top-file fallback and alias checks still prefer rtl/<top>.sv.
```

Correct behavior:

```text
ext = ".v" when RTL_DIALECT == "verilog_2001"
ext = ".sv" only when RTL_DIALECT == "systemverilog_2012"

Every fallback should use:
  rtl/<module>{ext}

No fallback should hardcode:
  rtl/<module>.sv
```

What rtl-gen may edit:

```text
<ip>/rtl/*
<ip>/list/*
<ip>/lint/*
<ip>/doc/<ip>_mas.md
RTL compile/lint/provenance reports
```

What rtl-gen must not edit to hide failure:

```text
<ip>/yaml/<ip>.ssot.yaml
<ip>/model/functional_model.py
coverage goals
interface contracts
performance targets
```

Escalation rules:

```text
Compile/lint/syntax issue     -> fix in rtl-gen.
Width/reset/driver issue      -> fix in rtl-gen.
RTL disagrees with FL         -> fix RTL unless SSOT is ambiguous.
SSOT ambiguity                -> escalate to ssot-gen/human gate.
Golden drift                  -> rerun fl-model-gen before continuing.
```

## 8. Stage 4: TB Gen

Stage owner:

```text
tb-gen
```

Purpose:

```text
Generate testbench, test cases, scoreboards, and simulation harnesses.
```

Default command:

```text
/ssot-tb <ip>
```

Alias:

```text
/stb <ip>
```

Backend commands:

```text
/ssot-tb-cocotb <ip>
/ssot-tb-verilog <ip>
/ssot-tb-uvm <ip>
```

Follow-up commands:

```text
/gen-tc <ip>
/sim <ip>
/coverage <ip>
```

Inputs:

```text
<ip>/yaml/<ip>.ssot.yaml
<ip>/rtl/*
<ip>/list/<ip>.f
<ip>/model/functional_model.py
<ip>/model/cycle_model.py, when present
<ip>/verify/equivalence_goals.json
SSOT test_requirements
SSOT registers
SSOT io_list
SSOT interrupts
SSOT memory
SSOT dataflow
```

Typical outputs:

```text
<ip>/tb/*
<ip>/tc/*
<ip>/sim/*
TB manifest
scoreboard implementation
coverage report inputs
simulation scripts or Makefiles
```

Entry criteria:

```text
RTL exists and compiles.
Filelist exists.
FL/golden artifacts exist.
SSOT test requirements are defined.
```

Exit criteria:

```text
TB compiles.
Simulation can be launched.
Scoreboard compares RTL observations against FL/golden expectations.
SSOT scenarios map to tests or explicit coverage gaps.
```

Failure routing:

```text
TB compile issue              -> fix in tb-gen.
Wrong signal hookup           -> fix in tb-gen if SSOT/RTL names are clear.
Scoreboard implementation bug -> fix in tb-gen.
RTL actual mismatch           -> escalate to rtl-gen.
Missing/ambiguous expected    -> escalate to SSOT/FL authority.
```

## 9. Stage 5: Sim

Stage owner:

```text
tb-gen sim stage
```

Purpose:

```text
Compile and run the generated TB against RTL.
```

Command:

```text
/sim <ip>
```

Inputs:

```text
<ip>/rtl/*
<ip>/tb/*
<ip>/tc/*
<ip>/list/<ip>.f
<ip>/model/functional_model.py
<ip>/verify/equivalence_goals.json
```

Typical outputs:

```text
<ip>/sim/*.log
<ip>/sim/*.vcd
<ip>/sim/scoreboard*.jsonl
<ip>/sim/sim_report.txt
coverage artifacts, when enabled
```

Entry criteria:

```text
RTL compile/lint gate passed or is explicitly allowed for a debug run.
TB compile gate passed.
Simulator backend is available.
```

Exit criteria:

```text
Simulation command exits cleanly.
Expected PASS markers are present.
Scoreboard mismatches are zero, or mismatch evidence is structured.
Waveform/log artifacts exist for debug when failures occur.
```

If sim fails:

```text
Capture log path.
Capture VCD path if available.
Capture scoreboard diff path if available.
Run /sim-debug <ip>.
Do not guess the owner from a single symptom.
```

## 10. Stage 6: Sim Debug

Stage owner:

```text
sim-debug
```

Purpose:

```text
Classify simulation failures, waveform evidence, coverage gaps, and FL-vs-RTL mismatches.
```

Commands:

```text
/sim-debug <ip>
/wave [file.vcd]
/sig <signal_name>
/goal-audit <ip>
```

Aliases:

```text
/sd <ip>
/w [file.vcd]
/audit <ip>
```

Inputs:

```text
<ip>/sim/*.log
<ip>/sim/*.vcd
<ip>/sim/scoreboard*.jsonl
<ip>/verify/equivalence_goals.json
<ip>/model/functional_model.py
<ip>/model/model_signature.json
```

Typical outputs:

```text
<ip>/sim/fl_rtl_compare.json
<ip>/sim/mismatch_classification.json
<ip>/sim/fl_rtl_goal_audit.json
failure classification
waveform summaries
coverage gap summaries
next-owner recommendation
```

Coverage channels:

```text
Static code analysis:
  Defines the universe of lines, branches, states, and cover bins.

VCD post-process:
  Uses existing waveform activity for toggles, state visits, and transitions.

Instrumented runtime:
  Uses simulator coverage counters for true line, branch, expression, and
  functional coverage.
```

Failure classes:

```text
TB bug
RTL bug
SSOT/FL semantic issue
environment/tool issue
coverage/stimulus gap
inconclusive
```

Exit criteria:

```text
Every failure has a class.
Every class has a next owner.
Every repairable issue has evidence.
Semantic changes are routed to SSOT/human approval.
```

## 11. Stage 7: Goal Audit And Signoff

Stage owner:

```text
goal-audit
```

Purpose:

```text
Audit FL-vs-RTL equivalence goal evidence against SSOT signoff criteria.
```

Command:

```text
/goal-audit <ip>
```

Alias:

```text
/audit <ip>
```

Inputs:

```text
<ip>/verify/equivalence_goals.json
<ip>/sim/scoreboard*.jsonl
<ip>/sim/fl_rtl_compare.json
<ip>/sim/mismatch_classification.json
<ip>/cov/*
<ip>/model/model_signature.json
```

Typical output:

```text
<ip>/sim/fl_rtl_goal_audit.json
```

Signoff requires:

```text
SSOT approved and current.
FL/golden model current.
RTL compile/lint evidence current.
TB evidence current.
Simulation evidence current.
Coverage evidence current or explicitly waived.
Sim-debug has no unresolved blocking mismatch.
Goal audit passes.
```

## 12. Handoff Blocks

Use compact handoff blocks when moving between stages.

SSOT to FL:

```text
[SSOT HANDOFF] -> fl-model-gen
Module  : <ip>
SSOT    : <ip>/yaml/<ip>.ssot.yaml
Task    : Generate FL/golden model, coverage goals, equivalence goals, and authority manifest.
Criteria: SSOT has no unresolved required decisions.
```

FL to RTL:

```text
[FL HANDOFF] -> rtl-gen
Module  : <ip>
SSOT    : <ip>/yaml/<ip>.ssot.yaml
Oracle  : <ip>/model/functional_model.py
Goals   : <ip>/verify/equivalence_goals.json
Task    : Implement RTL that satisfies SSOT and FL/golden goals.
Criteria: model_signature.json is current and no golden drift is detected.
```

RTL to TB:

```text
[RTL HANDOFF] -> tb-gen
Module  : <ip>
SSOT    : <ip>/yaml/<ip>.ssot.yaml
RTL     : <ip>/rtl/*
Filelist: <ip>/list/<ip>.f
Task    : Generate tests, scoreboard, and simulation harness.
Criteria: RTL compiles and lint/filelist evidence is available.
```

TB to Sim Debug:

```text
[SIM ESCALATE] -> sim-debug
Module  : <ip>
Logs    : <ip>/sim/*.log
Waves   : <ip>/sim/*.vcd
Diffs   : <ip>/sim/scoreboard*.jsonl
Task    : Classify mismatch or coverage gap and name the next owner.
Criteria: Fresh simulation evidence exists.
```

Sim Debug to Repair Owner:

```text
[DEBUG HANDOFF] -> <rtl-gen|tb-gen|ssot-gen|fl-model-gen>
Module  : <ip>
Class   : <failure_class>
Evidence: <paths>
Task    : <specific repair or human-gate decision>
Criteria: <objective rerun/audit condition>
```

## 13. Human-Owned Vs LLM-Editable

Human-owned:

```text
Requirement intent
Protocol choices
Undefined behavior decisions
Interface contract
Register semantics
Coverage goals
Waivers
Performance targets
Final signoff
```

Generated but locked after approval:

```text
<ip>/yaml/<ip>.ssot.yaml
<ip>/model/functional_model.py
<ip>/model/cycle_model.py
<ip>/cov/*
<ip>/verify/equivalence_goals.json
<ip>/governance/*
```

LLM-editable implementation artifacts:

```text
<ip>/rtl/*
<ip>/tb/*
<ip>/tc/*
<ip>/sim/*
<ip>/lint/*
<ip>/doc/<ip>_mas.md
generated reports
```

Change-control rule:

```text
Changing human-owned or golden artifacts after downstream work starts requires rerunning dependent stages.
```

## 14. Current IP: sqa_cmux_import_0506

Current source spec:

```text
sqa_cmux_import_0506/docs/spec.md
```

Current draft YAML:

```text
sqa_cmux_import_0506/yaml/sqa_cmux_import_0506.ssot.yaml
```

Current status:

```text
Draft scaffold exists.
custom.atlas_decisions is empty.
Import has not populated the SSOT decisions yet.
```

Recommended next commands:

```text
/import sqa_cmux_import_0506/docs/spec.md
/grill-me
approve sqa_cmux_import_0506
/to-ssot sqa_cmux_import_0506
/golden-all sqa_cmux_import_0506
/ssot-rtl sqa_cmux_import_0506
/ssot-tb sqa_cmux_import_0506
/sim sqa_cmux_import_0506
/sim-debug sqa_cmux_import_0506
/goal-audit sqa_cmux_import_0506
```

Current IP source evidence:

```text
Purpose:
SQA CMUX import demo validates request sequencing, queue status, and interrupt
reporting for an APB4 peripheral.

Bus interface:
APB4 slave interface using pclk, presetn, psel, penable, pwrite, paddr, pwdata,
prdata, pready, and pslverr.

Register map:
0x00 CTRL RW: bit0 enable, bit1 sw_reset.
0x04 STATUS RO: bit0 busy, bit1 queue_empty, bit2 queue_full.
0x08 DATA RW: enqueue or dequeue 32-bit request words.
0x0c PRESCALE RW: timing divisor.
0x10 IRQ_STATUS W1C: bit0 done, bit1 error.

Clock/reset:
pclk is the only clock. presetn is active-low asynchronous reset and is
synchronized internally.

Interrupt:
irq is level-high while IRQ_STATUS has unmasked done or error bits. STATUS
updates must not clear IRQ_STATUS.

Memory/buffering:
Request queue is a FIFO buffer. Overflow sets error and rejects the incoming
DATA write.

Parameters:
DATA_WIDTH default 32.
ADDR_WIDTH default 12.
FIFO_DEPTH default 8.

Submodules:
sqa_regs handles APB decode and W1C register behavior.
sqa_fifo stores request words.
sqa_engine consumes queued requests and raises done or error.

Verification:
cocotb must cover reset defaults, register read/write, FIFO full overflow,
IRQ W1C clear, and back-to-back DATA writes.
```

## 15. Current IP Acceptance Checklist

SSOT checklist:

```text
[ ] Imported sqa_cmux_import_0506/docs/spec.md.
[ ] /grill-me resolved all missing decisions.
[ ] approve sqa_cmux_import_0506 completed.
[ ] /to-ssot wrote sqa_cmux_import_0506/yaml/sqa_cmux_import_0506.ssot.yaml.
[ ] SSOT parses as YAML.
[ ] No required decision remains TBD.
```

FL/golden checklist:

```text
[ ] /golden-all sqa_cmux_import_0506 completed.
[ ] model/functional_model.py exists.
[ ] model/model_signature.json exists.
[ ] verify/equivalence_goals.json exists.
[ ] governance/authority.md exists.
```

RTL checklist:

```text
[ ] /ssot-rtl sqa_cmux_import_0506 completed.
[ ] rtl files exist.
[ ] list/sqa_cmux_import_0506.f exists.
[ ] RTL compile evidence exists.
[ ] DUT lint evidence exists.
[ ] No unresolved required rtl-gen TODO remains.
```

TB/sim checklist:

```text
[ ] /ssot-tb sqa_cmux_import_0506 completed.
[ ] tb files exist.
[ ] tc files exist or generated tests are documented.
[ ] /sim sqa_cmux_import_0506 completed.
[ ] sim report exists.
[ ] scoreboard mismatches are zero or classified.
```

Debug/signoff checklist:

```text
[ ] /sim-debug sqa_cmux_import_0506 completed if sim failed or coverage is incomplete.
[ ] mismatch classification exists when needed.
[ ] /goal-audit sqa_cmux_import_0506 completed.
[ ] Every equivalence goal is passed, waived, or escalated.
```

## 16. Command Reference

SSOT:

```text
/new-ip <ip> <kind>
/import <path>
/grill-me
approve <ip>
/to-ssot <ip>
```

FL/golden:

```text
/golden-all <ip>
/ga <ip>
/ssot-fl-model <ip>
/ssot-cycle-model <ip>
/ssot-dual-fcov <ip>
/ssot-equiv-goals <ip>
/ssot-verification-rtl <ip>
/ssot-golden-todos <ip>
/ssot-authority <ip>
```

RTL:

```text
/ssot-rtl <ip>
/sr <ip>
/lint <file.sv>
/syn-check <file.sv>
```

TB/sim:

```text
/ssot-tb <ip>
/stb <ip>
/ssot-tb-cocotb <ip>
/ssot-tb-verilog <ip>
/ssot-tb-uvm <ip>
/gen-tc <ip>
/sim <ip>
/coverage <ip>
```

Sim debug:

```text
/sim-debug <ip>
/sd <ip>
/wave [file.vcd]
/w [file.vcd]
/sig <signal_name>
/goal-audit <ip>
/audit <ip>
```

## 17. Common Failure Routing

Use this table before changing files.

| Symptom | Likely owner | First action |
| --- | --- | --- |
| SSOT missing behavior | ssot-gen/human | Run `/grill-me` or edit approved spec |
| YAML parse error | ssot-gen | Fix YAML structure |
| FL model drift | fl-model-gen | Rerun `/golden-all <ip>` |
| RTL compile error | rtl-gen | Patch RTL and rerun compile |
| RTL lint error | rtl-gen | Patch RTL or record explicit waiver |
| RTL/FL mismatch | rtl-gen first | Patch RTL unless SSOT/FL is ambiguous |
| TB compile error | tb-gen | Patch TB wiring/helpers |
| Scoreboard code wrong | tb-gen | Patch scoreboard |
| Test missing coverage | tb-gen | Add stimulus/testcase |
| Undefined expected result | ssot-gen/human | Clarify SSOT |
| Waveform missing signal | tb-gen or sim-debug | Add dump/probe |
| Tool/backend missing | environment | Report missing tool and next possible check |

## 18. Stop Rules

Stop a stage when:

```text
The stage exit criteria are met and evidence paths exist.
```

Escalate instead of editing when:

```text
The fix requires changing approved behavior.
The fix requires changing a protocol/interface contract.
The fix requires changing coverage goals or performance targets.
The evidence contradicts the SSOT.
The next step would hide a real mismatch by changing the oracle.
```

Do not claim completion unless:

```text
The relevant command ran.
The expected artifact exists.
The validator/check/audit result was read.
Known failures are classified.
```

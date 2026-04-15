# RTL Generation Workflow (Extracted)

```mermaid
flowchart TD
    A([Start]) --> B{Entry path}
    B -->|From mas-gen| C["/gen-rtl <module><br/>prints [MAS HANDOFF]"]
    B -->|Direct rtl-gen session| D["python3 src/main.py -w rtl-gen"]
    C --> E{Locate MAS file}
    D --> E

    E -->|MODULE_NAME set| F["Use ${MODULE_NAME}/mas/${MODULE_NAME}_mas.md"]
    E -->|Handoff contains MAS path| G["Use MAS path from handoff"]
    E -->|No target known| H["Run /find-mas"]
    H --> I{MAS count}
    I -->|0 found| I0["Stop: ask user to generate/select MAS"]
    I -->|1 found| J["Select discovered MAS"]
    I -->|>1 found| I1["Ask user to choose target MAS"]
    F --> J
    G --> J

    J --> K["Read MAS completely<br/>(sections §2 ~ §8 required for implementation)"]
    K --> L{Flow type}
    L -->|/new-ip-rtl| M["New RTL flow:<br/>skeleton -> header -> FSM -> datapath -> CSR -> IRQ -> memory"]
    L -->|/legacy-ip-rtl| N["Legacy RTL flow:<br/>read existing RTL + MAS delta -> surgical updates"]
    L -->|/todo template rtl-impl| O["Standard RTL flow:<br/>header -> registers -> FSM -> datapath -> IRQ -> memory"]

    M --> P["Write outputs:<br/><ip>/rtl/<ip>.sv<br/><ip>/list/<ip>.f"]
    N --> P
    O --> P

    P --> Q["Hook: post_write.sh logs rtl write events"]
    Q --> R["Run /lint <ip>/rtl/<ip>.sv<br/>(verilator or iverilog)"]
    R --> S{Lint clean?}
    S -->|No| T["Fix RTL and rerun /lint"]
    T --> R
    S -->|Yes| U["Optional: /syn-check <ip>/rtl/<ip>.sv<br/>(yosys else strict iverilog)"]

    U --> V["Report completion:<br/>[MAS RESULT] rtl-gen DONE"]
    V --> W([End])
```

## Source Mapping

- Workflow entry and commands: `workflow/GUIDE.md`, `workflow/mas-gen/commands/gen-rtl.json`
- Handoff contract: `workflow/mas-gen/scripts/handoff_rtl.sh`
- RTL-gen behavior and done criteria: `workflow/rtl-gen/system_prompt.md`
- Task variants: `workflow/rtl-gen/todo_templates/new-ip-rtl.json`, `workflow/rtl-gen/todo_templates/legacy-ip-rtl.json`, `workflow/rtl-gen/todo_templates/rtl-impl.json`
- Validation commands: `workflow/rtl-gen/commands/lint.json`, `workflow/rtl-gen/commands/syn-check.json`
- MAS discovery: `workflow/rtl-gen/commands/find-mas.json`, `workflow/rtl-gen/scripts/find-mas.sh`
- Hook behavior: `workflow/rtl-gen/scripts/hooks.json`, `workflow/rtl-gen/scripts/post_write.sh`
*** End Patch

# RTL Gate Tool Evidence Repair Notes

## Packet: rtl_gate_tool_evidence

### Lint warnings fixed

Two Verilator warnings were present in `dut_lint.`:

1. **EOFNEWLINE** (line 137): Missing newline at end of file.
   - Fix: Ensured the file ends with a trailing newline after `endmodule`.

2. **UNUSEDSIGNAL** (line 35): Signal `s1_state_visible_fire` is not used.
   - The signal was declared and assigned (`assign s1_state_visible_fire = s0_control_sample_fire`)
     but never consumed on any RHS or output port.
   - Fix: Removed the `s1_state_visible_fire` declaration and its continuous assignment.
     The `s0_control_sample_fire` signal remains since it drives the clocked enable condition.

### Tasks affected

- **RTL-0018** (dut_lint gate): Was open because lint had 2 warnings. Both root causes repaired.
- **RTL-0019** (dynamic_todo_closure gate): Was open because RTL-0018 was open. Should close after re-lint.

### No behavioral changes

The timer_core datapath, FSM transitions, priority ordering (flush > fetch_en > step_en),
and latency-1 registered output contract are unchanged.

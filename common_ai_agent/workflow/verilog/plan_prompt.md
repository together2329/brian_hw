# RTL Plan Mode Rules

When planning RTL work, apply these additional constraints:

1. Define the complete module interface (ports, parameters) in the first task
2. Separate tasks for: interface → internals → testbench → simulation → lint
3. Loop tasks REQUIRED for simulation iterations (exit_condition = "0 errors, 0 warnings")
4. Include a validator for simulation tasks: `bash scripts/check_sim_pass.sh`
5. Specify parameter widths and reset polarity in the task detail
6. Identify all clock domains — multi-clock designs need CDC analysis task
7. Flag any unresolved timing constraints as explicit TODO tasks

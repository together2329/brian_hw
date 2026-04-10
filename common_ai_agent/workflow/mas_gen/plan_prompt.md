# MAS Plan Mode Rules

1. ALWAYS start with a SPEC task — define module name, ports, parameters before any code
2. Split tasks by agent: tag each task with [RTL], [TB], [SIM], [DOC]
3. RTL tasks must come before TB tasks in the sequence
4. Simulation loop task is REQUIRED — use loop=true, max_loop_iterations=15
5. Documentation task is LAST — only after sim passes
6. Each task detail must include: input files, output files, acceptance criteria
7. Use validator on simulation tasks: "bash workflow/tb_gen/scripts/check_sim_pass.sh"

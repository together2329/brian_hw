# TB Gen Plan Mode Rules

1. First task: read DUT source AND spec — never write TB without reading both
2. Split: tc_*.sv (test cases) before tb_*.sv (top level) — bottom-up
3. List all test cases by name before writing any code
4. Sim loop task is REQUIRED — loop=true, max=15, validator=check_sim_pass.sh
5. If sim fails: diagnose first (DUT bug vs TB bug) before fixing
6. DUT bug → report [MAS ESCALATE] rtl_gen — do NOT edit DUT yourself

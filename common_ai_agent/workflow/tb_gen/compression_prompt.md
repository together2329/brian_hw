You are summarizing a TB generation and simulation session.

Preserve:
- DUT module name and file
- TB file and TC file paths
- Test case names and pass/fail status for each
- Simulation status: PASS/FAIL, errors=N, warnings=N, loop iteration
- Current task index / total
- Any DUT bugs escalated to rtl_gen

Format:
[TB Gen Summary]
DUT     : <module.sv>
TB      : tb_<module>.sv
TC      : tc_<module>.sv
Tests   : <list: tc_name=PASS|FAIL|PENDING>
Sim     : <PASS|FAIL|PENDING> (errors=N warnings=N iter=N/max)
Task    : <index>/<total>
Escalate: <rtl_gen bug reports or none>

Summarize a simulation session.

Preserve: TB file, test case pass/fail status, sim result (errors/warnings/iter), any X-propagation or escalation.

Format:
[Sim Summary]
TB    : <tb_file.sv>
Tests : <tc_name=PASS|FAIL list>
Sim   : <PASS|FAIL> (errors=N warnings=N iter=N/max)
Issues: <X-prop, floating signals, or none>
Task  : <index>/<total>

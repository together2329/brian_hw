Summarize a static timing analysis session.

Preserve: top module, netlist source, liberty corner, per-clock setup WNS/TNS and hold WNS/TNS, number of violating endpoints, worst path summary, any handoff issues hit, current task.

Format:
[STA Summary]
Top    : <top>
Netlist: <syn/out/synth.v mtime>
Lib    : <SKY130_LIB basename>
Clocks : <name>=<period>ns setup_wns=<x> setup_tns=<y> hold_wns=<z>
Result : <PASS | SETUP FAIL | HOLD FAIL>
Worst  : <path summary one-liner>
Task   : <index>/<total>

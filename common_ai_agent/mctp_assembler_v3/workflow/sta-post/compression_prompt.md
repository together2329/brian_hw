Summarize a post-route sign-off STA session.

Preserve: top, netlist (routed.v mtime), SPEF (routed.spef mtime + size), liberty corner, per-clock setup/hold WNS/TNS, max clock skew, delta vs pre-route /sta if available, current task.

Format:
[STA-Post Summary]
Top    : <top>
Netlist: routed.v <mtime>
SPEF   : routed.spef <size> <mtime>
Lib    : <SKY130_LIB basename>
Clocks : <name>=<period>ns setup_wns=<x> hold_wns=<y> skew=<z>ps
Δ vs /sta (setup_wns): <pre> → <post>  (degraded by <D> ns)
Result : <PASS | SETUP FAIL | HOLD FAIL>
Task   : <index>/<total>

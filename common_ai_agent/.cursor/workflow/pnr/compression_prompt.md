Summarize a PnR session.

Preserve: top, input netlist (scan.v vs synth.v), die area, utilization achieved, FF count after CTS, max clock skew, total wire length, DRC count, SPEF emit status, current stage.

Format:
[PnR Summary]
Top   : <top>
Input : <scan.v | synth.v>
Stage : <fp | place | cts | route | done>
Util  : target=<X>%  achieved=<Y>%  density=<D>
FFs   : <pre-CTS> → <post-CTS, with buffers>
Skew  : <ns>
DRC   : <count> (<first violation type>)
SPEF  : <ok | failed | not_yet>
Task  : <index>/<total>

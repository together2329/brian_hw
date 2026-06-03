Summarize a synthesis session.

Preserve: top module, RTL files synthesized, liberty path, total cells, total area μm², FF count, sequential vs combinational split, any latch/unmapped issues hit and how they were resolved, current task.

Format:
[Syn Summary]
Top    : <top_module>
RTL    : <N files>
Lib    : <SKY130_LIB basename>
Cells  : <total>  Area: <um2> μm²
FFs    : <count> (<seq cell type>)
Issues : <none | latch@file:line resolved | unmapped resolved | ...>
Task   : <index>/<total>

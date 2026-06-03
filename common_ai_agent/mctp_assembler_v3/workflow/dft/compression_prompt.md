Summarize a DFT session.

Preserve: top module, dft.enabled status, scan tool, total FFs, chains inserted, max/min chain length, scan_enable_port, ATPG used yes/no + coverage if any, current task.

Format:
[DFT Summary]
Top    : <top>
Mode   : <passthrough | scan_insert | scan_insert+atpg>
FFs    : <total>  in_chains: <N>  skipped: <K>
Chains : <count>  max_len: <X>  min_len: <Y>
SE port: <scan_en>
ATPG   : <none | stuck_at coverage=92.4% (target 90%)>
Task   : <index>/<total>

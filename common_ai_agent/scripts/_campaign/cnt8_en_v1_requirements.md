# cnt8_en_v1
8-bit synchronous up-counter. Ports: clk, rst_n(async low), en, clr, count[7:0]. en=1 -> count+=1 (wraps 255->0); en=0 hold; clr=1 -> count=0 next edge (clr dominates en); rst_n=0 -> count=0 async.

# shift8_lr_v1 — 8-bit bidirectional shift register

An 8-bit synchronous shift register with parallel load, a direction control,
and a shift enable. Ports: clk, rst_n (asynchronous active-low reset), load,
dir, sh_en, din[7:0], sin (serial input), q[7:0] (registered output).

Behavior (evaluated on the rising edge of clk):
- When load is 1, the register captures the parallel input: q becomes din.
- When load is 0 and sh_en is 1 and dir is 0, the register shifts left:
  q becomes {q[6:0], sin}, inserting sin at the least significant bit.
- When load is 0 and sh_en is 1 and dir is 1, the register shifts right:
  q becomes {sin, q[7:1]}, inserting sin at the most significant bit.
- When load is 0 and sh_en is 0, the register holds its current value.
- When rst_n is 0, q is asynchronously cleared to 0.
Load has priority over shifting; reset has priority over everything.

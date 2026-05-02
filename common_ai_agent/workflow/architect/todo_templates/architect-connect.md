# /connect — add a bus connection between two IP instances

When the user runs `/connect <a/iface> <b/iface> [proto]`, expand to:

1. **Read soc.ssot.yaml** + both leaf SSOTs (`<a>/yaml/<a>.ssot.yaml`
   and `<b>/yaml/<b>.ssot.yaml`).
2. **Verify endpoints.** `iface_a` must exist in A's `busInterfaces`
   (or be a clk/rst port). Same for `iface_b`. Reject with the
   list of valid ifaces if either is wrong.
3. **Verify roles.** One end must be `master`, the other `slave`. CLK
   and RST are exempt (broadcast).
4. **Resolve `proto`.** If the user supplied one, use it. Otherwise
   derive from the leaf SSOTs (both ends must agree).
5. **Reject if `proto` is not in the whitelist** (AXI4 / AXI4L / ACE /
   AHB / APB / AXIS / IRQ / CLK / RST).
6. **Patch soc.ssot.yaml.** Append to `connections[]`:
       { from: <a>/<iface_a>, to: <b>/<iface_b>, proto: <proto> }
7. **Disk-truth verification.** Run
   `Action: run_command("bash workflow/architect/scripts/check_architect_disk.sh")`.
   PASS = the connection is on disk. FAIL = re-open soc.ssot.yaml
   with `read_file`; the claimed edit didn't actually land.
8. **Suggest next step.** If the connection adds new bus traffic into
   an existing instance, hint that the user may want to `/wrapper-gen`
   to refresh the top-level wrapper.

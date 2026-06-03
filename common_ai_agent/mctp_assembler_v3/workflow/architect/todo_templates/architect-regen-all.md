# /regen-all — dispatch rtl-gen on every IP whose RTL is stale

When the user runs `/regen-all`, expand to:

1. **Read soc.ssot.yaml.** Pull the list of instances.
2. **For each instance**, fetch its current status (read each leaf
   SSOT's `<ip>/rtl/` directory). Pick the ones with `rtl != ok`
   (no SV files, or SSOT mtime newer than newest RTL mtime).
3. **Confirm with the user.** List the IPs to regenerate; ask `y/n`.
4. **Dispatch in sequence** (not parallel — keeps the chat readable):
   for each IP, call `dispatch_workflow(workflow="rtl-gen",
   scope="<ip>", prompt="regenerate RTL from <ip>.ssot.yaml")`.
5. **Per-IP summary.** After each dispatch, log: "✓ <ip>: +N/-M lines"
   or "✗ <ip>: <error>". Do NOT paste the sub-agent transcript.
6. **Disk-truth verification (per IP).** After each `[MAS RESULT] DONE`
   from rtl-gen, IMMEDIATELY run
   `Action: run_command("ls -la <ip>/rtl/ <ip>/list/")` to confirm
   `.sv` and `.f` files actually exist with non-zero size. The
   sub-workflow's DONE message alone is NOT proof — surface DONE as
   `(claimed)` until disk verification passes.
7. **Final.** Report the count of VERIFIED-on-disk successes / failures
   (claimed-only DONEs do NOT count as success) and suggest
   `/wrapper-gen` if any IP truly succeeded.

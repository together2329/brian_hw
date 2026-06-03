# /import-ipxact — register an IP-XACT XML as a new SoC instance

When the user runs `/import-ipxact <xml-path> [name] [cluster]`, expand
to this todo sequence:

1. **Read soc.ssot.yaml.** Capture current state (or create minimal).
2. **Run `ipxact_import`** with `xml_path=<path>`, `ip_name=<name>` (if
   provided). The tool returns the IP name + the leaf SSOT path it
   created at `<name>/yaml/<name>.ssot.yaml`.
3. **Pick `addr`** for the new instance. Prefer the IP-XACT-derived
   memoryMap base if present in the leaf SSOT; otherwise pick the next
   4-KiB-aligned hole.
4. **Patch soc.ssot.yaml.**
       instances:  + { id: <name>, ssot: <name>/yaml/<name>.ssot.yaml, addr: <addr> }
       addrMap:    + { name: <name>, base: <addr>, range: <range from leaf> }
   If a cluster was named, append `<name>` to that cluster's `members`.
   If no cluster named, leave the instance "uncategorized" — the
   architect view will surface it in a default cluster.
5. **Run `addrmap_check`.** Halt + revert step 4 on ✗.
6. **Disk-truth verification.** Run
   `Action: run_command("bash workflow/architect/scripts/check_architect_disk.sh")`
   AND `Action: read_file(path="<name>/yaml/<name>.ssot.yaml")` to
   confirm the leaf SSOT actually exists with parsed content. ipxact_import
   returning success is NOT proof — only the read_file output is.
7. **Summarize.** Read back the new instance + count its
   `busInterfaces` from the leaf SSOT. Report:
       "Imported `<name>` (vendor.library.version) — N busInterfaces,
        M parameters, base @ 0x…. Next: `/connect` to wire it up, or
        `/workflow rtl-gen` if RTL needs generating from the new SSOT."

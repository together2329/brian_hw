# /add-ip — add a new IP instance to the SoC

When the user runs `/add-ip <name> [cluster] [addr]`, expand to this
todo sequence (all items start as `pending`):

1. **Read soc.ssot.yaml** — capture current `instances`, `addrMap`,
   `clusters`. If the file is missing, create it from a minimal
   template (just `name`, `version`, `clusters: []`, `instances: []`).
2. **Validate args.** `name` must be `[A-Za-z][A-Za-z0-9_]*` and not
   already an instance id.
3. **Pick `addr`** if not provided. Find the next 4-KiB-aligned hole
   in `addrMap` after the highest existing entry; default range
   `0x1000`.
4. **Scaffold the IP layout.** `scaffold_ip(name=name)`. Confirm
   `<name>/yaml/<name>.ssot.yaml` was created with the standard TBD
   placeholders.
5. **Patch soc.ssot.yaml.** Add to `instances[]`:
       { id: <name>, ssot: <name>/yaml/<name>.ssot.yaml, addr: <addr> }
   Add to `addrMap[]`:
       { name: <name>, base: <addr>, range: 0x1000 }
   If a cluster was named, append `<name>` to that cluster's `members`.
6. **Run `addrmap_check`.** Halt + revert step 5 if it returns ✗.
7. **Suggest next step.** "IP `<name>` added. Next: `/workflow ssot-gen`
   to fill in the leaf SSOT (interfaces / parameters / memory map),
   or `/import-ipxact` if you have an XML to bring in."

## Failure handling

- If step 4 fails (filesystem error), abort the whole sequence and tell
  the user.
- If step 5 fails to write soc.ssot.yaml, restore from the in-memory
  copy captured in step 1.
- If step 6 fails, revert the soc.ssot.yaml change with `replace_in_file`
  and surface the offending overlap to the user.

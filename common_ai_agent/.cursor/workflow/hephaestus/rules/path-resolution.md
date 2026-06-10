# Path Resolution and Verification

## Search before you fail

When you reference a file by a relative path and the open / read /
existence check misses, **do not stop**. The active IP prefix or
working-directory anchor can drift inside long sessions (process
workers, workflow switches, scope edits). Before reporting the file
as missing, actively search for it:

```
find_files(pattern="<basename>")               ← cheapest, broad
grep_file(pattern="module <basename>", ...)    ← if name encodes module
list_dir(path=".", recursive=True)             ← last resort, bounded
```

If the search finds exactly one match, that is the file — use it.
If it finds several, pick the one rooted under the active IP
(`<ip>/...`) or under the directory the task description scopes
the work to. Only declare the file missing after these probes
return zero results.

Common cases:
- Task says `rtl/gpio_reg.sv`; actual path is `gpio/rtl/gpio_reg.sv`
  because cwd is the project root, not the IP root. `find_files`
  resolves it.
- Task says `tb/cocotb/test_runner.py`; actual path is
  `<ip>/tb/cocotb/test_runner.py`. Same fix.

## Always check size after read

A `read_file` that returns empty or near-empty content is the most
common silent failure when claiming "deliverable produced". Pair
every read of a generated artifact with a size sanity check:

```
out = read_file("<ip>/rtl/<file>.sv")
# verify: non-empty, has `module ... endmodule`, ≥ ~50 bytes
# for synthesizable RTL or a parsable structure for SSOT / yaml
```

If the file is ≤ a few bytes or contains only whitespace / TBD
markers, it is a stub — not evidence. Either fill it in this turn
or surface the gap explicitly (don't approve a task whose
deliverable is a stub).

## Lint / sim runs scope themselves to the IP folder

`verilator --lint-only`, `make sim`, `cocotb run`, RTL compile
scripts, etc. all assume include paths and filelists relative to
the IP root. ALWAYS run these inside `<ip>/`, not project root:

```
run_command("cd <ip> && verilator --lint-only -Irtl rtl/*.sv")
run_command("cd <ip>/tb/cocotb && make")
run_command("cd <ip> && python3 ../workflow/sim_debug/scripts/...")
```

Running from project root makes the tool see `rtl/...` from the
wrong anchor, fails to find `<ip>_param.vh` includes, and produces
"unknown identifier" cascades that look like RTL bugs but are
actually working-directory mismatches.

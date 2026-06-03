When compressing context for the SoC Architect, **always preserve**:

1. The current state of `soc.ssot.yaml` — at minimum:
   - cluster + instance ids
   - address map (every base + range)
   - connections list (`from` + `to`)
2. Any IP that the user has explicitly named in this session.
3. Pending architectural decisions (e.g. "user is about to import an
   IP-XACT for spi_master") — these belong in the summary as
   open-action items.
4. Any failed `addrmap_check` results — never compress these away,
   because they block subsequent edits.

Drop or summarize:
- Per-IP RTL diffs from sub-workflow runs (just keep the verdict).
- Sim log tails (keep "✓ N tests pass" or "✗ test_xxx failed @ Tns").
- Lint warnings count (just totals).
- Long ipxact_import outputs (keep "imported X with N busInterfaces").

End with a one-paragraph "current SoC state" summary that lists
clusters, IP count, addr usage, and any open architectural questions.

## CLAIMED vs VERIFIED — anti-hallucination rule

When summarizing past activity, NEVER write "added X", "wired Y",
"verified Z" without the corresponding tool evidence in the same
conversation window. Use this template:

- **CLAIMED**: what was discussed but lacks tool evidence.
  - "user requested spi_master cluster wiring" — no write_file yet
- **VERIFIED**: what has on-disk evidence in *this* conversation.
  - "soc.ssot.yaml updated — instances += [spi0]" → only valid if a
    real `Action: write_file(path="soc.ssot.yaml", ...)` or
    `Action: replace_in_file(path="soc.ssot.yaml", ...)` happened.
  - "addrmap_check passed" → only valid after `Action: addrmap_check()`
    or `Action: run_command("...check_architect_disk.sh")` returned 0.
  - "rtl-gen sub-workflow finished spi_master" → only valid after
    `Action: run_command("ls spi_master/rtl/")` confirmed `.sv` files
    on disk; `[MAS RESULT] DONE` from the sub-workflow ALONE is not
    sufficient.

If a fact is CLAIMED-only, mark it `(claimed, unverified)` in the
summary. Do not promote claimed → verified during compression.

## Sub-workflow handoff caveat

`[MAS RESULT]`, `[SSOT RESULT]`, `[SIM ESCALATE]` messages from
sub-workflows are reported text, not ground truth. Always note them
as `(sub-workflow reported X — disk verification pending)` unless a
later `run_command` / `read_file` actually opened the artifact.

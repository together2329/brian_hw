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

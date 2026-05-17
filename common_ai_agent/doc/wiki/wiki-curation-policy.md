# Wiki Curation Policy — what to capture, when to capture it

Working policy for `common_ai_agent/doc/wiki/` and the per-IP
`<ip>/wiki/` directories. Lives here so it can be revised in place as
we learn from real use. Until this page is rewritten, the rules below
apply.

Related: [[karpathy-llm-wiki-pattern]] · [[index]] · [[log]] ·
[[deterministic-emit-stages]]

## Why a policy

A wiki is a *compounding artifact*: each entry should make a future
session faster or prevent a repeated mistake. Without a policy the
wiki drifts into either an empty shell ("nobody wrote anything") or a
noisy log ("everything got dumped here"). Neither compounds.

This page picks a narrow corridor: *capture the rare things that
neither code nor commit history can preserve, and ignore the rest*.

## Rule of one line

> Write to the wiki only when the answer to **"will this exact
> decision / mistake / context happen again, AND can it not be baked
> into code?"** is **yes**.

Everything else stays in code, commit messages, or the LLM call trace.

## Write when (high signal)

1. **A decision that cannot live in code.** Examples: target scale is
   `educational-tiny` because the IP is a fixture, not a SoC; we
   accept this lint waiver because the SSOT explicitly waives it.
2. **A pattern that repeats across IPs.** First time the pattern
   shows up, fix it in code. Second time, write a wiki entry naming
   the pattern so future sessions can search it.
3. **A policy choice (not a code fix).** Examples: "feedback packets
   are the only cross-workflow channel", "all CPU IPs use sync reset
   with PC←0", "DSL-only `sample_condition`".
4. **External concept worth re-using.** Examples: Karpathy's LLM wiki
   pattern, a paper, a vendor pattern adapted into our flow.
5. **IP-handover context.** Anything a future engineer or future LLM
   session would need to re-read to make decisions about this IP.
6. **A real-use debugging lesson.** If a bug or confusing status can only be
   understood by comparing UI/API/worker/headless behavior, update the wiki in
   the same pass as the code/test change. Do not leave the next session to
   rediscover which path is product authority.

## Do NOT write when (noise)

1. The fix already lives in code (`_default_rule_helpers`, a new
   validator, a system prompt clause). Code + commit message *is* the
   memory.
2. The trace is a one-off debugging path with no general lesson.
3. The rule is already in `workflow/<stage>/system_prompt.md`.
4. The motivation is "this would be nice to have written down".
   Without an actual recurring need, do not start a page.

## When to write — the four moments

| Trigger | Action |
|---|---|
| A stage result is **surprising** | Drop a one-line entry in `[[log]]` (project) or `<ip>/wiki/log.md`. No page yet. |
| A **commit** carries a decision that the diff cannot explain on its own | Add one paragraph next to the relevant page; reference the commit SHA. |
| An IP reaches **handover or completion** | Finalize `<ip>/wiki/notes.md` with 3–5 bullets a future maintainer must know. |
| A **new IP starts** and a similar problem looms | Run `wiki_query(topic="...")`; if there is no entry, the current session is the right moment to start one. |
| A **debugging surface changes** | Update the relevant wiki page, usually [[pipeline-progress-debugging]], in the same branch as the code/test change. |

## Promotion ladder

```
1.  log line in <ip>/wiki/log.md (or doc/wiki/log.md)
2.  → repeated 2+ times → consolidated paragraph in an existing page
3.  → still recurring or cited often → dedicated page with YAML frontmatter
4.  → cross-IP rollup needed → entry in doc/wiki/_lessons_index.json (later)
```

Pages stay light until stage 3. Frontmatter (`type`, `tags`,
`updated`, `related`) is added only when we promote to a dedicated
page; that keeps `build_graph.py` happy without forcing tagging on
every line.

## What lives at each level

- `doc/wiki/` — project-wide policies, cross-IP patterns, external
  references, log. Anyone needs this regardless of IP.
- `<ip>/wiki/index.md` — auto-scaffolded ToC into the IP tree.
  Generally untouched by hand.
- `<ip>/wiki/log.md` — IP-specific append-only event log. Surprises
  and gotchas land here first.
- `<ip>/wiki/notes.md` — free-form IP-owner / manager notes; final
  handover summary; references to commits, DB rows, run logs.

## Cite, don't embed

When the underlying evidence is large (LLM trace, scoreboard JSON,
DB row), cite it as metadata instead of copying it into wiki:

```markdown
Evidence:
- atlas.db trace_events WHERE workflow_run_id=2076604 AND stage='sim'
- <ip>/sim/mismatch_classification.json
- commit 21249132
```

The wiki page stays compact; the LLM follows the citation only when it
needs raw detail. This is the L0/L1/L2 layering documented in
[[karpathy-llm-wiki-pattern]].

## Tooling reminders

- `python3 workflow/wiki/build_graph.py --check` — fail on broken refs;
  run before committing wiki changes.
- `python3 workflow/wiki/build_graph.py --ip <name>` — refresh the
  per-IP graph after a stage finishes or after editing
  `<ip>/wiki/*.md`. The headless engine already calls this for you on
  `_finish()`.
- `wiki_query(ip="<name>", topic="<keyword>")` — read-only chat tool
  for status and pages. Use before writing a new entry to make sure
  you are not duplicating one that already exists.

## Living document

If a future commit changes this policy, edit this page in the same
commit and add a `[[log]]` entry. The policy is part of the wiki, so
it compounds the same way the lessons do.

During active ATLAS pipeline development, wiki maintenance is not a separate
documentation phase. The implementation loop is:

```text
change code -> add/adjust tests -> validate in the closest real environment -> update wiki
```

This is especially important for orchestrator, worker, multi-user, and
progress-debug features, where the important knowledge is often the difference
between intended design, shipped UI behavior, and headless reproduction logs.

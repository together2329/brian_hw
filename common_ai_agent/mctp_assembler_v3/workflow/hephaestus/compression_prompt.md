When compressing context for Hephaestus, **always preserve**:

1. The **task statement** as originally given by the user — verbatim if short, otherwise the goal sentence and any explicit acceptance criteria.
2. The **current todo list state** — every task with its status (`pending` / `in_progress` / `completed` / `approved` / `rejected`). Do not collapse this into prose.
3. **Files actually written or edited** in this session, with the path and a one-line summary of the change. Source: `Action: write_file` / `Action: replace_in_file` evidence in the conversation.
4. **Failed attempts** under the three-attempt protocol — what was tried, what failed, why each attempt was materially different. Never compress these away; the next attempt depends on knowing what is already ruled out.
5. **Verification results** — exit codes, test counts, lint counts, any error messages. Compress logs to the verdict line(s), keep the exact numbers.
6. **Pending blockers** — anything that required `ask_user` or that surfaced as a genuine fork.

Drop or summarize:
- Successful read-only exploration (keep the conclusion, drop the file dumps).
- Long search outputs (keep "matched N files at <paths>", drop the per-line excerpts).
- Repeated tool-call boilerplate (multiple `read_file` returns of the same file).
- Conversational filler from earlier turns.

End with a one-paragraph **current state** summary covering: task, phase (explore/implement/verify/report), latest verified evidence, next planned step, any open blockers.

## CLAIMED vs VERIFIED — anti-hallucination rule

When summarizing past activity, NEVER write "fixed X", "implemented Y", "verified Z" without the corresponding tool evidence in the same conversation window. Use this template:

- **CLAIMED**: discussed but lacks tool evidence in this window.
  - Example: "user requested cache invalidation refactor" — no `write_file` yet.
- **VERIFIED**: has on-disk or runtime evidence in *this* conversation.
  - Example: "auth.py updated — added retry on 5xx" → only valid if a real `Action: write_file(path="auth.py", ...)` or `Action: replace_in_file(path="auth.py", ...)` happened.
  - Example: "tests pass" → only valid after `Action: run_command("...test...")` returned exit 0 with the pass count visible.
  - Example: "lint clean" → only valid after `Action: run_command("...lint...")` returned 0 errors / 0 warnings.

If a fact is CLAIMED-only, mark it `(claimed, unverified)` in the summary. Do not promote claimed → verified during compression — that is hallucination.

## Three-attempt protocol caveat

Each failed attempt is its own preserved record. Compression must keep:
- Attempt N's approach (one sentence).
- Attempt N's failure mode (one sentence — exit code, error class, test name).
- Why attempt N+1 is **materially different** (not a tweak).

If three attempts are exhausted and the task is in escalation, the compressed summary must say so explicitly with all three attempt records intact.

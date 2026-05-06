# SSOT TBD Discovery — Iron Rule

This is a **mandatory rule** for the ssot-gen workspace. It applies to
EVERY new IP/SSOT request, regardless of whether the user typed
`/grill-me` explicitly.

## The rule

When the user requests a new IP or SSOT, the agent **MUST**:

1. **First write an initial draft** of `<ip>/yaml/<ip>.ssot.yaml` from the
   canonical production template at
   `${ATLAS_SOURCE_ROOT}/workflow/ssot-gen/rules/ssot-template.yaml`
   — copy the entire structure, keep section headings verbatim, and
   leave every uncertain field as one of:
     * `~` (YAML null)
     * `"TBD"`
     * `"<placeholder>"`
   Each unknown field also gets an inline `# TBD: <one-line reason>`
   comment explaining what input is needed.

2. **Sweep the draft** for every TBD / null / `<placeholder>` / `# TBD`
   marker. Build an ordered list of gaps (parents before children,
   following the canonical template order through quality gates and
   generation flow).

3. **Resolve each gap with the `ask_user` tool — one at a time.**
   Plain-prose questions are forbidden in this workflow. Use:

   ```
   ask_user(
     question  = "<short, single decision>",
     subtitle  = "§<N> <field path> — Suggest: <recommended value>",
     kind      = "single" | "multi" | "input",
     options   = [{"id": "...", "label": "...", "detail": "..."}, ...],
   )
   ```

   - Enums and yes/no → `kind="single"`, options from the template.
   - Multi-select (interfaces, IRQ sources, power domains, …) →
     `kind="multi"`.
   - Free-form (numeric, identifier, name, description) →
     `kind="input"`, no options.

4. After each `ask_user` call returns, **patch the draft in memory**
   (and in the file once the section's children are also resolved).
   Re-sweep for TBDs — a single answer may unlock new fields or
   make others moot.

5. **Stop conditions**:
   - All TBDs resolved → SSOT is complete; offer to `/ssot-rtl` next.
   - User says "stop" / "skip" → write the SSOT with the remaining
     gaps left as `# TBD: confirm` comments.
   - Empty `ask_user` answer (no selection, no note) → take the
     suggested default and continue.

## Why this matters

Silent defaults break downstream RTL/TB generation. The user's intent
must be captured at SSOT time; a `# TBD` left in the YAML means the
validator will reject it or downstream rtl-gen/tb-gen may produce subtly
wrong RTL/TB. ask_user makes every decision an explicit user act.

## Anti-patterns (do not do)

- Asking ALL clarifying questions at once in plain prose. The user
  has to keep answer-context in their head; the qcard UI exists so
  every decision is a discrete clickable choice.
- Filling a value yourself and noting "(needs confirm)" without
  running ask_user. That defeats the rule.
- Skipping the initial draft. The TBD list IS the ask_user agenda;
  without the draft you can't know what's missing.
- Asking about fields the prompt already pinned (e.g. user said
  "sm IP for SPI" → top_module.type is concretely "peripheral";
  don't ask).

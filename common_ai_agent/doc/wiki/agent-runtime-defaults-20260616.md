---
title: Agent runtime defaults, June 2026
type: design
tags: [agent, tools, oag, frontend, config, defaults]
created: 2026-06-16
related: [agent-tool-surface-policy, oag-mode-integration, project_vite_env_stale_build]
---

# Agent Runtime Defaults

ATLAS local defaults should favor a small tool surface, visible audit trail, and
active-IP locality.

## Tool surface

Normal execution should not expose interactive planning or external retrieval
tools by default. `todo_write` / `todo_add` remain plan-mode tools.
`external_db_query`, external wiki aliases (`rtl-db`, `external-db`, `andes`),
and `ask_user` are opt-in because they add latency, side effects, or disruptive
UI flow. Requirements should be resolved in normal conversation unless a user
explicitly opts into a structured interaction mode.

## OAG active IP locality

The native `oag` tool operates from the active workspace IP root. When
`ATLAS_ACTIVE_IP` or `ATLAS_IP_ROOT` identifies an active IP, OAG calls must
default to that IP and reject a different `ip` / `ip_dir` leaf. This prevents a
scaffold or run checkpoint from creating folders under a name unrelated to the
current IP.

## IP scaffold shape

Creating an IP should create the IP's working directories under the IP name and
should not copy the platform workflow engine into `<ip>/workflow`. The workflow
tree stays external and shared. The IP-local scaffold contains only the
practical hardware workspace shape: `cov`, `doc`, `formal`, `handoff`,
`knowledge`, `lint`, `list`, `ontology`, `req`, `rtl`, `scripts`, `sdc`,
`signoff`, `sim`, `syn`, and `tb`, plus lightweight wiki/runbook pointers when
the ATLAS wiki generator is available.

## Chat scroll and OAG visibility

The workspace chat is primarily a live transcript, so new feed entries and
streaming text should scroll to the bottom by default. Tool cards must keep the
called command/tool visible in the header. OAG cards show the full `oag(...)`
call in the header, while long payload/result details start folded so OAG audit
information is available without flooding the chat.

## OAG workspace surface

When `OAG_MODE=1`, the default agent owns the IP workflow through the native OAG
tool for normal work, while the UI still exposes `default` and `sim_debug` as
separate workflow choices. Simulation inspection stays in the `sim_debug`
workflow so the VCD, RTL/source, hierarchy, and waveform panes remain available
without adding a `SIM_DEBUG` center tab to the default workspace.

The default workspace keeps the SSOT/DOC/REQ review tabs visible. OAG chat is
the main control plane, but the structured review surfaces should stay one click
away for requirement, document, and evidence inspection.

The right status/TODO rail is useful for diagnosis, but it consumes first-screen
space. New OAG/default workspaces start with that rail folded; the splitter can
restore it when the user wants the status panel.

## Markdown preview reading surface

The preview pane should render Markdown as a document surface, not as raw text
with light syntax coloring. `.md` and `.markdown` files already use the shared
`marked -> sanitize -> md-agent` pipeline; the preview-specific `.md-preview`
class adds document rhythm: constrained line length, stronger heading hierarchy,
readable tables, callout-style blockquotes, code blocks, checklists, and images.
This keeps README/OAG report artifacts readable without moving them into the
heavier SSOT DOC iframe exporter.

In dark theme, Markdown document surfaces use neutral black backgrounds instead
of accent-mixed browns. Accent colors should mark edges, headings, and chips,
not tint the full reading surface.

Preview Markdown can use an iframe document surface. Unlike chat, preview is a
file-reading pane rather than a streaming transcript, so iframe isolation helps
match the cleaner DOC feel without nested chat scrolling. The iframe receives
sanitized Markdown HTML through `srcDoc`, keeps scripts disabled, and lets the
parent perform the same image/path and Mermaid post-processing after load.

## Chat markdown reading surface

Assistant chat output also uses the shared `md-agent` Markdown pipeline. It
should read like a compact document card rather than terminal dump text:
assistant entries get a quiet panel, clear label, stronger heading hierarchy,
roomier paragraphs/lists, readable tables, callout blockquotes, and code blocks
with enough padding for scanability. User messages remain visually distinct and
tool-card internals keep their own compact affordances.

Dark chat Markdown follows the same neutral black surface rule as preview
Markdown, so rendered assistant output does not drift toward a brown panel.

## Perforce pane responsiveness

The Perforce Sync tab should not wait for a folder click before starting the
next scoped `/api/scm/pane` load. Once a pane is visible, the client can prefetch
the next directly visible folder panes during browser idle time and cache them
briefly. Clicking a prefetched folder then applies the cached payload
immediately while normal mutation actions clear the cache before reloading live
state.

## Reasoning effort

Local checked-in defaults target `gpt-5.5`-class reasoning. `REASONING_MODE` and
`REASONING_EFFORT` default to `xhigh`, while runtime settings can still lower
effort when the user selects a cheaper or faster mode.

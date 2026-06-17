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
`wiki_query`, `external_db_query`, external wiki aliases (`rtl-db`,
`external-db`, `andes`), and `ask_user` are opt-in because they add latency,
side effects, or disruptive UI flow. Requirements should be resolved in normal
conversation unless a user explicitly opts into a structured interaction mode.

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

Tool-call detail bodies can render inside a small iframe document surface once
the user expands them. The tool-card header, status glyph, line count, command
text, and fold control stay in the parent chat DOM so the audit trail remains
visible and clickable. The iframe is for the noisy result/details body only:
plain output, grep output, diffs, and workflow Markdown results get a clean
black reading surface without taking over chat interaction.

The live tool-call command text, streaming text, and reasoning blocks stay in
the parent chat DOM for stability and predictable folding. Iframe-backed
surfaces are limited to completed assistant Markdown and expanded tool-result
details. Those iframes schedule auto-height updates through
`requestAnimationFrame` and ignore unchanged heights, avoiding ResizeObserver
loop warnings. Live reasoning coalescing treats provider updates as cumulative
snapshots when possible, so repeated reasoning summaries replace earlier text
instead of duplicating it.

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

Completed assistant chat bodies can use the same isolated document-surface
idea as Preview, but only after streaming is done. Live token output, tool
cards, OAG command headers, and Q&A/tool affordances stay in the parent chat
DOM so scrolling, folding, copy buttons, and running-state updates remain
stable. The iframe receives sanitized Markdown through `srcDoc`, disables
scripts, auto-sizes to its document height, and keeps the tool-call audit trail
outside the frame.

Live streaming should still feel visually continuous with the completed
iframe-backed answer. The streaming body stays in the parent DOM for stable
scrolling and caret updates, but it uses the same reading-surface basics as the
iframe document: neutral black/white background, 88ch max width, 14px body text,
1.68 line-height, and parent-side whitespace wrapping. This reduces the visual
jump when a live answer settles into the completed Markdown iframe without
moving streaming into iframe lifecycle.

Agent/User chat rows should read like a compact transcript, not a stack of
terminal blobs. Each row uses a small mono role header (`Agent` / `You`) with a
thin rule and a document body below it; user Markdown uses the same sans-serif
reading rhythm as assistant Markdown instead of mono inline text. Tool-result
details remain visually separate, but their diff/replacement red-green row
tints must live inside the tool iframe CSS because outer `.tool-output-diff`
rules cannot cross the iframe boundary.

Role labels should not be vertically clipped or over-compressed: keep the label
line box taller than the glyphs and avoid forced uppercase transforms that make
`Agent` / `You` look half-rendered on mixed Korean/Latin font stacks. The
spacing after an Agent answer is a small transcript separator, not a mandatory
blank line; tool cards that immediately follow an answer should sit close enough
to read as the same turn.

Tool-call and reasoning surfaces should not feel like a separate terminal skin
beside the iframe-backed assistant answer. Use the same sans-serif document
rhythm for readable tool arguments, summaries, handoff rows, and reasoning
text; keep monospace only where exact code/command identity matters, such as
tool names, timestamps, inline code chips, and preformatted output.

The page-level error banner should not surface browser `ResizeObserver` loop
notifications as fatal uncaught errors. Those notifications can be emitted by
native layout delivery after otherwise valid observer callbacks or third-party
canvas/layout libraries, and they do not identify a broken ATLAS action by
themselves. The reporter suppresses only the exact ResizeObserver loop
notification strings while leaving generic uncaught errors, promise rejections,
and asset-load failures visible.

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

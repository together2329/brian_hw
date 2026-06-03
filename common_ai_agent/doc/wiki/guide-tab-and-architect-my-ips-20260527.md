# Guide Tab + Architect "My IPs" Landing (2026-05-27)

> **Updated**: 2026-05-27
> **Scope**: Two frontend-only UI changes — a new **Guide** tab, and replacing the
> Architect screen's demo-SoC mock landing with the user's own IP card grid.
> **Related**: [[default-agent-ip-flow]] · [[workflow-ownership-and-boundaries]] ·
> [[atlas-pipeline-screen]] · [[common-ai-agent-map]]

## Why

1. The Architect screen opened on a bundled **mock SoC** (`window.SOC` = `aurora_soc`,
   fake cpu0/cpu1/l2_cache). Users saw demo data instead of their own work.
2. There was no in-app explanation of what the tool does or what each workflow is for.

## Guide tab

- New screen component `frontend/atlas/guide.tsx` → `window.AtlasGuide`, now compiled
  into the Vite bundle (the old `_inline_html_cached` auto-inline of per-file `.jsx`
  was retired with the `index.html` shell on 2026-05-30; see the comment at
  `src/atlas_ui.py:~1443`). Nav button sits between `◇ Architect` and the `run`
  selector; `screen === 'guide'` is wired into the router and the URL/localStorage
  valid-screen checks in `app.tsx`.
- Content is **authored HTML** rendered through `DOMPurify.sanitize` (scoped CSS lives
  in a sibling `<style>`; classes survive sanitize).
- **Framing (intentional):** ATLAS is presented as an **SSOT · RTL Generation Agent**.
  `ssot-gen` → `rtl-gen` is the product core; every other workflow (TB/SIM/LINT/
  COVERAGE/SYN/STA/PnR/STA-post) is framed as **RTL-quality assurance**. Text is
  distilled from [[default-agent-ip-flow]] (default mode), [[workflow-ownership-and-boundaries]]
  (per-workflow ownership), and `workflow/wiki/ip_knowledge/*.md`.

## Architect "My IPs" landing

- `frontend/atlas/soc-architect.jsx`: `SocArchitect(props)` now takes `ipOptions` /
  `activeIp` (from `app.jsx`). New `selectedIp` state — `''` shows the landing grid,
  a name shows that IP's diagram.
- The `window.SOC` / `window.SOC_LOOKUP` mock fallback is removed (→ `EMPTY_SOC`). The
  mock module stays in `soc-data.jsx` but is now dead code on this path.
- New `ArchitectMyIps` card grid self-fetches `/api/ip/list` (owner-scoped via the auth
  cookie when no `session_id` is passed) for rich cards (SSOT badge, workflow chips,
  updated-at); the `ipOptions` name list seeds an instant paint. Empty state when the
  user has no IPs.
- Opening a card sets `selectedIp` → `_fetchLiveSoc(ipName)` requests
  `/api/soc?ip=<name>` (the existing per-IP, owner-safe, cached path) and the existing
  diagram renders. A "← All IPs" run-bar button returns to the grid.

## Safety / blast radius

- **Pure frontend** — no backend/DB/server/schema change; revert = `git checkout` the
  frontend files. (Originally JSX inlined fresh on mtime change; under the current
  Vite path a `vite build` / dist refresh is the equivalent reload step.)
- `window.SOC` had exactly two call sites (both replaced). Existing `soc`-dependent
  hooks were already empty-safe (`soc.clusters || []`, guarded `clusters[0]`), and the
  179 `soc` refs live in the diagram render which only runs once a card is opened
  (real data present). The grid is reached via an early return before the diagram.

## Verify

```bash
CK="atlas_session=$(cat /tmp/atlas_cookie)"
curl -s http://192.168.45.139:3000/ -b "$CK" | grep -c "window.AtlasGuide"        # ≥1 inlined
curl -s "http://192.168.45.139:3000/api/ip/list" -b "$CK"                          # owner-scoped items
curl -s "http://192.168.45.139:3000/api/soc?ip=demo_counter8" -b "$CK"             # source=scoped-dir-walk (not aurora)
```
Browser (hard-refresh): Guide tab between Architect and `run`; Architect opens on the
**My IPs** grid (no aurora mock); card click → that IP's SoC diagram; "← All IPs" back.

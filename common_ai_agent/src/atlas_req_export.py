"""REQ bundle aggregation + HTML rendering for the ATLAS REQ tab.

The REQ tab unifies the per-IP "locked-truth" bundle into a single
human-reviewable HTML document, modeled after the DOC tab (server-rendered
HTML streamed into an iframe). The canonical bundle lives under ``<ip>/req/``
and is the single source of truth (all IPs are normalized to this shape):

  - requirements : ``req/requirements_index.json`` (requirements[]) — and the
                   optional ``req/*_requirements.md`` prose / ``req/locked_truth.md``
  - obligations  : ``req/obligations.json`` (obligations[])
  - contract     : ``req/contract_refs.json`` (contract_refs[])
  - evidence     : ``req/evidence_plan.json`` (evidence_plan[])
  - approval/lock: ``req/approval_manifest.json`` + ``req/ssot_validation.json``

Everything is cross-linked by id (requirement_id ↔ obligation_id ↔
contract_ref_id ↔ evidence_id), so the rendered doc surfaces the full
requirement→obligation→contract→evidence chain for human review.

Read-only with respect to IP artifacts: this module never writes into the
``req/`` dir. The caller persists the rendered HTML under
``<ip>/doc/<ip>_req.html`` (same convention as the SSOT export). The route is
wired in src/atlas_ui.py as ``GET /api/req/export``.
"""
from __future__ import annotations

import html
import json as _json
from pathlib import Path
from typing import Any

try:  # markdown is a soft dependency; fall back to <pre> when absent.
    import markdown as _markdown
except Exception:  # pragma: no cover - environment without markdown
    _markdown = None


# ---------------------------------------------------------------------------
# data loading (read-only)
# ---------------------------------------------------------------------------
def _read_json(path: Path) -> Any:
    try:
        return _json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_req_bundle(ip_dir: Path, ip: str) -> dict[str, Any]:
    """Collect the canonical REQ bundle for ``ip`` rooted at ``ip_dir``."""
    ip_dir = Path(ip_dir)
    req = ip_dir / "req"
    req_md = next(iter(sorted(req.glob("*_requirements.md"))), None)
    return {
        "ip": ip,
        "requirements_md": _read_text(req_md) if req_md else "",
        "requirements_md_path": (
            str(req_md.relative_to(ip_dir)) if req_md else ""
        ),
        "locked_truth_md": _read_text(req / "locked_truth.md"),
        "requirements": _read_json(req / "requirements_index.json"),
        "obligations": _read_json(req / "obligations.json"),
        "contract": _read_json(req / "contract_refs.json"),
        "evidence": _read_json(req / "evidence_plan.json"),
        "approval": _read_json(req / "approval_manifest.json"),
        "validation": _read_json(req / "ssot_validation.json"),
    }


# ---------------------------------------------------------------------------
# html helpers
# ---------------------------------------------------------------------------
def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


_OK = {"pass", "passed", "approved", "locked", "requirements_locked", "ok", "true"}
_BAD = {"fail", "failed", "blocked", "error", "false", "rejected"}


def _badge(status: Any) -> str:
    text = "" if status is None else str(status)
    key = text.lower()
    cls = "ok" if key in _OK else ("bad" if key in _BAD else "warn")
    return f'<span class="badge {cls}">{_esc(text or "n/a")}</span>'


def _refs(values: Any) -> str:
    items = values if isinstance(values, list) else ([] if values is None else [values])
    if not items:
        return "<span class='muted'>—</span>"
    return " ".join(f"<code class='ref'>{_esc(v)}</code>" for v in items)


def _clip(text: Any, n: int = 160) -> str:
    s = "" if text is None else str(text)
    return _esc(s[:n]) + ("…" if len(s) > n else "")


def _md_to_html(text: str) -> str:
    if not text:
        return ""
    if _markdown is None:
        return f"<pre class='raw'>{_esc(text)}</pre>"
    try:
        return _markdown.markdown(
            text, extensions=["tables", "fenced_code", "toc", "sane_lists"],
        )
    except Exception:
        return f"<pre class='raw'>{_esc(text)}</pre>"


def _items(doc: Any, key: str) -> list:
    if isinstance(doc, dict):
        val = doc.get(key)
        return val if isinstance(val, list) else []
    if isinstance(doc, list):
        return doc
    return []


# ---------------------------------------------------------------------------
# section renderers
# ---------------------------------------------------------------------------
def _sec_approval(b: dict[str, Any]) -> str:
    a = b.get("approval") or {}
    val = b.get("validation") or {}
    if not a and not val:
        return (
            "<section id='approval'><h2><span class='kicker'>LOCK</span> "
            "Approval &amp; Locked Truth</h2>"
            "<p class='muted'>(no approval manifest)</p></section>"
        )
    reqs = _items(a, "requirements")
    locked = sum(1 for r in reqs if str((r or {}).get("status", "")).lower() in _OK)
    sha = str(a.get("bundle_sha256") or "")
    grid = [
        ("status", _badge(a.get("status"))),
        ("approved_by", f"<b>{_esc(a.get('approved_by'))}</b>"),
        ("approved_at", f"<b class='sm'>{_esc(a.get('approved_at_utc'))}</b>"),
    ]
    if a.get("approval_mode"):
        grid.append(("mode", f"<b>{_esc(a.get('approval_mode'))}</b>"))
    if a.get("locked_truth_scope"):
        grid.append(("scope", f"<b>{_esc(a.get('locked_truth_scope'))}</b>"))
    if reqs:
        grid.append(("requirements", f"<b>{locked}/{len(reqs)} locked</b>"))
    if sha:
        grid.append(("bundle_sha256", f"<b class='sm'>{_esc(sha[:16])}…</b>"))
    grid_html = "".join(
        f"<div class='kv'><span>{_esc(k)}</span>{v}</div>" for k, v in grid
    )
    note = ""
    if a.get("decision_note"):
        note = f"<div class='note'>{_esc(a.get('decision_note'))}</div>"

    # SSOT validation (preview gate) — blockers/warnings.
    val_html = ""
    if val:
        blockers = _items(val, "blockers")
        warnings = _items(val, "warnings")
        rows = "".join(
            f"<tr><td>{_badge(bk.get('severity') or 'blocker')}</td>"
            f"<td class='mono sm'>{_esc(bk.get('path') or bk.get('id'))}</td>"
            f"<td class='sm'>{_esc(bk.get('message'))}</td>"
            f"<td class='sm muted'>{_clip(bk.get('fix'), 140)}</td></tr>"
            for bk in blockers if isinstance(bk, dict)
        )
        val_table = (
            "<table><thead><tr><th>severity</th><th>path</th><th>message</th>"
            f"<th>fix</th></tr></thead><tbody>{rows}</tbody></table>"
            if rows else "<p class='muted'>no blockers</p>"
        )
        val_html = f"""
      <h3>SSOT validation {_badge('pass' if val.get('ok') else 'fail')}
        <span class='muted' style='font-weight:400'>· {_esc(val.get('mode',''))}
        · {len(blockers)} blockers · {len(warnings)} warnings</span></h3>
      {val_table}"""
    return f"""
    <section id="approval">
      <h2><span class="kicker">LOCK</span> Approval &amp; Locked Truth</h2>
      <div class="grid3">{grid_html}</div>
      {note}
      {val_html}
    </section>"""


def _sec_requirements(b: dict[str, Any]) -> str:
    reqs = _items(b.get("requirements"), "requirements")
    val = b.get("validation") or {}
    rows = "".join(
        f"<tr><td class='mono'>{_esc(r.get('requirement_id'))}</td>"
        f"<td>{_esc(r.get('title'))}</td>"
        f"<td class='mono sm'>{_esc(r.get('kind'))}</td>"
        f"<td>{_badge(r.get('status'))}</td>"
        f"<td class='sm'>{_clip(r.get('statement'), 220)}</td>"
        f"<td class='sm'>{_refs(r.get('obligation_refs'))}</td></tr>"
        for r in reqs if isinstance(r, dict)
    )
    table = (
        "<table><thead><tr><th>requirement_id</th><th>title</th><th>kind</th>"
        "<th>status</th><th>statement</th><th>→ obligations</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        if reqs else "<p class='muted'>(no requirements index)</p>"
    )
    locked = sum(1 for r in reqs if str((r or {}).get("status", "")).lower() in _OK)

    # optional prose doc: prefer *_requirements.md, else locked_truth.md
    doc = ""
    if b.get("requirements_md"):
        size = len(b["requirements_md"])
        doc = (
            f"<details class='doc'><summary>requirements document · "
            f"{_esc(b.get('requirements_md_path'))} ({size:,} bytes)</summary>"
            f"<div class='md'>{_md_to_html(b['requirements_md'])}</div></details>"
        )
    elif b.get("locked_truth_md"):
        size = len(b["locked_truth_md"])
        doc = (
            f"<details class='doc'><summary>locked truth · req/locked_truth.md "
            f"({size:,} bytes)</summary>"
            f"<div class='md'>{_md_to_html(b['locked_truth_md'])}</div></details>"
        )
    return f"""
    <section id="req">
      <h2><span class="kicker">REQ</span> Requirements</h2>
      <div class="metarow">
        <span class="stat"><b>{locked}</b>/{len(reqs)} locked</span>
        {_badge('pass' if val.get('ok') else 'fail') if val else ''}
        <span class="muted">requirement → obligation chain</span>
      </div>
      {table}
      {doc}
    </section>"""


def _sec_obligations(b: dict[str, Any], compact: bool = False) -> str:
    obls = _items(b.get("obligations"), "obligations")
    shown = obls[:12] if compact else obls
    rows = "".join(
        f"<tr><td class='mono'>{_esc(o.get('obligation_id'))}</td>"
        f"<td>{_badge(o.get('status'))}</td>"
        f"<td class='sm'>{_clip(o.get('statement'), 200)}</td>"
        f"<td class='sm'>{_refs(o.get('requirement_refs'))}</td>"
        f"<td class='sm'>{_refs(o.get('contract_refs'))}</td></tr>"
        for o in shown if isinstance(o, dict)
    )
    more = (
        f"<tr><td colspan='5' class='muted'>… {len(obls) - 12} more obligations</td></tr>"
        if compact and len(obls) > 12 else ""
    )
    table = (
        "<table><thead><tr><th>obligation_id</th><th>status</th><th>statement</th>"
        "<th>← requirements</th><th>→ contract</th></tr></thead>"
        f"<tbody>{rows}{more}</tbody></table>"
        if obls else "<p class='muted'>(no obligations)</p>"
    )
    ok = sum(1 for o in obls if str((o or {}).get("status", "")).lower() in _OK)
    return f"""
    <section id="obli">
      <h2><span class="kicker">OBLI</span> Obligations</h2>
      <div class="metarow">
        <span class="stat"><b>{len(obls)}</b> obligations</span>
        <span class="stat"><b>{ok}</b> locked</span>
        <span class="muted">each obligation binds a requirement to a contract check</span>
      </div>
      {table}
    </section>"""


def _sec_contract(b: dict[str, Any], compact: bool = False) -> str:
    refs = _items(b.get("contract"), "contract_refs")
    rows = "".join(
        f"<tr><td class='mono'>{_esc(c.get('contract_ref_id'))}</td>"
        f"<td class='mono sm'>{_esc(c.get('kind'))}</td>"
        f"<td class='mono sm'>{_esc(c.get('check_type'))}</td>"
        f"<td class='mono sm'>{_esc(c.get('signal') or ', '.join(c.get('signal_refs') or []))}</td>"
        f"<td class='sm'>{_clip(c.get('statement'), 180)}</td>"
        f"<td class='sm'>{_refs(c.get('obligation_refs'))}</td></tr>"
        for c in refs if isinstance(c, dict)
    )
    table = (
        "<table><thead><tr><th>contract_ref_id</th><th>kind</th><th>check</th>"
        "<th>signal(s)</th><th>statement</th><th>← obligations</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        if refs else "<p class='muted'>(no contract refs)</p>"
    )
    return f"""
    <section id="contract">
      <h2><span class="kicker">CONTRACT</span> Contract References</h2>
      <div class="metarow">
        <span class="stat"><b>{len(refs)}</b> contract refs</span>
        <span class="muted">checkable assertions derived from obligations</span>
      </div>
      {table}
    </section>"""


def _sec_evidence(b: dict[str, Any], compact: bool = False) -> str:
    plan = _items(b.get("evidence"), "evidence_plan")
    rows = "".join(
        f"<tr><td class='mono'>{_esc(e.get('evidence_id'))}</td>"
        f"<td class='mono sm'>{_esc(e.get('contract_ref'))}</td>"
        f"<td class='mono sm'>{_clip(e.get('validator'), 70)}</td>"
        f"<td class='mono sm'>{_clip(e.get('artifact'), 70)}</td>"
        f"<td class='sm'>{_clip(e.get('pass_condition'), 180)}</td></tr>"
        for e in plan if isinstance(e, dict)
    )
    table = (
        "<table><thead><tr><th>evidence_id</th><th>contract_ref</th><th>validator</th>"
        "<th>artifact</th><th>pass condition</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        if plan else "<p class='muted'>(no evidence plan)</p>"
    )
    return f"""
    <section id="evidence">
      <h2><span class="kicker">EVIDENCE</span> Evidence Plan</h2>
      <div class="metarow">
        <span class="stat"><b>{len(plan)}</b> planned</span>
        <span class="muted">how each contract ref will be proven</span>
      </div>
      {table}
    </section>"""


# ---------------------------------------------------------------------------
# document shell
# ---------------------------------------------------------------------------
_CSS = """
:root{--fg:#1c2430;--mut:#67738a;--line:#e3e8f0;--bg:#fff;--panel:#f7f9fc;
--ok:#117a3d;--okbg:#e7f6ec;--bad:#b42318;--badbg:#fdecea;--warn:#8a5a00;--warnbg:#fcf3df;--acc:#315fdc;}
*{box-sizing:border-box}
body{margin:0;color:var(--fg);background:var(--bg);
font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}
.mono,code,.path{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;}
.wrap{max-width:1040px;margin:0 auto;padding:0 28px 80px;}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);
border-bottom:1px solid var(--line);padding:18px 28px;margin:0 -28px 8px;}
.top .ttl{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.top h1{font-size:20px;margin:0;letter-spacing:.01em}
.wordmark{font-weight:800;letter-spacing:.16em;font-size:12px;color:var(--acc);
border:1px solid var(--acc);border-radius:4px;padding:2px 7px}
.sub{color:var(--mut);font-size:12px;margin-top:6px}
.scorecard{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
.score{flex:1;min-width:140px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:var(--panel)}
.score .lab{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.07em}
.score .val{font-size:18px;font-weight:700;margin-top:2px;display:flex;align-items:center;gap:8px}
nav.toc{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0 6px}
nav.toc a{font-size:12px;color:var(--mut);text-decoration:none;border:1px solid var(--line);
border-radius:999px;padding:3px 11px}
nav.toc a:hover{color:var(--acc);border-color:var(--acc)}
section{border-top:1px solid var(--line);padding:22px 0 6px;scroll-margin-top:90px}
h2{font-size:16px;margin:0 0 12px;display:flex;align-items:center;gap:10px}
h3{font-size:12.5px;color:var(--fg);letter-spacing:0;margin:18px 0 8px;display:flex;align-items:center;gap:8px}
.kicker{font-size:10px;font-weight:800;letter-spacing:.12em;color:#fff;background:var(--acc);
border-radius:4px;padding:2px 6px}
.path{font-size:11px;color:var(--mut);font-weight:400}
.metarow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px;font-size:12px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:2px 9px}
.stat b{font-size:14px}
.badge{font-size:11px;font-weight:700;border-radius:999px;padding:2px 9px;text-transform:uppercase;letter-spacing:.04em;white-space:nowrap}
.badge.ok{color:var(--ok);background:var(--okbg)}
.badge.bad{color:var(--bad);background:var(--badbg)}
.badge.warn{color:var(--warn);background:var(--warnbg)}
.muted{color:var(--mut)}
.note{border-left:3px solid var(--acc);background:var(--panel);padding:8px 12px;margin:10px 0;
font-size:12.5px;border-radius:0 6px 6px 0}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin:6px 0;table-layout:fixed}
th{text-align:left;color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;
letter-spacing:.05em;border-bottom:1px solid var(--line);padding:7px 8px}
td{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top;overflow-wrap:anywhere}
tr:hover td{background:var(--panel)}
td.mono,.mono{font-size:11.5px}
td.sm,.sm{font-size:11.5px;color:#3a4658}
code.ref{background:color-mix(in oklch,var(--acc) 9%,transparent);color:var(--acc);
border-radius:4px;padding:1px 5px;font-size:11px;white-space:nowrap;display:inline-block;margin:1px 2px 1px 0}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}
.kv{border:1px solid var(--line);border-radius:7px;padding:8px 10px;background:var(--panel)}
.kv span{display:block;font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px}
.kv b{font-size:13px}
details.doc{border:1px solid var(--line);border-radius:8px;background:var(--panel);padding:0 14px;margin-top:12px}
details.doc>summary{cursor:pointer;padding:10px 0;font-size:12px;color:var(--mut);font-weight:600}
.md{background:#fff;border-radius:6px;padding:6px 16px 16px;max-height:560px;overflow:auto}
.md h1{font-size:18px}.md h2{font-size:15px;border:0;padding:0;display:block}
.md h3{color:var(--fg);text-transform:none;letter-spacing:0}
.md table{font-size:12px;table-layout:auto}.md code{background:var(--panel);padding:1px 5px;border-radius:4px;font-size:12px}
.md pre{background:#0f1622;color:#d6e2ff;padding:12px;border-radius:8px;overflow:auto;font-size:12px}
.raw{white-space:pre-wrap}
.variant{font-size:11px;color:var(--mut);float:right}
"""


def _score_cards(b: dict[str, Any], full: bool) -> str:
    reqs = _items(b.get("requirements"), "requirements")
    obls = _items(b.get("obligations"), "obligations")
    refs = _items(b.get("contract"), "contract_refs")
    plan = _items(b.get("evidence"), "evidence_plan")
    val = b.get("validation") or {}
    cards = [
        ("Requirements", f"{len(reqs)} reqs"),
        ("Obligations", f"{len(obls)} obli"),
        ("Contract", f"{len(refs)} refs"),
        ("Evidence", f"{len(plan)} planned"),
    ]
    if full:
        a = b.get("approval") or {}
        cards.append(("Approval", _badge(a.get("status") or ("pass" if val.get("ok") else "n/a"))))
    return "".join(
        f"<div class='score'><div class='lab'>{_esc(label)}</div>"
        f"<div class='val'>{value}</div></div>"
        for label, value in cards
    )


def render_req_html(bundle: dict[str, Any], ip: str, variant: str = "full") -> str:
    """Render the canonical REQ bundle to a standalone HTML document.

    ``variant``:
      - ``full``  : approval/lock section first, every table expanded (default).
      - ``core4`` : lean req+obli+contract+evidence; lock shown as header badge.
    """
    full = variant != "core4"
    a = bundle.get("approval") or {}
    val = bundle.get("validation") or {}
    if full:
        toc_items = [("approval", "Lock"), ("req", "Requirements"),
                     ("obli", "Obligations"), ("contract", "Contract"),
                     ("evidence", "Evidence")]
        body = (_sec_approval(bundle) + _sec_requirements(bundle)
                + _sec_obligations(bundle) + _sec_contract(bundle)
                + _sec_evidence(bundle))
    else:
        toc_items = [("req", "Requirements"), ("obli", "Obligations"),
                     ("contract", "Contract"), ("evidence", "Evidence")]
        body = (_sec_requirements(bundle) + _sec_obligations(bundle, compact=True)
                + _sec_contract(bundle, compact=True)
                + _sec_evidence(bundle, compact=True))
    toc = "".join(f"<a href='#{i}'>{_esc(label)}</a>" for i, label in toc_items)
    status = a.get("status") or ("locked" if val.get("ok") else "n/a")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(ip)} · REQ</title><style>{_CSS}</style></head>
<body><div class="wrap">
<header class="top">
  <span class="variant">variant: <b>{_esc(variant)}</b></span>
  <div class="ttl"><span class="wordmark">REQ</span><h1>{_esc(ip)}</h1>
    {_badge(status)}
    <span class="muted" style="font-size:12px">{_esc(a.get('approved_by',''))}</span></div>
  <div class="sub">Unified requirements · obligations · contract · evidence — one human-reviewable view.</div>
  <div class="scorecard">{_score_cards(bundle, full)}</div>
  <nav class="toc">{toc}</nav>
</header>
{body}
</div></body></html>"""


def req_html_for_ip(ip_dir: Path, ip: str, variant: str = "full") -> str:
    """Convenience: load the bundle and render it in one call."""
    return render_req_html(load_req_bundle(ip_dir, ip), ip, variant=variant)

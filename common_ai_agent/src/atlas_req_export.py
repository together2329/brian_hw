"""REQ bundle aggregation + HTML rendering for the ATLAS REQ tab.

The REQ tab unifies a per-IP "locked-truth" bundle into a single
human-reviewable HTML document, modeled after the DOC tab (server-rendered
HTML streamed into an iframe). It aggregates:

  - requirements : ``req/<ip>_requirements.md`` + ``req/ssot_validation.json``
  - obligations  : ``signoff/evidence_contract_coverage.json`` (obligations[])
  - contract     : ``verify/ip_contract.json`` + ``signoff/contract_check.json``
  - evidence     : sign-off gates from ``signoff/ip_signoff.json`` + coverage
  - approval/lock: ``req/approval_manifest.json``

Read-only with respect to IP artifacts: this module never writes into the
``req/``, ``verify/`` or ``signoff/`` dirs. The caller persists the rendered
HTML under ``<ip>/doc/<ip>_req.html`` (same convention as the SSOT export).

Companion to src/atlas_ssot_export.py (the DOC export). The route is wired in
src/atlas_ui.py as ``GET /api/req/export``.
"""
from __future__ import annotations

import html
import json
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
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_req_bundle(ip_dir: Path, ip: str) -> dict[str, Any]:
    """Collect the REQ bundle for ``ip`` rooted at ``ip_dir`` (read-only)."""
    ip_dir = Path(ip_dir)
    req = ip_dir / "req"
    signoff = ip_dir / "signoff"
    verify = ip_dir / "verify"
    req_md = next(iter(sorted(req.glob("*_requirements.md"))), None)
    return {
        "ip": ip,
        "requirements_md": _read_text(req_md) if req_md else "",
        "requirements_md_path": (
            str(req_md.relative_to(ip_dir)) if req_md else ""
        ),
        "ssot_validation": _read_json(req / "ssot_validation.json"),
        "approval": _read_json(req / "approval_manifest.json"),
        "contract": _read_json(verify / "ip_contract.json"),
        "contract_check": _read_json(signoff / "contract_check.json"),
        "evidence": _read_json(signoff / "evidence_contract_coverage.json"),
        "signoff": _read_json(signoff / "ip_signoff.json"),
    }


# ---------------------------------------------------------------------------
# html helpers
# ---------------------------------------------------------------------------
def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


_OK = {"pass", "approved", "locked", "ok", "true", "passed"}
_BAD = {"fail", "failed", "blocked", "error", "false", "rejected"}


def _badge(status: Any) -> str:
    text = "" if status is None else str(status)
    key = text.lower()
    cls = "ok" if key in _OK else ("bad" if key in _BAD else "warn")
    return f'<span class="badge {cls}">{_esc(text or "n/a")}</span>'


def _md_to_html(text: str) -> str:
    if not text:
        return "<p class='muted'>(no requirements document)</p>"
    if _markdown is None:
        return f"<pre class='raw'>{_esc(text)}</pre>"
    try:
        return _markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "toc", "sane_lists"],
        )
    except Exception:
        return f"<pre class='raw'>{_esc(text)}</pre>"


# ---------------------------------------------------------------------------
# section renderers
# ---------------------------------------------------------------------------
def _sec_approval(b: dict[str, Any]) -> str:
    a = b.get("approval") or {}
    checks = a.get("checks") or {}
    crows = "".join(
        f"<tr><td class='mono sm'>{_esc(k)}</td>"
        f"<td>{_badge('pass' if v else 'fail')}</td></tr>"
        for k, v in checks.items()
    )
    if not a:
        return (
            "<section id='approval'><h2><span class='kicker'>LOCK</span> "
            "Approval &amp; Locked Truth</h2>"
            "<p class='muted'>(no approval manifest)</p></section>"
        )
    return f"""
    <section id="approval">
      <h2><span class="kicker">LOCK</span> Approval &amp; Locked Truth</h2>
      <div class="grid3">
        <div class="kv"><span>status</span>{_badge(a.get('status'))}</div>
        <div class="kv"><span>mode</span><b>{_esc(a.get('approval_mode'))}</b></div>
        <div class="kv"><span>scope</span><b>{_esc(a.get('locked_truth_scope'))}</b></div>
        <div class="kv"><span>approved_by</span><b class="sm">{_esc(a.get('approved_by'))}</b></div>
        <div class="kv"><span>approved_at</span><b class="sm">{_esc(a.get('approved_at_utc'))}</b></div>
        <div class="kv"><span>artifact</span><b class="sm">{_esc(a.get('artifact'))}</b></div>
      </div>
      <table>
        <thead><tr><th>approval check</th><th>status</th></tr></thead>
        <tbody>{crows}</tbody>
      </table>
    </section>"""


def _sec_requirements(b: dict[str, Any]) -> str:
    val = b.get("ssot_validation") or {}
    meta = []
    if val:
        meta.append(_badge("pass" if val.get("ok") else "fail"))
        stdout = (((val.get("check_ssot_disk") or {}).get("stdout")) or "").strip()
        if stdout:
            tail = stdout.split("PASS:")[-1].strip() or stdout
            meta.append(f"<code class='chip'>{_esc(tail)}</code>")
    body = _md_to_html(b.get("requirements_md", ""))
    size = len(b.get("requirements_md", "") or "")
    return f"""
    <section id="req">
      <h2><span class="kicker">REQ</span> Requirements
        <span class="path">{_esc(b.get('requirements_md_path'))}</span></h2>
      <div class="metarow">{' '.join(meta)}</div>
      <details open class="doc">
        <summary>requirements document ({size:,} bytes)</summary>
        <div class="md">{body}</div>
      </details>
    </section>"""


def _sec_obligations(b: dict[str, Any], compact: bool = False) -> str:
    ev = b.get("evidence") or {}
    obls = ev.get("obligations") or []
    summ = ev.get("summary") or {}
    total = summ.get("total", len(obls))
    passed = summ.get(
        "passed", sum(1 for o in obls if o.get("status") == "pass")
    )
    failed = summ.get("failed", max(total - passed, 0))
    shown = obls[:12] if compact else obls
    rows = []
    for o in shown:
        rid = o.get("obligation_id", "")
        matched = (o.get("matched_rows") or [{}])[0]
        conds = o.get("condition_results") or {}
        cond_ok = sum(1 for v in conds.values() if v)
        rows.append(
            f"<tr><td class='mono'>{_esc(rid)}</td>"
            f"<td>{_badge(o.get('status'))}</td>"
            f"<td class='mono sm'>{_esc(matched.get('goal_id', ''))}</td>"
            f"<td class='mono sm'>{_esc(matched.get('scenario_id', ''))}</td>"
            f"<td class='num'>{cond_ok}/{len(conds)}</td></tr>"
        )
    more = ""
    if compact and len(obls) > 12:
        more = (
            f"<tr><td colspan='5' class='muted'>… {len(obls) - 12} "
            "more obligations</td></tr>"
        )
    table = (
        "<table><thead><tr><th>obligation_id</th><th>status</th><th>goal</th>"
        "<th>scenario</th><th>cond</th></tr></thead>"
        f"<tbody>{''.join(rows)}{more}</tbody></table>"
    )
    if not obls:
        table = "<p class='muted'>(no obligations recorded)</p>"
    return f"""
    <section id="obli">
      <h2><span class="kicker">OBLI</span> Obligations</h2>
      <div class="metarow">
        <span class="stat"><b>{passed}</b>/{total} pass</span>
        {_badge('fail') if failed else _badge('pass')}
        <span class="muted">each obligation links a contract requirement to simulated evidence</span>
      </div>
      {table}
    </section>"""


def _sec_contract(b: dict[str, Any], compact: bool = False) -> str:
    c = b.get("contract") or {}
    cc = b.get("contract_check") or {}
    caps = c.get("capabilities") or []
    ccsum = cc.get("summary") or {}
    rows = []
    for cap in caps:
        ev = cap.get("evidence") or []
        ev0 = ev[0] if ev else ""
        rows.append(
            f"<tr><td class='mono'>{_esc(cap.get('id'))}</td>"
            f"<td class='mono sm'>{_esc(', '.join(cap.get('sources') or []))}</td>"
            f"<td class='sm'>{_esc(ev0[:120])}{'…' if len(ev0) > 120 else ''}</td></tr>"
        )
    table = (
        "<table><thead><tr><th>capability</th><th>sources</th>"
        "<th>evidence</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )
    if not caps:
        table = "<p class='muted'>(no capability contract)</p>"
    extra = ""
    if not compact:
        src = c.get("source_artifacts")
        src0 = src[0] if isinstance(src, list) and src else ""
        extra = f"""
      <div class="grid3">
        <div class="kv"><span>required_evidence</span><b>{len(c.get('required_evidence') or [])}</b></div>
        <div class="kv"><span>required_monitors</span><b>{len(c.get('required_monitors') or [])}</b></div>
        <div class="kv"><span>required_mutations</span><b>{len(c.get('required_mutations') or [])}</b></div>
        <div class="kv"><span>interfaces</span><b>{len(c.get('interfaces') or [])}</b></div>
        <div class="kv"><span>reflection</span><b>{ccsum.get('reflection_passed', '?')}/{ccsum.get('reflection_total', '?')}</b></div>
        <div class="kv"><span>source</span><b class="sm">{_esc(src0)}</b></div>
      </div>"""
    return f"""
    <section id="contract">
      <h2><span class="kicker">CONTRACT</span> Capability Contract</h2>
      <div class="metarow">
        <span class="stat"><b>{len(caps)}</b> capabilities</span>
        {_badge(cc.get('status'))}
      </div>
      {table}
      {extra}
    </section>"""


def _sec_evidence(b: dict[str, Any], compact: bool = False) -> str:
    so = b.get("signoff") or {}
    gates = so.get("gates") or []
    gp = sum(1 for g in gates if g.get("status") == "pass")
    ev = b.get("evidence") or {}
    evs = ev.get("summary") or {}
    gate_rows = "".join(
        f"<tr><td class='mono'>{_esc(g.get('name'))}</td>"
        f"<td>{_badge(g.get('status'))}</td>"
        f"<td class='sm'>{_esc(g.get('summary', ''))}</td></tr>"
        for g in gates
    )
    gate_block = ""
    if not compact and gates:
        gate_block = f"""
      <h3>Sign-off gates</h3>
      <table>
        <thead><tr><th>gate</th><th>status</th><th>summary</th></tr></thead>
        <tbody>{gate_rows}</tbody>
      </table>"""
    return f"""
    <section id="evidence">
      <h2><span class="kicker">EVIDENCE</span> Evidence &amp; Sign-off</h2>
      <div class="metarow">
        <span class="stat"><b>{evs.get('passed', '?')}</b>/{evs.get('total', '?')} evidence obligations</span>
        <span class="stat"><b>{gp}</b>/{len(gates)} gates</span>
        {_badge(so.get('status'))}
      </div>
      {gate_block}
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
.wrap{max-width:980px;margin:0 auto;padding:0 28px 80px;}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);
border-bottom:1px solid var(--line);padding:18px 28px;margin:0 -28px 8px;}
.top .ttl{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.top h1{font-size:20px;margin:0;letter-spacing:.01em}
.wordmark{font-weight:800;letter-spacing:.16em;font-size:12px;color:var(--acc);
border:1px solid var(--acc);border-radius:4px;padding:2px 7px}
.sub{color:var(--mut);font-size:12px;margin-top:6px}
.scorecard{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
.score{flex:1;min-width:150px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:var(--panel)}
.score .lab{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.07em}
.score .val{font-size:18px;font-weight:700;margin-top:2px;display:flex;align-items:center;gap:8px}
nav.toc{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0 6px}
nav.toc a{font-size:12px;color:var(--mut);text-decoration:none;border:1px solid var(--line);
border-radius:999px;padding:3px 11px}
nav.toc a:hover{color:var(--acc);border-color:var(--acc)}
section{border-top:1px solid var(--line);padding:22px 0 6px;scroll-margin-top:90px}
h2{font-size:16px;margin:0 0 12px;display:flex;align-items:center;gap:10px}
h3{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em;margin:18px 0 8px}
.kicker{font-size:10px;font-weight:800;letter-spacing:.12em;color:#fff;background:var(--acc);
border-radius:4px;padding:2px 6px}
.path{font-size:11px;color:var(--mut);font-weight:400}
.metarow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px;font-size:12px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:2px 9px}
.stat b{font-size:14px}
.badge{font-size:11px;font-weight:700;border-radius:999px;padding:2px 9px;text-transform:uppercase;letter-spacing:.04em}
.badge.ok{color:var(--ok);background:var(--okbg)}
.badge.bad{color:var(--bad);background:var(--badbg)}
.badge.warn{color:var(--warn);background:var(--warnbg)}
.muted{color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin:6px 0}
th{text-align:left;color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;
letter-spacing:.05em;border-bottom:1px solid var(--line);padding:7px 8px}
td{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top}
tr:hover td{background:var(--panel)}
td.mono,.mono{font-size:11.5px}
td.sm,.sm{font-size:11.5px;color:#3a4658}
td.num,.num{text-align:right;font-variant-numeric:tabular-nums}
.chip{background:var(--panel);border:1px solid var(--line);border-radius:5px;padding:1px 7px;font-size:11px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}
.kv{border:1px solid var(--line);border-radius:7px;padding:8px 10px;background:var(--panel)}
.kv span{display:block;font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
.kv b{font-size:13px}
details.doc{border:1px solid var(--line);border-radius:8px;background:var(--panel);padding:0 14px}
details.doc>summary{cursor:pointer;padding:10px 0;font-size:12px;color:var(--mut);font-weight:600}
.md{background:#fff;border-radius:6px;padding:6px 16px 16px;max-height:560px;overflow:auto}
.md h1{font-size:18px}.md h2{font-size:15px;border:0;padding:0;display:block}
.md h3{color:var(--fg);text-transform:none;letter-spacing:0}
.md table{font-size:12px}.md code{background:var(--panel);padding:1px 5px;border-radius:4px;font-size:12px}
.md pre{background:#0f1622;color:#d6e2ff;padding:12px;border-radius:8px;overflow:auto;font-size:12px}
.raw{white-space:pre-wrap}
.variant{font-size:11px;color:var(--mut);float:right}
.empty{padding:40px 0;color:var(--mut);font-family:ui-monospace,monospace}
"""


def _score_cards(b: dict[str, Any], full: bool) -> str:
    ev = (b.get("evidence") or {}).get("summary") or {}
    so = b.get("signoff") or {}
    gates = so.get("gates") or []
    gp = sum(1 for g in gates if g.get("status") == "pass")
    caps = (b.get("contract") or {}).get("capabilities") or []
    val = b.get("ssot_validation") or {}
    cards = [
        ("Requirements", _badge("pass" if val.get("ok") else "fail")),
        ("Obligations", f"{ev.get('passed', '?')}/{ev.get('total', '?')}"),
        ("Contract", f"{len(caps)} caps"),
        ("Evidence", f"{gp}/{len(gates)} gates"),
    ]
    if full:
        a = b.get("approval") or {}
        cards.append(("Approval", _badge(a.get("status"))))
    return "".join(
        f"<div class='score'><div class='lab'>{_esc(label)}</div>"
        f"<div class='val'>{value}</div></div>"
        for label, value in cards
    )


def render_req_html(bundle: dict[str, Any], ip: str, variant: str = "full") -> str:
    """Render the REQ bundle to a standalone HTML document.

    ``variant``:
      - ``full``  : approval section first, every table expanded (default).
      - ``core4`` : lean req+obli+contract+evidence; lock as header badge only.
    """
    full = variant != "core4"
    a = bundle.get("approval") or {}
    if full:
        toc_items = [
            ("approval", "Lock"), ("req", "Requirements"),
            ("obli", "Obligations"), ("contract", "Contract"),
            ("evidence", "Evidence"),
        ]
        body = (
            _sec_approval(bundle) + _sec_requirements(bundle)
            + _sec_obligations(bundle) + _sec_contract(bundle)
            + _sec_evidence(bundle)
        )
    else:
        toc_items = [
            ("req", "Requirements"), ("obli", "Obligations"),
            ("contract", "Contract"), ("evidence", "Evidence"),
        ]
        body = (
            _sec_requirements(bundle) + _sec_obligations(bundle, compact=True)
            + _sec_contract(bundle, compact=True)
            + _sec_evidence(bundle, compact=True)
        )
    toc = "".join(
        f"<a href='#{i}'>{_esc(label)}</a>" for i, label in toc_items
    )
    lock_meta = (
        f"{_esc(a.get('approval_mode', ''))} · "
        f"{_esc(a.get('locked_truth_scope', ''))}"
    ) if a else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(ip)} · REQ</title><style>{_CSS}</style></head>
<body><div class="wrap">
<header class="top">
  <span class="variant">variant: <b>{_esc(variant)}</b></span>
  <div class="ttl"><span class="wordmark">REQ</span><h1>{_esc(ip)}</h1>
    {_badge(a.get('status') or 'n/a')}
    <span class="muted" style="font-size:12px">{lock_meta}</span></div>
  <div class="sub">Unified requirements · obligations · contract · evidence — one human-reviewable view.</div>
  <div class="scorecard">{_score_cards(bundle, full)}</div>
  <nav class="toc">{toc}</nav>
</header>
{body}
</div></body></html>"""


def req_html_for_ip(ip_dir: Path, ip: str, variant: str = "full") -> str:
    """Convenience: load the bundle and render it in one call."""
    return render_req_html(load_req_bundle(ip_dir, ip), ip, variant=variant)

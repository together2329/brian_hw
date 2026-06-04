"""Session Flow Dashboard — Task 3 read-model + backfill tests.

Covers ``core/session_flow_usage.py``:

  * Seeded COMPLETE session -> risk_level='ok', populated input/LLM/worker/IP/
    artifact counters, attribution_confidence='exact'.
  * Seeded STALE running workflow -> risk_level='critical' AND in needs_attention.
  * Seeded UNMATCHED LLM call -> surfaces in attribution_gaps (confidence
    'missing'); NEVER a fabricated session row; llm_calls.session_id untouched.
  * Backfill REPEAT-SAFE: counts identical after a 2nd run (no double-count).
  * RS-3: ip_flow totals == SUM of constituent session_flow_rollups rows.
  * DM-2: non-additive STATE is RECOMPUTED-from-latest across a re-rollup, while
    additive counters are NOT summed on repeat.
  * Runtime mode: build_session_flow_payload reads control rollups ONLY and does
    NOT open a per-session runtime DB file.
  * Privacy: no raw prompt text leaks into the payload.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
for _c in (_REPO, _REPO / "src"):
    p = str(_c)
    if p not in sys.path:
        sys.path.insert(0, p)

from core.atlas_db import AtlasDB  # noqa: E402
import core.session_flow_usage as sf  # noqa: E402


# ============================================================
# seeding helpers
# ============================================================


def _seed_complete_session(db: AtlasDB, *, owner: str = "alice") -> str:
    """A clean end-to-end session: input -> worker -> llm -> ip -> artifact,
    finished and marked completed."""
    u = db.create_user(owner, owner.title())
    s = db.create_session(u["id"], "complete", workflow="rtl-gen", ip="ipC")
    sid = s["id"]
    ip = db.upsert_ip_block(
        "ws1", f"ip-{owner}", created_by_user_id=u["id"], source_session_id=sid,
        source_type="workflow", source_confidence="exact",
    )
    db.record_session_input(
        sid, source="enqueue", source_ref_id="q1", user_id=u["id"],
        char_count=10, token_estimate=3, attribution_confidence="exact",
    )
    wr = db.start_worker_run(
        session_id=sid, user_id=u["id"], workflow="rtl-gen",
        worker_kind="workflow", status="running",
    )
    call = db.record_llm_call(
        session_id=sid, model="m", cost_usd=0.2, status="ok",
        tokens_input=5, tokens_output=7, worker_run_id=wr["id"],
        attribution_confidence="exact",
    )
    db.register_artifact_version(
        ip["id"], "ssot", workspace_id="ws1", version="v1",
        source_session_id=sid, source_worker_run_id=wr["id"],
        source_llm_call_id=call["id"], attribution_confidence="exact",
    )
    db.finish_worker_run(wr["id"], status="completed")
    conn = db._connect()
    conn.execute(
        "UPDATE sessions SET status='completed', completed_at=?, ip_id=? WHERE id=?",
        (time.time(), ip["id"], sid),
    )
    conn.execute(
        "UPDATE artifact_versions SET ip_id=? WHERE source_session_id=?",
        (ip["id"], sid),
    )
    conn.commit()
    return sid


def _seed_stale_running_session(db: AtlasDB, *, owner: str = "bob",
                                age_h: float = 30.0) -> str:
    """An active session whose every timestamp is older than 24h."""
    old = time.time() - age_h * 3600.0
    u = db.create_user(owner, owner.title())
    s = db.create_session(u["id"], "stale", workflow="rtl-gen", ip="ipS", ip_id="ipS")
    sid = s["id"]
    db.record_session_input(
        sid, source="enqueue", source_ref_id="q1", char_count=5,
        attribution_confidence="exact", created_at=old,
    )
    wr = db.start_worker_run(
        session_id=sid, workflow="rtl-gen", worker_kind="workflow",
        status="running", started_at=old,
    )
    conn = db._connect()
    conn.execute(
        "UPDATE sessions SET status='active', created_at=?, updated_at=?, "
        "last_flow_event_at=? WHERE id=?", (old, old, old, sid),
    )
    conn.execute("UPDATE worker_runs SET updated_at=?, created_at=? WHERE id=?",
                 (old, old, wr["id"]))
    conn.execute("UPDATE session_flow_events SET created_at=? WHERE session_id=?",
                 (old, sid))
    conn.commit()
    return sid


# ============================================================
# Section 1 — complete session classification
# ============================================================


def test_complete_session_is_ok_with_exact_confidence(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    sid = _seed_complete_session(db)
    sf.recompute_rollups(db)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["flow_state"] == "completed"
    assert row["risk_level"] == "ok"
    assert row["attribution_confidence"] == "exact"
    # Every dimension populated.
    assert row["input_count"] == 1
    assert row["llm_attempts"] == 1
    assert row["llm_success"] == 1
    assert row["worker_runs"] == 1
    assert row["artifact_count"] == 1
    assert abs(row["cost_usd"] - 0.2) < 1e-9
    assert row["tokens_input"] == 5 and row["tokens_output"] == 7


def test_complete_session_not_in_needs_attention(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    sid = _seed_complete_session(db)
    payload = sf.build_session_flow_payload(db, {})
    na_ids = {s["session_id"] for s in payload["needs_attention"]}
    assert sid not in na_ids
    # It still appears in the full sessions list.
    assert sid in {s["session_id"] for s in payload["sessions"]}


# ============================================================
# Section 2 — stale running -> critical + needs_attention
# ============================================================


def test_stale_running_session_is_critical_and_flagged(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    sid = _seed_stale_running_session(db, age_h=30.0)
    now = time.time()
    sf.recompute_rollups(db, now=now)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["flow_state"] == "stale"
    assert row["risk_level"] == "critical"
    assert row["stale_age_s"] >= 24 * 3600.0

    payload = sf.build_session_flow_payload(db, {})
    assert sid in {s["session_id"] for s in payload["needs_attention"]}


def test_needs_attention_excludes_ok_sessions(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    ok_sid = _seed_complete_session(db, owner="okuser")
    crit_sid = _seed_stale_running_session(db, owner="crituser")
    payload = sf.build_session_flow_payload(db, {})
    na = {s["session_id"]: s["risk_level"] for s in payload["needs_attention"]}
    assert crit_sid in na and na[crit_sid] == "critical"
    assert ok_sid not in na


# ============================================================
# Section 3 — unmatched LLM spend -> attribution_gaps, no fake row
# ============================================================


def test_unmatched_llm_call_is_attribution_gap_not_fake_session(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    _seed_complete_session(db)
    # A call whose session_id has no sessions row at all.
    db.record_llm_call(session_id="ghost-session-xyz", model="m",
                       cost_usd=2.5, status="ok")
    # And a null-session call.
    db.record_llm_call(session_id=None, model="m", cost_usd=0.1, status="ok")

    payload = sf.build_session_flow_payload(db, {})
    gap_sids = {g.get("session_id") for g in payload["attribution_gaps"]}
    assert "ghost-session-xyz" in gap_sids
    for g in payload["attribution_gaps"]:
        assert g["confidence"] == "missing"
        assert g["missing_reason"] == "no_source_session"
    # Never a fabricated session row.
    assert "ghost-session-xyz" not in {s["session_id"] for s in payload["sessions"]}


def test_unmatched_spend_does_not_overwrite_llm_session_id(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    db.record_llm_call(session_id="ghost-session-xyz", model="m",
                       cost_usd=2.5, status="ok")
    sf.recompute_rollups(db)
    # The raw llm_calls row keeps its original (unroutable) session_id.
    kept = db._fetchall(
        "SELECT session_id FROM llm_calls WHERE session_id = 'ghost-session-xyz'"
    )
    assert len(kept) == 1
    assert kept[0]["session_id"] == "ghost-session-xyz"


def test_high_cost_unmatched_surfaces_in_needs_attention_not_session_critical(tmp_path):
    """MAJOR-2(b): high-cost unmatched LLM spend is a FLEET-level gap.
    It must:
      - appear in attribution_gaps with confidence='missing'
      - appear in needs_attention as category='unmatched_cost' (NOT a session row)
      - be reflected in summary.unmatched_cost_usd
      - NOT mark any real session row as critical
    """
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("dave", "Dave")
    s = db.create_session(u["id"], "real-session", workflow="rtl-gen",
                          ip="ipD", ip_id="ipD")
    sid = s["id"]
    # High-cost spend under a completely unroutable (ghost) session id.
    db.record_llm_call(session_id="ghost-high-cost-xyz", model="m",
                       cost_usd=5.0, status="ok")

    payload = sf.build_session_flow_payload(db, {})

    # attribution_gaps carries the unmatched spend.
    gaps = payload["attribution_gaps"]
    assert any(g.get("cost_usd", 0) >= 1.0 and g["confidence"] == "missing"
               for g in gaps), "high-cost gap missing from attribution_gaps"
    assert payload["summary"]["unmatched_cost_usd"] >= 5.0

    # needs_attention has the fleet-level unmatched_cost entry.
    fleet_entries = [n for n in payload["needs_attention"]
                     if n.get("category") == "unmatched_cost"]
    assert fleet_entries, "unmatched_cost entry missing from needs_attention"
    assert fleet_entries[0]["cost_usd"] >= 5.0

    # The REAL session is NOT critical (its own counters are zero / no LLM).
    real_session_rows = [s for s in payload["sessions"] if s["session_id"] == sid]
    assert real_session_rows, "real session row missing"
    assert real_session_rows[0]["risk_level"] != "critical", (
        "real session incorrectly marked critical by unmatched fleet spend"
    )

    # ghost id is never a fabricated session row.
    assert "ghost-high-cost-xyz" not in {s["session_id"] for s in payload["sessions"]}


# ============================================================
# Section 4 — backfill repeat-safe (no double count)
# ============================================================


def test_backfill_repeat_safe(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    sid = _seed_complete_session(db)
    sf.backfill_session_flow(db)
    first = db.list_session_flow_rollups(session_id=sid)[0]
    sf.backfill_session_flow(db)
    second = db.list_session_flow_rollups(session_id=sid)[0]
    # Additive counters are identical (recompute-overwrite, not accumulate).
    for col in ("input_count", "llm_attempts", "worker_runs", "artifact_count",
                "tokens_input", "tokens_output"):
        assert first[col] == second[col], f"{col} doubled on 2nd backfill"
    assert abs(first["cost_usd"] - second["cost_usd"]) < 1e-9
    # Exactly one rollup row per session.
    cnt = db._fetchall("SELECT COUNT(*) AS c FROM session_flow_rollups")[0]["c"]
    assert cnt == 1


# ============================================================
# Section 5 — RS-3: ip_flow == SUM of session rollups
# ============================================================


def test_ip_flow_totals_equal_sum_of_session_rollups(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("carol", "Carol")
    ip = db.upsert_ip_block("ws1", "ipR", created_by_user_id=u["id"],
                            source_session_id="seed", source_type="workflow",
                            source_confidence="exact")
    ipid = ip["id"]
    for n in range(3):
        s = db.create_session(u["id"], f"s{n}", workflow="rtl-gen", ip="ipR", ip_id=ipid)
        sid = s["id"]
        db.record_session_input(sid, source="enqueue", source_ref_id=f"q{n}",
                                char_count=10, attribution_confidence="exact")
        wr = db.start_worker_run(session_id=sid, workflow="rtl-gen",
                                 worker_kind="workflow", status="completed")
        db.record_llm_call(session_id=sid, model="m", cost_usd=0.5, status="ok",
                           tokens_input=5, tokens_output=5)
        db.register_artifact_version(ipid, "ssot", workspace_id="ws1",
                                     version=f"v{n}", source_session_id=sid)
        db.finish_worker_run(wr["id"], status="completed")

    sf.recompute_rollups(db)
    sess = db.list_session_flow_rollups(ip_id=ipid)
    ipr = db.list_ip_flow_rollups(ip_id=ipid)[0]
    # RS-3: every additive IP total equals the SUM of its session rollups.
    assert ipr["sessions"] == len(sess)
    assert ipr["llm_attempts"] == sum(r["llm_attempts"] for r in sess)
    assert ipr["worker_runs"] == sum(r["worker_runs"] for r in sess)
    assert ipr["artifact_count"] == sum(r["artifact_count"] for r in sess)
    assert abs(ipr["cost_usd"] - sum(r["cost_usd"] for r in sess)) < 1e-9


def test_ip_flow_is_derived_after_session_rollups(tmp_path):
    """RS-3: IP rollup risk is the worst-case member, proving it is derived from
    the per-session rollups (not folded independently)."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("eve", "Eve")
    ip = db.upsert_ip_block("ws1", "ipMix")
    ipid = ip["id"]
    # one ok session
    ok = db.create_session(u["id"], "ok", workflow="rtl-gen", ip="ipMix", ip_id=ipid)
    db.record_session_input(ok["id"], source="enqueue", source_ref_id="q",
                            char_count=1, attribution_confidence="exact")
    db.start_worker_run(session_id=ok["id"], workflow="rtl-gen",
                        worker_kind="workflow", status="completed")
    db.register_artifact_version(ipid, "ssot", workspace_id="ws1", version="v1",
                                 source_session_id=ok["id"])
    db.record_llm_call(session_id=ok["id"], model="m", cost_usd=0.1, status="ok")
    # one critical (stale) session on the SAME ip
    old = time.time() - 30 * 3600.0
    crit = db.create_session(u["id"], "crit", workflow="rtl-gen", ip="ipMix", ip_id=ipid)
    db.start_worker_run(session_id=crit["id"], workflow="rtl-gen",
                        worker_kind="workflow", status="running", started_at=old)
    conn = db._connect()
    conn.execute("UPDATE sessions SET status='active', created_at=?, updated_at=?, "
                 "last_flow_event_at=? WHERE id=?", (old, old, old, crit["id"]))
    conn.execute("UPDATE worker_runs SET updated_at=?, created_at=? WHERE session_id=?",
                 (old, old, crit["id"]))
    conn.execute("UPDATE session_flow_events SET created_at=? WHERE session_id=?",
                 (old, crit["id"]))
    conn.commit()

    sf.recompute_rollups(db)
    ipr = db.list_ip_flow_rollups(ip_id=ipid)[0]
    assert ipr["sessions"] == 2
    assert ipr["risk_level"] == "critical"  # worst member wins (derived)
    assert ipr["problem_count"] >= 1


# ============================================================
# Section 6 — DM-2: state recomputed across a re-rollup (not summed)
# ============================================================


def test_dm2_state_recomputed_across_rerollup(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    sid = _seed_stale_running_session(db, age_h=30.0)
    sf.recompute_rollups(db)
    first = db.list_session_flow_rollups(session_id=sid)[0]
    assert first["risk_level"] == "critical"
    assert first["flow_state"] == "stale"

    # The session is now completed -> a fresh recompute must RECOMPUTE the state,
    # not keep the stale/critical STATE and not sum counters.
    conn = db._connect()
    conn.execute("UPDATE sessions SET status='completed', completed_at=?, "
                 "updated_at=?, last_flow_event_at=? WHERE id=?",
                 (time.time(), time.time(), time.time(), sid))
    conn.commit()
    sf.recompute_rollups(db)
    second = db.list_session_flow_rollups(session_id=sid)[0]
    assert second["flow_state"] == "completed"  # recomputed from latest
    assert second["risk_level"] == "ok"          # recomputed, not stuck critical
    # Additive counter was NOT summed across the two recomputes.
    assert second["input_count"] == first["input_count"]


def test_dm2_counters_not_summed_on_repeat(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    sid = _seed_complete_session(db)
    sf.recompute_rollups(db)
    a = db.list_session_flow_rollups(session_id=sid)[0]
    sf.recompute_rollups(db)
    sf.recompute_rollups(db)
    b = db.list_session_flow_rollups(session_id=sid)[0]
    assert a["llm_attempts"] == b["llm_attempts"] == 1
    assert a["worker_runs"] == b["worker_runs"] == 1
    assert abs(a["cost_usd"] - b["cost_usd"]) < 1e-9


# ============================================================
# Section 7 — payload shape + filters + limit clamp
# ============================================================


def test_payload_top_level_shape(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    _seed_complete_session(db)
    payload = sf.build_session_flow_payload(db, {})
    for key in ("generated_at", "runtime_mode", "summary", "lenses",
                "needs_attention", "funnel", "sessions", "ip_flow",
                "attribution_gaps", "limits"):
        assert key in payload, f"missing top-level key {key}"
    # Funnel covers the full stage chain.
    stages = [f["stage"] for f in payload["funnel"]]
    assert stages == ["created", "input", "worker", "llm", "artifact",
                      "verified", "completed"]


def test_payload_limit_is_clamped(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    _seed_complete_session(db)
    payload = sf.build_session_flow_payload(db, {"limit": 99999})
    assert payload["limits"]["limit"] == 500
    payload2 = sf.build_session_flow_payload(db, {"limit": 0})
    assert payload2["limits"]["limit"] == 1


def test_payload_risk_filter(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    _seed_complete_session(db, owner="okuser")
    crit_sid = _seed_stale_running_session(db, owner="crituser")
    payload = sf.build_session_flow_payload(db, {"risk": "critical"})
    sids = {s["session_id"] for s in payload["sessions"]}
    assert sids == {crit_sid}


# ============================================================
# Section 8 — runtime mode: rollups only, no fanout
# ============================================================


def test_runtime_mode_reads_rollups_no_source_recompute(tmp_path, monkeypatch):
    """In runtime mode the payload comes from control rollups; the source-table
    recompute is NOT triggered (so a normal read never fans out)."""
    db = AtlasDB(str(tmp_path / "control.db"))
    # Pre-seed control rollups as if the Task 7 fold had written them.
    db.upsert_session_flow_rollup("s-rt", fields={
        "user_id": "u1", "ip_id": "ip1", "ip": "ipR", "workflow": "rtl-gen",
        "input_count": 2, "llm_attempts": 3, "cost_usd": 0.9,
        "worker_runs": 1, "artifact_count": 1,
        "flow_state": "running", "risk_level": "warning",
        "attribution_confidence": "inferred", "attribution_gap_count": 1,
    })
    db.upsert_ip_flow_rollup("ip1", fields={
        "ip": "ipR", "sessions": 1, "llm_attempts": 3, "cost_usd": 0.9,
        "risk_level": "warning", "source_confidence": "inferred",
    })

    monkeypatch.setattr(sf, "_runtime_mode_active", lambda: True)
    # If the source recompute were called it would overwrite our seeded rollups;
    # fail loud if it is reached.
    monkeypatch.setattr(sf, "recompute_rollups",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("runtime read must not recompute")))

    payload = sf.build_session_flow_payload(db, {})
    assert payload["runtime_mode"] is True
    sids = {s["session_id"] for s in payload["sessions"]}
    assert "s-rt" in sids
    row = next(s for s in payload["sessions"] if s["session_id"] == "s-rt")
    assert row["llm_attempts"] == 3
    assert abs(row["cost_usd"] - 0.9) < 1e-9
    # The persisted gap counter surfaces as an attribution gap summary.
    assert payload["attribution_gaps"]
    assert payload["attribution_gaps"][0]["confidence"] == "missing"


def test_runtime_mode_does_not_open_runtime_db(tmp_path, monkeypatch):
    """Hard no-fanout: a normal runtime-mode read opens zero runtime sqlite files."""
    db = AtlasDB(str(tmp_path / "control.db"))
    db.upsert_session_flow_rollup("s-rt", fields={
        "user_id": "u1", "ip_id": "ip1", "input_count": 1, "risk_level": "ok",
        "flow_state": "running",
    })
    monkeypatch.setattr(sf, "_runtime_mode_active", lambda: True)

    opened_runtime: list[str] = []
    real_connect = sqlite3.connect

    def _spy_connect(path, *args, **kwargs):
        if isinstance(path, str) and "/runtime/" in path.replace("\\", "/"):
            opened_runtime.append(path)
        return real_connect(path, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", _spy_connect)
    payload = sf.build_session_flow_payload(db, {})
    assert payload["runtime_mode"] is True
    assert not opened_runtime, f"runtime file opened on read: {opened_runtime}"


# ============================================================
# Section 9 — privacy: no raw prompt text in payload
# ============================================================


_SECRET = "SUPER_SECRET_PROMPT_that_must_never_reach_the_admin_payload_xyz"


def test_no_raw_prompt_text_in_payload(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("frank", "Frank")
    s = db.create_session(u["id"], "priv", workflow="rtl-gen", ip="ipP", ip_id="ipP")
    sid = s["id"]
    # Inputs store only counts/hash (helper drops raw text by design); we also
    # drop a queue row carrying the secret to prove backfill never reads payload.
    db.record_session_input(sid, source="enqueue", source_ref_id="q1",
                            char_count=len(_SECRET), input_hash="h",
                            attribution_confidence="exact")
    conn = db._connect()
    conn.execute(
        "INSERT INTO session_queue (id, session_id, direction, msg_type, payload, created_at) "
        "VALUES ('q-secret', ?, 'in', 'prompt', ?, ?)",
        (sid, '{"text": "%s"}' % _SECRET, time.time()),
    )
    conn.commit()

    payload = sf.build_session_flow_payload(db, {})
    import json
    blob = json.dumps(payload, default=str)
    assert _SECRET not in blob


# ============================================================
# Section 10 — MAJOR-1: completed/abandoned sessions are never warning
# ============================================================


def test_completed_session_without_artifact_is_ok_not_warning(tmp_path):
    """MAJOR-1: a completed session with no artifact must be ok, not warning."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("grace", "Grace")
    s = db.create_session(u["id"], "done-no-art", workflow="rtl-gen",
                          ip="ipG", ip_id="ipG")
    sid = s["id"]
    # Has LLM spend but no artifact — would trigger warning for an active session.
    db.record_session_input(sid, source="enqueue", source_ref_id="q1",
                            char_count=5, attribution_confidence="exact")
    wr = db.start_worker_run(session_id=sid, workflow="rtl-gen",
                             worker_kind="workflow", status="completed")
    db.record_llm_call(session_id=sid, model="m", cost_usd=0.3, status="ok")
    db.finish_worker_run(wr["id"], status="completed")
    # Mark completed.
    conn = db._connect()
    conn.execute("UPDATE sessions SET status='completed', completed_at=? WHERE id=?",
                 (time.time(), sid))
    conn.commit()

    sf.recompute_rollups(db)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["flow_state"] == "completed"
    assert row["risk_level"] == "ok", (
        f"completed session without artifact wrongly classified {row['risk_level']}"
    )


def test_completed_session_without_ip_is_ok_not_warning(tmp_path):
    """MAJOR-1: a completed session with no IP/workflow must be ok, not warning."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("henry", "Henry")
    # No ip_id, no workflow — would trigger missing_ip_or_workflow for active.
    s = db.create_session(u["id"], "done-no-ip")
    sid = s["id"]
    db.record_session_input(sid, source="enqueue", source_ref_id="q1",
                            char_count=5, attribution_confidence="exact")
    conn = db._connect()
    conn.execute("UPDATE sessions SET status='completed', completed_at=? WHERE id=?",
                 (time.time(), sid))
    conn.commit()

    sf.recompute_rollups(db)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["risk_level"] == "ok", (
        f"completed session without IP wrongly classified {row['risk_level']}"
    )

    payload = sf.build_session_flow_payload(db, {})
    na_ids = {n.get("session_id") for n in payload["needs_attention"]
              if "session_id" in n}
    assert sid not in na_ids, "completed session (no IP) in needs_attention"


def test_abandoned_session_is_ok_not_warning(tmp_path):
    """MAJOR-1: an abandoned session must be ok, not warning."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("iris", "Iris")
    s = db.create_session(u["id"], "abandoned", workflow="rtl-gen", ip="ipI")
    sid = s["id"]
    conn = db._connect()
    conn.execute("UPDATE sessions SET status='abandoned', abandoned_at=? WHERE id=?",
                 (time.time(), sid))
    conn.commit()

    sf.recompute_rollups(db)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["flow_state"] == "abandoned"
    assert row["risk_level"] == "ok"


# ============================================================
# Section 11 — MAJOR-2(c): attribution_gap_count meaningful for real sessions
# ============================================================


def test_attribution_gap_count_nonzero_for_missing_confidence(tmp_path):
    """MAJOR-2(c): a session that has never been touched (missing confidence)
    gets attribution_gap_count > 0 so Task 7 runtime fold can surface it."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("jake", "Jake")
    # Empty session — no inputs, no workers, no LLM, no artifacts.
    s = db.create_session(u["id"], "empty-session")
    sid = s["id"]

    sf.recompute_rollups(db)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["attribution_confidence"] == "missing"
    assert row["attribution_gap_count"] > 0, (
        "missing-confidence session must have attribution_gap_count > 0"
    )


def test_attribution_gap_count_zero_for_exact_confidence(tmp_path):
    """MAJOR-2(c): a fully-instrumented session gets attribution_gap_count == 0."""
    db = AtlasDB(str(tmp_path / "full.db"))
    sid = _seed_complete_session(db, owner="kate")
    sf.recompute_rollups(db)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["attribution_confidence"] == "exact"
    assert row["attribution_gap_count"] == 0


# ============================================================
# Section 12 — MINOR-2: risk_reason field distinct from missing_reason
# ============================================================


def test_risk_reason_field_present_in_session_row(tmp_path):
    """MINOR-2: every session row in the payload has a risk_reason field."""
    db = AtlasDB(str(tmp_path / "full.db"))
    _seed_complete_session(db)
    payload = sf.build_session_flow_payload(db, {})
    for row in payload["sessions"]:
        assert "risk_reason" in row, f"risk_reason missing from session row {row.get('session_id')}"


def test_risk_reason_differs_from_missing_reason_for_queue_backlog(tmp_path):
    """MINOR-2: a queue-backlog session must have risk_reason='queue_backlog_no_worker',
    not masked by missing_reason='no_source_session'."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("leo", "Leo")
    s = db.create_session(u["id"], "queued", workflow="rtl-gen",
                          ip="ipL", ip_id="ipL")
    sid = s["id"]
    db.record_session_input(sid, source="enqueue", source_ref_id="q1",
                            char_count=5, attribution_confidence="exact")
    # Enqueue a pending inbound message (queue_in > 0) but no active worker.
    conn = db._connect()
    conn.execute(
        "INSERT INTO session_queue (id, session_id, direction, msg_type, "
        "payload, created_at) VALUES ('qmsg1', ?, 'in', 'prompt', '{}', ?)",
        (sid, time.time()),
    )
    conn.commit()

    sf.recompute_rollups(db)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["risk_level"] == "critical"

    payload = sf.build_session_flow_payload(db, {})
    srow = next(x for x in payload["sessions"] if x["session_id"] == sid)
    assert srow["risk_reason"] == "queue_backlog_no_worker"
    # missing_reason is empty (attribution is exact via session_inputs).
    assert not srow.get("missing_reason"), (
        f"missing_reason should be empty, got {srow.get('missing_reason')!r}"
    )


# ============================================================
# Section 13 — MINOR-3: LLM success + errors are mutually exclusive
# ============================================================


def test_llm_success_errors_mutually_exclusive(tmp_path):
    """MINOR-3: success + errors <= attempts; a row with status='ok' AND
    error_type set must NOT count in both buckets."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("mia", "Mia")
    s = db.create_session(u["id"], "llm-counts", workflow="rtl-gen", ip="ipM")
    sid = s["id"]
    # success call (status ok, no error_type).
    conn = db._connect()
    import uuid, time as t
    now = t.time()
    # 1 clean success
    conn.execute(
        "INSERT INTO llm_calls (id, session_id, model, status, cost_usd, "
        "tokens_input, tokens_output, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (uuid.uuid4().hex, sid, "m", "ok", 0.1, 5, 5, now),
    )
    # 1 clean error
    conn.execute(
        "INSERT INTO llm_calls (id, session_id, model, status, cost_usd, "
        "tokens_input, tokens_output, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (uuid.uuid4().hex, sid, "m", "error", 0.0, 0, 0, now),
    )
    # 1 ambiguous row: status='ok' but error_type set — must count as SUCCESS only
    conn.execute(
        "INSERT INTO llm_calls (id, session_id, model, status, error_type, "
        "cost_usd, tokens_input, tokens_output, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (uuid.uuid4().hex, sid, "m", "ok", "timeout_recovered", 0.05, 2, 2, now),
    )
    conn.commit()

    sf.recompute_rollups(db)
    row = db.list_session_flow_rollups(session_id=sid)[0]
    assert row["llm_attempts"] == 3
    assert row["llm_success"] == 2   # the two status='ok' rows
    assert row["llm_errors"] == 1    # only the status='error' row
    assert row["llm_success"] + row["llm_errors"] <= row["llm_attempts"], (
        "success + errors exceeded attempts (double-count)"
    )


# ============================================================
# Section 14 — MINOR-1 (strengthened): runtime no-fanout with router guard
# ============================================================


def test_runtime_mode_no_fanout_with_router_guard(tmp_path, monkeypatch):
    """MINOR-1: strengthen the no-fanout test with a router guard that raises
    if the runtime DB is opened, AND assert the returned rows come from the
    seeded control rollups (not empty defaults)."""
    from core.atlas_db_router import AtlasDBRouter

    db = AtlasDB(str(tmp_path / "control.db"))
    db.upsert_session_flow_rollup("s-guarded", fields={
        "user_id": "u1", "ip_id": "ip1", "ip": "ipG", "workflow": "rtl-gen",
        "input_count": 7, "llm_attempts": 4, "cost_usd": 1.5,
        "worker_runs": 2, "artifact_count": 3,
        "flow_state": "running", "risk_level": "warning",
        "attribution_confidence": "inferred", "attribution_gap_count": 1,
    })

    monkeypatch.setattr(sf, "_runtime_mode_active", lambda: True)
    monkeypatch.setattr(sf, "recompute_rollups",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("runtime read must not call recompute_rollups")))

    # Guard the router's runtime_db accessor to raise if reached.
    real_runtime_db = AtlasDBRouter.runtime_db

    def _no_runtime_open(self, *a, **k):
        raise AssertionError("runtime_db opened via router during no-fanout read")

    monkeypatch.setattr(AtlasDBRouter, "runtime_db", _no_runtime_open)

    try:
        payload = sf.build_session_flow_payload(db, {})
    finally:
        monkeypatch.setattr(AtlasDBRouter, "runtime_db", real_runtime_db)

    assert payload["runtime_mode"] is True
    sids = {s["session_id"] for s in payload["sessions"]}
    assert "s-guarded" in sids, "seeded rollup row not returned in runtime mode"
    row = next(s for s in payload["sessions"] if s["session_id"] == "s-guarded")
    # Values must come from the seeded rollup, not zero defaults.
    assert row["llm_attempts"] == 4
    assert row["input_count"] == 7
    assert abs(row["cost_usd"] - 1.5) < 1e-9


# ============================================================
# Section 15 — NIT: FLOW_STATES is load-bearing (recompute returns valid state)
# ============================================================


def test_recompute_flow_state_returns_valid_flow_state(tmp_path):
    """NIT: every state recompute_flow_state can return is in FLOW_STATES."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("nina", "Nina")

    scenarios = [
        # (session kwargs, fact overrides, description)
        ({}, {}, "bare created"),
        ({"workflow": "rtl-gen", "ip": "ipN"}, {"input_count": 1}, "input_received"),
        ({"workflow": "rtl-gen"}, {"worker_runs": 1, "worker_started": True,
                                    "worker_active": True}, "running"),
        ({"workflow": "rtl-gen"}, {"has_artifact": True, "artifact_count": 1}, "artifact_produced"),
        ({"workflow": "rtl-gen"}, {"verification_seen": True}, "verification_seen"),
    ]
    base_fact = sf._collect_empty_fact()
    for kwargs, fact_overrides, desc in scenarios:
        s = db.create_session(u["id"], desc, **kwargs)
        f = {**base_fact, **fact_overrides}
        state = sf.recompute_flow_state(
            s,
            has_input=f["input_count"] > 0,
            worker_started=f["worker_started"],
            worker_active=f["worker_active"],
            worker_failed=f["worker_failed"],
            workflow_blocked=f["workflow_blocked"],
            has_artifact=f["has_artifact"],
            verification_seen=f["verification_seen"],
            stale_age_s=0.0,
        )
        assert state in sf.FLOW_STATES, (
            f"scenario '{desc}': recompute_flow_state returned {state!r} "
            f"which is not in FLOW_STATES"
        )


# ============================================================
# Section 16 — C2: next_action is a single-source per-session directive
# ============================================================


def test_next_action_empty_for_ok_nonempty_for_critical(tmp_path):
    """C2: ok sessions get an empty next_action; critical sessions get a
    bounded, non-empty directive. Derived in session_flow_usage (one source)."""
    db = AtlasDB(str(tmp_path / "full.db"))
    ok_sid = _seed_complete_session(db, owner="okuser")
    crit_sid = _seed_stale_running_session(db, owner="crituser", age_h=30.0)

    payload = sf.build_session_flow_payload(db, {})
    rows = {s["session_id"]: s for s in payload["sessions"]}

    assert "next_action" in rows[ok_sid]
    assert rows[ok_sid]["risk_level"] == "ok"
    assert rows[ok_sid]["next_action"] == ""

    assert "next_action" in rows[crit_sid]
    assert rows[crit_sid]["risk_level"] == "critical"
    assert rows[crit_sid]["next_action"], "critical session must have a next_action"


def test_next_action_helper_maps_reasons(tmp_path):
    """C2: the derivation lives in session_flow_usage and keys on
    risk_level + flow_state + risk_reason."""
    assert sf._derive_next_action("ok", "completed", "completed") == ""
    assert sf._derive_next_action("critical", "blocked", "workflow_blocked") == "resolve block"
    assert sf._derive_next_action("critical", "stale", "stale_gt_24h") == "inspect or close"
    assert sf._derive_next_action(
        "critical", "running", "queue_backlog_no_worker") == "assign/restart worker"
    assert sf._derive_next_action(
        "warning", "input_received", "no_worker_after_input") == "assign/restart worker"
    assert sf._derive_next_action(
        "warning", "running", "no_artifact_after_llm") == "inspect failed/empty run"
    # Unmapped reason falls back by flow_state (still non-empty for non-ok).
    assert sf._derive_next_action("warning", "failed", "something_new") == "inspect failed/empty run"
    assert sf._derive_next_action("warning", "created", "something_new") == "review session"

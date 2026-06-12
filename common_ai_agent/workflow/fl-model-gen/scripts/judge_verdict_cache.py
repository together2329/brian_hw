#!/usr/bin/env python3
"""Content-keyed verdict cache for the FL/CL semantic LLM judges.

The FL/CL semantic gates (``validate_fl_semantics`` / ``validate_cl_semantics``)
run an LLM judge per locked behavioral contract on *every* validation pass — even
when the judged inputs are byte-for-byte unchanged. Live cnt8 profiling
(``scripts/orch_profile.py``) showed the FL judge alone burning 420 LLM calls /
3.8h / $75 in a 12h window, with same-input verdicts flipping nondeterministically
(PASS 13:10 vs FAIL 13:11) and the CL stage redundantly re-judging FL content.

This module turns determinism into a structural property: a per-CONTRACT cache
keyed by a sha256 over the canonical-JSON of every input that determines the
verdict (the contract entry, the SSOT-derived content the judge actually sees,
the judge model name and a bumpable ``JUDGE_PROMPT_VERSION``). Identical content
reuses the stored verdict and makes NO LLM call; a one-line transaction edit only
re-judges the contracts whose judged content changed.

Closes ``OBL_SEMANTIC_JUDGE_CACHED_DETERMINISTIC`` (campaign finding 29).

Behaviour contract:
  * Cache key = sha256(canonical-JSON(contract, judged_content, model, prompt_ver)).
  * Cache file = ``<ip_dir>/model/.judge_cache/<domain>-<contract-slug>-<key12>.json``
    storing ``{key, contract_id, verdict, model, created_at}``.
  * On hit: reuse the stored verdict, mark it ``cache_hit=True`` (observability for
    orch_profile), make NO LLM call.
  * On miss: run ``judge_call()``, persist the returned verdict, return it unmarked.
  * ``ATLAS_JUDGE_CACHE=0`` disables the cache (always judge); default enabled.
  * Corrupt / unreadable cache files are treated as misses and never crash.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# Bump this marker whenever the judge SYSTEM/USER prompt structure changes so that
# stored verdicts produced by an older prompt are invalidated.
JUDGE_PROMPT_VERSION = "1"

_SLUG_RE = re.compile(r"[^0-9A-Za-z._-]+")


def cache_enabled() -> bool:
    """Cache is on by default; ``ATLAS_JUDGE_CACHE=0`` (or false/off/no) disables it."""
    return os.getenv("ATLAS_JUDGE_CACHE", "1").strip().lower() not in {"0", "false", "off", "no", ""}


def _canonical(obj: Any) -> str:
    """Deterministic JSON dump used for the cache key (stable across runs)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), default=str)


def compute_key(
    *,
    contract: dict[str, Any],
    judged_content: dict[str, Any],
    model: str,
    prompt_version: str = JUDGE_PROMPT_VERSION,
) -> str:
    """sha256 over every input that determines the per-contract verdict."""
    payload = {
        "prompt_version": prompt_version,
        "model": model,
        "contract": contract,
        "judged_content": judged_content,
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _slug(contract_id: str) -> str:
    slug = _SLUG_RE.sub("-", str(contract_id)).strip("-")
    return (slug or "contract")[:60]


def _cache_dir(ip_dir: Path) -> Path:
    return Path(ip_dir) / "model" / ".judge_cache"


def _cache_path(ip_dir: Path, domain: str, contract_id: str, key: str) -> Path:
    return _cache_dir(ip_dir) / f"{domain}-{_slug(contract_id)}-{key[:12]}.json"


def load_cached_verdict(
    ip_dir: Path,
    domain: str,
    contract_id: str,
    key: str,
) -> dict[str, Any] | None:
    """Return the stored verdict dict on a content hit, else ``None``.

    Corrupt / unreadable / mismatched-key files are treated as misses (never raise).
    """
    path = _cache_path(ip_dir, domain, contract_id, key)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(record, dict):
        return None
    if record.get("key") != key:
        return None
    verdict = record.get("verdict")
    return verdict if isinstance(verdict, dict) else None


def store_verdict(
    ip_dir: Path,
    domain: str,
    contract_id: str,
    key: str,
    verdict: dict[str, Any],
    model: str,
) -> None:
    """Persist a verdict. Best-effort: write failures never break validation."""
    path = _cache_path(ip_dir, domain, contract_id, key)
    record = {
        "key": key,
        "contract_id": contract_id,
        "verdict": verdict,
        "model": model,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}-{int(time.time()*1000)}")
        tmp.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        return


def judge_with_cache(
    *,
    ip_dir: Path,
    domain: str,
    contract_id: str,
    contract: dict[str, Any],
    judged_content: dict[str, Any],
    model: str,
    judge_call: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Return a per-contract verdict dict, reusing a cached one on a content hit.

    ``judge_call`` is the zero-arg closure that performs the real LLM judge and
    returns the verdict dict for this contract. It is invoked only on a miss (or
    when caching is disabled). On a hit the stored verdict is returned with
    ``cache_hit=True`` and NO LLM call is made. On a miss the freshly judged
    verdict is stored and returned (without a ``cache_hit`` marker).
    """
    if not cache_enabled():
        return judge_call()

    key = compute_key(contract=contract, judged_content=judged_content, model=model)
    cached = load_cached_verdict(ip_dir, domain, contract_id, key)
    if cached is not None:
        hit = dict(cached)
        hit["cache_hit"] = True
        return hit

    verdict = judge_call()
    if isinstance(verdict, dict):
        store_verdict(ip_dir, domain, contract_id, key, verdict, model)
    return verdict

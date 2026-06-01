from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Final

BOOST_TAGS: Final = ("module", "sub", "submodule", "hierarchy", "instance")
CHUNK_SIZE: Final = 64
FACT_CATEGORIES: Final = (
    ("modules", "module"),
    ("ports", "port"),
    ("parameters", "parameter"),
    ("registers", "register"),
    ("memories", "memory"),
    ("clocks", "clock"),
    ("resets", "reset"),
    ("fsm_candidates", "fsm"),
    ("datapaths", "datapath"),
)
IDENT_RE: Final = re.compile(r"\b[A-Za-z_]\w*\b")


def write_top_level_search_artifacts(wiki: Path, block_id: str, facts: dict[str, Any]) -> None:
    indexed_facts = _load_fact_sidecar(wiki, block_id, facts)
    boost_top_level_search_terms(wiki, block_id, _fact_terms(indexed_facts, "modules"))
    for key, label in FACT_CATEGORIES:
        _write_fact_page(wiki, block_id, key, label, _fact_terms(indexed_facts, key))


def boost_top_level_search_terms(wiki: Path, block_id: str, modules: list[str]) -> None:
    if len(modules) < 2:
        return
    page = wiki / f"{block_id}.md"
    if not page.is_file():
        return
    lines = page.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            break
        if line.startswith("tags: [") and line.endswith("]"):
            current = [item.strip() for item in line.removeprefix("tags: [").removesuffix("]").split(",")]
            tags = [item for item in current if item]
            tags.extend(tag for tag in BOOST_TAGS if tag not in tags)
            lines[index] = f"tags: [{', '.join(tags)}]"
            page.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return


def _load_fact_sidecar(wiki: Path, block_id: str, fallback: dict[str, Any]) -> dict[str, Any]:
    path = wiki / "_rtl_facts" / f"{block_id}.json"
    if not path.is_file():
        return fallback
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return fallback
    parsed: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(key, str):
            parsed[key] = _json_value(value)
    return parsed


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return str(value)


def _fact_terms(facts: dict[str, Any], key: str) -> list[str]:
    value = facts.get(key)
    if not isinstance(value, list):
        return []
    terms: list[str] = []
    for item in value:
        terms.extend(_item_terms(item))
    return list(dict.fromkeys(terms))


def _item_terms(item: Any) -> list[str]:
    if isinstance(item, str):
        return _identifier_terms(item)
    if not isinstance(item, dict):
        return []
    terms: list[str] = []
    for key in ("name", "state", "text", "left", "right"):
        value = item.get(key)
        if isinstance(value, str):
            terms.extend(_identifier_terms(value))
    states = item.get("states")
    if isinstance(states, list):
        for state in states:
            if isinstance(state, str):
                terms.extend(_identifier_terms(state))
    return terms


def _identifier_terms(text: str) -> list[str]:
    return [match.group(0) for match in IDENT_RE.finditer(text)]


def _write_fact_page(wiki: Path, block_id: str, key: str, label: str, terms: list[str]) -> None:
    page_id = f"facts-{block_id}-{key}"
    page = wiki / f"{page_id}.md"
    _remove_term_pages(wiki, block_id, key)
    if not terms:
        if page.is_file():
            page.unlink()
        return
    tags = ["rtl-db", "andes", "facts", block_id, key, label]
    preview = ", ".join(f"`{term}`" for term in terms[:96])
    if len(terms) > 96:
        preview += f", ... ({len(terms) - 96} more)"
    body = "\n".join(
        [
            "---",
            f"id: {page_id}",
            f"title: {block_id} {label} facts",
            "type: reference",
            f"tags: [{', '.join(dict.fromkeys(tags))}]",
            f"related: [{block_id}, rtl-inventory, coverage]",
            "---",
            f"# {block_id} {label} facts",
            "",
            f"Searchable RTL fact names generated from `_rtl_facts/{block_id}.json` for exact `{label}` queries.",
            "",
            f"Terms: {preview}",
            "",
            f"See [[{block_id}]], [[rtl-inventory]], and [[coverage]].",
            "",
        ]
    )
    page.write_text(body, encoding="utf-8")
    _write_chunk_pages(wiki, block_id, key, label, terms, page_id)


def _remove_term_pages(wiki: Path, block_id: str, key: str) -> None:
    for page in wiki.glob(f"fact-{block_id}-{key}-*.md"):
        page.unlink()


def _write_chunk_pages(
    wiki: Path,
    block_id: str,
    key: str,
    label: str,
    terms: list[str],
    category_page_id: str,
) -> None:
    for start in range(0, len(terms), CHUNK_SIZE):
        chunk = terms[start : start + CHUNK_SIZE]
        chunk_num = (start // CHUNK_SIZE) + 1
        page_id = f"fact-{block_id}-{key}-{chunk_num:03d}"
        tags = ["rtl-db", "andes", "fact", block_id, key, label, *chunk]
        preview = ", ".join(f"`{term}`" for term in chunk)
        body = "\n".join(
            [
                "---",
                f"id: {page_id}",
                f"title: {block_id} {label} facts {start + 1}-{start + len(chunk)}",
                "type: reference",
                f"tags: [{', '.join(dict.fromkeys(tags))}]",
                f"related: [{block_id}, {category_page_id}, rtl-inventory, coverage]",
                "---",
                f"# {block_id} {label} facts {start + 1}-{start + len(chunk)}",
                "",
                f"Exact `{label}` terms generated from `_rtl_facts/{block_id}.json`: {preview}.",
                "",
                f"See [[{block_id}]], [[{category_page_id}]], [[rtl-inventory]], and [[coverage]].",
                "",
            ]
        )
        (wiki / f"{page_id}.md").write_text(body, encoding="utf-8")

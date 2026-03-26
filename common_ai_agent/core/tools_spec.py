"""
Generic spec navigation tool — 모든 스펙(pcie/ucie/nvme 등)을 하나의 tool로 탐색.
spec_navigate(spec, node_id) 형태로 호출.
"""
import json
import os
import sys

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))

def _dbg(msg: str):
    """DEBUG_MODE=true일 때 stderr에 출력."""
    _src_dir = os.path.join(_CORE_DIR, "..", "src")
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)
    try:
        import config
        if config.DEBUG_MODE:
            print(f"[DEBUG spec] {msg}", flush=True)
    except Exception:
        pass
_SKILLS_DIR = os.path.join(_CORE_DIR, "..", "skills")
_PROJECT_ROOT = os.path.abspath(os.path.join(_CORE_DIR, ".."))  # = common_ai_agent/ (CWD)


def _find_node(node, target_id):
    if node.get("id") == target_id:
        return node
    for child in node.get("children", []):
        found = _find_node(child, target_id)
        if found:
            return found
    return None


def spec_navigate(spec: str, node_id: str = "root") -> str:
    """
    스펙 계층 탐색기. spec='pcie'/'ucie'/'nvme' 등.
    node_id='root'로 챕터 목록 시작, 반환된 id로 드릴다운.
    leaf node는 {"leaf":true, "content":"...", "path":"..."} 반환.
    IMPORTANT: leaf response already includes full file content in "content" field.
    Do NOT call read_file/read_lines separately — content is already included.
    path는 프로젝트 루트 기준 상대 경로.
    """
    index_path = os.path.join(
        _SKILLS_DIR, f"{spec}-expert", "data", f"{spec}_index.json"
    )
    try:
        with open(index_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        available = _list_available_specs()
        return json.dumps({
            "error": f"Spec '{spec}' not found. Available: {available}",
            "hint": "Run convert_to_md.py --spec <name> --pdf <path> to add a new spec."
        })

    if node_id == "root":
        children = data.get("children", [])
        # 노이즈 제거: 앞에 0이 없는 숫자(1~99) + Appendix만 유지
        def _is_valid_chapter(cid: str) -> bool:
            if cid in {"Appendix", "appendix"}:
                return True
            # "1", "12" 형식
            if cid.isdigit() and not cid.startswith("0"):
                return 1 <= int(cid) <= 99
            # "1.0", "12.0" 형식 (UCIe 스타일)
            parts = cid.split(".")
            if len(parts) == 2 and parts[0].isdigit() and parts[1] == "0":
                return not parts[0].startswith("0") and 1 <= int(parts[0]) <= 99
            return False
        children = [
            c for c in children
            if _is_valid_chapter(c["id"]) and c.get("children")  # 자식 없는 N.0 노이즈 제거
        ]
    else:
        wrapper = {"id": "root", "children": data.get("children", [])}
        node = _find_node(wrapper, node_id)
        if not node:
            return json.dumps({"error": f"Node {node_id!r} not found in spec '{spec}'"})
        children = node.get("children", [])
        if not children:
            data_dir = os.path.abspath(os.path.join(_SKILLS_DIR, f"{spec}-expert", "data"))
            raw_path = node["path"]
            # 절대 경로이면 그대로, 상대 경로이면 data_dir 기준으로 절대화
            if os.path.isabs(raw_path):
                abs_path = raw_path
            else:
                abs_path = os.path.normpath(os.path.join(data_dir, raw_path))
            rel_path = os.path.relpath(abs_path, _PROJECT_ROOT)
            result = {
                "leaf": True,
                "id": node["id"],
                "title": node["title"],
                "path": rel_path,
                "description": node.get("description", "")
            }
            # Auto-read file content
            try:
                with open(abs_path, encoding="utf-8") as f:
                    lines = f.readlines()
                content = "".join(lines[:300])
                if len(lines) > 300:
                    content += f"\n[...truncated, {len(lines)} lines total]"
                result["content"] = content
            except Exception:
                pass
            return json.dumps(result, ensure_ascii=False)

    data_dir = os.path.abspath(os.path.join(_SKILLS_DIR, f"{spec}-expert", "data"))

    def _child_entry(c):
        entry = {
            "id": c["id"],
            "title": c["title"],
            "description": c.get("description", ""),
            "has_children": bool(c.get("children")),
        }
        if not c.get("children") and "path" in c:
            raw = c["path"]
            abs_p = raw if os.path.isabs(raw) else os.path.normpath(os.path.join(data_dir, raw))
            entry["path"] = os.path.relpath(abs_p, _PROJECT_ROOT)
        return entry

    return json.dumps({
        "spec": spec,
        "node_id": node_id,
        "children": [_child_entry(c) for c in children]
    }, ensure_ascii=False, indent=2)


def _tokenize_query(query: str) -> list:
    """쿼리를 단순 토큰화. LLM 없이 원래 단어만 사용."""
    import re as _re
    return [_re.sub(r'[^\w]', '', w).lower() for w in query.split()
            if len(_re.sub(r'[^\w]', '', w)) > 2]


def _collect_all_nodes(node, nodes=None):
    """index JSON 전체 노드를 재귀적으로 수집."""
    if nodes is None:
        nodes = []
    nid = node.get("id", "")
    if nid and nid != "root":
        nodes.append({
            "id": nid,
            "title": node.get("title", ""),
            "description": node.get("description", ""),
            "path": node.get("path", ""),
        })
    for child in node.get("children", []):
        _collect_all_nodes(child, nodes)
    return nodes


def _score_node(node, keywords, phrases):
    """
    구문(phrase) 매칭 우선, 개별 키워드 보조.
    - phrase match in title: +10 (exact phrase, highest priority)
    - phrase match in description: +5
    - keyword match in title: +2
    - keyword match in description: +1
    """
    title = node["title"].lower()
    description = node.get("description", "").lower()
    score = 0

    # Phrase matching (highest weight)
    for phrase in phrases:
        if phrase in title:
            score += 10
        if phrase in description:
            score += 5

    # Individual keyword matching (fallback)
    for kw in keywords:
        if kw in title:
            score += 2
        if kw in description:
            score += 1
    return score


def _extract_phrases(query: str, keywords: list) -> list:
    """쿼리와 키워드에서 2단어 이상 구문 추출."""
    phrases = []
    q = query.lower().strip()
    # Query itself as a phrase (if meaningful length)
    if len(q) > 5:
        phrases.append(q)
    # Multi-word keywords are already phrases
    for kw in keywords:
        if ' ' in kw and len(kw) > 5:
            phrases.append(kw.lower())
    # Deduplicate, longest first (more specific phrases score first)
    seen = set()
    result = []
    for p in sorted(phrases, key=len, reverse=True):
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _llm_select_sections(query: str, candidates: list) -> list:
    """
    LLM이 후보 섹션 목록에서 쿼리에 가장 관련된 node_id를 선택.
    candidates: [{"id": ..., "title": ..., "description": ...}, ...]
    반환: 선택된 node_id 리스트 (최대 2개)
    """
    try:
        import sys, re as _re
        _src_dir = os.path.join(_CORE_DIR, "..", "src")
        if _src_dir not in sys.path:
            sys.path.insert(0, _src_dir)
        from llm_client import call_llm_raw

        candidate_lines = "\n".join(
            f"{i+1}. [{c['id']}] {c['title']}"
            + (f" — {c['description'][:80]}" if c.get('description') else "")
            for i, c in enumerate(candidates)
        )
        prompt = (
            f"You are selecting the most relevant sections from a technical spec index.\n"
            f"Query: {query}\n\n"
            f"Candidates:\n{candidate_lines}\n\n"
            f"Return ONLY the node_id(s) of the 1-2 most relevant sections as a JSON array. "
            f"Example: [\"4.3.2\"] or [\"7.7.9\", \"7.7.9.2\"]. No explanation."
        )
        result = call_llm_raw(
            prompt="",
            messages=[{"role": "user", "content": prompt}],
        )
        if result:
            match = _re.search(r'\[.*?\]', result, _re.DOTALL)
            if match:
                ids = json.loads(match.group())
                return [str(i) for i in ids if isinstance(i, str)]
    except Exception:
        pass
    # Fallback: return top 2 candidates
    return [c["id"] for c in candidates[:2]]


def spec_search(spec: str, query: str) -> str:
    """
    키워드로 후보 섹션 추출 → LLM이 제목 보고 최적 섹션 선택 → 내용 반환.
    spec='pcie'/'ucie'/'nvme', query=사용자 질문.
    매칭 없으면 spec-navigator sub-agent로 fallback.
    """
    available = _list_available_specs()
    if spec not in available:
        return f"[spec_search error] spec '{spec}' not found. Available: {available}"

    index_path = os.path.join(_SKILLS_DIR, f"{spec}-expert", "data", f"{spec}_index.json")
    try:
        with open(index_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return f"[spec_search error] Failed to load index: {e}"

    _dbg(f"spec={spec!r}  query={query!r}")

    # 1. Tokenize query (no LLM — LLM title selection handles the intelligence)
    keywords = _tokenize_query(query)
    _dbg(f"keywords: {keywords}")

    # 2. Extract phrases
    phrases = _extract_phrases(query, keywords)
    _dbg(f"phrases:  {phrases}")

    # 3. Score all nodes → top 10 candidates (title only)
    all_nodes = _collect_all_nodes({"id": "root", "children": data.get("children", [])})
    scored = [(n, _score_node(n, keywords, phrases)) for n in all_nodes if n.get("path")]
    scored = [(n, s) for n, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    _dbg(f"total scored nodes: {len(scored)}")
    for n, s in scored[:10]:
        _dbg(f"  score={s:3d}  [{n['id']}] {n['title']}")

    if not scored:
        _dbg("no candidates → fallback to subagent")
        return _spec_search_subagent(spec, query)

    candidates = [n for n, _ in scored[:10]]

    # 4. LLM selects best matching sections from candidate titles
    selected_ids = _llm_select_sections(query, candidates)
    _dbg(f"LLM selected: {selected_ids}")

    # 5. Read selected files
    data_dir = os.path.abspath(os.path.join(_SKILLS_DIR, f"{spec}-expert", "data"))
    id_to_node = {n["id"]: n for n in candidates}
    results = []
    for nid in selected_ids:
        node = id_to_node.get(nid)
        if not node:
            _dbg(f"  [{nid}] not found in candidates — skip")
            continue
        raw_path = node["path"]
        abs_path = raw_path if os.path.isabs(raw_path) else os.path.normpath(os.path.join(data_dir, raw_path))
        try:
            with open(abs_path, encoding="utf-8") as f:
                lines = f.readlines()
            content = "".join(lines[:300])
            if len(lines) > 300:
                content += f"\n[...truncated, {len(lines)} lines total]"
            rel_path = os.path.relpath(abs_path, _PROJECT_ROOT)
            _dbg(f"  reading [{nid}] {node['title']} — {len(lines)} lines from {rel_path}")
            results.append(f"## {node['title']} (node_id: {nid})\n\n{content}\n\n---\nSource: {rel_path}")
        except Exception as e:
            results.append(f"## {node['title']}\n[Error reading: {e}]")

    if not results:
        _dbg("no results after file read → fallback to subagent")
        return _spec_search_subagent(spec, query)

    return "\n\n".join(results)


def _spec_search_subagent(spec: str, query: str) -> str:
    """Fallback: spec-navigator sub-agent 실행."""
    try:
        import sys
        _src_dir = os.path.join(_CORE_DIR, "..", "src")
        if _src_dir not in sys.path:
            sys.path.insert(0, _src_dir)
        from core.agent_runner import run_agent_session
    except ImportError as e:
        return f"[spec_search error] agent_runner import failed: {e}"

    model = os.getenv("SPEC_NAVIGATOR_MODEL", "")
    result = run_agent_session(
        agent_name="spec-navigator",
        prompt=f"Spec: {spec}\nQuery: {query}",
        model_override=model or None,
        max_iterations=12,
        allowed_tools=["spec_navigate", "read_lines", "grep_file"],
        verbose=False,
    )
    return result.output or "[spec_search] No content extracted."


def spec_ask(spec: str, query: str) -> str:
    """
    Spec Q&A tool — spec-navigator sub-agent를 실행하여 질문에 답변.
    spec='pcie'/'ucie'/'nvme', query=자연어 질문.
    내부에서 spec_search + spec_navigate를 사용하여 관련 섹션을 찾고 답변을 반환.
    primary agent는 이 도구 하나만 사용하면 됨.
    """
    available = _list_available_specs()
    if spec not in available:
        return f"[spec_ask] spec '{spec}' not found. Available: {available}"

    _dbg(f"spec_ask: spec={spec!r} query={query!r}")

    try:
        import sys
        _src_dir = os.path.join(_CORE_DIR, "..", "src")
        if _src_dir not in sys.path:
            sys.path.insert(0, _src_dir)
        from core.agent_runner import run_agent_session
    except ImportError as e:
        return f"[spec_ask error] agent_runner import failed: {e}"

    model = os.getenv("SPEC_NAVIGATOR_MODEL", "")
    result = run_agent_session(
        agent_name="spec-navigator",
        prompt=f"Spec: {spec}\nQuery: {query}",
        model_override=model or None,
        max_iterations=12,
        allowed_tools={"spec_search", "spec_navigate", "read_lines", "grep_file"},
        verbose=False,
    )
    return result.output or "[spec_ask] No answer extracted."


def _list_available_specs() -> list:
    """skills/ 폴더에서 *-expert/data/*_index.json 존재하는 스펙 목록 반환"""
    specs = []
    skills_dir = os.path.abspath(_SKILLS_DIR)
    if not os.path.isdir(skills_dir):
        return specs
    for entry in os.listdir(skills_dir):
        if entry.endswith("-expert"):
            spec = entry[:-len("-expert")]
            idx = os.path.join(skills_dir, entry, "data", f"{spec}_index.json")
            if os.path.isfile(idx):
                specs.append(spec)
    return sorted(specs)

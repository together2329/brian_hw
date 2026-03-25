"""
Generic spec navigation tool — 모든 스펙(pcie/ucie/nvme 등)을 하나의 tool로 탐색.
spec_navigate(spec, node_id) 형태로 호출.
"""
import json
import os

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILLS_DIR = os.path.join(_CORE_DIR, "..", "skills")
_PROJECT_ROOT = os.path.abspath(os.path.join(_CORE_DIR, "..", ".."))


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
    leaf node는 {"leaf":true,"path":"..."} 반환 → read_lines로 내용 읽기.
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
            return json.dumps({
                "leaf": True,
                "id": node["id"],
                "title": node["title"],
                "path": rel_path,
                "description": node.get("description", "")
            }, ensure_ascii=False)

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

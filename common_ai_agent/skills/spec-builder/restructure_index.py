"""
{spec}_index.json 재구성: x.1, x.2, ... 섹션을 x.0 챕터 노드의 자식으로 이동

Before: root → [4.0, 4.1, 4.2, 4.3, 5.0, 5.1, ...]
After:  root → [4.0 → [4.1, 4.2, 4.3], 5.0 → [5.1, ...], ...]

Usage:
  python3 restructure_index.py --spec ucie
  python3 restructure_index.py --spec pcie
  python3 restructure_index.py --spec nvme
"""
import os
import json
import argparse


def get_chapter_prefix(node_id):
    """'4.0' -> '4', '4.1' -> '4', '12.3' -> '12', 기타 -> None"""
    parts = node_id.split(".")
    if parts[0].isdigit():
        return parts[0]
    return None


def is_chapter_root(node_id):
    """챕터 헤더인지: '4', '4.0' -> True / '4.1', '4.3.2' -> False"""
    parts = node_id.split(".")
    if not parts[0].isdigit():
        return False
    if len(parts) == 1:
        return True
    if len(parts) == 2 and parts[1] == "0":
        return True
    return False


def restructure_children(children):
    """flat 자식 목록을 챕터 계층으로 재구성"""
    chapters = {}   # prefix -> chapter node
    result = []     # 최종 순서 유지용

    for node in children:
        node_id = node.get("id", "")
        prefix = get_chapter_prefix(node_id)

        if prefix and is_chapter_root(node_id):
            # 챕터 헤더 노드
            chapters[prefix] = node
            result.append(node)
        elif prefix and prefix in chapters:
            # 이미 챕터 헤더가 나온 경우 → 그 챕터의 자식으로
            chapters[prefix]["children"].append(node)
        else:
            # 챕터에 속하지 않는 노드 (Figures, Appendix 등)
            result.append(node)

    return result


def count_nodes(children):
    total = len(children)
    for c in children:
        total += count_nodes(c.get("children", []))
    return total


def main():
    parser = argparse.ArgumentParser(description="spec index 챕터 계층 재구성")
    parser.add_argument("--spec", required=True, help="스펙 이름 (e.g. ucie, pcie, nvme)")
    parser.add_argument("--dry-run", action="store_true", help="변경 내용만 출력, 저장 안 함")
    args = parser.parse_args()

    spec = args.spec.lower()
    skill_dir = os.path.join(os.path.dirname(__file__), "..", f"{spec}-expert", "data")
    index_path = os.path.abspath(os.path.join(skill_dir, f"{spec}_index.json"))

    if not os.path.exists(index_path):
        print(f"[error] {index_path} not found")
        return

    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)

    before = len(data.get("children", []))
    print(f"[{spec}] 재구성 전 root children: {before}개")

    new_children = restructure_children(data.get("children", []))
    after = len(new_children)

    print(f"[{spec}] 재구성 후 root children: {after}개 (챕터 수)")

    # 챕터별 자식 수 출력
    for node in new_children:
        ch = node.get("children", [])
        if ch:
            print(f"  [{node['id']}] {node['title'][:50]} → 자식 {len(ch)}개")

    if args.dry_run:
        print("\n[dry-run] 저장 안 함")
        return

    data["children"] = new_children

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {index_path}")


if __name__ == "__main__":
    main()

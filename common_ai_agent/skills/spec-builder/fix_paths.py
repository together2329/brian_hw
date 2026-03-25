"""
{spec}_index.json의 절대 경로를 data_dir 기준 상대 경로로 변환.

Usage:
  python3 fix_paths.py --spec ucie
  python3 fix_paths.py --spec nvme
  python3 fix_paths.py --spec pcie
"""
import os
import json
import argparse


def fix_paths(node, data_dir):
    path = node.get("path")
    if path:
        # 절대 경로이면 data_dir 기준 상대 경로로 변환
        if os.path.isabs(path):
            node["path"] = os.path.relpath(path, data_dir)
        # Windows 백슬래시 → 슬래시 통일
        node["path"] = node["path"].replace("\\", "/")
    for child in node.get("children", []):
        fix_paths(child, data_dir)


def main():
    parser = argparse.ArgumentParser(description="index.json 절대 경로 → 상대 경로 변환")
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()

    spec = args.spec.lower()
    skill_dir = os.path.join(os.path.dirname(__file__), "..", f"{spec}-expert", "data")
    data_dir = os.path.abspath(skill_dir)
    index_path = os.path.join(data_dir, f"{spec}_index.json")

    if not os.path.exists(index_path):
        print(f"[error] {index_path} not found")
        return

    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)

    # 변환
    count = [0]
    def _fix(node):
        path = node.get("path")
        if path and os.path.isabs(path):
            node["path"] = os.path.relpath(path, data_dir).replace("\\", "/")
            count[0] += 1
        elif path:
            node["path"] = path.replace("\\", "/")
        for c in node.get("children", []):
            _fix(c)

    for c in data.get("children", []):
        _fix(c)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[{spec}] 절대 경로 {count[0]}개 → 상대 경로 변환 완료")
    print(f"저장: {index_path}")


if __name__ == "__main__":
    main()

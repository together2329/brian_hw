"""
{spec}_index.json에서 description이 비어있는 노드만 LLM으로 재생성.

Pass 1 (기본): leaf 노드 → 파일 내용 기반 description 생성
Pass 2 (--bottom-up): 부모 노드 → 자식 descriptions 요약으로 생성

Usage:
  python3 refill_descriptions.py --spec pcie
  python3 refill_descriptions.py --spec pcie --bottom-up
  python3 refill_descriptions.py --spec pcie --all   # pass1 + pass2
"""
import os
import json
import argparse


def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "../../.env")
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()

    def _env(key, default=None):
        return os.getenv(key) or env_vars.get(key) or default

    return {
        "base_url": _env("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        "api_key":  _env("LLM_API_KEY"),
        "model":    _env("DESCRIPTION_MODEL") or _env("LLM_MODEL_NAME", "openai/gpt-oss-120b"),
    }


def llm_call(client, model, prompt):
    """LLM 호출 공통 함수"""
    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.choices[0].message.content
        if not text and hasattr(resp.choices[0].message, "reasoning"):
            resp2 = client.chat.completions.create(
                model=model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt[:500] + "\nOne sentence only."}]
            )
            text = resp2.choices[0].message.content
        return text.strip() if text else ""
    except Exception as e:
        print(f"  [warn] LLM 실패: {e}")
        return ""


# ─────────────────────────────────────────
# Pass 1: leaf 노드 → 파일 내용 기반
# ─────────────────────────────────────────

def generate_from_file(client, model, path, title):
    """마크다운 파일 읽어서 description 생성"""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read(2000)
    except Exception as e:
        print(f"  [skip] 파일 읽기 실패 ({title}): {e}")
        return ""

    if len(content.strip()) < 50:  # 내용이 너무 적으면 스킵
        return ""

    return llm_call(client, model,
        f"Section: {title}\n\n{content[:1500]}\n\n"
        "Write a 1-2 sentence routing description listing key topics, "
        "technical terms, and what questions this section answers. "
        "Be specific and keyword-rich. No filler words."
    )


def maybe_save(data, index_path, stats):
    """save_interval마다 중간 저장"""
    interval = stats.get("save_interval", 50)
    stats["since_save"] = stats.get("since_save", 0) + 1
    if stats["since_save"] >= interval:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [save] {stats['filled']}개 저장 완료")
        stats["since_save"] = 0


def fill_pass1(node, client, model, data_dir, stats, data, index_path):
    """Pass 1: 파일 내용이 있는 빈 노드 채우기"""
    if not node.get("description") and node.get("path"):
        path = node["path"]
        abs_path = path if os.path.isabs(path) else os.path.join(data_dir, path)
        print(f"  [P1] {node['title'][:60]}")
        desc = generate_from_file(client, model, abs_path, node["title"])
        if desc:
            node["description"] = desc
            stats["filled"] += 1
            maybe_save(data, index_path, stats)
        else:
            stats["failed"] += 1

    for child in node.get("children", []):
        fill_pass1(child, client, model, data_dir, stats, data, index_path)


# ─────────────────────────────────────────
# Pass 2: 부모 노드 → 자식 descriptions 요약 (bottom-up)
# ─────────────────────────────────────────

def fill_pass2(node, client, model, stats, data, index_path):
    """Pass 2 (bottom-up): 자식 먼저 처리 후 부모 요약"""
    # 자식 먼저 재귀
    for child in node.get("children", []):
        fill_pass2(child, client, model, stats, data, index_path)

    # 자식이 있고 description이 비어있는 부모 노드만 처리
    if not node.get("children"):
        return
    if node.get("description"):
        return

    # 자식 descriptions 수집
    child_descs = [
        f"- {c['title']}: {c['description']}"
        for c in node["children"]
        if c.get("description")
    ]
    if not child_descs:
        return

    summary_input = "\n".join(child_descs[:20])  # 최대 20개
    print(f"  [P2] {node['title'][:60]}")
    desc = llm_call(client, model,
        f"Parent section: {node['title']}\n\n"
        f"Child sections:\n{summary_input}\n\n"
        "Write a 1-2 sentence routing description summarizing what topics "
        "this parent section covers. Be specific and keyword-rich."
    )
    if desc:
        node["description"] = desc
        stats["filled"] += 1
        maybe_save(data, index_path, stats)
    else:
        stats["failed"] += 1


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def count_empty(node):
    count = 1 if not node.get("description") and node.get("path") else 0
    return count + sum(count_empty(c) for c in node.get("children", []))


def main():
    parser = argparse.ArgumentParser(description="빈 description LLM으로 재생성")
    parser.add_argument("--spec", required=True, help="스펙 이름 (e.g. pcie, ucie, nvme)")
    parser.add_argument("--bottom-up", action="store_true", help="Pass 2: 부모 노드를 자식 요약으로 채우기")
    parser.add_argument("--all", action="store_true", help="Pass 1 + Pass 2 모두 실행")
    parser.add_argument("--dry-run", action="store_true", help="빈 항목 수만 출력")
    parser.add_argument("--save-interval", type=int, default=50, help="N개 채울 때마다 중간 저장 (기본: 50)")
    args = parser.parse_args()

    spec = args.spec.lower()
    skill_dir = os.path.join(os.path.dirname(__file__), "..", f"{spec}-expert", "data")
    index_path = os.path.join(skill_dir, f"{spec}_index.json")
    data_dir = os.path.abspath(skill_dir)

    if not os.path.exists(index_path):
        print(f"[error] {index_path} not found")
        return

    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)

    total_empty = sum(count_empty(c) for c in data.get("children", []))
    print(f"[{spec}] 빈 description: {total_empty}개")

    if args.dry_run or total_empty == 0:
        return

    cfg = load_env()
    from openai import OpenAI
    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    print(f"모델: {cfg['model']}\n")

    stats = {"filled": 0, "failed": 0, "skipped": 0, "save_interval": args.save_interval, "since_save": 0}

    run_p1 = not args.bottom_up or args.all
    run_p2 = args.bottom_up or args.all

    if run_p1:
        print("=== Pass 1: 파일 내용 기반 ===")
        for child in data.get("children", []):
            fill_pass1(child, client, cfg["model"], data_dir, stats, data, index_path)

    if run_p2:
        print("\n=== Pass 2: 부모 bottom-up 요약 ===")
        for child in data.get("children", []):
            fill_pass2(child, client, cfg["model"], stats, data, index_path)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n완료: filled={stats['filled']}, failed={stats['failed']}, skipped={stats['skipped']}")
    print(f"저장: {index_path}")


if __name__ == "__main__":
    main()

import os
import fitz
import re
import json
import argparse
from markitdown import MarkItDown


def clean_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name[:100]


def get_section_id(title):
    """타이틀에서 섹션 번호 추출
    'Chapter 2. ...' → '2', 'Section 2.1 ...' → '2.1', '3.2 TLP ...' → '3.2'
    """
    # "Chapter N." or "Section N.M" 패턴
    match = re.search(r'\b(\d+(?:\.\d+)*)\b', title)
    return match.group(1) if match else clean_filename(title)[:20]


def build_tree(toc):
    root = {'item': [0, 'Root', 0], 'children': []}
    stack = [root]

    for item in toc:
        level, title, page = item
        node = {'item': item, 'children': []}

        while len(stack) > 1 and len(stack) >= level:
            stack.pop()

        stack[-1]['children'].append(node)
        stack.append(node)

    return root


def generate_description(client, section_content: str, title: str, model: str = "openai/gpt-oss-120b") -> str:
    """LLM으로 섹션 내용 → 라우팅용 description 생성"""
    if not section_content.strip():
        return ""
    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    f"Section: {title}\n\n"
                    f"{section_content[:1500]}\n\n"
                    "Write a 1-2 sentence routing description listing key topics, "
                    "technical terms, and what questions this section answers. "
                    "Be specific and keyword-rich. No filler words."
                )
            }]
        )
        content = resp.choices[0].message.content
        if not content and hasattr(resp.choices[0].message, 'reasoning'):
            # reasoning 모델이 content 없이 reasoning만 반환한 경우 재시도
            resp2 = client.chat.completions.create(
                model=model,
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Section: {title}\n\n"
                        f"{section_content[:500]}\n\n"
                        "One sentence: what is this section about? Key terms only."
                    )
                }]
            )
            content = resp2.choices[0].message.content
        return content.strip() if content else ""
    except Exception as e:
        print(f"  [warn] description 생성 실패 ({title}): {e}")
        return ""


def process_node(doc, base_dir, node, next_sibling, total_pages, client, output_dir, model="openai/gpt-oss-120b"):
    level, title, start_page = node['item']
    safe_title = clean_filename(title)

    end_page_exclusive = total_pages
    if node['children']:
        end_page_exclusive = node['children'][0]['item'][2]
    elif next_sibling:
        end_page_exclusive = next_sibling['item'][2]

    pages_to_extract = list(range(start_page - 1, end_page_exclusive - 1)) if start_page <= end_page_exclusive else []

    content_text = ""
    md_content = f"# {title}\n\n"
    for p in pages_to_extract:
        if 0 <= p < total_pages:
            try:
                text = doc[p].get_text("text")
                md_content += text + "\n\n"
                content_text += text + " "
            except Exception as e:
                md_content += f"\n> Error extracting page {p}: {e}\n"

    description = ""
    if client and content_text.strip():
        print(f"    Generating description for: {title}")
        description = generate_description(client, content_text, title, model=model)

    if node['children']:
        node_dir = os.path.join(base_dir, safe_title) if level > 0 else base_dir
        os.makedirs(node_dir, exist_ok=True)

        index_path = os.path.join(node_dir, "index.md")
        index_content = md_content + "\n## Contents\n"
        for child in node['children']:
            child_safe = clean_filename(child['item'][1])
            if child['children']:
                index_content += f"- [{child['item'][1]}]({child_safe}/index.md)\n"
            else:
                index_content += f"- [{child['item'][1]}]({child_safe}.md)\n"

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)

        children_dicts = []
        for i, child in enumerate(node['children']):
            next_sib = node['children'][i + 1] if i + 1 < len(node['children']) else None
            child_dict = process_node(doc, node_dir, child, next_sib, total_pages, client, output_dir, model=model)
            if child_dict:
                children_dicts.append(child_dict)

        return {
            "id": get_section_id(title),
            "title": title,
            "level": level,
            "description": description,
            "path": os.path.relpath(os.path.abspath(index_path), os.path.abspath(output_dir)),
            "children": children_dicts
        }
    else:
        file_path = os.path.join(base_dir, f"{safe_title}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return {
            "id": get_section_id(title),
            "title": title,
            "level": level,
            "description": description,
            "path": os.path.relpath(os.path.abspath(file_path), os.path.abspath(output_dir)),
            "children": []
        }


def main():
    parser = argparse.ArgumentParser(description="Spec PDF → Markdown + {spec}_index.json")
    parser.add_argument("--spec", required=True, help="스펙 이름 (e.g. pcie, ucie, nvme)")
    parser.add_argument("--pdf", required=True, help="PDF 파일 경로")
    parser.add_argument("--output-dir", help="출력 디렉토리 (기본: common_ai_agent/skills/{spec}-expert/data)")
    parser.add_argument("--chapter", help="특정 챕터만 처리 (e.g. 'Transaction Layer')")
    parser.add_argument("--no-description", action="store_true", help="LLM description 생성 스킵")
    parser.add_argument("--skip-fullmd", action="store_true", help="markitdown full.md 생성 스킵")
    args = parser.parse_args()

    spec = args.spec.lower()
    pdf_path = args.pdf
    output_dir = args.output_dir or f"common_ai_agent/skills/{spec}-expert/data"
    markdown_dir = os.path.join(output_dir, "markdown")

    print(f"Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    total_pages = len(doc)
    print(f"Found TOC with {len(toc)} entries, {total_pages} pages.")

    os.makedirs(markdown_dir, exist_ok=True)

    # markitdown으로 full.md 생성 (선택적)
    full_md_path = os.path.join(output_dir, "full.md")
    if not args.skip_fullmd and not os.path.exists(full_md_path):
        print("Converting full PDF with markitdown (this may take a few minutes)...")
        try:
            md = MarkItDown()
            result = md.convert(pdf_path)
            with open(full_md_path, 'w', encoding='utf-8') as f:
                f.write(result.text_content)
            print(f"Saved full.md ({len(result.text_content):,} chars)")
        except Exception as e:
            print(f"[warn] markitdown failed: {e}")
    elif os.path.exists(full_md_path):
        print(f"full.md already exists, skipping.")
    else:
        print("Skipping full.md generation (--skip-fullmd)")

    # .env 로드 (환경변수 우선, 없으면 common_ai_agent/.env 파일)
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

    llm_base_url = _env("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    llm_model    = _env("DESCRIPTION_MODEL") or _env("LLM_MODEL_NAME", "openai/gpt-oss-120b")
    llm_api_key  = _env("LLM_API_KEY")

    # LLM client for descriptions
    client = None
    if not args.no_description:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=llm_base_url, api_key=llm_api_key)
            print(f"LLM client initialized (base_url={llm_base_url}, model={llm_model}).")
        except Exception as e:
            print(f"[warn] LLM client init failed: {e}, skipping descriptions.")

    clean_toc = [item for item in toc if item[2] > 0 and item[2] <= total_pages]

    # 챕터 필터
    if args.chapter:
        chapter_lower = args.chapter.lower()
        chapter_toc = []
        in_chapter = False
        chapter_level = None
        for item in clean_toc:
            level, title, page = item
            if chapter_lower in title.lower() and not in_chapter:
                in_chapter = True
                chapter_level = level
                chapter_toc.append(item)
            elif in_chapter:
                if level <= chapter_level:
                    break  # 같은/상위 레벨 챕터 만나면 종료
                chapter_toc.append(item)

        if chapter_toc:
            print(f"Chapter filter '{args.chapter}': {len(chapter_toc)} TOC entries")
            clean_toc = chapter_toc
        else:
            print(f"[warn] Chapter '{args.chapter}' not found, processing all")

    tree = build_tree(clean_toc)

    print("Building markdown tree...")
    children_dicts = []
    root_children = tree['children']
    for i, child in enumerate(root_children):
        next_sib = root_children[i + 1] if i + 1 < len(root_children) else None
        print(f"  Processing: {child['item'][1]}")
        child_dict = process_node(doc, markdown_dir, child, next_sib, total_pages, client, output_dir, model=llm_model)
        if child_dict:
            children_dicts.append(child_dict)

    # {spec}_index.json 저장
    index_data = {
        "spec": spec,
        "source_pdf": pdf_path,
        "total_pages": total_pages,
        "chapter_filter": args.chapter,
        "children": children_dicts
    }

    index_path = os.path.join(output_dir, f"{spec}_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {spec}_index.json saved ({len(children_dicts)} top-level entries)")
    print(f"Output: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()

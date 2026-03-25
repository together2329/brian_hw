---
name: spec-builder
description: >
  새로운 스펙 PDF를 expert skill로 변환. PDF → markdown 계층 분해 → {spec}_index.json 생성 →
  spec_navigate 도구로 즉시 탐색 가능. UCIe/NVMe/기타 스펙 추가 시 호출.
  Trigger on: 새 스펙 추가, PDF를 스킬로, create expert, add spec, new spec skill.
priority: 70
activation:
  keywords: ["add spec", "new spec", "create expert", "스펙 추가", "pdf를 스킬로",
             "expert 만들기", "spec skill", "스펙 스킬", "build skill", "convert pdf"]
  auto_detect: true
requires_tools: [run_command, read_lines]
related_skills: [pcie-expert, ucie-expert, nvme-expert]
---

# Spec Builder — PDF → Expert Skill

새 스펙을 `spec_navigate` 로 탐색 가능한 expert skill로 변환한다.

---

## 필요 정보 확인

사용자에게 확인:
1. **spec 이름** (소문자, 예: `ucie`, `nvme`, `cxl`)
2. **PDF 경로** (예: `UCIe/UCIe_Specification_rev3p0.pdf`)
3. **description 생성 여부** (LLM 호출, 느리지만 탐색 품질 향상)

---

## 변환 실행

```bash
# 기본 (description 없이, 빠름)
python3 common_ai_agent/skills/spec-builder/convert_to_md.py \
  --spec <name> \
  --pdf <pdf_path> \
  --no-description \
  --skip-fullmd

# description 포함 (LLM_API_KEY 필요, 권장)
python3 common_ai_agent/skills/spec-builder/convert_to_md.py \
  --spec <name> \
  --pdf <pdf_path> \
  --skip-fullmd
```

출력: `common_ai_agent/skills/<name>-expert/data/`
- `<name>_index.json` — 계층 인덱스
- `markdown/` — 섹션별 markdown 파일

---

## SKILL.md 생성

변환 완료 후 `common_ai_agent/skills/<name>-expert/SKILL.md` 생성:

```markdown
---
name: <name>-expert
description: >
  <SPEC 전체 이름> 스펙 관련 질문 시 호출.
  spec_navigate 도구로 TOC를 계층적으로 탐색하여 정확한 스펙 섹션을 찾는다.
priority: 85
activation:
  keywords: [<name>, <주요 기술 키워드들>]
  auto_detect: true
requires_tools: [spec_navigate, read_lines]
---

# ⚠️ MANDATORY: 반드시 spec_navigate로 시작할 것

첫 번째 도구는 반드시 `spec_navigate("<name>", "root")`여야 한다.

## 탐색 절차

1. spec_navigate("<name>", "root")     → 챕터 목록, 관련 챕터 id 선택
2. spec_navigate("<name>", "<id>")     → 섹션 목록
3. spec_navigate("<name>", "<id.sub>") → 서브섹션 또는 leaf
4. leaf → read_lines(path="<leaf.path>", start_line=1, end_line=200)

## 규칙
- leaf 도달 전 파일 읽기 금지
- grep_file은 spec_navigate 완료 후에만 사용
```

---

## 완료 확인

```bash
python3 -c "
from common_ai_agent.core.spec_navigate_tool import spec_navigate
print(spec_navigate('<name>', 'root'))
"
```

정상이면 챕터 목록 JSON 출력.

---

## 현재 등록된 스펙

| 스펙 | 폴더 | 인덱스 |
|------|------|--------|
| pcie | skills/pcie-expert/data/ | pcie_index.json |
| ucie | skills/ucie-expert/data/ | ucie_index.json |
| nvme | skills/nvme-expert/data/ | nvme_index.json |

새 스펙은 변환 후 자동으로 `spec_navigate`에서 사용 가능 — tools.py 수정 불필요.

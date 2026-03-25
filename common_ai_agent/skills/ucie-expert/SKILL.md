---
name: ucie-expert
description: >
  UCIe (Universal Chiplet Interconnect Express) 스펙 관련 모든 질문 시 호출.
  Die-to-Die interface, Physical Layer, Die Adapter, Protocol Layer, FDI/RDI interface,
  Streaming Protocol, CXL over UCIe, PCIe over UCIe, Link Training, Parameter Exchange,
  Advanced/Standard Package 등.
  spec_navigate 도구로 TOC를 계층적으로 탐색하여 정확한 스펙 섹션을 찾는다.
priority: 85
activation:
  keywords: [ucie, "universal chiplet", "die-to-die", "d2d", chiplet, "die adapter",
             fdi, rdi, "protocol layer", "die interface", "link training",
             "parameter exchange", "streaming protocol", "advanced package",
             "standard package", "chiplet interconnect"]
  file_patterns: ["*.md", "*.pdf", "*.txt"]
  auto_detect: true
requires_tools: [spec_navigate, read_lines]
related_skills: [pcie-expert]
---

# ⚠️ MANDATORY: 반드시 spec_navigate로 시작할 것

**grep_file, find_files, read_file, list_dir 사용 금지** — 첫 번째 도구는 반드시 `spec_navigate("ucie", "root")`여야 한다.

---

## 탐색 절차 (4단계)

```
1. spec_navigate("ucie", "root")       → 챕터 목록, 관련 챕터 id 선택
2. spec_navigate("ucie", "<id>")       → 섹션 목록, 관련 섹션 id 선택
3. spec_navigate("ucie", "<id.sub>")   → 서브섹션 목록 또는 leaf
4. leaf → read_lines(path="<정확히 반환된 path>", start_line=1, end_line=200)
```

**leaf 판단 (둘 중 하나):**
- 응답에 `"leaf": true` → 해당 응답의 `path` 필드를 그대로 read_lines에 전달
- children 목록에서 `"has_children": false` → 해당 child의 `path` 필드를 그대로 read_lines에 전달 (**추가 spec_navigate 호출 불필요**)

---

## 규칙

- leaf 도달 전 파일 읽기 금지
- 한 레벨에서 최대 2개 분기 선택 가능
- **find_files, run_command 사용 금지** — 탐색은 spec_navigate만 사용
- **grep_file은 파일 경로에만 가능** — 디렉토리 경로에 사용 시 에러 발생, 반드시 leaf path에만 사용
- **같은 파일 반복 읽기 금지** — read_lines는 파일당 1회, end_line=500으로 충분히 읽을 것

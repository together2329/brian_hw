---
name: nvme-expert
description: >
  NVMe (Non-Volatile Memory Express) Base Spec 2.3 관련 모든 질문 시 호출.
  Command Set, Admin Commands, I/O Commands, Queue Model, Submission/Completion Queue,
  Namespace, Controller, PCIe Transport, Fabrics, NVM Command Set, Zoned Namespace,
  Key Value, Power Management, Error Handling, Sanitize, Security (TCG), Telemetry 등.
  spec_navigate 도구로 TOC를 계층적으로 탐색하여 정확한 스펙 섹션을 찾는다.
priority: 85
activation:
  keywords: [nvme, "nvm express", "non-volatile memory", "submission queue", "completion queue",
             "admin command", "i/o command", namespace, controller, "queue model",
             "nvme over fabrics", "zoned namespace", "key value", sanitize, telemetry,
             "nvm command set", "identify command", doorbell, "prp", "sgl",
             "스토리지", "큐", "컨트롤러", "네임스페이스"]
  file_patterns: ["*.md", "*.pdf", "*.txt"]
  auto_detect: true
requires_tools: [spec_navigate, read_lines]
related_skills: [pcie-expert, protocol-spec-expert]
---

# ⚠️ MANDATORY: 반드시 spec_navigate로 시작할 것

**grep_file, find_files, read_file, list_dir 사용 금지** — 첫 번째 도구는 반드시 `spec_navigate("nvme", "root")`여야 한다.

---

## 탐색 절차 (4단계)

```
1. spec_navigate("nvme", "root")       → 챕터 목록, 관련 챕터 id 선택
2. spec_navigate("nvme", "<id>")       → 섹션 목록, 관련 섹션 id 선택
3. spec_navigate("nvme", "<id.sub>")   → 서브섹션 목록 또는 leaf
4. leaf → read_lines(path="<정확히 반환된 path>", start_line=1, end_line=200)
```

**leaf 판단:** 반환값에 `"leaf": true` 이면 반드시 해당 `path` 값을 그대로 사용.
- ⚠️ path를 절대 추측하거나 수정하지 말 것
- ⚠️ spec_navigate가 반환한 path 문자열을 **복사해서 그대로** read_lines에 전달

예시:
```
spec_navigate 반환: {"leaf": true, "path": "common_ai_agent/skills/nvme-expert/data/markdown/4.3.../4.3.2.1_SGL_Example.md"}
→ read_lines(path="common_ai_agent/skills/nvme-expert/data/markdown/4.3.../4.3.2.1_SGL_Example.md", start_line=1, end_line=200)
```

---

## 규칙

- leaf 도달 전 파일 읽기 금지
- 한 레벨에서 최대 2개 분기 선택 가능
- **grep_file은 spec_navigate 완료 후, 특정 값/코드 추가 검색 시에만** 사용
- path를 직접 구성하거나 추측 금지 — spec_navigate 반환값만 사용

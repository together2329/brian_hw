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

**leaf 판단 (둘 중 하나):**
- 응답에 `"leaf": true` → 해당 응답의 `path` 필드를 그대로 read_lines에 전달
- children 목록에서 `"has_children": false` → 해당 child의 `path` 필드를 그대로 read_lines에 전달 (**추가 spec_navigate 호출 불필요**)

- ⚠️ path를 절대 추측하거나 수정하지 말 것 — spec_navigate 반환값만 사용

---

## 규칙

- leaf 도달 전 파일 읽기 금지
- 한 레벨에서 최대 2개 분기 선택 가능
- **grep_file, find_files, run_command 사용 금지** — spec_navigate + read_lines만 사용
- **같은 파일 반복 읽기 금지** — read_lines는 파일당 1회, end_line=500으로 충분히 읽을 것
- path를 직접 구성하거나 추측 금지 — spec_navigate 반환값만 사용

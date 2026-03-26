---
name: pcie-expert
description: >
  PCIe 7.0 스펙 관련 모든 질문 시 호출. TLP/DLLP 패킷 구조, LTSSM 상태머신, Flow Control,
  Lane Equalization, Power Management, AER, ACS, TDISP, IDE, ATS, IOV, Physical/Data Link/Transaction Layer,
  Flit Mode, Link Training, Virtual Channel, Root Complex, Endpoint 등.
  spec_navigate 도구로 TOC를 계층적으로 탐색하여 정확한 스펙 섹션을 찾는다.
  Trigger on: pcie, pci express, tlp, dllp, ltssm, tdisp, ide, ats, aer, acs, flit, equalization,
  power management, link training, physical layer, data link, transaction layer.
priority: 85
activation:
  keywords: [pcie, "pci express", tlp, dllp, ltssm, "state machine", "flow control",
             equalization, aer, acs, ide, tdisp, "root complex", endpoint, completion,
             "power management", "physical layer", "data link layer", "transaction layer",
             "address translation", ats, iov, "virtual channel", flit, "lane equalization",
             "link training", register, config, specification, spec,
             "상태머신", "프로토콜", "스펙", "레인", "링크"]
  file_patterns: ["*.md", "*.pdf", "*.txt", "*.rst"]
  auto_detect: true
requires_tools: [spec_search, spec_navigate, read_lines]
related_skills: [verilog-expert, protocol-spec-expert]
---

# ⚠️ MANDATORY: 반드시 spec_search로 시작할 것

**첫 번째 도구는 반드시 `spec_search("pcie", "<질문>")`이어야 한다.**
spec_search가 spec-navigator sub-agent를 실행하여 관련 스펙 내용을 추출해서 반환한다.
그 결과를 바탕으로 답변한다.

```
spec_search("pcie", "What is OHC in Flit Mode?")
→ sub-agent가 자동으로 spec 탐색 후 관련 섹션 내용 반환
→ 반환된 내용으로 답변 작성
```

---

## spec_navigate 직접 사용 (fallback only)

spec_search가 충분한 내용을 못 찾았을 때만 spec_navigate를 직접 사용.

```
1. spec_navigate("pcie", "root")       → 챕터 1~12 목록, 관련 챕터 id 선택
2. spec_navigate("pcie", "<id>")       → 섹션 목록, 관련 섹션 id 선택
3. spec_navigate("pcie", "<id.sub>")   → 서브섹션 목록 또는 leaf
4. leaf 판단 → 즉시 read_lines
```

**leaf 판단 (둘 중 하나):**
- 응답에 `"leaf": true` → `path` 필드가 응답에 포함됨 → `read_lines(path=<path>)`
- children 목록에서 `"has_children": false` → 해당 child 항목에 `path` 필드가 포함됨 → `read_lines(path=<child.path>)` (**추가 spec_navigate 호출 불필요**)

---

## 예시

**"TDISP가 뭐야?"**
```
spec_navigate("pcie", "root")  → "11" (Chapter 11. TEE Device Interface Security Protocol) 선택
spec_navigate("pcie", "11")    → 관련 섹션 선택
spec_navigate("pcie", "11.1")  → leaf → read_lines
```

**"TLP header format"**
```
spec_navigate("pcie", "root")   → "2" 선택
spec_navigate("pcie", "2")      → "2.2" 선택
spec_navigate("pcie", "2.2")    → "2.2.1" 선택
spec_navigate("pcie", "2.2.1")  → leaf → read_lines
```

**"IDE가 뭐야?"**
```
spec_navigate("pcie", "root")  → "6" (Chapter 6. System Architecture) 선택
spec_navigate("pcie", "6")     → "6.33" (IDE) 선택
spec_navigate("pcie", "6.33")  → leaf → read_lines
```

---

## 규칙

- leaf 도달 전 파일 읽기 금지
- 한 레벨에서 최대 2개 분기 선택 가능
- **find_files, run_command 사용 금지** — 탐색은 spec_navigate만 사용
- **grep_file은 파일 경로에만 가능** — 디렉토리 경로에 사용 시 에러 발생, 반드시 leaf path에만 사용
- **같은 파일 반복 읽기 금지** — read_lines는 파일당 1회, end_line=500으로 충분히 읽을 것

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
requires_tools: [spec_navigate, read_lines]
related_skills: [verilog-expert, protocol-spec-expert]
---

# ⚠️ MANDATORY: 반드시 spec_navigate로 시작할 것

**grep_file, find_files, read_file, list_dir 사용 금지** — 첫 번째 도구는 반드시 `spec_navigate("pcie", "root")`여야 한다.

---

## 탐색 절차 (4단계)

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
- **grep_file은 spec_navigate 완료 후, 특정 값/코드 추가 검색 시에만** 사용

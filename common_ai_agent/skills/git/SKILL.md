---
name: git
description: >
  Git version control operations: 히스토리 조회, 파일 복구(revert), diff 확인.
  이 agent는 write_file / replace_in_file 실행 시 자동으로 git add + commit을 수행함
  (GIT_VERSION_CONTROL_ENABLE=true, .config에서 설정).
  Trigger on: 'revert', 'undo', '이전 버전', '되돌려', 'git log', 'git history',
  'restore', '복구', '어떤 파일 바뀌었어', 'what changed'.
priority: 85
activation:
  keywords: ["revert", "undo", "이전 버전", "되돌려", "restore", "복구", "git log", "git history", "what changed", "어떤 파일"]
  auto_detect: true
requires_tools: [git_status, git_diff, run_command]
---

# SKILL: Git Version Control

## 핵심 개념

이 agent는 **write_file / replace_in_file 호출 시 자동으로 커밋**을 생성한다:

```
auto: write rtl/dma_top.v [2026-03-26 17:11:57] — DMA top AXI4 인터페이스 추가
auto: replace core/tools.py (+5/-3 lines) [2026-03-26 17:14:31] — timeout 파라미터 추가
```

따라서 모든 파일 변경은 git 히스토리에 남는다.

---

## 히스토리 조회

```
Action: run_command(command="git log --oneline -20")
Action: run_command(command="git log --oneline --all -- <path>")
```

특정 파일의 변경 이력:
```
Action: run_command(command="git log --oneline -- rtl/dma_top.v")
```

---

## Diff 확인

현재 상태 vs 최근 커밋:
```
Action: git_diff()
Action: git_diff(path="rtl/dma_top.v")
```

특정 커밋 vs 현재:
```
Action: run_command(command="git diff <hash> -- <path>")
```

두 커밋 비교:
```
Action: run_command(command="git diff <hash1> <hash2> -- <path>")
```

---

## 파일 복구 (Revert)

### 직전 커밋으로 되돌리기
```
Action: run_command(command="git checkout HEAD~1 -- <path>")
```

### 특정 커밋으로 되돌리기
```
# 1. 먼저 log로 hash 확인
Action: run_command(command="git log --oneline -- <path>")

# 2. 해당 hash로 복구
Action: run_command(command="git checkout <hash> -- <path>")
```

### 복구 후 자동 커밋
파일을 복구한 뒤 write_file로 저장하면 자동 커밋됨.
또는 수동으로:
```
Action: run_command(command="git add <path> && git commit -m 'revert: <path>'")
```

---

## 전체 작업 되돌리기 (여러 파일)

```
# 특정 커밋으로 전체 reset (주의: 이후 커밋 삭제됨)
Action: run_command(command="git reset --hard <hash>")

# 안전하게 revert commit 생성
Action: run_command(command="git revert <hash>")
```

---

## Gotchas

- `git checkout <hash> -- <file>` 은 해당 파일만 복구, 다른 파일 영향 없음
- `git reset --hard` 는 이후 모든 커밋이 사라짐 → **반드시 사용자 확인 후 실행**
- auto-commit은 `GIT_VERSION_CONTROL_ENABLE=true` 일 때만 동작 (.config)
- commit msg 포맷은 `GIT_COMMIT_MSG_MODE=simple|summary` 로 제어
- summary 모드는 `GIT_COMMIT_SUMMARY_MODEL` (기본: qwen) 로 생성

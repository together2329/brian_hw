# Plan Mode - 실시간 Tracking 개선안

## 현재 상태

### ✅ 이미 구현된 실시간 Tracking

**1. 초기 Progress 표시** (line 1244-1246)
```python
print(Color.system("\n[Claude Flow] ========================================"))
print(Color.info(todo_tracker.format_progress()))
print(Color.system("[Claude Flow] ========================================\n"))
```

**2. 각 Step 시작 시** (line 1254-1257)
```python
todo_tracker.mark_in_progress(step_index)
print(Color.system("\n[Claude Flow] ========================================"))
print(Color.info(todo_tracker.format_progress()))
print(Color.system("[Claude Flow] ========================================\n"))
```

**3. 각 Step 완료 시** (line 1330-1334)
```python
todo_tracker.mark_completed(step_index)
print(Color.system("\n[Claude Flow] ========================================"))
print(Color.success(todo_tracker.format_progress()))
print(Color.system("[Claude Flow] ========================================\n"))
```

**4. 최종 Summary** (line 1349-1352)
```python
print(Color.system("\n[Claude Flow] ========================================"))
print(Color.system("[Claude Flow] Final Progress:"))
print(Color.info(todo_tracker.format_progress()))
print(Color.system("[Claude Flow] ========================================\n"))
```

## 개선 방안

### 1. Plan 생성 중 Explore Agent Progress 표시 (NEW)

**현재 문제**:
- Plan 생성 중 explore agents가 실행되는데 progress가 안 보임
- 사용자는 "뭔가 진행 중"인지 알 수 없음

**개선안**:
```python
# _spawn_parallel_explore_agents() 수정

print("\n╔═══════════════════════════════════════════════════════╗")
print("║  Spawning 3 Explore Agents in Parallel...            ║")
print("╚═══════════════════════════════════════════════════════╝\n")

explore_todos = [
    {"content": f"Explore Agent 1: {target1}", "status": "in_progress", ...},
    {"content": f"Explore Agent 2: {target2}", "status": "pending", ...},
    {"content": f"Explore Agent 3: {target3}", "status": "pending", ...}
]

explore_tracker = TodoTracker()
explore_tracker.add_todos(explore_todos)

print(explore_tracker.format_progress())

# Agent 실행...
for i, agent in enumerate(agents):
    explore_tracker.mark_in_progress(i)
    print(f"\n▶️  Agent {i+1} started")
    print(explore_tracker.format_progress())

    # Wait for completion
    result = agent.get_result()

    explore_tracker.mark_completed(i)
    print(f"\n✅ Agent {i+1} completed")
    print(explore_tracker.format_progress())
```

### 2. Step 실행 중 Sub-Actions Progress (NEW)

**현재 문제**:
- Step 실행 중 내부에서 여러 actions가 실행되는데 보이지 않음
- 예: "Analyze architecture" step이 10개 파일을 읽는데 어디까지 진행됐는지 모름

**개선안**:
```python
# ReAct loop에서 action 실행 시

Action: read_file(path="module1.v")
  [1/10] Reading module1.v...

Action: read_file(path="module2.v")
  [2/10] Reading module2.v...

Action: analyze_verilog_module(path="module3.v")
  [3/10] Analyzing module3.v...
```

### 3. Plan 파일에 Progress 실시간 저장 (선택사항)

**현재**:
- TodoTracker는 메모리에만 존재
- Plan 파일의 `[x]` 마크는 `mark_step_done()` 호출 시만 업데이트

**개선안**:
- Progress를 plan 파일 상단에 실시간 저장
```markdown
# Plan

## Progress: 2/5 (40%)
- [x] Step 1: Explore codebase
- [>] Step 2: Analyzing architecture (IN PROGRESS)
- [ ] Step 3: Write tests
- [ ] Step 4: Run simulation
- [ ] Step 5: Generate report

## Task
analyze caliptra subsystem
...
```

### 4. Status Bar 스타일 Progress (NEW)

**개선안**:
```
╔════════════════════════════════════════════════════════════╗
║ PLAN EXECUTION PROGRESS                                    ║
╠════════════════════════════════════════════════════════════╣
║ Task: Analyze Caliptra Subsystem                           ║
║ Progress: [████████░░░░░░░░] 40% (2/5 steps)              ║
║                                                            ║
║ ✅ Step 1: Repository Setup                   (Completed)  ║
║ ✅ Step 2: Architecture Extraction            (Completed)  ║
║ ▶️  Step 3: Deep-Dive Analysis                (In Progress)║
║    └─ [████████████░░░░░] 60% (12/20 files analyzed)      ║
║ ⏸️  Step 4: Verification                       (Pending)    ║
║ ⏸️  Step 5: Report Generation                  (Pending)    ║
╚════════════════════════════════════════════════════════════╝
```

## 구현 우선순위

### Priority 1: Explore Agent Progress (높음)
- 사용자가 plan 생성 중 뭔가 진행 중인지 알 수 있음
- 구현 난이도: 낮음 (TodoTracker 재사용)

### Priority 2: Status Bar Progress (중간)
- 더 명확하고 직관적인 UI
- 구현 난이도: 중간 (format_progress() 함수 수정)

### Priority 3: Plan 파일에 Progress 저장 (낮음)
- 중단 후 재개 시 유용하지만, 현재도 `[x]` 마크로 가능
- 구현 난이도: 중간

## 사용자 경험 Before/After

### Before (현재)
```
$ python3 src/main.py
> /plan
Task: analyze caliptra subsystem

[Plan Mode] Spawning explore agents...
[20초 동안 아무 출력 없음...]  ← 사용자 불안

[Plan Mode] Draft plan created: ...
```

### After (개선)
```
$ python3 src/main.py
> /plan
Task: analyze caliptra subsystem

╔═══════════════════════════════════════════════════════╗
║  Spawning 3 Explore Agents in Parallel...            ║
╚═══════════════════════════════════════════════════════╝

=== EXPLORE PROGRESS ===
▶️ 1. Exploring repository structure
⏸️ 2. Searching for Caliptra modules
⏸️ 3. Finding documentation

Progress: 0/3

[5초 후]
✅ 1. Exploring repository structure
▶️ 2. Searching for Caliptra modules
⏸️ 3. Finding documentation

Progress: 1/3

[10초 후]
✅ 1. Exploring repository structure
✅ 2. Searching for Caliptra modules
▶️ 3. Finding documentation

Progress: 2/3

[15초 후]
✅ 1. Exploring repository structure
✅ 2. Searching for Caliptra modules
✅ 3. Finding documentation

Progress: 3/3

[Plan Mode] Draft plan created: ...
```

## 다음 단계

어떤 개선을 원하시나요?

1. **Explore Agent Progress** - Plan 생성 중 실시간 표시
2. **Status Bar Progress** - 더 fancy한 progress bar
3. **둘 다** - 완전한 실시간 tracking

선택해주시면 바로 구현하겠습니다!

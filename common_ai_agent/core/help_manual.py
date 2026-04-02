"""
Man Page System for Common AI Agent

Provides detailed command reference with options and usage examples.
Access via: /man <topic>
"""

from typing import Dict

_SEP = "=" * 60

MAN_PAGES: Dict[str, str] = {

    "guide": f"""
{_SEP}
 GETTING STARTED  Common AI Agent
{_SEP}

 개요
   Common AI Agent는 LLM 기반 코딩 어시스턴트입니다.
   자연어로 대화하거나 슬래시 커맨드로 기능을 제어합니다.

 ─────────────────────────────────────────────────────
 전체 워크플로우 (Plan → Todo → 실행)
 ─────────────────────────────────────────────────────

 1단계: 작업 시작
   /plan "로그인 모듈 JWT 방식으로 리팩토링"
   → AI가 코드베이스를 탐색합니다 (자동)

 2단계: Todo 목록 생성 (AI 자동)
   AI가 todo_write 툴로 태스크 목록을 작성합니다:
   > ⏸️  1. auth.py JWT 검증 로직 추가
   > ⏸️  2. tests/test_auth.py 테스트 작성
   > ⏸️  3. README 업데이트
   /todo  ← 목록 확인
   /todo add "추가 태스크"   ← 필요 시 수동 추가
   /todo rm 2               ← 불필요한 태스크 제거

 3단계: 계획 검토 & 승인
   AI가 계획을 제시하면:
   y      ← 승인 → 즉시 실행 시작
   n      ← 거절 → 재계획 요청
   (수정 요청도 가능: "2번 태스크 빼고 진행해")

 4단계: 태스크 실행 사이클 (태스크마다 반복)
   ┌─ AI가 작업 수행
   │   ↓
   │  in_progress  ← 태스크 시작
   │   ↓
   │  completed    ← 작업 완료, AI가 검토 요청
   │   ↓
   ├─ approved     ← 검토 통과 → 다음 태스크로 자동 이동
   └─ rejected     ← 재작업 필요 → 다시 in_progress로

   /todo  ← 언제든 현재 상태 확인

 5단계: 태스크 stuck 시 수동 제어
   /todo s 1 a      태스크 1 강제 승인 (AI가 멈췄을 때)
   /todo s 1 r      태스크 1 반려 (재작업 지시)
   /todo s all p    전체 pending 리셋 후 재시작
   /todo rule       현재 실행 규칙 확인

 6단계: 완료 후 정리
   /compact         대화 요약 압축 (컨텍스트 절약)
   /context         남은 컨텍스트 확인

 ─────────────────────────────────────────────────────
 빠른 참조
 ─────────────────────────────────────────────────────

 모델 관리
   /model               현재 모델 확인
   /model 2             보조 모델로 전환
   /model claude-opus-4-6  직접 지정

 컨텍스트 관리
   /context             사용량 시각화
   /compact             요약 압축 (맥락 유지)
   /clear               완전 초기화 (새 시작)

 TAB 자동완성
   / 입력 후 TAB → 커맨드 목록 표시

 도움말
   /help                핵심 커맨드 목록
   /help -v             전체 커맨드 상세 목록
   /man <topic>         상세 매뉴얼
   topic: plan todo compact context skills git model clear guide
{_SEP}
""",

    "plan": f"""
{_SEP}
 PLAN MODE  /plan
{_SEP}

 개요
   복잡한 작업을 단계별로 구조화하여 실행합니다.
   AI가 먼저 계획을 제시하고, 사용자 승인 후 실행합니다.

 사용법
   /plan              Plan Mode 진입 (빈 상태로)
   /plan <task>       태스크 설명과 함께 진입
   /mode normal       Plan Mode 종료, 일반 모드로 복귀

 워크플로우
   Clarify  → 요구사항 명확화 (AI가 질문)
   Explore  → 코드베이스 탐색 (병렬 에이전트)
   Propose  → 구현 계획 제시
   [승인]   → 사용자가 계획 확인
   Execute  → 단계별 실행 + /todo 자동 업데이트

 예시
   /plan "로그인 모듈 JWT 방식으로 리팩토링"
   > AI: 현재 구조 탐색 중...
   > AI: 1단계: auth.py 수정, 2단계: 테스트 추가 ...
   > 승인 후 실행

   /plan "버그: 로그인 시 500 에러"
   > AI: 에러 원인 분석 후 수정 계획 제시

 설정 (.config)
   CLAUDE_FLOW_MODE=off|auto|always
     off    : /plan 명시 필요 (기본값)
     auto   : AI가 복잡도 판단 후 자동 진입
     always : 모든 작업을 plan mode로 처리
   PLAN_MODE_EXPLORE_COUNT=3     탐색 에이전트 수 (1-5)
   PLAN_MODE_PARALLEL_EXPLORE=true   병렬 탐색 활성화

 관련 커맨드
   /todo    현재 태스크 목록 확인
   /mode    모드 전환
   /step    단계별 실행 모드 (각 태스크 후 일시정지)
{_SEP}
""",

    "todo": f"""
{_SEP}
 TODO LIST  /todo
{_SEP}

 개요
   현재 진행 중인 태스크 목록을 관리합니다.
   /plan 실행 후 AI가 자동으로 등록하며, 수동 조작도 가능합니다.

 사용법 (alias 모두 동일 동작)
   /todo                                현재 Todo 목록 표시
   /todo clear                          Todo 목록 전체 초기화
   /todo add <text>                     새 태스크 추가
   /todo remove <N>  / rm <N>           태스크 N 삭제
   /todo move <N> <M> / mv <N> <M>      태스크 N을 위치 M으로 이동
   /todo goal <N> <text> / g            태스크 N 내용(goal) 변경
   /todo set <N> <status> / s           상태 강제 변경
   /todo set all <status>               전체 상태 강제 변경
   /todo edit <N> <field> <value>       개별 필드 수정
   /todo edit <N> <field>+ <value>      필드에 내용 추가(append)
   (edit alias: e)
   /todo revert <N> [opts] [reason]     태스크 N 승인 시점으로 롤백
   /todo rv <N> [opts] [reason]         (alias)

 edit 필드 목록
   content / c        태스크 설명 (goal과 동일, active_form도 동기화)
   detail / d         구현 방법/상세 설명
   criteria / cr      완료 판단 기준 (줄바꿈으로 구분)
   priority / pr      우선순위: high(h) / medium(m) / low(l)
   active_form / af   진행 중일 때 표시 텍스트
   rejection_reason / rr  반려 사유
   approved_reason / ar   승인 메모

 상태 종류
   pending       대기 중 ⏸️
   in_progress   진행 중 ▶️
   completed     완료(미승인) ✅
   approved      승인 완료 ✅✅
   rejected      반려 ❌

 예시
   /todo add "JWT 인증 모듈 작성"        새 태스크 추가
   /todo rm 3                           태스크 3 삭제
   /todo mv 3 1                         태스크 3을 맨 앞으로 이동
   /todo g 2 "auth.py 리팩토링"          태스크 2 내용 변경
   /todo s 1 a                          태스크 1 강제 승인 (a=approved)
   /todo s all p                        전체 pending 리셋
   /todo e 1 d "JWT 라이브러리 사용"     detail 설정
   /todo e 1 d+ "\n- RS256 알고리즘"    detail에 내용 추가
   /todo e 2 cr "테스트 통과\n리뷰 완료" criteria 설정
   /todo e 1 pr h                       priority=high
   /todo e 1 ar "모든 테스트 통과"       approved reason 설정

 서브커맨드 Alias
   remove → rm       move → mv
   goal   → g        set  → s
   edit   → e        revert → rv

 Status Alias (/todo s, /todo set)
   p = pending    i/ip = in_progress
   c = completed  a = approved    r = rejected

 Edit 필드 Alias (/todo e, /todo edit)
   c  = content          d  = detail
   cr = criteria         pr = priority
   af = active_form      rr = rejection_reason
   ar = approved_reason
   field+  = 덮어쓰기 대신 내용 추가(append)

 Priority Alias (edit pr)
   h = high    m = medium    l = low

 Todo Rule (.TODO_RULE.md)
   태스크 시작 시 AI에게 자동 주입되는 실행 규칙 파일.
   파일 위치 (둘 다 있으면 합쳐서 주입):
     ~/.common_ai_agent/.TODO_RULE.md   전역 규칙
     <프로젝트>/.TODO_RULE.md           프로젝트 규칙
   /todo rule   현재 규칙 내용 확인

 revert 옵션
   --hard          git reset --hard (커밋 삭제, 비가역)
   --reset-conv    승인 시점의 conversation 스냅샷 복원
   기본 (옵션 없음): git revert (revert commit 추가, 히스토리 보존)

 revert 예시
   /todo revert 2 "JWT 로직 오류"
   > git revert commit 생성 + conversation에 rollback 주입

   /todo rv 2 --hard "완전 초기화"
   > git reset --hard + conversation rollback 주입

   /todo rv 2 --reset-conv "재작업"
   > git revert + conversation 승인 시점 스냅샷 복원

   /todo rv 2 --hard --reset-conv "이유"
   > 코드 + conversation 완전 하드 리셋

 AI 상태 흐름 (정상)
   pending → in_progress → completed → approved

 강제 변경이 필요한 경우
   - AI가 멈춰서 진행이 안 될 때
   - 잘못된 상태로 stuck 됐을 때
   - 일부 태스크만 건너뛰고 싶을 때

 설정 (.config)
   TODO_FILE=current_todos.json   저장 파일 경로

 TodoWrite 도구 입력 스펙
   AI가 태스크를 생성할 때 사용하는 도구. 각 항목은 dict.

   필수 필드:
     content       str   태스크 설명 (목표, "동사+목적어" 형태)
                         예) "로그인 API 401 오류 수정"

   선택 필드:
     activeForm    str   진행 중 표시 텍스트 (미입력 시 자동 생성)
                         예) "로그인 API 401 오류 수정 중"
     status        str   초기 상태 (기본: pending)
                         pending / in_progress / completed / approved / rejected
     priority      str   우선순위: high / medium / low (기본: medium)
     detail        str   구체적 구현 방법 또는 접근 방식
                         예) "HTTPError 핸들러에서 토큰 만료 케이스 분리"
     criteria      str   완료 판단 기준 체크리스트 (줄바꿈 \\n 으로 구분)
                         예) "유닛 테스트 통과\\n수동 로그인 확인\\n코드 리뷰 완료"

   제약:
     - in_progress 상태는 동시에 1개만 허용
     - content 필수 (누락 시 에러)
     - status 오타 시 에러 (aliases: todo→pending, done→completed 등)

   예시 (full):
     todo_write([
       {{
         "content":    "SSL 인증서 검증 오류 수정",
         "activeForm": "SSL 인증서 검증 오류 수정 중",
         "status":     "in_progress",
         "priority":   "high",
         "detail":     "_make_https_conn에서 SSL_VERIFY=false 옵션 분기 추가",
         "criteria":   "사내 Linux에서 연결 성공\\nSSL_VERIFY=false 설정 시 우회 확인\\n기존 테스트 통과"
       }},
       {{
         "content":  "PERF 로그 reused/new-conn 태그 확인",
         "status":   "pending",
         "priority": "low",
         "criteria": "PERF=true 환경에서 reused 출력 확인"
       }}
     ])

 /todo 표시 모드
   /todo        아이콘 + 내용 + criteria 목록
   /todo -v     전체 상세 (detail, criteria, 경과시간, 반려/승인 사유)
   /make todo   대화 분석 → TodoWrite 자동 호출 (criteria 포함)

 관련 커맨드
   /plan    Plan Mode (태스크 자동 생성)
   /mode    실행 모드 전환 (agent/chat/step)
   /step    태스크 단위 일시정지 모드
   /make    대화 기반 자동 생성: /make todo
{_SEP}
""",

    "compact": f"""
{_SEP}
 COMPACT  /compact
{_SEP}

 개요
   대화 기록을 AI로 요약하여 컨텍스트를 줄입니다.
   요약본은 유지되므로 기존 대화 내용을 참조할 수 있습니다.

 사용법
   /compact                    기본 압축 (최근 메시지 보존)
   /compact --keep <N>         최근 N개 메시지 보존 후 압축
   /compact --dry-run          압축 미리보기 (실제 저장 안 함)
   /compact <instruction>      커스텀 요약 지시

 예시
   /compact
   > 대화 요약 중... 완료 (128개 → 3개 메시지)

   /compact --keep 10
   > 최근 10개 메시지 유지 후 이전 기록 요약

   /compact "코드 변경사항 위주로 요약해줘"
   > 커스텀 지시로 요약

   /compact --dry-run
   > [미리보기] 요약될 내용: ...

 /compact vs /clear
   /compact   요약 유지 (기억은 남음, 컨텍스트 절약)
   /clear     완전 초기화 (새 대화 시작)

 설정 (.config)
   ENABLE_COMPRESSION=true         자동 압축 활성화
   COMPRESSION_THRESHOLD=0.8       압축 시작 임계값 (80%)
   COMPRESSION_KEEP_RECENT=0       자동 압축 시 유지할 최근 메시지 수
   COMPRESSION_MODE=single|chunked 압축 방식

 관련 커맨드
   /clear       완전 초기화
   /context     현재 컨텍스트 사용량 확인
   /compression 자동 압축 임계값 설정
{_SEP}
""",

    "context": f"""
{_SEP}
 CONTEXT  /context
{_SEP}

 개요
   현재 컨텍스트(토큰) 사용량을 시각화합니다.
   컨텍스트가 가득 차면 AI 응답 품질이 저하되거나 오류가 발생합니다.

 사용법
   /context           컨텍스트 사용량 시각화
   /context -v        전체 대화 내용 상세 표시
   /context debug     디버그 정보 포함 표시

 출력 해석
   ████░░░░░░ 40%   사용량 바 차트
   시스템 프롬프트 / 대화 / 남은 공간 구분 표시

 컨텍스트 관리 전략
   50% 이하   여유 있음
   50-80%     /compact 권장
   80% 이상   /clear 또는 /compact 필요

 설정 (.config)
   MAX_CONTEXT_CHARS=262144    최대 컨텍스트 크기 (~65K 토큰)
   COMPRESSION_THRESHOLD=0.8  자동 압축 시작 임계값

 관련 커맨드
   /compact     요약 압축으로 컨텍스트 줄이기
   /clear       완전 초기화
   /window      롤링 윈도우로 전송 메시지 제한
{_SEP}
""",

    "skills": f"""
{_SEP}
 SKILLS  /skills
{_SEP}

 개요
   Skills는 특정 상황에서 AI 동작을 커스터마이징하는 규칙 파일입니다.
   .md 파일로 정의하며, 컨텍스트에 자동 삽입됩니다.

 사용법
   /skills              현재 로드된 스킬 목록
   /skill list          전체 스킬 목록 (활성화 여부 포함)
   /skill enable <name> 특정 스킬 강제 활성화
   /skill disable <name> 특정 스킬 비활성화
   /skill active        수동 설정된 스킬 목록
   /skill clear         모든 수동 설정 초기화

 스킬 파일 위치
   ~/.common_ai_agent/skills/    전역 스킬
   <프로젝트>/.skills/           프로젝트별 스킬

 스킬 파일 구조 (.md)
   ---
   name: my_skill
   description: 이 스킬이 활성화될 상황 설명
   priority: 10
   ---
   AI에게 전달할 지시사항...

 설정 (.config)
   ENABLE_SKILL_SYSTEM=true   스킬 시스템 활성화

 관련 커맨드
   /context     스킬 로드 상태 확인 (컨텍스트 하단)
{_SEP}
""",

    "git": f"""
{_SEP}
 GIT  /git
{_SEP}

 개요
   Git 관련 작업을 수행합니다.
   AI가 파일을 수정할 때 자동으로 커밋하도록 설정할 수 있습니다.

 사용법
   /git diff            현재 변경사항 표시 (git diff)
   /git clear           .git 디렉토리 삭제 (버전 관리 초기화)

 자동 Git 커밋
   AI가 write_file / replace_in_file 실행 시 자동으로 커밋됩니다.

 설정 (.config)
   GIT_VERSION_CONTROL_ENABLE=true   자동 커밋 활성화
   GIT_COMMIT_MSG_MODE=simple|summary
     simple  : "auto: write src/main.py [2026-03-26 14:32]"
     summary : AI가 변경 내용 요약 후 커밋 메시지 생성
   GIT_COMMIT_SUMMARY_MODEL=openrouter/qwen/qwen-2.5-7b-instruct
     커밋 메시지 생성에 사용할 모델 (cheap/fast 권장)

 예시
   /git diff
   > diff --git a/src/main.py b/src/main.py
   > ...

   /git clear
   > ⚠️  이 작업은 되돌릴 수 없습니다. .git이 삭제됩니다.

 주의
   /git clear는 복구 불가. 신중하게 사용하세요.

 관련 커맨드
   /snapshot    대화 스냅샷 저장/복원
{_SEP}
""",

    "model": f"""
{_SEP}
 MODEL  /model
{_SEP}

 개요
   사용할 LLM 모델을 전환합니다.
   1번(PRIMARY)과 2번(SECONDARY) 두 모델을 빠르게 전환하거나
   직접 모델명을 지정할 수 있습니다.

 사용법
   /model             현재 모델 및 설정된 모델 목록 표시
   /model 1           PRIMARY 모델로 전환
   /model 2           SECONDARY 모델로 전환
   /model <name>      지정 모델로 전환 (임시)

 예시
   /model
   > Current model: claude-opus-4-6
   >   1: claude-opus-4-6 ◀ active
   >   2: deepseek/deepseek-r1

   /model 2
   > 모델을 deepseek/deepseek-r1 로 전환했습니다.

   /model gpt-4o
   > 모델을 gpt-4o 로 전환했습니다.

 설정 (.config)
   PRIMARY_MODEL=claude-opus-4-6          기본 모델
   SECONDARY_MODEL=deepseek/deepseek-r1   보조 모델
   MODEL_NAME=claude-opus-4-6             현재 활성 모델
   BASE_URL=https://api.anthropic.com     API 엔드포인트
   API_KEY=...                            API 키

 OpenRouter 사용 시
   BASE_URL=https://openrouter.ai/api/v1
   OPENROUTER_API_KEY=sk-or-...
   MODEL_NAME=openrouter/google/gemini-2.5-pro-preview-03-25

 관련 커맨드
   /status      현재 모델 및 설정 상태 확인
   /config      전체 설정 확인
{_SEP}
""",

    "clear": f"""
{_SEP}
 CLEAR  /clear
{_SEP}

 개요
   대화 기록 또는 전체 상태를 초기화합니다.

 사용법
   /clear             대화 기록만 초기화
   /clear all         git(.git) + todo + 대화 기록 전체 초기화
   /clear <N>         최근 N쌍(user+assistant)만 유지하고 나머지 삭제

 예시
   /clear
   > 대화 기록이 초기화되었습니다.

   /clear all
   > ✅ All cleared: git + todo + conversation.

   /clear 3
   > 최근 3쌍 유지, 이전 기록 삭제

 /clear vs /compact
   /clear     완전 초기화 (요약도 없음, 진짜 새 시작)
   /compact   요약 유지 (맥락은 남김, 컨텍스트 절약)

 관련 커맨드
   /compact        요약 유지 압축
   /context        현재 컨텍스트 사용량 확인
   /todo clear     todo만 초기화
   /git clear      .git만 삭제
{_SEP}
""",
}


def get_man_page(topic: str) -> str:
    """
    Return man page for the given topic.
    If topic is empty or unknown, show available topics.
    """
    if not topic:
        return _topics_list()

    page = MAN_PAGES.get(topic)
    if page:
        return page

    # Partial match
    matches = [k for k in MAN_PAGES if k.startswith(topic)]
    if len(matches) == 1:
        return MAN_PAGES[matches[0]]
    if len(matches) > 1:
        return f"\n'{topic}'에 해당하는 토픽이 여러 개입니다: {', '.join(matches)}\n더 구체적으로 입력해주세요.\n"

    return f"\n알 수 없는 토픽: '{topic}'\n\n{_topics_list()}"


def _topics_list() -> str:
    topics = sorted(MAN_PAGES.keys())
    lines = [
        "",
        f"{_SEP}",
        " /man — 상세 매뉴얼 시스템",
        f"{_SEP}",
        "",
        " 사용법",
        "   /man <topic>   해당 토픽의 상세 매뉴얼 표시",
        "",
        " 사용 가능한 토픽",
    ]
    for t in topics:
        # Get first non-empty line after the header as a brief description
        page = MAN_PAGES[t]
        brief = ""
        for line in page.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("=") and " " in stripped and not stripped.startswith("/"):
                brief = stripped[:50]
                break
        lines.append(f"   /man {t:<12} {brief}")
    lines.append("")
    lines.append(f"{_SEP}")
    return "\n".join(lines) + "\n"

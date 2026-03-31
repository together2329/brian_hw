"""
Man Page System for Common AI Agent

Provides detailed command reference with options and usage examples.
Access via: /man <topic>
"""

_SEP = "=" * 60

MAN_PAGES: dict[str, str] = {

    "guide": f"""
{_SEP}
 GETTING STARTED  Common AI Agent
{_SEP}

 개요
   Common AI Agent는 LLM 기반 코딩 어시스턴트입니다.
   자연어로 대화하거나 슬래시 커맨드로 기능을 제어합니다.

 기본 사용법
   그냥 메시지 입력        일반 대화 / 코딩 질문
   /plan <task>           계획 후 실행 (복잡한 작업)
   /todo                  현재 진행 중인 태스크 확인
   /model                 모델 전환
   /compact               컨텍스트 정리

 빠른 시작
   1. 모델 확인:       /model
   2. 컨텍스트 확인:   /context
   3. 작업 시작:       /plan "무엇을 만들고 싶은지 설명"
   4. 진행 확인:       /todo
   5. 정리:            /compact

 TAB 자동완성
   / 입력 후 TAB → 커맨드 목록
   /m + TAB → /man, /model, /mode ...

 도움말
   /help              핵심 커맨드 목록
   /help -v           전체 커맨드 목록
   /man <topic>       상세 매뉴얼
   /man guide         이 페이지

 토픽 목록
   plan, todo, compact, context, skills, git, model, clear
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

 사용법
   /todo              현재 Todo 목록 표시
   /todo clear        Todo 목록 초기화

 상태 아이콘
   ▶️  in_progress    현재 진행 중
   ⏸️  pending        대기 중
   ✅  completed      완료

 예시
   /todo
   > ▶️  1. auth.py JWT 토큰 검증 로직 수정
   > ⏸️  2. tests/test_auth.py 테스트 추가
   > ✅  3. README 업데이트

   /todo clear
   > ✅ Todo list cleared.

 설정 (.config)
   TODO_FILE=current_todos.json   저장 파일 경로

 자동 등록
   /plan 승인 후 AI가 단계별 태스크를 자동으로 등록합니다.
   각 태스크 완료 시 상태가 자동으로 업데이트됩니다.

 관련 커맨드
   /plan    Plan Mode (태스크 자동 생성)
   /step    태스크 단위 일시정지 모드
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
   대화 기록을 초기화합니다.
   완전히 새로운 대화를 시작하고 싶을 때 사용합니다.

 사용법
   /clear             전체 대화 기록 초기화
   /clear <N>         최근 N쌍(user+assistant)만 유지하고 나머지 삭제

 예시
   /clear
   > 대화 기록이 초기화되었습니다. (새 대화 시작)

   /clear 3
   > 최근 3쌍 유지, 이전 기록 삭제

 /clear vs /compact
   /clear     완전 초기화 (요약도 없음, 진짜 새 시작)
   /compact   요약 유지 (맥락은 남김, 컨텍스트 절약)

 관련 커맨드
   /compact     요약 유지 압축
   /context     현재 컨텍스트 사용량 확인
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

# 컬러 출력 (Colored Output) 기능

## 개요

`main.py`에 ANSI 색상 코드를 사용한 컬러 출력 기능이 추가되었습니다. 
별도의 라이브러리 없이 터미널에서 색상으로 구분된 출력을 볼 수 있습니다.

## 색상 구분

각 메시지 타입별로 다른 색상이 적용됩니다:

- **시스템 메시지** (System): `Cyan` - 기본 시스템 안내
- **정보 메시지** (Info): `Dim Cyan` - 부가 정보
- **사용자 입력** (User): `Green` - 사용자가 입력하는 메시지
- **에이전트 응답** (Agent): `Blue` - AI 에이전트의 응답
- **도구 호출** (Tool): `Magenta` - 실행되는 도구 이름
- **성공 메시지** (Success): `Bold Green` - 작업 성공
- **경고 메시지** (Warning): `Yellow` - 주의가 필요한 상황
- **에러 메시지** (Error): `Bold Red` - 오류 발생

## 사용 예시

### 데모 실행
```bash
python3 demo_colors.py
```

### 메인 프로그램 실행
```bash
python3 main.py
```

대화형 모드에서 색상으로 구분된 출력을 확인할 수 있습니다:
- 시스템 초기화 정보: Cyan
- 사용자 입력 프롬프트: Green
- 에이전트 반복 표시: Blue
- 도구 실행: Magenta
- 성공/실패 메시지: Green/Red

## Color 클래스 API

프로그램 내에서 색상을 사용하려면:

```python
from main import Color

# 기본 사용법
print(Color.system("시스템 메시지"))
print(Color.user("사용자 메시지"))
print(Color.agent("에이전트 메시지"))
print(Color.tool("도구 이름"))

# 상태별 메시지
print(Color.success("성공!"))
print(Color.warning("경고"))
print(Color.error("에러 발생"))
print(Color.info("추가 정보"))

# 직접 색상 코드 사용
print(Color.BOLD + Color.CYAN + "굵은 Cyan" + Color.RESET)
```

## 기술 세부사항

- 구현: ANSI escape codes 사용
- 의존성: 없음 (표준 라이브러리만 사용)
- 호환성: 대부분의 현대 터미널 (macOS Terminal, iTerm2, Linux terminals 등)
- Windows: Windows 10 이상의 최신 터미널에서 지원

## 변경사항

### `main.py`
- `Color` 클래스 추가 (라인 18-72)
- 모든 print 문에 색상 적용:
  - Rate limit 대기: `Color.info()`
  - 히스토리 저장/로드: `Color.success()` / `Color.error()`
  - Context 압축: `Color.warning()` / `Color.success()`
  - 에이전트 반복: `Color.agent()`
  - 도구 호출: `Color.tool()`
  - 에러 감지: `Color.warning()` / `Color.error()`

### `demo_colors.py` (신규)
- 모든 색상 타입을 시연하는 독립 실행 데모 스크립트
- 실제 사용 예시 포함

## 장점

✅ **가독성 향상**: 메시지 타입을 한눈에 구분
✅ **디버깅 용이**: 에러와 경고를 빠르게 식별
✅ **사용자 경험**: 전문적이고 현대적인 CLI 인터페이스
✅ **제로 의존성**: 추가 라이브러리 불필요

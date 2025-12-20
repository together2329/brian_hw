# TAB 자동완성 설정 가이드

## 🎯 목표

Brian Coder에서 TAB 키를 눌러 `/help`, `/status` 같은 slash commands를 자동완성할 수 있도록 설정합니다.

---

## ✅ 1단계: 작동 테스트

먼저 자동완성이 작동하는지 테스트해봅니다:

```bash
python3 test_tab_completion_interactive.py
```

**테스트 방법**:
1. `/h` 입력 후 TAB 누르기 → `/help`로 자동완성되어야 함
2. `/c` 입력 후 TAB TAB (두 번) → `/clear`, `/compact`, `/config`, `/context` 목록 표시
3. `/st` 입력 후 TAB → `/status`로 자동완성

**결과**:
- ✅ 작동함 → 추가 설정 불필요
- ❌ 작동 안 함 → 2단계로 진행

---

## 🔧 2단계: macOS/Linux 설정 (작동 안 할 때)

macOS는 기본적으로 `libedit`를 사용하기 때문에 TAB 자동완성이 작동하지 않을 수 있습니다.

### 방법 1: ~/.inputrc 파일 생성 (추천)

1. 홈 디렉토리에 `.inputrc` 파일 생성:

```bash
cat > ~/.inputrc << 'EOF'
# Enable TAB completion
set editing-mode emacs
TAB: complete

# Show all completions on double TAB
set show-all-if-ambiguous on

# Case-insensitive completion
set completion-ignore-case on

# Show completion type indicators (* for executables, / for directories)
set visible-stats on
EOF
```

2. 변경사항 적용:

```bash
# 새 터미널 열기
# 또는
source ~/.bashrc
# 또는
source ~/.zshrc
```

3. 다시 테스트:

```bash
python3 test_tab_completion_interactive.py
```

### 방법 2: 환경 변수 설정

`.bashrc` 또는 `.zshrc`에 추가:

```bash
echo 'export INPUTRC=~/.inputrc' >> ~/.zshrc
source ~/.zshrc
```

### 방법 3: GNU readline 설치 (고급)

macOS의 libedit 대신 GNU readline 사용:

```bash
# Homebrew로 설치
brew install readline

# Python을 GNU readline과 함께 재설치
brew reinstall python --with-brewed-readline
```

⚠️ **주의**: 이 방법은 시스템 Python 설정을 변경하므로 권장하지 않습니다.

---

## 🪟 Windows 설정

Windows에서는 `pyreadline`이 필요할 수 있습니다:

```bash
pip install pyreadline3
```

하지만 Brian Coder는 zero-dependency이므로, Windows에서는 자동완성이 제한적일 수 있습니다.

---

## 🧪 3단계: Brian Coder에서 테스트

설정 완료 후 실제 Brian Coder에서 테스트:

```bash
cd brian_coder
python3 src/main.py
```

**테스트**:
```
You: /h[TAB]          → /help
You: /c[TAB][TAB]     → /clear /compact /config /context
You: /st[TAB]         → /status
```

---

## 📋 문제 해결

### Q1: TAB을 눌렀는데 아무 반응이 없어요

**원인**: readline이 제대로 설정되지 않음

**해결**:
1. `~/.inputrc` 파일이 있는지 확인
2. 새 터미널 세션 시작
3. Python에서 readline 확인:
   ```bash
   python3 -c "import readline; print(readline.__file__)"
   ```

### Q2: TAB을 누르면 ^I가 입력돼요

**원인**: libedit이 TAB 바인딩을 인식 못함

**해결**:
`~/.inputrc`에 다음 추가:
```
"\C-i": complete
```

### Q3: 자동완성은 되는데 목록이 안 보여요 (TAB TAB)

**원인**: `show-all-if-ambiguous` 설정 누락

**해결**:
`~/.inputrc`에 다음 추가:
```
set show-all-if-ambiguous on
```

### Q4: 대소문자 구분이 너무 엄격해요

**원인**: Case-insensitive 설정 누락

**해결**:
`~/.inputrc`에 다음 추가:
```
set completion-ignore-case on
```

---

## 🎨 고급 설정

### 컬러 자동완성

```bash
# ~/.inputrc
set colored-stats on
set colored-completion-prefix on
```

### 자동완성 벨 소리 끄기

```bash
# ~/.inputrc
set bell-style none
```

### 부분 매칭 자동완성

```bash
# ~/.inputrc
# /sta 입력 후 TAB → /status로 자동완성
set skip-completed-text on
```

---

## 📊 현재 상태 확인

### readline 백엔드 확인

```bash
python3 << 'EOF'
import readline
import sys

print(f"Python version: {sys.version}")
print(f"Readline module: {readline.__file__}")

# Try to detect backend
try:
    readline.parse_and_bind("tab: complete")
    print("Backend: GNU Readline")
except:
    try:
        readline.parse_and_bind("bind ^I rl_complete")
        print("Backend: libedit (macOS)")
    except:
        print("Backend: Unknown")
EOF
```

### inputrc 설정 확인

```bash
# inputrc 파일 위치 확인
echo $INPUTRC

# 내용 확인
cat ~/.inputrc
```

---

## 🚀 최종 권장 설정

**~/.inputrc** (모든 설정 포함):

```
# Brian Coder TAB Autocomplete Settings
# =====================================

# Enable TAB completion
set editing-mode emacs
TAB: complete
"\C-i": complete

# Show all completions immediately
set show-all-if-ambiguous on

# Case-insensitive
set completion-ignore-case on

# Show type indicators
set visible-stats on

# Colored completion
set colored-stats on
set colored-completion-prefix on

# Skip completed text
set skip-completed-text on

# No bell
set bell-style none

# Show common prefix
set menu-complete-display-prefix on
```

적용 후:
```bash
source ~/.bashrc  # 또는 source ~/.zshrc
python3 test_tab_completion_interactive.py
```

---

## ✅ 확인 체크리스트

- [ ] `~/.inputrc` 파일 생성
- [ ] TAB 바인딩 설정 확인
- [ ] 새 터미널 세션 시작
- [ ] `test_tab_completion_interactive.py` 테스트
- [ ] `/h[TAB]` → `/help` 자동완성 확인
- [ ] `/c[TAB][TAB]` → 목록 표시 확인
- [ ] Brian Coder에서 실제 테스트

---

## 📝 결론

TAB 자동완성이 작동하지 않는다면 **~/.inputrc 파일**을 생성하는 것이 가장 확실한 해결책입니다.

```bash
# Quick Setup (한 줄로 설정)
echo -e "set editing-mode emacs\nTAB: complete\nset show-all-if-ambiguous on" > ~/.inputrc
```

그래도 안 되면 Issue를 열어주세요! 🐛

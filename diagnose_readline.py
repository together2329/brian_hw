"""
Readline 진단 도구
"""

import sys
import os

print("=" * 70)
print("🔍 Readline 진단")
print("=" * 70)

# 1. Readline 모듈 확인
try:
    import readline
    print("\n✅ readline 모듈: 로드 성공")
    print(f"   위치: {readline.__file__}")
except ImportError:
    print("\n❌ readline 모듈: 로드 실패")
    print("   → readline이 없는 환경입니다")
    sys.exit(1)

# 2. Backend 확인
print("\n🔧 Backend 확인:")
backend = "Unknown"
try:
    readline.parse_and_bind("tab: complete")
    backend = "GNU Readline"
    print(f"   ✅ {backend}")
except Exception as e:
    print(f"   ❌ GNU Readline 실패: {e}")
    try:
        readline.parse_and_bind("bind ^I rl_complete")
        backend = "libedit (macOS)"
        print(f"   ✅ {backend}")
    except Exception as e2:
        print(f"   ❌ libedit 실패: {e2}")
        backend = "Unknown/Broken"

# 3. inputrc 확인
print("\n📄 ~/.inputrc 파일:")
inputrc = os.path.expanduser("~/.inputrc")
if os.path.exists(inputrc):
    print(f"   ✅ 존재함: {inputrc}")
    with open(inputrc) as f:
        content = f.read()
        print(f"   내용 ({len(content)} bytes):")
        for line in content.split('\n')[:10]:
            if line.strip() and not line.startswith('#'):
                print(f"      {line}")
else:
    print(f"   ❌ 없음: {inputrc}")
    print(f"   → 자동완성이 작동하지 않을 수 있습니다")

# 4. 환경 변수 확인
print("\n🌍 환경 변수:")
inputrc_env = os.environ.get('INPUTRC')
if inputrc_env:
    print(f"   INPUTRC={inputrc_env}")
else:
    print(f"   INPUTRC 설정 안됨 (기본값 사용)")

# 5. 실제 자동완성 테스트
print("\n🧪 자동완성 테스트:")

commands = ["/help", "/status", "/clear", "/context"]

def completer(text, state):
    options = [cmd for cmd in commands if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    return None

readline.set_completer(completer)
readline.set_completer_delims(' \t\n')

# Test completer function directly
test_cases = [
    ("/h", 0),  # Should return "/help"
    ("/c", 0),  # Should return "/clear"
    ("/c", 1),  # Should return "/context"
]

print("\n   Completer 함수 직접 테스트:")
for text, state in test_cases:
    result = completer(text, state)
    if result:
        print(f"   ✅ completer('{text}', {state}) → '{result}'")
    else:
        print(f"   ⚠️  completer('{text}', {state}) → None")

# 6. 권장 사항
print("\n" + "=" * 70)
print("📋 진단 결과")
print("=" * 70)
print(f"Backend: {backend}")

if backend == "libedit (macOS)":
    print("\n⚠️  macOS libedit 감지!")
    print("   TAB 자동완성이 작동하지 않을 수 있습니다.")
    print()
    print("💡 해결 방법:")
    print()
    if not os.path.exists(inputrc):
        print("   1. ~/.inputrc 파일 생성:")
        print("      cat > ~/.inputrc << 'EOF'")
        print("      set editing-mode emacs")
        print("      TAB: complete")
        print("      set show-all-if-ambiguous on")
        print("      EOF")
        print()
    print("   2. 새 터미널 열기")
    print()
    print("   3. 다시 테스트")
    print()
    print("   여전히 안 되면:")
    print("   → Ctrl+D를 누르면 자동완성 목록이 표시될 수 있습니다")
    print("   → 또는 readline 대신 다른 방법 사용")

elif backend == "GNU Readline":
    print("\n✅ GNU Readline 감지!")
    print("   TAB 자동완성이 정상 작동해야 합니다.")
    if not os.path.exists(inputrc):
        print()
        print("💡 더 나은 경험을 위해 ~/.inputrc 파일 생성 권장")

else:
    print("\n❌ Backend를 감지할 수 없습니다!")
    print("   TAB 자동완성이 작동하지 않을 가능성이 높습니다.")
    print()
    print("💡 대안:")
    print("   → /help 명령어로 모든 커맨드 확인")
    print("   → 또는 readline 없는 버전 사용")

print("\n" + "=" * 70)

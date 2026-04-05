#!/usr/bin/env bash
# setup.sh — brian_hw agentic 환경 구성
#
# 실행: bash setup.sh
#
# 결과:
#   pane left:  modifiable_ai_agent (textual_main.py)
#   pane right: common_ai_agent     (textual_main.py)
#   ~/.config/agentic_test/surfaces.json 에 modifiable surface ref 자동 저장
#
# 이후 common_ai_agent에서 cmux_capture(), cmux_send() 등 사용 가능

set -e

# ── 경로 설정 ──────────────────────────────────────────────────────────────
ACT_DIR="$(cd "$(dirname "$0")" && pwd)"          # common_ai_agent (이 파일 위치)
MOD_DIR="/Users/brian/Desktop/Project/brian_hw_modifiable"  # modifiable_ai_agent
SURFACES_JSON="$HOME/.config/agentic_test/surfaces.json"

# ── 경로 검증 ──────────────────────────────────────────────────────────────
if [ ! -d "$MOD_DIR" ]; then
    echo "ERROR: modifiable_ai_agent 디렉터리를 찾을 수 없습니다: $MOD_DIR"
    echo "       MOD_DIR 경로를 setup.sh에서 수정하세요."
    exit 1
fi

echo "=== Agentic Setup ==="
echo "  modifiable : $MOD_DIR"
echo "  agent      : $ACT_DIR"
echo ""

# ── Step 1: modifiable_ai_agent 워크스페이스 생성 ─────────────────────────
echo "[1] modifiable_ai_agent 워크스페이스 생성..."
cmux new-workspace \
    --name "modifiable" \
    --cwd  "$MOD_DIR" \
    --command "python3 src/textual_main.py"

# Textual 앱이 뜨고 cmux가 surface를 등록할 때까지 대기
sleep 3

# ── Step 2: modifiable surface ref 자동 탐색 ──────────────────────────────
echo "[2] modifiable surface ref 탐색..."
MOD_SURFACE=$(python3 - "$MOD_DIR" <<'PYEOF'
import subprocess, json, sys

mod_dir = sys.argv[1]

result = subprocess.run(["cmux", "tree", "--json"], capture_output=True, text=True)
if result.returncode != 0:
    print(f"cmux tree --json 실패: {result.stderr}", file=sys.stderr)
    sys.exit(1)

try:
    data = json.loads(result.stdout)
except Exception as e:
    print(f"JSON 파싱 실패: {e}", file=sys.stderr)
    sys.exit(1)

def search(node):
    """재귀적으로 workspace 'modifiable'의 terminal surface ref를 탐색."""
    if isinstance(node, list):
        for item in node:
            r = search(item)
            if r:
                return r
    elif isinstance(node, dict):
        # workspace named "modifiable" 안의 terminal surface 탐색
        if node.get("type") == "workspace" and "modifiable" in (node.get("name") or ""):
            for pane in node.get("panes", []):
                for surface in pane.get("surfaces", []):
                    if surface.get("type") == "terminal":
                        ref = surface.get("ref") or surface.get("id")
                        if ref:
                            return ref
        # 재귀
        for v in node.values():
            r = search(v)
            if r:
                return r
    return None

ref = search(data)
if ref:
    print(ref)
else:
    # fallback: tree 텍스트 출력해서 사용자가 수동으로 확인하도록
    print("NOT_FOUND", file=sys.stderr)
    print("--- cmux tree 출력 ---", file=sys.stderr)
    text = subprocess.run(["cmux", "tree"], capture_output=True, text=True).stdout
    print(text, file=sys.stderr)
    sys.exit(1)
PYEOF
)

if [ $? -ne 0 ] || [ -z "$MOD_SURFACE" ]; then
    echo ""
    echo "ERROR: surface ref 자동 탐색 실패."
    echo "       위의 cmux tree 출력에서 modifiable_ai_agent의 surface ref를 확인 후"
    echo "       수동으로 실행하세요:"
    echo "         python3 -c \"import json,pathlib; p=pathlib.Path('$SURFACES_JSON'); d=json.loads(p.read_text()) if p.exists() else {}; d['modifiable_surface']='surface:XX'; p.write_text(json.dumps(d,indent=2))\""
    exit 1
fi

echo "    발견: $MOD_SURFACE"

# ── Step 3: surfaces.json 저장 ────────────────────────────────────────────
echo "[3] surfaces.json 저장..."
mkdir -p "$(dirname "$SURFACES_JSON")"
python3 - "$SURFACES_JSON" "$MOD_SURFACE" <<'PYEOF'
import json, pathlib, sys

path = pathlib.Path(sys.argv[1])
ref  = sys.argv[2]

data = json.loads(path.read_text()) if path.exists() else {}
data["modifiable_surface"] = ref
path.write_text(json.dumps(data, indent=2))
print(f"    저장: {ref} → {path}")
PYEOF

# ── Step 4: common_ai_agent 실행 (오른쪽 새 pane) ─────────────────────────
echo "[4] common_ai_agent 시작 (오른쪽 pane)..."
cmux new-pane --direction right
sleep 1
cmux send "cd '$ACT_DIR' && python3 src/textual_main.py"

echo ""
echo "=== Setup 완료 ==="
echo "  modifiable surface : $MOD_SURFACE"
echo "  surfaces.json      : $SURFACES_JSON"
echo ""
echo "  이제 common_ai_agent에서 cmux_capture(), cmux_send() 등을 바로 사용할 수 있습니다."

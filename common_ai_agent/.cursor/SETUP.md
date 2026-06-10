# .cursor 전달본 — 도구 설치 가이드

`.cursor` 팩을 돌리는 데 필요한 도구 설치법. OS별로 골라서 따라간다.
검증된 버전(이 팩이 실제로 돌아간 환경): **Python 3.9+, Icarus Verilog 12.0,
cocotb 1.9.2, (선택) Verilator 5.x**. 시뮬레이터는 **icarus(iverilog)** 를 쓴다.

---

## macOS (Homebrew)

```bash
# Homebrew 없으면: https://brew.sh
brew install python@3.12 icarus-verilog verilator   # verilator는 선택(lint)
python3 -m pip install --upgrade pip
python3 -m pip install cocotb cocotb-bus pyyaml
```

확인:
```bash
python3 --version        # 3.9 이상
iverilog -V | head -1     # Icarus Verilog version 12.x
python3 -c "import cocotb; print(cocotb.__version__)"   # 1.9+
```

---

## Linux (Debian/Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip iverilog verilator
python3 -m pip install --upgrade pip
python3 -m pip install cocotb cocotb-bus pyyaml
```

Fedora/RHEL:
```bash
sudo dnf install -y python3 python3-pip iverilog verilator
python3 -m pip install cocotb cocotb-bus pyyaml
```

---

## Windows

가장 안정적인 경로는 **WSL2 (Ubuntu)** — 위 Linux 절차를 그대로 따른다:

```powershell
wsl --install -d Ubuntu      # 재부팅 후 Ubuntu 셸에서 Linux 절차 실행
```

WSL 없이 네이티브로 가려면:
- Python: https://www.python.org/downloads/ (설치 시 "Add to PATH" 체크)
- Icarus Verilog: http://bleyer.org/icarus/ (Windows 바이너리)
- `pip install cocotb cocotb-bus pyyaml`
- 단, iverilog/cocotb 조합은 Windows 네이티브에서 종종 깨진다 → **WSL2 권장**.

---

## 설치 후 — 팩 스모크 (1분)

프로젝트 루트(`.cursor`가 있는 곳)에서:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py --help   # usage → OK
python3 .cursor/workflow/sim/scripts/check_sim_disk.py ghost_ip          # FAIL verdict → OK
mkdir demo_ip && python3 .cursor/scripts/ip_wiki.py init demo_ip \
  && python3 .cursor/scripts/ip_wiki.py check demo_ip                    # ip_wiki PASS → OK
```

실제 cocotb 시뮬이 도는지 최종 확인(캠페인 IP가 함께 전달된 경우):
```bash
python3 <ip>/tb/cocotb/test_runner.py    # TESTS=1 PASS=1 → 시뮬 체인 정상
```

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `iverilog: command not found` | 설치 후 새 셸 열기 / PATH 확인 |
| cocotb `ValueError: Unable to accurately represent 10(ns)...` | RTL에 `` `timescale 1ns/1ps `` 누락 — KNOWN_TRAPS 참조 |
| cocotb VPI 로드 실패 (`.vpl` vs `.vpi`) | `cocotb.runner`(test_runner.py)를 쓰면 자동 처리. 직접 vvp 호출 금지 |
| `No top level modules` | `stage_gate sim`의 알려진 버그 — `test_runner.py` 직접 실행으로 우회 (KNOWN_TRAPS) |
| LLM 저작 스테이지 실패/멈춤 | provider 키 미설정. 결정론적 게이트/시뮬은 키 없이 동작 |

LLM 저작(ssot→fl 자동 생성)을 쓰려면 provider 키를 환경변수로 설정해야 한다.
키 없이도 게이트·시뮬레이션은 전부 돈다.

자세한 사용법은 `DELIVERY.md`, 함정은 `skills/rocev-chain/KNOWN_TRAPS.md` 참조.

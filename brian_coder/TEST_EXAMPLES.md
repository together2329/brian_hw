# Brian Coder 테스트 예시

## 🚀 빠른 시작

### 1. API 키 설정
```bash
# OpenAI 사용 시
export LLM_API_KEY="sk-proj-YOUR_KEY_HERE"

# 또는 OpenRouter 무료 모델 사용 시
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="sk-or-v1-YOUR_KEY_HERE"
export LLM_MODEL_NAME="meta-llama/llama-3.3-70b-instruct:free"
```

---

## 📝 기본 테스트

### Test 1: 간단한 질문
```bash
python3 main.py --prompt "What is 2+2?"
```

**예상 결과:**
```
Agent: The result of 2 + 2 is 4.
```

---

### Test 2: 파일 읽기
```bash
python3 main.py --prompt "Read config.py and tell me what model is configured"
```

**예상 결과:**
```
Action: read_file(path="config.py")
Observation: [파일 내용]
Agent: The configured model is gpt-4o-mini.
```

---

### Test 3: 파일 생성 (Single line)
```bash
python3 main.py --prompt "Create a file named test.txt with content 'Hello World'"
```

**예상 결과:**
```
Action: write_file(path="test.txt", content="Hello World")
Observation: Successfully wrote to 'test.txt'.
```

---

## 🔧 Verilog 디자인 테스트

### Test 4: 카운터 설계 (Triple-quote 자동 사용)
```bash
python3 main.py --prompt "Create a simple 4-bit counter in Verilog"
```

**예상 결과:**
```
Action: write_file(path="counter.v", content="""module counter(
    input clk,
    input reset,
    output reg [3:0] count
);
    always @(posedge clk) begin
        if (reset)
            count <= 0;
        else
            count <= count + 1;
    end
endmodule
""")
```

---

### Test 5: 카운터 전체 설계 + 시뮬레이션
```bash
python3 main.py --prompt "Design and simulate an 8-bit counter in Verilog.

Requirements:
1. Create counter.v with 8-bit synchronous counter
2. Create counter_tb.v testbench with clock and reset
3. Compile with iverilog
4. Run simulation and show results"
```

**예상 작업:**
1. ✅ counter.v 생성
2. ✅ counter_tb.v 생성
3. ✅ `iverilog -o counter_sim counter.v counter_tb.v` 실행
4. ✅ `vvp counter_sim` 실행
5. ✅ 시뮬레이션 결과 출력

---

### Test 6: FIFO 설계
```bash
python3 main.py --prompt "Create a 4-entry FIFO in Verilog with read/write pointers"
```

---

## 🐍 Python 코드 테스트

### Test 7: Python 스크립트 생성
```bash
python3 main.py --prompt "Create a Python script that prints numbers 1 to 10"
```

---

### Test 8: 복잡한 Python 프로그램
```bash
python3 main.py --prompt "Create a Python class for a simple calculator with add, subtract, multiply, divide methods"
```

---

## 🔍 디버깅 테스트

### Test 9: 코드 분석
```bash
python3 main.py --prompt "Read counter.v and explain how it works"
```

---

### Test 10: 에러 수정
```bash
# 먼저 에러가 있는 파일 생성
echo "module bad;" > bad.v

python3 main.py --prompt "Read bad.v, find syntax errors, and fix them"
```

---

## 🛠️ 복합 작업 테스트

### Test 11: 프로젝트 생성
```bash
python3 main.py --prompt "Create a simple Verilog project:
1. Create a 16-bit adder module (adder.v)
2. Create a testbench (adder_tb.v)
3. Compile with iverilog
4. Run simulation
5. Show the result"
```

---

### Test 12: 디렉토리 탐색 + 파일 수정
```bash
python3 main.py --prompt "List all .v files in current directory, then add a comment header to each one"
```

---

## 💻 셸 명령 테스트

### Test 13: 파일 검색
```bash
python3 main.py --prompt "Find all Python files in the current directory and count lines in each"
```

---

### Test 14: Git 작업
```bash
python3 main.py --prompt "Show me the git status and list recent commits"
```

---

## 🎨 고급 테스트

### Test 15: SPI Controller 설계
```bash
python3 main.py --prompt "Design a simple SPI master controller in Verilog with:
- 8-bit data width
- CPOL=0, CPHA=0
- Configurable clock divider
- Ready/valid handshake

Create the module and a testbench, then simulate it."
```

---

### Test 16: 파서 테스트 (Triple-quote)
```bash
python3 main.py --prompt "Create a Python file with a multi-line docstring"
```

**예상 결과:**
```python
Action: write_file(path="example.py", content="""
def my_function():
    '''
    This is a multi-line
    docstring example
    '''
    pass
""")
```

---

## 🔄 대화형 모드 테스트

### Test 17: 대화형 세션
```bash
python3 main.py
```

대화 예시:
```
You: Create counter.v
Agent: [파일 생성]

You: Now create a testbench for it
Agent: [테스트벤치 생성]

You: Compile and simulate
Agent: [컴파일 및 시뮬레이션]

You: What was the final count?
Agent: The final count was 20.

You: exit
```

---

## 🧪 파서 기능 검증

### Test 18: Triple-quote 파싱
```bash
python3 test_parser.py
```

**예상 결과:**
```
======================================================================
개선된 파서 테스트
======================================================================
[Test 1] 기본 인자 파싱 ✅
[Test 2] 여러 인자 파싱 ✅
[Test 3] Triple-quoted string 파싱 ✅
...
모든 테스트 통과! ✅
```

---

### Test 19: Tool Demo
```bash
python3 tool_demo.py
```

**Tool Call 동작 원리 확인**

---

### Test 20: 보안 비교
```bash
python3 eval_danger_demo.py
```

**eval() vs 안전한 파서 비교**

---

## ⚙️ 환경 변수 테스트

### Test 21: Rate Limiting 조정
```bash
export RATE_LIMIT_DELAY=0
python3 main.py --prompt "Create hello.py"
```

**결과:** Rate limit 없이 즉시 실행

---

### Test 22: Max Iterations 조정
```bash
export MAX_ITERATIONS=10
python3 main.py --prompt "Design a complex state machine"
```

**결과:** 최대 10번 반복 가능

---

### Test 23: History 비활성화
```bash
export SAVE_HISTORY=false
python3 main.py --prompt "Test without history"
```

**결과:** conversation_history.json 생성 안 됨

---

## 📊 성능 테스트

### Test 24: 큰 파일 생성
```bash
python3 main.py --prompt "Create a Verilog module with 100 registers"
```

---

### Test 25: 여러 파일 동시 생성
```bash
python3 main.py --prompt "Create 5 different Verilog modules: adder, subtractor, multiplier, divider, and comparator"
```

---

## 🎯 실전 시나리오

### Test 26: 완전한 프로젝트 워크플로우
```bash
python3 main.py --prompt "I want to create a complete UART transmitter project:

1. Create uart_tx.v - UART transmitter module
   - 8-bit data
   - Configurable baud rate
   - Start/stop bits
   - Busy flag

2. Create uart_tx_tb.v - Comprehensive testbench
   - Test sending 0x55, 0xAA, 0xFF
   - Monitor waveforms

3. Compile with iverilog
4. Run simulation
5. Analyze the results and tell me if it works correctly"
```

---

## 💡 팁

### 성공적인 프롬프트 작성법

**좋은 예:**
```
"Create counter.v with an 8-bit synchronous counter"
```

**더 좋은 예:**
```
"Design an 8-bit synchronous counter in Verilog with:
- Clock and reset inputs
- Active-high reset
- Increment on positive edge
Then create a testbench and simulate it"
```

**최고의 예:**
```
"Design and simulate an 8-bit synchronous counter.

Requirements:
1. Create counter.v with triple-quoted content
2. Include proper reset logic
3. Create testbench with VCD output
4. Compile with iverilog
5. Run simulation
6. Show final count value

Execute all steps automatically."
```

---

## 🐛 트러블슈팅

### 파싱 실패 시
```bash
# DEBUG 출력 확인
python3 main.py --prompt "..." 2>&1 | grep DEBUG
```

### API 에러 시
```bash
# API 키 확인
echo $LLM_API_KEY

# Base URL 확인
echo $LLM_BASE_URL
```

### Rate Limit 에러 시
```bash
# 대기 시간 늘리기
export RATE_LIMIT_DELAY=10
```

---

## 📈 기대 결과

모든 테스트가 성공하면:
- ✅ Triple-quote 파싱 정상 동작
- ✅ Multi-line 코드 생성 가능
- ✅ Verilog/Python/Shell 작업 자동화
- ✅ 파일 생성/읽기/실행 완벽 동작
- ✅ ReAct loop 정상 작동

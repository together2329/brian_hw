# API 설정 가이드

## 🔑 OpenAI ChatGPT 사용하기 (기본 설정)

### 1. API 키 발급
1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. API 키 복사 (sk-proj-... 형식)

### 2. config.py 수정
```python
API_KEY = os.getenv("LLM_API_KEY", "sk-proj-YOUR_ACTUAL_KEY_HERE")
```

### 3. 환경변수로 설정 (권장)
```bash
export LLM_API_KEY="sk-proj-YOUR_ACTUAL_KEY_HERE"
python3 main.py
```

### 4. 모델 선택
- `gpt-4o-mini` (기본, 저렴하고 빠름) ✅
- `gpt-4o` (강력하지만 비쌈)
- `gpt-3.5-turbo` (구형, 가장 저렴)

```python
# config.py에서 변경
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o")
```

또는 환경변수:
```bash
export LLM_MODEL_NAME="gpt-4o"
```

---

## 🌐 OpenRouter 사용하기 (무료 모델 지원)

### config.py 수정
```python
# OpenAI 설정 주석 처리
# BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
# API_KEY = os.getenv("LLM_API_KEY", "your-openai-api-key-here")
# MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

# OpenRouter 활성화
BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("LLM_API_KEY", "sk-or-v1-...")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct:free")
```

### 무료 모델
- `meta-llama/llama-3.3-70b-instruct:free`
- `google/gemini-flash-1.5:free`
- `qwen/qwen-2-7b-instruct:free`

---

## 🔧 고급 설정

### Rate Limiting 조정
```bash
# ChatGPT는 rate limit이 높으므로 0으로 설정 가능
export RATE_LIMIT_DELAY=0

# 무료 모델은 5초 권장
export RATE_LIMIT_DELAY=5
```

### 최대 반복 횟수 조정
```bash
# 복잡한 작업은 더 많은 반복 필요
export MAX_ITERATIONS=10
```

### 히스토리 비활성화
```bash
export SAVE_HISTORY=false
```

---

## 💰 비용 비교

### OpenAI ChatGPT
| 모델 | 입력 (1M tokens) | 출력 (1M tokens) |
|------|------------------|------------------|
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4o | $2.50 | $10.00 |
| gpt-3.5-turbo | $0.50 | $1.50 |

### OpenRouter
| 모델 | 비용 |
|------|------|
| Llama 3.3 70B (free) | **무료** |
| Gemini Flash 1.5 (free) | **무료** |

---

## 🚀 빠른 시작

### OpenAI 사용
```bash
# 1. API 키 설정
export LLM_API_KEY="sk-proj-YOUR_KEY"

# 2. Rate limit 제거 (선택사항)
export RATE_LIMIT_DELAY=0

# 3. 실행
python3 main.py
```

### OpenRouter 사용
```bash
# 1. config.py에서 OpenRouter 활성화 (주석 해제)

# 2. 실행 (기본 설정 사용)
python3 main.py
```

---

## 🔍 테스트

실행 후:
```
You: Read config.py and tell me what's inside
```

정상 동작하면:
```
Agent (Thinking): Thought: I need to read the config.py file.
Action: read_file(path="config.py")
[System] Executing read_file...
[System] Observation: import os...
```

---

## ❓ 문제 해결

### "HTTP Error 401"
- API 키가 잘못되었거나 만료됨
- `config.py` 또는 환경변수 확인

### "HTTP Error 429"
- Rate limit 초과
- `RATE_LIMIT_DELAY`를 늘리세요 (5초 이상)

### "Model not found"
- 모델 이름 확인
- OpenAI: `gpt-4o-mini`, `gpt-4o`
- OpenRouter: `meta-llama/llama-3.3-70b-instruct:free`

### Action이 파싱되지 않음
- 모델이 형식을 지키지 않음
- gpt-4o-mini 이상 권장 (gpt-3.5-turbo는 불안정할 수 있음)

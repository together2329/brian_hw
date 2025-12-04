"""
임베딩 API 호출 테스트

실제 OpenAI Embedding API를 호출해서 임베딩을 받아옵니다.
"""
import json
import urllib.request
import urllib.error
import os

# .env 파일 로드
def load_env():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value and key not in os.environ:
                        os.environ[key] = value

load_env()

# 설정
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY") or os.getenv("LLM_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

print("\n" + "="*60)
print("임베딩 API 호출 테스트")
print("="*60 + "\n")

print(f"API URL: {EMBEDDING_BASE_URL}")
print(f"Model: {EMBEDDING_MODEL}")
print(f"API Key: {'✓ 설정됨' if EMBEDDING_API_KEY else '❌ 없음'}")
print()

if not EMBEDDING_API_KEY:
    print("❌ API 키가 설정되지 않았습니다!")
    print("   .env 파일에 EMBEDDING_API_KEY 또는 LLM_API_KEY를 설정하세요.\n")
    exit(1)

# 테스트 텍스트
test_text = "Hello, this is a test for embedding API"

print(f"테스트 텍스트: \"{test_text}\"\n")
print("API 호출 중...\n")

try:
    # API 요청 준비
    url = f"{EMBEDDING_BASE_URL}/embeddings"

    payload = {
        "input": test_text,
        "model": EMBEDDING_MODEL
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {EMBEDDING_API_KEY}"
    }

    # HTTP 요청
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    # API 호출
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))

    # 결과 파싱
    embedding = result['data'][0]['embedding']

    print("="*60)
    print("✅ API 호출 성공!")
    print("="*60 + "\n")

    print(f"임베딩 차원: {len(embedding)}")
    print(f"첫 10개 값: {embedding[:10]}")
    print()

    # 토큰 사용량
    if 'usage' in result:
        usage = result['usage']
        print(f"사용 토큰: {usage.get('total_tokens', 'N/A')}")
        print()

    print("="*60)
    print("🎉 임베딩 API 정상 작동!")
    print("="*60 + "\n")

except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8')
    print("="*60)
    print("❌ API 호출 실패 (HTTP Error)")
    print("="*60 + "\n")
    print(f"상태 코드: {e.code}")
    print(f"에러 메시지:\n{error_body}\n")

    if e.code == 401:
        print("💡 API 키가 잘못되었습니다. .env 파일을 확인하세요.\n")
    elif e.code == 404:
        print("💡 API URL이 잘못되었습니다. EMBEDDING_BASE_URL을 확인하세요.\n")

except urllib.error.URLError as e:
    print("="*60)
    print("❌ 네트워크 연결 실패")
    print("="*60 + "\n")
    print(f"에러: {e.reason}\n")

except Exception as e:
    print("="*60)
    print("❌ 예상치 못한 에러")
    print("="*60 + "\n")
    print(f"에러: {e}\n")
    import traceback
    traceback.print_exc()

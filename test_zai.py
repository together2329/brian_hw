from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

api_key = os.getenv("ZAI_API_KEY")
if not api_key or api_key.startswith("your_"):
    raise ValueError("Set ZAI_API_KEY in .env first")

# Coding Plan uses a different base URL
client = OpenAI(
    api_key=api_key,
    base_url="https://api.z.ai/api/coding/paas/v4/",
)

print("Testing Z.AI Coding Plan...")

response = client.chat.completions.create(
    model="glm-4.5",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
)

print("Model:", response.model)
print("Response:", response.choices[0].message.content)
print("Tokens used:", response.usage.total_tokens)

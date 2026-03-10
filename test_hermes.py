from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=10.0
)

try:
    t0 = time.time()
    response = client.chat.completions.create(
        model="nousresearch/hermes-3-llama-3.1-405b:free",
        messages=[{"role": "user", "content": "Hola"}],
        max_tokens=10
    )
    print(f"SUCCESS ({time.time()-t0:.2f}s)! Response: {response.choices[0].message.content.strip()}")
except Exception as e:
    print(f"FAILED ({time.time()-t0:.2f}s): {type(e).__name__} - {e}")

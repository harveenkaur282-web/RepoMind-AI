import requests
from backend.app.core.config import get_settings

settings = get_settings()
api_key = settings.openrouter_api_key
url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "openai/gpt-oss-20b",
    "messages": [
        {"role": "user", "content": "Hello, is this working?"}
    ],
    "max_tokens": 1000
}

response = requests.post(url, headers=headers, json=payload)
print("Status Code:", response.status_code)
print("Response text:", response.text)

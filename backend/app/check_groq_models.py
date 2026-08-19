import requests

from backend.app.core.config import get_settings

settings = get_settings()
api_key = settings.groq_api_key
url = "https://api.groq.com/openai/v1/models"

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

response = requests.get(url, headers=headers)
print("Available Groq Models:")
for model in response.json().get("data", []):
    print(f"- {model.get('id')}")

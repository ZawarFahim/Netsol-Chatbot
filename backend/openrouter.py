import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")


def get_ai_response(messages: list, tools=None):
    if not API_KEY:
        raise ValueError("Missing OPENROUTER_API_KEY")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "RAG Tool Chatbot"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()

    except Exception as e:
        return {
            "error": str(e)
        }
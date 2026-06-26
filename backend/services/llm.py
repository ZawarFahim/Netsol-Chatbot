import requests
import os

def get_ai_response(messages: list, tools=None):
    payload = {"model": "google/gemini-2.5-flash:free", "messages": messages}
    if tools:
        payload.update({"tools": tools, "tool_choice": "auto"})
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "RAG Tool Chatbot"
            },
            json=payload,
            timeout=60
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}
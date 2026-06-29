import os
from groq import Groq

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq()
    return _client

def get_ai_response(messages: list, tools=None):
    try:
        kwargs = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        completion = get_client().chat.completions.create(**kwargs)
        
        message = completion.choices[0].message
        message_dict = {
            "role": message.role or "assistant",
            "content": message.content or ""
        }
        if hasattr(message, "tool_calls") and message.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]

        usage_dict = {}
        if hasattr(completion, "usage") and completion.usage:
            usage_dict = {
                "prompt_tokens": getattr(completion.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(completion.usage, "completion_tokens", 0),
                "total_tokens": getattr(completion.usage, "total_tokens", 0)
            }

        return {
            "choices": [{"message": message_dict}],
            "usage": usage_dict
        }
    except Exception as e:
        return {"error": str(e)}
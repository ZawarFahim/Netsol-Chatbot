import json
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.models import ChatRequest
from backend.openrouter import get_ai_response
from backend.db import chat_collection
from datetime import datetime, timezone
from backend.tools import rag_tool
from backend.audio import transcribe_audio_local, text_to_speech_kokoro

router = APIRouter()
USER_ID = "2024494"

tools = [
    {
        "type": "function",
        "function": {
            "name": "rag_tool",
            "description": "Fetch relevant documents from knowledge base",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]

def execute_llm_pipeline(user_message: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Use tools when needed."}
    ]
    
    # Fetch recent chat history from MongoDB (sort descending to get newest, then reverse for chronological order)
    try:
        history = list(chat_collection.find({"user_id": USER_ID}).sort("created_at", -1).limit(10))
        for msg in reversed(history):
            messages.append({"role": msg["role"], "content": msg["content"]})
    except Exception as e:
        print("Failed to fetch history:", e)
        
    messages.append({"role": "user", "content": user_message})
    
    response = get_ai_response(messages, tools=tools)
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
        
    message = response["choices"][0]["message"]
    
    if "tool_calls" in message:
        tool_call = message["tool_calls"][0]
        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])
        
        tool_result = ""
        if name == "rag_tool":
            tool_result = rag_tool(args["query"])
            
        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": tool_result
        })
        
        final_response = get_ai_response(messages)
        return final_response["choices"][0]["message"]["content"]
    
    return message["content"]

def persist_to_db(user_msg: str, ai_msg: str):
    try:
        now = datetime.now(timezone.utc)
        chat_collection.insert_one({
            "user_id": USER_ID, "role": "user", "content": user_msg, "created_at": now
        })
        chat_collection.insert_one({
            "user_id": USER_ID, "role": "assistant", "content": ai_msg, "created_at": now
        })
    except Exception as e:
        print("DB logging trace error:", e)

@router.post("/chat")
def chat(req: ChatRequest):
    ai_reply = execute_llm_pipeline(req.message)
    persist_to_db(req.message, ai_reply)
    
    response_data = {"response": ai_reply}
    if req.generate_audio:
        bot_audio_bytes = text_to_speech_kokoro(ai_reply)
        response_data["bot_audio"] = base64.b64encode(bot_audio_bytes).decode("utf-8")
        
    return response_data

@router.post("/chat-audio")
async def chat_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        user_message = transcribe_audio_local(audio_bytes, file.filename)
        
        if not user_message.strip():
            return {"error": "Could not extract speech clearly from the request segment."}
            
        ai_reply = execute_llm_pipeline(user_message)
        persist_to_db(user_message, ai_reply)
        
        bot_audio_bytes = text_to_speech_kokoro(ai_reply)
        bot_audio_base64 = base64.b64encode(bot_audio_bytes).decode("utf-8")
        
        return {
            "user_text": user_message,
            "bot_text": ai_reply,
            "bot_audio": bot_audio_base64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
def clear_chat():
    try:
        chat_collection.delete_many({"user_id": USER_ID})
        return {"status": "success", "message": "Chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
import json
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from backend.schemas import ChatRequest, SessionCreate
from backend.services.llm import get_ai_response
from backend.database import chat_collection, sessions_collection
from datetime import datetime, timezone
from backend.rag.tools import rag_tool
from backend.services.audio import transcribe_audio_local, text_to_speech_kokoro
from backend.services.auth import decode_token

router = APIRouter()

def execute_llm_pipeline(user_message: str, user_id: str, session_id: str) -> str:
    messages = [{"role": "system", "content": "You are a helpful AI Assistant. You have access to the user's uploaded documents (PDFs, text) via the rag_tool. If the user asks about a document, PDF, or specific knowledge, you MUST call rag_tool with a search query to find the answer."}]
    
    query = {"user_id": user_id}
    if session_id: query["session_id"] = session_id
        
    for msg in reversed(list(chat_collection.find(query).sort("created_at", -1).limit(10))):
        role = msg.get("role")
        if not role:
            # Fallback for old schema
            role = "assistant" if "bot" in msg and msg["bot"] == msg.get("content") else "user"
        content = msg.get("content", msg.get("bot", msg.get("user", "")))
        messages.append({"role": role, "content": content})
        
    messages.append({"role": "user", "content": user_message})
    
    tools = [{
        "type": "function",
        "function": {
            "name": "rag_tool",
            "description": "Search the user's uploaded documents and PDFs for relevant text.",
            "parameters": {
                "type": "object", 
                "properties": {"query": {"type": "string", "description": "The search query to look up in the documents"}}, 
                "required": ["query"]
            }
        }
    }]
    response = get_ai_response(messages, tools=tools)
    if "error" in response: raise HTTPException(status_code=500)
        
    message = response["choices"][0]["message"]
    if "tool_calls" in message:
        tool_call = message["tool_calls"][0]
        args = json.loads(tool_call["function"]["arguments"])
        
        messages.append(message)
        messages.append({"role": "tool", "tool_call_id": tool_call["id"], "content": rag_tool(args["query"], user_id)})
        
        return get_ai_response(messages)["choices"][0]["message"]["content"]
    
    return message["content"]

def persist_to_db(user_msg: str, ai_msg: str, user_id: str, session_id: str, login_method: str):
    import time
    now_user = datetime.now(timezone.utc)
    time.sleep(0.001)  # Ensure distinct timestamps for correct chronological sorting
    now_ai = datetime.now(timezone.utc)
    
    chat_collection.insert_many([
        {"user_id": user_id, "session_id": session_id, "role": "user", "content": user_msg, "created_at": now_user, "login_method": login_method},
        {"user_id": user_id, "session_id": session_id, "role": "assistant", "content": ai_msg, "created_at": now_ai, "login_method": login_method}
    ])

@router.post("/chat")
def chat(req: ChatRequest, token_data: dict = Depends(decode_token)):
    user_id = token_data["user_id"]
    login_method = token_data["login_method"]
    ai_reply = execute_llm_pipeline(req.message, user_id, req.session_id)
    persist_to_db(req.message, ai_reply, user_id, req.session_id, login_method)
    
    res = {"response": ai_reply}
    if req.generate_audio:
        res["bot_audio"] = base64.b64encode(text_to_speech_kokoro(ai_reply)).decode("utf-8")
    return res

@router.post("/chat-audio")
async def chat_audio(file: UploadFile = File(...), session_id: str = Form(None), token_data: dict = Depends(decode_token)):
    user_id = token_data["user_id"]
    login_method = token_data["login_method"]
    user_message = transcribe_audio_local(await file.read(), file.filename)
    if not user_message.strip():
        raise HTTPException(status_code=400)
        
    ai_reply = execute_llm_pipeline(user_message, user_id, session_id)
    persist_to_db(user_message, ai_reply, user_id, session_id, login_method)
    
    return {
        "user_text": user_message,
        "bot_text": ai_reply,
        "bot_audio": base64.b64encode(text_to_speech_kokoro(ai_reply)).decode("utf-8")
    }

@router.get("/chat/sessions")
def get_sessions(token_data: dict = Depends(decode_token)):
    user_id = token_data["user_id"]
    sessions = list(sessions_collection.find({"user_id": user_id}).sort("created_at", -1))
    for s in sessions:
        s["_id"] = str(s["_id"])
        s["id"] = s["session_id"]
        if "created_at" in s:
            if isinstance(s["created_at"], datetime):
                s["ts"] = int(s["created_at"].timestamp() * 1000)
            else:
                s["ts"] = s["created_at"]
    return {"sessions": sessions}

@router.post("/chat/sessions")
def create_session(session_req: SessionCreate, token_data: dict = Depends(decode_token)):
    user_id = token_data["user_id"]
    login_method = token_data["login_method"]
    if not sessions_collection.find_one({"user_id": user_id, "session_id": session_req.session_id}):
        sessions_collection.insert_one({
            "session_id": session_req.session_id,
            "user_id": user_id,
            "title": session_req.title,
            "login_method": login_method,
            "created_at": datetime.now(timezone.utc)
        })
    return {"message": "Success"}

@router.delete("/clear")
def clear_chat(token_data: dict = Depends(decode_token)):
    user_id = token_data["user_id"]
    chat_collection.delete_many({"user_id": user_id})
    sessions_collection.delete_many({"user_id": user_id})
    return {"status": "success"}

@router.get("/chat/{session_id}")
def get_chat_history(session_id: str, token_data: dict = Depends(decode_token)):
    user_id = token_data["user_id"]
    history = list(chat_collection.find({"user_id": user_id, "session_id": session_id}).sort("created_at", 1))
    for msg in history: 
        msg["_id"] = str(msg["_id"])
        if "role" not in msg:
            if "bot" in msg:
                msg["role"] = "assistant"
                msg["content"] = msg["bot"]
            elif "user" in msg:
                msg["role"] = "user"
                msg["content"] = msg["user"]
    return {"history": history}
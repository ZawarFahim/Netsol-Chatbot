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

from backend.services.tracing import start_trace
from backend.services.guardrails import check_input_guardrail, check_output_guardrail
from backend.services.evaluations import run_evaluation
from langfuse import propagate_attributes

router = APIRouter()

def execute_llm_pipeline(user_message: str, user_id: str, session_id: str) -> str:
    input_warning = check_input_guardrail(user_message)
    if input_warning:
        try:
            with propagate_attributes(user_id=user_id, session_id=session_id):
                trace = start_trace("chat-pipeline", user_id, session_id)
                if trace:
                    trace.score(name="safety", value=0.0, comment="Input guardrail violation")
                    trace.end()
        except Exception as e:
            print(f"Error logging guardrail violation to Langfuse: {e}")
        return input_warning

    with propagate_attributes(user_id=user_id, session_id=session_id):
        trace = None
        try:
            trace = start_trace("chat-pipeline", user_id, session_id)
        except Exception as e:
            print(f"Error starting Langfuse trace: {e}")

        messages = [{"role": "system", "content": "You are a helpful AI Assistant. You have access to the user's uploaded documents (PDFs, text) via the rag_tool. If the user asks about a document, PDF, or specific knowledge, you MUST call rag_tool with a search query to find the answer."}]
        
        query = {"user_id": user_id}
        if session_id: query["session_id"] = session_id
            
        for msg in reversed(list(chat_collection.find(query).sort("created_at", -1).limit(10))):
            role = msg.get("role")
            if not role:
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
        
        generation1 = None
        if trace:
            try:
                generation1 = trace.start_observation(
                    name="llm-initial-call",
                    as_type="generation",
                    model="openai/gpt-4o-mini",
                    input=messages
                )
            except Exception as e:
                print(f"Error starting Langfuse generation1: {e}")
                
        response = get_ai_response(messages, tools=tools)
        
        if generation1:
            try:
                usage = response.get("usage", {}) if isinstance(response, dict) else {}
                usage_details = {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
                generation1.update(
                    output=response,
                    usage_details=usage_details
                )
                generation1.end()
            except Exception as e:
                print(f"Error ending Langfuse generation1: {e}")
                
        if "error" in response: 
            if trace: trace.end()
            print(f"OpenRouter Error Details: {response['error']}")
            raise HTTPException(status_code=500)
            
        message = response["choices"][0]["message"]
        rag_context = None
        
        if "tool_calls" in message:
            tool_call = message["tool_calls"][0]
            args = json.loads(tool_call["function"]["arguments"])
            
            tool_span = None
            if trace:
                try:
                    tool_span = trace.start_observation(
                        name="rag-tool-execution",
                        as_type="tool",
                        input=args["query"]
                    )
                except Exception as e:
                    print(f"Error starting Langfuse tool_span: {e}")
                    
            rag_context = rag_tool(args["query"], user_id)
            
            if tool_span:
                try:
                    tool_span.update(output=rag_context)
                    tool_span.end()
                except Exception as e:
                    print(f"Error ending Langfuse tool_span: {e}")
            
            messages.append(message)
            messages.append({"role": "tool", "tool_call_id": tool_call["id"], "content": rag_context})
            
            generation2 = None
            if trace:
                try:
                    generation2 = trace.start_observation(
                        name="llm-final-call",
                        as_type="generation",
                        model="openai/gpt-4o-mini",
                        input=messages
                    )
                except Exception as e:
                    print(f"Error starting Langfuse generation2: {e}")
                    
            response2 = get_ai_response(messages)
            
            if generation2:
                try:
                    usage2 = response2.get("usage", {}) if isinstance(response2, dict) else {}
                    usage_details2 = {
                        "input_tokens": usage2.get("prompt_tokens", 0),
                        "output_tokens": usage2.get("completion_tokens", 0),
                        "total_tokens": usage2.get("total_tokens", 0)
                    }
                    generation2.update(
                        output=response2,
                        usage_details=usage_details2
                    )
                    generation2.end()
                except Exception as e:
                    print(f"Error ending Langfuse generation2: {e}")
                    
            if "error" in response2: 
                if trace: trace.end()
                raise HTTPException(status_code=500)
            content_out = response2["choices"][0]["message"]["content"]
        else:
            content_out = message["content"]
            
        output_warning = check_output_guardrail(content_out)
        if output_warning:
            if trace:
                try:
                    trace.score(name="safety", value=0.0, comment="Output guardrail violation")
                    trace.end()
                except Exception as e:
                    print(f"Error logging output violation to Langfuse: {e}")
            return output_warning
            
        try:
            eval_score = run_evaluation(user_message, content_out, rag_context)
            if trace:
                trace.score(name="relevance-score", value=eval_score)
                trace.score(name="safety", value=1.0)
        except Exception as e:
            print(f"Error running evaluations or logging score: {e}")
            
        if trace:
            try:
                trace.end()
            except Exception as e:
                print(f"Error ending Langfuse trace: {e}")
                
        return content_out

def persist_to_db(user_msg: str, ai_msg: str, user_id: str, session_id: str, login_method: str):
    import time
    now_user = datetime.now(timezone.utc)
    time.sleep(0.001)
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
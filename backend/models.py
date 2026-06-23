from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    generate_audio: bool = False
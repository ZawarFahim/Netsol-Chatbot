from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    generate_audio: bool = False
    session_id: str = None

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str
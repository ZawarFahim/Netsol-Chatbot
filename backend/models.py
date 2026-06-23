"""
models.py
---------
Pydantic models (data shapes) for all API request bodies.
- ChatRequest:   body for /chat
- UserRegister:  body for /auth/register
- UserLogin:     body for /auth/login
"""

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    generate_audio: bool = False

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str
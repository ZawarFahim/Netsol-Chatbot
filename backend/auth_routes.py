from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
import numpy as np
from backend.db import users_collection
from backend.models import UserRegister, UserLogin
from backend.auth import hash_password, verify_password, create_token, decode_token
from backend.face_verifier import get_face_embedding, SIMILARITY_THRESHOLD

auth_router = APIRouter(prefix="/auth")

@auth_router.post("/register")
def register(user: UserRegister):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400)
    users_collection.insert_one({"username": user.username, "password": hash_password(user.password)})
    return {"message": "Account created successfully"}

@auth_router.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401)
    return {"access_token": create_token(user.username), "token_type": "bearer"}

@auth_router.get("/me")
def me(user_id: str = Depends(decode_token)):
    return {"username": user_id}

@auth_router.post("/register-face")
async def register_face(username: str = Form(...), file: UploadFile = File(...)):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=400)
    try:
        embedding = get_face_embedding(await file.read()).tolist()
        users_collection.update_one({"username": username}, {"$set": {"face_embedding": embedding}})
        return {"message": "Face ID registered successfully!"}
    except Exception:
        raise HTTPException(status_code=400)

@auth_router.post("/login-face")
async def login_face(username: str = Form(...), file: UploadFile = File(...)):
    user = users_collection.find_one({"username": username})
    if not user or not user.get("face_embedding"):
        raise HTTPException(status_code=400)
    try:
        similarity = float(np.dot(np.array(user["face_embedding"]), get_face_embedding(await file.read())))
        if similarity >= SIMILARITY_THRESHOLD:
            return {"access_token": create_token(username), "token_type": "bearer"}
        raise HTTPException(status_code=401)
    except Exception:
        raise HTTPException(status_code=400)

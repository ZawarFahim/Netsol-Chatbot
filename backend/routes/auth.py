from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
import numpy as np
from backend.database import users_collection
from backend.schemas import UserRegister, UserLogin
from backend.services.auth import hash_password, verify_password, create_token, decode_token
from backend.services.face import get_face_embedding, SIMILARITY_THRESHOLD

auth_router = APIRouter(prefix="/auth")

@auth_router.post("/register")
def register(user: UserRegister):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    users_collection.insert_one({"username": user.username, "password": hash_password(user.password), "name": user.name})
    return {"message": "Account created successfully"}

@auth_router.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": create_token(user.username, login_method="password"), "token_type": "bearer"}

@auth_router.get("/me")
def me(token_data: dict = Depends(decode_token)):
    return {"username": token_data["user_id"], "login_method": token_data["login_method"]}

@auth_router.post("/register-face")
async def register_face(username: str = Form(...), password: str = Form(...), file: UploadFile = File(...)):
    user = users_collection.find_one({"username": username})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Authentication failed")
    try:
        embedding = get_face_embedding(await file.read()).tolist()
        users_collection.update_one({"username": username}, {"$set": {"face_embedding": embedding}})
        return {"message": "Face ID registered successfully!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Face registration failed: {str(e)}")

@auth_router.post("/login-face")
async def login_face(username: str = Form(...), file: UploadFile = File(...)):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    if not user.get("face_embedding"):
        raise HTTPException(status_code=400, detail="Face ID not registered for this user")
    try:
        similarity = float(np.dot(np.array(user["face_embedding"]), get_face_embedding(await file.read())))
        if similarity >= SIMILARITY_THRESHOLD:
            return {"access_token": create_token(username, login_method="face_id"), "token_type": "bearer"}
        raise HTTPException(status_code=401, detail="Face verification failed (no match)")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Face verification failed: {str(e)}")

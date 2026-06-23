"""
auth_routes.py
--------------
API endpoints for user authentication:
- POST /auth/register  → create a new account
- POST /auth/login     → get a JWT token
- GET  /auth/me        → verify token & return current user info
"""

from fastapi import APIRouter, HTTPException, Depends
from backend.db import users_collection
from backend.models import UserRegister, UserLogin
from backend.auth import hash_password, verify_password, create_token, decode_token

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/register")
def register(user: UserRegister):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")
    users_collection.insert_one({
        "username": user.username,
        "password": hash_password(user.password)
    })
    return {"message": "Account created successfully"}


@auth_router.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(user.username)
    return {"access_token": token, "token_type": "bearer"}


@auth_router.get("/me")
def me(user_id: str = Depends(decode_token)):
    return {"username": user_id}


from fastapi import Form, File, UploadFile
import numpy as np
from backend.face_verifier import get_face_embedding, SIMILARITY_THRESHOLD

@auth_router.post("/register-face")
async def register_face(username: str = Form(...), file: UploadFile = File(...)):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=400, detail="User not found. Register with password first.")
        
    try:
        file_bytes = await file.read()
        embedding = get_face_embedding(file_bytes).tolist()
        
        users_collection.update_one(
            {"username": username},
            {"$set": {"face_embedding": embedding}}
        )
        return {"message": "Face ID registered successfully!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No face detected or verification failed: {e}")


@auth_router.post("/login-face")
async def login_face(username: str = Form(...), file: UploadFile = File(...)):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username")
        
    stored_embedding = user.get("face_embedding")
    if not stored_embedding:
        raise HTTPException(status_code=400, detail="No Face ID registered for this user.")
        
    try:
        file_bytes = await file.read()
        login_emb = get_face_embedding(file_bytes)
        
        # Calculate cosine similarity (dot product of L2 normalized vectors)
        similarity = float(np.dot(np.array(stored_embedding), login_emb))
        print(f"Face comparison similarity: {similarity:.4f} (Threshold: {SIMILARITY_THRESHOLD})")
        
        if similarity >= SIMILARITY_THRESHOLD:
            token = create_token(username)
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Face does not match registered profile.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Face verification error: {e}")


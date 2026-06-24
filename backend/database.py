import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI missing")

kwargs = {"serverSelectionTimeoutMS": 10000, "connectTimeoutMS": 10000, "retryWrites": True}
if MONGO_URI.startswith("mongodb+srv"):
    kwargs.update({"tls": True, "tlsCAFile": certifi.where()})

client = MongoClient(MONGO_URI, **kwargs)
db = client[os.getenv("DB_NAME", "voice_rag_ai")]
chat_collection, users_collection, sessions_collection = db["chats"], db["users"], db["sessions"]
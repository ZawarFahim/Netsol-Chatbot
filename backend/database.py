import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI missing")

# Dynamically enable TLS/SSL for remote Atlas (mongodb+srv) connections, disable for local.
is_atlas = MONGO_URI.startswith("mongodb+srv")
client_kwargs = {
    "serverSelectionTimeoutMS": 10000,
    "connectTimeoutMS": 10000,
    "retryWrites": True,
}
if is_atlas:
    client_kwargs["tls"] = True
    client_kwargs["tlsCAFile"] = certifi.where()
else:
    client_kwargs["tls"] = False

client = MongoClient(MONGO_URI, **client_kwargs)

db = client[os.getenv("DB_NAME", "voice_rag_ai")]
chat_collection = db["chats"]
users_collection = db["users"]
sessions_collection = db["sessions"]
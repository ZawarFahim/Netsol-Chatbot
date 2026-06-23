import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "voice_rag_ai")

if not MONGO_URI:
    raise ValueError("MONGO_URI missing")

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    retryWrites=True,
)

db = client[DB_NAME]

chat_collection = db["chats"]
memory_collection = db["memory"]
users_collection = db["users"]          # stores registered user accounts


def database_status():
    try:
        client.admin.command("ping")
        return True, "Connected"
    except Exception as e:
        return False, str(e)
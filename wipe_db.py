import os
import sys
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

# Load env variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "voice_rag_ai")

if not MONGO_URI:
    print("Error: MONGO_URI is missing in .env")
    sys.exit(1)

print(f"Connecting to database: {DB_NAME}")
# Configure connection with SSL CA file for Atlas, or fallback to local
connection_kwargs = {
    "serverSelectionTimeoutMS": 10000,
    "connectTimeoutMS": 10000,
}
if MONGO_URI.startswith("mongodb+srv"):
    connection_kwargs["tls"] = True
    connection_kwargs["tlsCAFile"] = certifi.where()

try:
    client = MongoClient(MONGO_URI, **connection_kwargs)
    db = client[DB_NAME]
    
    print("Verifying connection...")
    client.admin.command('ping')
    print("Connection: SUCCESS!")
    
    # 1. Clear users
    users_coll = db["users"]
    users_count = users_coll.count_documents({})
    users_coll.delete_many({})
    print(f"Wiped 'users' collection (removed {users_count} records).")
    
    # 2. Clear chats
    chats_coll = db["chats"]
    chats_count = chats_coll.count_documents({})
    chats_coll.delete_many({})
    print(f"Wiped 'chats' collection (removed {chats_count} records).")
    
    # 3. Clear user-uploaded vector document chunks (preserving global FAQ chunks)
    faq_coll = db["faq_vectors"]
    user_docs_count = faq_coll.count_documents({"metadata.uploaded_by": {"$exists": True}})
    faq_coll.delete_many({"metadata.uploaded_by": {"$exists": True}})
    print(f"Wiped user-uploaded documents from 'faq_vectors' (removed {user_docs_count} records).")
    
    # Keep track of global FAQ vectors
    global_docs_count = faq_coll.count_documents({})
    print(f"Preserved {global_docs_count} global FAQ vector document(s).")
    
    print("\nDatabase wipe completed successfully! You now have a completely fresh start.")

except Exception as e:
    print(f"\nFailed to connect or modify database: {e}")
    sys.exit(1)

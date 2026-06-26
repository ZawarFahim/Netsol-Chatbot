import os
from langfuse import get_client

langfuse_client = None

try:
    # Clean environment variables from literal quotes
    for key in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL", "OPENROUTER_API_KEY", "MONGO_URI"]:
        val = os.getenv(key)
        if val:
            os.environ[key] = val.strip('"').strip("'")

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if public_key and secret_key:
        langfuse_client = get_client()
    else:
        langfuse_client = get_client()
except Exception as e:
    print(f"Langfuse not configured: {e}")

def start_trace(name: str, user_id: str, session_id: str = None):
    if langfuse_client:
        try:
            return langfuse_client.start_observation(name=name)
        except Exception as e:
            print(f"Error starting Langfuse trace: {e}")
    return None

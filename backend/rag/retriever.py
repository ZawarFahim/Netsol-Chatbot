from backend.rag.vectorstore import similarity_search

def get_relevant_docs(query: str, user_id: str, limit: int = 3):
    try:
        return similarity_search(query, user_id, limit=limit)
    except Exception:
        return []

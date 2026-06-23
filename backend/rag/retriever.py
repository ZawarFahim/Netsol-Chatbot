from backend.rag.vectorstore import similarity_search

def get_relevant_docs(query: str, limit: int = 3):
    try:
        return similarity_search(query, limit=limit)
    except Exception:
        return []

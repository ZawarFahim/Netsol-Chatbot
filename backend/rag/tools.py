from backend.rag.vectorstore import similarity_search

def rag_tool(query: str, user_id: str):
    try:
        return "\n\n".join([d.page_content for d in similarity_search(query, user_id, limit=10)])
    except Exception:
        return ""
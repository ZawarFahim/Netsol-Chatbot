from langchain_core.documents import Document
from backend.rag.vectorstore import similarity_search

def get_relevant_docs(query: str, limit: int = 3) -> list[Document]:
    """Retrieve top relevant Document objects from the vector store."""
    try:
        return similarity_search(query, limit=limit)
    except Exception as e:
        print(f"Error in get_relevant_docs: {e}")
        return []

def retrieve_context(query: str, limit: int = 3) -> str:
    """Retrieve top relevant chunks and format them into a context string."""
    docs = get_relevant_docs(query, limit=limit)
    if not docs:
        return ""
    
    context_parts = []
    for doc in docs:
        context_parts.append(doc.page_content)
        
    return "\n\n".join(context_parts)

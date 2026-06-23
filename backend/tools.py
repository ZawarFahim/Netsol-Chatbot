from backend.rag.retriever import get_relevant_docs

def rag_tool(query: str):
    """
    Tool: Fetch relevant documents from vector DB
    """
    docs = get_relevant_docs(query)

    return "\n\n".join([d.page_content for d in docs])
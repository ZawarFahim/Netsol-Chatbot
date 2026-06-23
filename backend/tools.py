from backend.rag.retriever import get_relevant_docs

def rag_tool(query: str):
    return "\n\n".join([d.page_content for d in get_relevant_docs(query)])
import os
import numpy as np
from pymongo import MongoClient
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

from backend.database import db

def get_collection():
    return db["faq_vectors"]

def save_vectorstore(chunks, clear_existing: bool = False):
    if not chunks:
        return
    collection = get_collection()
    if clear_existing:
        collection.delete_many({})
        
    texts = [c.page_content for c in chunks]
    embeddings = get_embeddings().embed_documents(texts)
    collection.insert_many([
        {"text": t, "embedding": e, "metadata": c.metadata} 
        for t, e, c in zip(texts, embeddings, chunks)
    ])

def similarity_search(query: str, user_id: str, limit: int = 3):
    collection = get_collection()
    query_vector = get_embeddings().embed_query(query)

    try:
        results = list(collection.aggregate([{
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": limit,
                "filter": {"metadata.uploaded_by": user_id}
            }
        }]))
        if results:
            return [Document(page_content=d.get("text", ""), metadata=d.get("metadata", {})) for d in results]
    except Exception:
        pass

    scored_docs = []
    for doc in collection.find({"metadata.uploaded_by": user_id}, {"text": 1, "embedding": 1, "metadata": 1}):
        emb = doc.get("embedding")
        if emb and len(emb) == len(query_vector):
            score = float(np.dot(query_vector, emb) / (np.linalg.norm(query_vector) * np.linalg.norm(emb)))
            scored_docs.append((score, doc))

    return [Document(page_content=d.get("text", ""), metadata=d.get("metadata", {})) for _, d in sorted(scored_docs, key=lambda x: x[0], reverse=True)[:limit]]

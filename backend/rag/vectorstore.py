import os
import numpy as np
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

FAQ_COLLECTION_NAME = "faq_vectors"
VECTOR_INDEX_NAME = "vector_index"

def get_embeddings() -> OpenAIEmbeddings:
    """Initialize OpenRouter embeddings client."""
    return OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        check_embedding_ctx_length=False
    )

def get_collection():
    """Get the MongoDB collection object for vectors."""
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME")
    if not mongo_uri or not db_name:
        raise ValueError("MONGO_URI and DB_NAME environment variables must be set.")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    return db[FAQ_COLLECTION_NAME]

def save_vectorstore(chunks) -> None:
    """Generate embeddings and save chunks to MongoDB."""
    if not chunks:
        print("No chunks provided to save.")
        return

    print("Connecting to MongoDB Atlas...")
    collection = get_collection()

    print("Generating embeddings...")
    embeddings_client = get_embeddings()

    texts = [chunk.page_content for chunk in chunks]
    metadata_list = [chunk.metadata for chunk in chunks]

    embeddings = embeddings_client.embed_documents(texts)
    
    documents = []
    for text, meta, emb in zip(texts, metadata_list, embeddings):
        documents.append({
            "text": text,
            "embedding": emb,
            "metadata": meta
        })

    print("Clearing existing vector database collection...")
    collection.delete_many({})
    
    print(f"Inserting {len(documents)} document embeddings into MongoDB...")
    collection.insert_many(documents)
    print("Vector database successfully written to MongoDB Atlas.")

def cosine_similarity(v1, v2) -> float:
    """Calculate the cosine similarity between two vectors."""
    v1_arr = np.array(v1)
    v2_arr = np.array(v2)
    dot_product = np.dot(v1_arr, v2_arr)
    norm_v1 = np.linalg.norm(v1_arr)
    norm_v2 = np.linalg.norm(v2_arr)
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

def similarity_search(query: str, limit: int = 3) -> list[Document]:
    """Search for similar documents in MongoDB using Atlas Vector Search with a manual similarity fallback."""
    collection = get_collection()
    embeddings_client = get_embeddings()

    query_vector = embeddings_client.embed_query(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": limit
            }
        }
    ]
    
    try:
        results = list(collection.aggregate(pipeline))
        if results:
            print("Atlas Vector Search index search succeeded.")
            docs = []
            for doc in results:
                docs.append(Document(
                    page_content=doc.get("text", ""),
                    metadata=doc.get("metadata", {})
                ))
            return docs
    except Exception as e:
        print(f"Atlas Vector Search failed or index '{VECTOR_INDEX_NAME}' is not yet created. Error: {e}")
        print("Falling back to local cosine similarity calculation in Python...")

    all_docs = list(collection.find({}, {"text": 1, "embedding": 1, "metadata": 1}))
    if not all_docs:
        print("No documents found in the vector database collection.")
        return []

    scored_docs = []
    for doc in all_docs:
        emb = doc.get("embedding")
        if emb and len(emb) == len(query_vector):
            score = cosine_similarity(query_vector, emb)
            scored_docs.append((score, doc))

    scored_docs.sort(key=lambda x: x[0], reverse=True)

    top_results = scored_docs[:limit]
    
    docs = []
    for score, doc in top_results:
        docs.append(Document(
            page_content=doc.get("text", ""),
            metadata=doc.get("metadata", {})
        ))
        
    return docs

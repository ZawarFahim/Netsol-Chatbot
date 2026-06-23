import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag.loader import scrape_netsol_faq
from backend.rag.splitter import split_documents
from backend.rag.vectorstore import save_vectorstore

def build():
    print("=== NETSOL FAQ Index Builder ===")
    print("Step 1: Retrieving NETSOL FAQs...")
    docs = scrape_netsol_faq()
    
    if not docs:
        print("Error: No documents retrieved. Aborting build index.")
        return

    print(f"Loaded {len(docs)} documents.")

    print("Step 2: Splitting text into semantic fragments...")
    chunks = split_documents(docs)
    print(f"  -> Generated {len(chunks)} text chunks.")

    print("Step 3: Generating embeddings and saving to MongoDB Atlas...")
    try:
        save_vectorstore(chunks, clear_existing=True)
        print("Success: Vector database successfully built in MongoDB Atlas!")
    except Exception as e:
        print(f"Error building index: {e}")

if __name__ == "__main__":
    build()
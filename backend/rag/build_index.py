import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag.loader import scrape_netsol_faq
from backend.rag.splitter import split_documents
from backend.rag.vectorstore import save_vectorstore

def build():
    docs = scrape_netsol_faq()
    if docs:
        save_vectorstore(split_documents(docs), clear_existing=True)

if __name__ == "__main__":
    build() 
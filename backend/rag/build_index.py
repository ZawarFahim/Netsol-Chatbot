import os
import sys
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.rag.vectorstore import save_vectorstore

def scrape_netsol_faq(url: str = "https://careers.netsoltech.com/faqs"):
    faq_documents = []
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        for s in soup(["script", "style"]):
            s.decompose()
        for panel in soup.find_all("div", class_="vc_tta-panel"):
            heading = panel.find("div", class_="vc_tta-panel-heading")
            body = panel.find("div", class_="vc_tta-panel-body")
            if heading and body:
                q = heading.get_text(strip=True)
                a = body.get_text(separator="\n", strip=True)
                if q and a:
                    faq_documents.append(Document(page_content=f"Question: {q}\nAnswer: {a}", metadata={"source": url, "question": q}))
    except Exception:
        pass
    return faq_documents

def build():
    docs = scrape_netsol_faq()
    if docs:
        chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
        save_vectorstore(chunks, clear_existing=True)

if __name__ == "__main__":
    build()
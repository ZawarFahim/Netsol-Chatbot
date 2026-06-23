import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

def scrape_netsol_faq(url: str = "https://careers.netsoltech.com/faqs"):
    faq_documents = []
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        for script in soup(["script", "style"]):
            script.decompose()
            
        for panel in soup.find_all("div", class_="vc_tta-panel"):
            heading = panel.find("div", class_="vc_tta-panel-heading")
            body = panel.find("div", class_="vc_tta-panel-body")
            
            if heading and body:
                question = heading.get_text(strip=True)
                answer = body.get_text(separator="\n", strip=True)
                if question and answer:
                    faq_documents.append(Document(page_content=f"Question: {question}\nAnswer: {answer}", metadata={"source": url, "question": question}))
    except Exception:
        pass
    return faq_documents
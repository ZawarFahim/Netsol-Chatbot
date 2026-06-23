import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

def scrape_netsol_faq(url: str = "https://careers.netsoltech.com/faqs") -> list[Document]: 
    """Scrape FAQs from the official NETSOL careers FAQ page."""
    faq_documents = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        for script in soup(["script", "style"]):
            script.decompose()
            
        panels = soup.find_all("div", class_="vc_tta-panel")
        print(f"Scraper: Found {len(panels)} FAQ panels on the page.")
        
        for panel in panels:
            heading = panel.find("div", class_="vc_tta-panel-heading")
            body = panel.find("div", class_="vc_tta-panel-body")
            
            if heading and body:
                question = heading.get_text(strip=True)
                answer = body.get_text(separator="\n", strip=True)
                
                if question and answer:
                    combined_text = f"Question: {question}\nAnswer: {answer}"
                    print(combined_text)
                    faq_documents.append(
                        Document(
                            page_content=combined_text, 
                            metadata={"source": url, "question": question}
                        )
                    )
                
    except Exception as e:
        print(f"Error scraping {url}: {e}")

    return faq_documents

scrape_netsol_faq()
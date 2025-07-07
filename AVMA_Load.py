import re
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
from langchain.schema import Document
import os
from dotenv import load_dotenv

load_dotenv()

def load_avma_article(url: str) -> list[Document]:
    parsed = urlparse(url)
    if "avma.org" not in parsed.netloc:
        return []

    headers = {"User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0")}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")


    content_div = soup.find("div", class_="col avma__column avma__column--50 avma__column--second")
    
    if not content_div:
        content_div = soup.find("article")
    if not content_div:
        print("Failed to locate the main content container.")
        return []
    
    # Extract paragraphs, headings, and list items
    # and join them into a single text block
    paragraphs = content_div.find_all(["p", "h2", "h3", "li"])
    text_blocks = [p.get_text(separator="\n", strip=True) for p in paragraphs]
    full_text = "\n\n".join(text_blocks)

    clean_text = re.split(r"(©|\bCopyright\b)", full_text)[0]

    return [Document(page_content=clean_text, metadata={"source": url})]

# Main execution block to test the function
if __name__ == "__main__":
    url = "https://www.avma.org/resources-tools/pet-owners/petcare"
    docs = load_avma_article(url)

    if docs:
        print(docs[0].page_content)
    else:
        print("No main content was scraped.")

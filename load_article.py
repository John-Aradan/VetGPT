from langchain.schema import Document
import re
from urllib.parse import urlparse
import os
import requests
from bs4 import BeautifulSoup

# Step 1a: Custom Loader for VCAHospitals
def load_vca_sections(resp, url) -> list[Document]:
    
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    start = soup.find("section", class_="py-5")
    if not start:
        return []
    sibling = start.find_next_sibling("section")
    parts = [start, sibling] if sibling else [start]
    combined = "\n\n".join(p.get_text(separator="\n", strip=True) for p in parts)

    text = re.split(r'© Copyright', combined)[0]   # Stop at copyright
    text = text.replace("\n", " ").replace("\r", "").replace("\\","")

    return [Document(page_content=text, metadata={"source": url})]

# Step 1b: Custom Loader for AKC
def load_akc_article(resp, url) -> list[Document]:

    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    container = soup.find("div", class_="page-container")
    if not container:
        print(f"[ERROR] .page-container not found {url}")
        return []
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    container = soup.find("div", class_="page-container")
    if not container:
        print(f"[ERROR] .page-container not found {url}")
        return []
    header = container.find("div", class_="article-header")
    if not header:
        print(f"[ERROR] .article-header not found inside page-container {url}")
        return []
    title_tag = header.find("h1", class_="page-header__title")
    if not title_tag:
        print(f"[ERROR] h1.page-header__title not found {url}")
        return []    
    
    title = title_tag.get_text(strip=True) if title_tag else "AKC Article"

    article_container = soup.find("div", class_="article-body")
    if not article_container:
        return []

    paragraphs = article_container.find_all(["p", "h2", "h3"])
    content = []
    for tag in paragraphs:
        text = tag.get_text(strip=True)
        content.append(text)
    content = "\n".join(content)
    if "we may receive a portion of the sale." in content.lower():
        content = re.split("we may receive a portion of the sale.", content)[1] # Start after affiliate disclaimer
    if " This article is intended solely " in content.lower():
        content = re.split("This article is intended solely ", content)[0]  # Stop at content disclaimer if present

    full_text = f"{title}\n" + content.replace("\n", " ").replace("\r", "").replace("\\","")

    return [Document(page_content=full_text, metadata={"source": url})]

# Step 1c: Custom Loader for PetMD
def load_petmd_article(resp, url) -> list[Document]:

    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("h1", class_="article_title_article_title__98_zt")
    title = title_tag.get_text(strip=True) if title_tag else "PetMD Article"

    article_container = soup.find("div", class_="article_content_article_body__GQzms")
    if not article_container:
        return []

    content = []
    for tag in article_container.find_all(["p", "h2", "h3"]):
        text = tag.get_text(strip=True)
        content.append(text)
    content = "\n".join(content)
    content = re.split("WRITTEN BY", content)[0]  # Stop at Written By     

    full_text = f"{title}\n\n" + content.replace("\n", " ").replace("\r", "").replace("\\","")

    return [Document(page_content=full_text, metadata={"source": url})]

SCRAPPER_MAP = {
    "vcahospitals.com": load_vca_sections,
    "www.akc.org": load_akc_article,
    "www.petmd.com": load_petmd_article
}

def load_article(url: str) -> list[Document]:
    parsed = urlparse(url)
    resp = requests.get(url, headers={"User-Agent": os.getenv("USER_AGENT", "")})
    if resp.status_code == 404:
        print(f"[ERROR] 404 Not Found {url}")
        return []
    
    domain = parsed.netloc
    return SCRAPPER_MAP.get(domain, lambda r, u: [])(resp, url)
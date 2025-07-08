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

# Step 1d: Custom Loader for AVMA
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

# Step 1e: Custom Loader for Tufts
def load_tufts_vet_article(url: str) -> list[Document]:
    """
    A web content loader specifically tailored for the vet.tufts.edu website.
    """
    # 1. Validate that the URL belongs to vet.tufts.edu
    parsed = urlparse(url)
    if "vet.tufts.edu" not in parsed.netloc:
        print(f" Link {url} is not a valid vet.tufts.edu link.")
        return []

    try:
        headers = {"User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0")}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        content_div = soup.find("div", class_="text-long stack-l component")
        
        # Fallback: If the div above is not found, try finding the main content area with role="main"
        if not content_div:
            content_div = soup.find("div", role="main__content")

        # If both methods fail, the scrape fails
        if not content_div:
            print("Failed to locate the main content container.")
            return []
        
        # 3. Extract all paragraphs, headings, and list items (this logic is generic and needs no changes)
        # This list contains all the element types to be scraped from the page
        elements_to_find = ["p", "h2", "h3", "li"]
        paragraphs = content_div.find_all(elements_to_find)
        
        text_blocks = [p.get_text(separator="\n", strip=True) for p in paragraphs]
        full_text = "\n\n".join(text_blocks)

        # 4. Text cleaning (Removed the AVMA-specific copyright cleaning for better generality)
        clean_text = full_text

        return [Document(page_content=clean_text, metadata={"source": url})]

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the URL request: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        return []

SCRAPPER_MAP = {
    "vcahospitals.com": load_vca_sections,
    "www.akc.org": load_akc_article,
    "www.petmd.com": load_petmd_article,
    "vet.tufts.edu": load_tufts_vet_article,
    "avma.org": load_avma_article
}

def load_article(url: str) -> list[Document]:
    parsed = urlparse(url)
    resp = requests.get(url, headers={"User-Agent": os.getenv("USER_AGENT", "")})
    if resp.status_code == 404:
        print(f"[ERROR] 404 Not Found {url}")
        return []
    
    domain = parsed.netloc
    return SCRAPPER_MAP.get(domain, lambda r, u: [])(resp, url)
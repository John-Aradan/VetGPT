import re
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
from langchain.schema import Document
import os
from dotenv import load_dotenv

load_dotenv()

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

# --- Main execution block for testing ---
if __name__ == "__main__":
    test_url = "https://vet.tufts.edu/news-events/news/how-does-being-overweight-affect-my-cat"
    
    docs = load_tufts_vet_article(test_url)

    if docs:
        print(docs[0].page_content)
    else:
        print("No main content was scraped.")
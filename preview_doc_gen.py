import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import requests

from langchain.schema import Document

# Step 1: Custom Loader for VCAHospitals
def load_vca_sections(url: str) -> list[Document]:
    parsed = urlparse(url)
    if parsed.netloc not in ("vcahospitals.com", "www.vcahospitals.com"):
        return []
    
    resp = requests.get(url, headers={"User-Agent": os.getenv("USER_AGENT", "")})
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    start = soup.find("section", class_="py-5")
    if not start:
        return []
    sibling = start.find_next_sibling("section")
    parts = [start, sibling] if sibling else [start]
    combined = "\n\n".join(p.get_text(separator="\n", strip=True) for p in parts)

    text = re.split(r'© Copyright', combined)[0]   # Stop at copyright

    return [Document(page_content=text, metadata={"source": url})]

url = "https://vcahospitals.com/know-your-pet/preventive-health-care-guidelines-for-dogs"
doc = load_vca_sections(url)

# Step 2: Save the fetched document content to a file
if doc:
    filename = "preview_doc.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(doc[0].page_content)
    print(f"Saved content to: {filename}")
else:
    print("No document fetched. Nothing to save.")
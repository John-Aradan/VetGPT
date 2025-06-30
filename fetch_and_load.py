import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
import json
import openai
from bs4 import BeautifulSoup
import requests

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Pinecone
from langchain.schema import Document
from pinecone import Pinecone, ServerlessSpec

#Step 0: Load environment variables from .env file
load_dotenv()

# Step 1: Set API keys and initialize Pinecone
openai.api_key = os.getenv("OPENAI_API_KEY")
user_agent = os.getenv("USER_AGENT")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "vetgpt"
if index_name not in pc.list_indexes().names():
    raise ValueError(f"Index '{index_name}' does not exist in Pinecone!")
index = pc.Index(index_name)

# Step 2: Load URLs and metadata from JSON file
def load_urls_and_metadata(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    urls = []
    metadata_list = []

    for entry in raw_data:
        url = entry.get("source")
        if url:
            urls.append(url)
            metadata_list.append({
                "title": entry.get("title"),
                "source": url,
                "tags": entry.get("topic_tags", []),
                "age_group": entry.get("age_group", []),
                "severity": entry.get("severity_level"),
                "persona_category": entry.get("persona_category", [])
            })

    return urls, metadata_list

urls, metas = load_urls_and_metadata(r"D:\VetAI\data\John.json")

# Step 3: Custom Loader for VCAHospitals
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


# Step 4: Fetch Full Text from URLs via Custom Loader
docs = []
for url, meta in zip(urls, metas):
    loaded_docs = load_vca_sections(url)
    if not loaded_docs:
        continue
    for doc in loaded_docs:
        doc.metadata.update(meta)
        docs.append(doc)

print(f"📄 Total clean documents ready: {len(docs)}")

# Step 5: Saving docs as pickle for later use
import pickle
with open(r"D:\VetAI\Cleaned-Data\clean_docs.pkl", "wb") as f:
    pickle.dump(docs, f)
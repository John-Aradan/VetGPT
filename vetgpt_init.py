from dotenv import load_dotenv
import os
import json
import openai

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Pinecone
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from pinecone import Pinecone, ServerlessSpec

#Step 0: Load environment variables from .env file
load_dotenv()

# Step 1: Set API keys and initialize Pinecone
openai.api_key = os.getenv("OPENAI_API_KEY")

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

urls, metadata_list = load_urls_and_metadata(r"D:\VetAI\data\John.json")
from dotenv import load_dotenv
import os
import json
import openai
from load_article import load_article

#Step 0: Load environment variables from .env file
load_dotenv()

# Step 1: Set API keys and initialize Pinecone
openai.api_key = os.getenv("OPENAI_API_KEY")
user_agent = os.getenv("USER_AGENT")

with open("data/Main-JSON.json", "r+", encoding="utf-8") as f:
    raw_data = json.load(f)

# Step 2: Load URLs and metadata from JSON file
def load_urls_and_metadata():
    
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

urls, metas = load_urls_and_metadata()

# Step 4: Fetch Full Text from URLs via Custom Loader
docs = []
for url, meta in zip(urls, metas):
    loaded_docs = load_article(url)
    if not loaded_docs:
        # Remove URL from JSON file if no documents were loaded
        raw_data = [entry for entry in raw_data if entry.get("source") != url]
        continue
    for doc in loaded_docs:
        doc.metadata.update(meta)
        docs.append(doc)

print(f"Total clean documents ready: {len(docs)}")

with open("data/Main-JSON.json", "w+", encoding="utf-8") as f:
    json.dump(raw_data, f, indent=4, ensure_ascii=False)

# Step 5: Saving docs as pickle for later use
import pickle
with open(r"Cleaned-Data\clean_docs.pkl", "wb") as f:
    pickle.dump(docs, f)
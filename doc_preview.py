from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import FireCrawlLoader
from dotenv import load_dotenv
import os, json
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

sample_url = "https://vcahospitals.com/know-your-pet/preventive-health-care-guidelines-for-dogs"

loader_web = WebBaseLoader(sample_url)
loaded_docs_web = loader_web.load()

loader_fire = FireCrawlLoader(sample_url, api_key=os.getenv("FIRECRAWL_API_KEY"))
loaded_docs_fire = loader_fire.load()

# for i, doc in enumerate(loaded_docs):
#     print(f"--- Document {i} ---")
#     print("Page Content:\n", doc, "\n")

print(len(loaded_docs_web))

for i, doc in enumerate(loaded_docs_web):
    filename = f"preview_doc_{i}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(doc.page_content)
    print(f"✅ Saved Document {i} content to {filename}")

for i, doc in enumerate(loaded_docs_fire):
    filename = f"fire_preview_doc_{i}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(doc.page_content)
    print(f"✅ Saved Document {i} content to {filename}")
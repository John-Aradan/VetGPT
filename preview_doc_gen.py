import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import requests

from langchain.schema import Document
from load_article import load_article

url = "https://www.petmd.com/dog/nutrition/what-fruits-can-dogs-eat"
doc = load_article(url)

# Step 2: Save the fetched document content to a file
if doc:
    filename = "preview_doc_petmd.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(doc[0].page_content)
    print(f"Saved content to: {filename}")
else:
    print("No document fetched. Nothing to save.")
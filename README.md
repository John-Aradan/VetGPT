# VetAI

## Overview

A retrieval‑augmented assistant for veterinary health content. VetAI indexes reference articles, retrieves the most relevant chunks for a user question, and generates grounded answers with clear citations. A simple Streamlit UI is included for interactive use.

Checkout Cloud version at [VetGPT](https://vet-gpt.streamlit.app/)

## 🚀 Features

- **Document indexing** – scripts to parse and chunk source material, then push embeddings to a vector store.
- **Retriever + generator** – a thin pipeline that fetches the top‑K relevant chunks and composes an answer with sources.
- **Streamlit UI** – quick demo interface for local Q&A and previewing retrieved context.
- **Utilities** – helpers for fetching, loading, and previewing articles/json before indexing.

## 📁 Project Structure

```
VetAI/
├── .streamlit/              # Streamlit app configuration
├── Background-Images/       # UI background assets
├── Cleaned-Data/           # Processed documents ready for indexing
├── Data/                   # Raw/processed sources you index locally
├── fetch_and_load.py       # Fetch remote source(s) and stage locally
├── generate.py             # Local generation helper(s)
├── index_docs.py           # Build embeddings + index documents
├── load_article.py         # Load/clean article content
├── load_json.py            # Load/normalize JSON sources
├── preview_doc_gen.py      # Preview chunking/context for a doc
├── retrieve_and_generate.py # Retrieval + answer composition pipeline
├── ui_v2.py               # Streamlit app entrypoint
├── FAILED_LOGS.sql        # Debug/inspection artifact(s)
└── requirements.txt       # Python dependencies
```

## ❤️ What makes VetAI better for Pet Care than just using ChatGPT

- **No Hallucinations**

  Provides responses based only on actual medical articles and references

- **Email Integration**

  Ability to send summarized content and conversation history via email, making it easy to share information with your veterinarian

- **Custom Pet Profiles**

  Develop personalized profiles for pets based on conversations _(In Progress)_

- **Triage Classifier**

  Early disease detection based on pet profile analysis _(In Progress)_

- **Auto-Learning**

  System improves over time based on 'Missing prompts' that are saved

- **Database Integration**

  Integration with vet-standard databases (e.g., IDEXX Cornerstone) _(Future)_

## 🔧 Setup and Installation

### 1) Environment

- Python 3.10+ recommended
- Create and activate a virtual environment, then install deps:

```bash
# Clone repository
git clone https://github.com/yourusername/VetAI.git
cd VetAI

# Setup virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2) Secrets & config

Create a `.env` in the project root (or export environment variables some other way). Typical variables for a Pinecone + OpenAI stack look like:

```bash
# .env
OPENAI_API_KEY=...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...     # e.g., us-east-1-aws
PINECONE_INDEX=vetai
```

### 3) Prepare your data

Place your source files under `Data/` (markdown, HTML, TXT, JSON, etc.). Use the helpers to normalize before indexing:

```bash
# Option A: fetch from a URL, then stage locally
python fetch_and_load.py --url https://example.org/article --out Data/articles/

# Option B: load/clean a local article or JSON source
python load_article.py --in Data/raw/ --out Data/clean/
python load_json.py --in Data/json/ --out Data/clean/
```

### 4) Index documents

Create embeddings and push them to your vector index:

```bash
python index_docs.py --in Data/clean/ --index ${PINECONE_INDEX}
```

### 5) Ask questions (two options)

**A. Streamlit app**

```bash
streamlit run ui_v2.py
```

**B. CLI pipeline**

```bash
python retrieve_and_generate.py --query "What are common causes of vomiting in adult dogs?"
```

## TODO

- Make the code I wrote locally to retreive article URLs and scraping open source.
- Provide alternate cloud based storage method for atricle information ontop of local.
- Implement 'Missing query' PostgreSQL store for Strealmit Cloud.
- Implement Self-Learning feature

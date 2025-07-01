import hashlib
import os
import pickle
from dotenv import load_dotenv

from pinecone import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

# Step 0: Load environment variables, import from pickle, initialize Pinecone
load_dotenv()
with open(r"Cleaned-Data\clean_docs.pkl", "rb") as f:
    docs = pickle.load(f)
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

## Delete all existing vectors in the namespace (optional)
# Uncomment the following lines if you want to clear the namespace before indexing new chunks
# index.delete(delete_all=True, namespace="vetgpt")

# Step 1: Chunk Documents
print(len(docs))
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = splitter.split_documents(docs)
print(len(chunks))

# Step 2: Prepare Deterministic IDs for Chunks
def make_chunk_id(source_url: str, chunk_index: int) -> str:
    base = f"{source_url}||{chunk_index}"
    return hashlib.sha1(base.encode()).hexdigest()

# pair chunks with their IDs
chunk_pairs = []
for i, chunk in enumerate(chunks):
    chunk.metadata["chunk_index"] = i  # Add chunk index to metadata
    cid = make_chunk_id(chunk.metadata["source"], i)
    chunk_pairs.append((cid, chunk))

print("Created Chunks IDs")

# Check for existing IDs in Pinecone
ids = [cid for cid, _ in chunk_pairs]  # List of all chunk IDs

existing = index.fetch(ids, namespace="vetgpt")
existing_ids = set(existing.vectors.keys())
print(f"Found {len(existing_ids)} existing vector IDs in index")

# Filter to only new chunks
to_index_pairs = [(cid, chunk) for cid, chunk in chunk_pairs if cid not in existing_ids]
print(f"{len(to_index_pairs)} chunks to be indexed (new)")

# Step 3: Embed and Upsert new Chunks
emb = OpenAIEmbeddings()
BATCH_SIZE = 50

for i in range(0, len(to_index_pairs), BATCH_SIZE):
    batch = to_index_pairs[i:i + BATCH_SIZE]

    upsert_vectors = []
    for cid, chunk in batch:
        vector = emb.embed_documents([chunk.page_content])[0]  # Embed the chunk content
        # add chuck into the metadata
        chunk.metadata["text"] = chunk.page_content
        upsert_vectors.append({
            "id": cid,
            "values": vector,
            "metadata": chunk.metadata
        })
    
    # Upsert the batch into Pinecone
    index.upsert(vectors=upsert_vectors,namespace="vetgpt")
    print(f"Upserted batch {i // BATCH_SIZE + 1}/{(len(to_index_pairs) + BATCH_SIZE - 1) // BATCH_SIZE}")

print("Indexing complete.")
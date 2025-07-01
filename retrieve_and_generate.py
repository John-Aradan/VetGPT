from dotenv import load_dotenv
import os

from pinecone import Pinecone
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain

# Step 0: Load env variables
load_dotenv()

# Step 1: Initialize Pinecone Vector Store
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))
embedding = OpenAIEmbeddings()
vectorstore = PineconeVectorStore(index=index, 
                                  embedding=embedding,
                                  text_key="text",  # Ensure this matches the field in your documents
                                  namespace="vetgpt")  # Use the same namespace as when you indexed your documents

# Step 2: Create Retrieval Chain
# Retriever does embedding of the query and searches the vector store for similar documents.
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})    # Retrieve top 5 documents for the query

# Step 3: Create a Chat Model
llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

# Step 4: Create a Prompt Template
system_prompt = (
    "Use the following context to answer the question.\n"
    "If unsure, say 'I don't know.'\n\n"
    "Context:\n{context}"
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# Step 5: Create a Chain to combine documents and generate answers
create_chain = create_stuff_documents_chain(llm, prompt)    # This chain will format the retrieved documents and generate an answer using the LLM.

# Step 6: Create the final retrieval chain (RAG chain)
qa_chain = create_retrieval_chain(
    retriever=retriever,
    combine_docs_chain=create_chain
)

# Step 7: Query the chain with a sample question
query = "What are the preventive health guidelines for dogs?"

""" When we make this call, the chain will:
1. Retrieve relevant documents from the Pinecone vector store based on the query. (This is done by the retriever.
2. Pass the retrieved documents to the `create_stuff_documents_chain`, which will format them according to the prompt and generate an answer using the LLM.
3. Return the answer along with source documents.)"""
result = qa_chain.invoke({"input": query})

print("Result keys:", result.keys())  # To see the keys in the result dictionary

 # Step 8: Retrieve the answer and source documents
answer = result.get("answer", "No answer generated.")
source_docs = result.get("context", [])
print("Query:", result.get("input"))
print("Answer:", answer)
print("Source Documents: ", len(source_docs))
from dotenv import load_dotenv
import os

from pinecone import Pinecone
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.memory import ConversationBufferMemory
import psycopg2

# Step 0: Load env variables
load_dotenv()

# setup PostgreSQL connection
conn = psycopg2.connect(
    host = os.getenv("POSTGRESQL_HOST"),
    port = 5432,
    database = "postgres",
    user = "postgres",
    password = os.getenv("POSTGRESQL_PASSWORD")
)
cur = conn.cursor()
# create table to store failed logs if not exists as in FAILED_LOGS.sql
with open("FAILED_LOGS.sql", "r") as f:
    cur.execute(f.read())
conn.commit()
print("Table 'failed_logs' created or already exists.")

# Step 1: Initialize Pinecone Vector Store
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))
embedding = OpenAIEmbeddings()
vectorstore = PineconeVectorStore(index=index, 
                                  embedding=embedding,
                                  text_key="text",  # Ensure this matches the field in your documents
                                  namespace="vetgpt")  # Use the same namespace as when you indexed your documents

# Add Conversation Memory
memory = ConversationBufferMemory(return_messages=True)  

# Step 2: Create Retrieval Chain
# Retriever does embedding of the query and searches the vector store for similar documents.
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})    # Retrieve top 5 documents for the query

# Step 3: Create a Chat Model
llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

# Create a function that takes in query to generate response while also considering conversation history
def generate_response(query):
    """
    Takes the user's query, retrieves relevant vet documents, and generates
    a grounded answer using the LLM, while preserving multi-turn context.
    """

    # retrieve relevant documents based on the query
    retrieved_docs = retriever.invoke(query)

    title = None
    url = None

    # extract title and url from the top retrieved document
    if retrieved_docs:
        top_doc = retrieved_docs[0]
        title = top_doc.metadata.get("title", None)
        url = top_doc.metadata.get("source", None)
    else:
        # add the query to sql
        conn.execute("""
            INSERT INTO failed_logs (log_message)
            VALUES (%s)
        """, (query,))
        conn.commit()

        return {
            "answer": "I'm sorry I do not have relevant information to answer that question.",
            "title": title,
            "url": url,
        }

    system_prompt = (
    "Use the following context to answer the question.\n"
    "If unsure, say 'I'm sorry I do not have relevant information to answer that question.'\n\n" \
    "If the question is unrelated to veterinary care, pet health, or animal behavior, say 'I'm sorry I can only provide information on veterinary topics.'\n\n"
    "Context:\n{context}"
    )

    # ChatPromptTemplate builds the structured multi-turn message prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            *memory.chat_memory.messages,  # Include conversation history
            ("human", "{input}")
        ]
    )

    # Create a chain to format the retrieved documents and generate an answer using the LLM
    combine_chat = create_stuff_documents_chain(llm=llm, prompt=prompt)

    # Create the final retrieval chain (RAG chain)
    response = combine_chat.invoke({
        "input": query,
        "context": retrieved_docs
    })

    # Append the new query and response to the conversation memory
    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(response)

    if response == "I'm sorry I do not have relevant information to answer that question.":
        # add the query to sql
        cur.execute("""
            INSERT INTO failed_logs (log_message)
            VALUES (%s)
        """, (query,))
        conn.commit()
        title = None
        url = None
    
    if response == "I'm sorry I can only provide information on veterinary topics.":
        title = None
        url = None

    return {
        "answer": response,
        "title": title,
        "url": url,
    }

if __name__ == "__main__":
    # Step 7: Query the chain with a sample question
    query = "What to do if my dog is backflipping?"

    # When we make this call, the chain will:
    # 1. Retrieve relevant documents from the Pinecone vector store based on the query. (This is done by the retriever.
    # 2. Pass the retrieved documents to the `create_stuff_documents_chain`, which will format them according to the prompt and generate an answer using the LLM.
    # 3. Return the answer along with source documents.)
    result = generate_response(query)

    print("Answer:", result["answer"])
    print("Title:", result["title"])
    print("URL:", result["url"])
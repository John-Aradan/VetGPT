import streamlit as st
import os
from dotenv import load_dotenv
from retrieve_and_generate import qa_chain

# Step 0: Load environment variables

# local
load_dotenv()

# cloud (Streamlit)
if hasattr(st, "secrets"):
    for key in ("OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX"):
        if key in st.secrets:
            os.environ[key] = st.secrets[key]

# Step 1: Initialize Streamlit app
st.set_page_config(page_title="VetGPT", page_icon=":dog:", layout="centered")
st.title("VetGPT: Your Veterinary AI Assistant")
st.markdown("""
    Welcome to VetGPT! Ask me anything about veterinary care, pet health, or animal behavior.
    I can provide information based on a wide range of veterinary articles and guidelines.
""")

# Step 2: Create a text input for user queries
query = st.text_input("Ask your question:", placeholder="e.g., What are the preventive health guidelines for dogs?")

# Step 3: Create a button to submit the query
if st.button("Get Answer"):
    if not query.strip():
        st.error("Please enter a question.")
    else:
        with st.spinner("Fetching answer..."):
            try:
                response = qa_chain.invoke({"input": query})
                answer = response.get("answer")

                st.markdown("### Answer:")
                st.write(answer)
            except Exception as e:
                st.error(f"An error occurred while fetching the answer: {str(e)}")

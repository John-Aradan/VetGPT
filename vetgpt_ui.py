import streamlit as st
import os
from dotenv import load_dotenv
from retrieve_and_generate import qa_chain

# Step 0: Load environment variables
load_dotenv()

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

# Step 2: Unified logic for query submission
def run_query():
    query = st.session_state.query
    if not query.strip():
        st.error("Please enter a question.")
        return

    with st.spinner("Fetching answer..."):
        try:
            response = qa_chain.invoke({"input": query})
            answer = response.get("answer", "No answer found.")
            st.session_state["last_answer"] = answer
        except Exception as e:
            st.session_state["last_answer"] = f"An error occurred: {str(e)}"

# Step 3: Text input (Enter key triggers)
st.text_input(
    "Ask your question:",
    placeholder="What are the preventive health guidelines for dogs?",
    key="query",
    on_change=run_query
)

# Step 4: Optional Button
if st.button("Get Answer"):
    run_query()

# Step 5: Show the last answer if available
if "last_answer" in st.session_state:
    st.markdown("### Answer:")
    st.write(st.session_state["last_answer"])


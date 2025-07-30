import streamlit as st
import os
from dotenv import load_dotenv
from retrieve_and_generate import generate_response

# Step 0: load secrets
load_dotenv()

if hasattr(st, "secrets"):
    for key in ("OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX", "POSTGRESQL_HOST", "POSTGRESQL_PASSWORD"):
        if key in st.secrets:
            os.environ[key] = st.secrets[key]

# This is an updated version of the VetGPT_UI.py the main change is that we would now be able to continue
# the conversation with the LLM and it will remember the context of the conversation. Streamlit should diplay 
# the conversation history and the user can continue to ask questions.

# Step 1: Initialize Streamlit app
st.title("VetGPT: Your Veterinary AI Assistant")
st.markdown("""
    Welcome to VetGPT! Ask me anything about veterinary care, pet health, or animal behavior.
    I can provide information based on a wide range of veterinary articles and guidelines.
""")

# Initialize messages in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Step 2: Display conversation history
# Display all messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.markdown("----")

# --- Input Area (text field + button on same row) ---
with st.form("chat_form", clear_on_submit=True):
    user_query = st.text_input(
        "Type a question:",
        placeholder="e.g., Why is my dog vomiting?"
    )
    submitted = st.form_submit_button("Send")

# Trigger answer generation when the button is clicked or Enter is pressed
if submitted and user_query:
    # Add user message to conversation history
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # call backend to generate response
    result = generate_response(user_query)
    
    # combine resrul (content, title, url)
    output = result["answer"]
    if result["title"] and result["title"] != None:
        source_info = f"Source: {result['title']}"

    # Add assistant message to conversation history
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})

    # Add source information if available
    if result.get("title"):
        source_info = f"**Source**: {result['title']}"
        if result.get("url"):
            source_info += f" - [More details]({result['url']})"
        st.session_state.messages.append({"role": "assistant", "content": source_info})

    # Force rerun so new messages appear immediately
    st.rerun()


import streamlit as st
import os
from dotenv import load_dotenv
from generate import generate_response
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import datetime

# Step 0: load secrets
load_dotenv()

if hasattr(st, "secrets"):
    for key in ("OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX", "SENDGRID_API_KEY"):
        if key in st.secrets:
            os.environ[key] = st.secrets[key]

# generate a Subject line as well as content for the email based on the conversation history
def generate_email_content(messages):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    date_str = datetime.datetime.now().strftime("%B {}, %Y").format(datetime.datetime.now().day)
    subject = f"VetGPT Conversation Summary – Your Pet: {date_str}"

    # 2. Build prompt to generate summary
    summary_prompt = (
        f"Please provide a clear, factual *summary* of the following veterinary chat:\n\n" +
        "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in messages)
    )
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    llm_response = llm.predict(summary_prompt)
    summary_text = llm_response.strip()

    # 3. Create email body with proper HTML formatting
    lines = []
    lines.append("<p>Hello,</p>")
    lines.append(f"<p>Here's a summary of your VetGPT session on your pet:</p>")
    lines.append("<h3>Summary:</h3>")
    lines.append(f"<p>{summary_text}</p>")
    lines.append("<h3>Full Chat:</h3>")
    lines.append("<div>")
    for m in messages:
        prefix = "<strong>Q:</strong>" if m["role"] == "user" else "<strong>A:</strong>"
        lines.append(f"<p>{prefix} {m['content']}</p>")
    lines.append("</div>")
    lines.append("<p><br>Thank you for using VetGPT!</p>")
    lines.append("<p>Best regards,<br>VetGPT Team</p>")
    lines.append(
        "<p><em>[Note: VetGPT answers are based only on five trusted sources: "
        "PetMD, AVMA, AKC, VCA Hospitals, and Tufts Clinical Nutrition Center — "
        "and focused on dog-related medical info.] "
        "Please consult a veterinarian for specific medical advice.</em></p>"
    )
    body = "\n".join(lines)
    return subject, body

def send_email(to_email, subject):
    subject, body = generate_email_content(st.session_state.messages)
    message = Mail(
        from_email='johnaradan246@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=body
    )
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
    except Exception as e:
        print(e)
    return response.status_code

# This is an updated version of the VetGPT_UI.py the main change is that we would now be able to continue
# the conversation with the LLM and it will remember the context of the conversation. Streamlit should diplay 
# the conversation history and the user can continue to ask questions.

# Set up a background image for the Streamlit app
def set_background_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
              linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)),
              url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Set the background image
set_background_image(r"Background-Images/dog5.avif")

# Create a warning message for the user

# Initialize session state for gatekeeping
if "agreed_to_disclaimer" not in st.session_state:
    st.session_state.agreed_to_disclaimer = False

# Disclaimer message
if not st.session_state.agreed_to_disclaimer:
    st.warning(
        "VetGPT is an AI assistant designed to provide general information about pet health and veterinary care. "
        "It is not a substitute for professional veterinary advice, diagnosis, or treatment. Always seek the advice of your veterinarian with any questions you may have regarding a medical condition."
    )
    
    if st.button("I Agree"):
        st.session_state.agreed_to_disclaimer = True
        st.rerun()  # Rerun to clear the disclaimer
    st.stop()  # Stop further execution until the user agrees

# Step 1: Initialize Streamlit app
st.markdown('<h2 style="text-align:center;">VetGPT: Your Veterinary AI Assistant</h2>', unsafe_allow_html=True)

st.markdown("""
Welcome to **VetGPT**, your trusted AI companion for reliable, up-to-date veterinary guidance.

You can ask anything about **pet health, veterinary care, or animal behavior** — with a special focus on **dogs**, which is our current area of expertise.

VetGPT generates answers based on carefully retrieved content from **five leading veterinary medicine sources**:
[PetMD](https://www.petmd.com), [AVMA](https://www.avma.org), [AKC](https://www.akc.org), [VCA Hospitals](https://vcahospitals.com), and [Tufts Clinical Nutrition Center](https://vetnutrition.tufts.edu).

All responses are grounded in professionally authored veterinary articles.
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

# Step 3: Email functionality
st.markdown("---")
if st.button("📧 Email this conversation"):
    st.session_state.email_modal = True

# Only one modal allowed per run
@st.dialog("📬 Send Conversation Summary", width="small")
def show_email_modal():
    # All input widgets inside the dialog
    recipient = st.text_input("Recipient email:", placeholder="you@example.com", key="modal_email")
    if st.button("Send Email"):
        if not recipient:
            st.error("Please enter a valid email address.")
        else:
            with st.spinner("Composing & sending email..."):
                res = send_email(recipient, "VetGPT Conversation Summary")
                if (200 <= res < 300):
                    st.success("Email sent successfully!")
                else:
                    st.error("Failed to send email. Please try again later.")

# Conditionally open the modal
if st.session_state.get("email_modal", False):
    show_email_modal()
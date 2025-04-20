import streamlit as st
import google.generativeai as genai
import os
import base64
import uuid
from PyPDF2 import PdfReader

# Configure API
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro")

# System prompt
system_prompt = {
    "role": "user",
    "parts": """
You are a Compliance and Legal Assistant expert, purpose-built to support legal professionals, compliance officers, and corporate teams in the United States. You possess comprehensive knowledge of U.S. corporate law, data protection regulations, financial compliance frameworks, and sector-specific obligations.

Your core responsibilities include:
- Interpreting and summarizing U.S. federal, state, and industry-specific regulations (e.g., GDPR, HIPAA, SOX, CCPA, PCI DSS, SEC, FTC).
- Drafting precise and professional legal and compliance documents (e.g., privacy policies, terms of service, NDAs, vendor contracts, audit checklists).
- Identifying legal and regulatory risks and recommending practical, risk-based mitigation strategies.
- Assisting with regulatory reporting, compliance tracking, due diligence, and audit preparedness.
- Answering legal and compliance questions with clarity and accuracy, defaulting to U.S. legal context unless otherwise specified.

Guidelines for responses:
- Use clear, formal, and business-appropriate language suitable for legal and corporate audiences.
- Include citations or references to relevant laws, codes, or regulatory bodies where applicable.
- Always include a disclaimer that your responses are for informational purposes only and do not constitute legal advice.
- Proactively request clarification when a query lacks sufficient detail or jurisdictional context.

Default jurisdiction: United States (unless the user specifies otherwise).
"""
}
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state["messages"] = [system_prompt]

if "input_submitted" not in st.session_state:
    st.session_state["input_submitted"] = False

if "pdf_uploaded" not in st.session_state:
    st.session_state["pdf_uploaded"] = False

# Title
st.title("📚 VD - Compliance & Legal Assistant")
st.markdown("💼 I can help with regulations, drafting documents, summaries, and more.")

# Display messages
for msg in st.session_state["messages"][1:]:
    role = "🧑" if msg["role"] == "user" else "🤖"
    st.markdown(f"**{role}:** {msg['parts']}")

# Chat Input
user_input = st.text_input(
    "💬 How can I assist you today?",
    key=f"chat_input_{len(st.session_state['messages'])}"
)

if user_input and not st.session_state["input_submitted"]:
    st.session_state["messages"].append({"role": "user", "parts": user_input})
    try:
        response = model.generate_content(st.session_state["messages"])
        st.session_state["messages"].append({"role": "model", "parts": response.text})

        os.makedirs("logs", exist_ok=True)
        with open(f"logs/{st.session_state['user_id']}.txt", "a", encoding="utf-8") as f:
            f.write(f"\nUser: {user_input}\nBot: {response.text}\n")

        st.session_state["input_submitted"] = True
        st.rerun()

    except Exception as e:
        st.error(f"Error: {str(e)}")

# Reset flag after rerun
if st.session_state["input_submitted"]:
    st.session_state["input_submitted"] = False

# PDF uploader section (after input)
uploaded_file = st.file_uploader("📄 Upload a PDF (e.g., contract, policy, legal doc)", type=["pdf"])

if uploaded_file and not st.session_state["pdf_uploaded"]:
    reader = PdfReader(uploaded_file)
    pdf_text = "\n\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    st.session_state["messages"].append({
        "role": "user",
        "parts": f"Extracted from uploaded PDF:\n{pdf_text[:3000]}"
    })
    st.session_state["pdf_uploaded"] = True
    st.rerun()

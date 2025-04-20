import streamlit as st
import google.generativeai as genai
import os
import uuid
from datetime import datetime
from PyPDF2 import PdfReader
import streamlit.components.v1 as components

# === Configure API ===
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro")

# === Session State Initialization ===
if "step" not in st.session_state:
    st.session_state.step = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "company_data" not in st.session_state:
    st.session_state.company_data = {}
if "onboarding_complete" not in st.session_state:
    st.session_state.onboarding_complete = False
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "uploaded_texts" not in st.session_state:
    st.session_state.uploaded_texts = {}

# === Title ===
st.title("📚 VD - Compliance & Legal Assistant")

# === Onboarding Prompts ===
onboarding_questions = [
    {"role": "bot", "text": "Hi there! What's your company name?"},
    {"role": "bot", "text": "Great, and which sector or field are you in?"},
    {"role": "bot", "text": "Got it. Is your company new or established?"},
    {"role": "bot", "text": "When was the company established? (MM/DD/YYYY)"},
    {"role": "bot", "text": "✅ Thanks! Launching the assistant..."},
]

def display_chat():
    for message in st.session_state.chat_history:
        if message["role"] == "bot":
            st.markdown(f"🤖: {message['text']}")
        else:
            st.markdown(f"🦁: {message['text']}")

def handle_onboarding():
    display_chat()
    step = st.session_state.step

    if step == 0:
        if onboarding_questions[0] not in st.session_state.chat_history:
            st.session_state.chat_history.append(onboarding_questions[0])
        company_name = st.text_input("Your company name")
        if company_name:
            st.session_state.chat_history.append({"role": "user", "text": company_name})
            st.session_state.company_data["company_name"] = company_name
            st.session_state.step += 1
            st.rerun()

    elif step == 1:
        st.session_state.chat_history.append(onboarding_questions[1])
        sector = st.text_input("Your sector or field")
        if sector:
            st.session_state.chat_history.append({"role": "user", "text": sector})
            st.session_state.company_data["sector"] = sector
            st.session_state.step = 2  # Explicitly set step to 2 to ask for "New or Established?"
            st.rerun()

    elif step == 2:
        if onboarding_questions[2] not in st.session_state.chat_history:
            st.session_state.chat_history.append(onboarding_questions[2])
        status = st.selectbox("New or Established?", ["New", "Established"])
        if status:
            st.session_state.chat_history.append({"role": "user", "text": status})
            st.session_state.company_data["status"] = status
            st.session_state.step += 1 if status == "Established" else 2
            st.rerun()

    elif step == 3:
        if onboarding_questions[3] not in st.session_state.chat_history:
            st.session_state.chat_history.append(onboarding_questions[3])
        date_input = st.text_input("Establishment date (MM/DD/YYYY)")
        if date_input:
            try:
                parsed_date = datetime.strptime(date_input.strip(), "%m/%d/%Y")
                st.session_state.chat_history.append({"role": "user", "text": date_input})
                st.session_state.company_data["established_date"] = parsed_date.strftime("%Y-%m-%d")
                st.session_state.step += 1
                st.rerun()
            except ValueError:
                st.error("❌ Please enter a valid date in MM/DD/YYYY format.")

    elif step == 4:
        if onboarding_questions[4] not in st.session_state.chat_history:
            st.session_state.chat_history.append(onboarding_questions[4])
        st.session_state.onboarding_complete = True
        st.rerun()

# === Show Onboarding or Assistant ===
if not st.session_state.onboarding_complete:
    handle_onboarding()
    st.stop()

# === Add system prompt and transition to main chat ===
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

if "messages" not in st.session_state:
    st.session_state.messages = [system_prompt] + st.session_state.chat_history

# === Show previous messages ===
display_chat()

# === Chat input ===
user_input = st.text_input("💬 How can I assist you today?")
if user_input:
    st.session_state.messages.append({"role": "user", "parts": user_input})
    st.session_state.chat_history.append({"role": "user", "text": user_input})

    try:
        response = model.generate_content(st.session_state.messages)
        reply = response.text
        st.session_state.messages.append({"role": "model", "parts": reply})
        st.session_state.chat_history.append({"role": "bot", "text": reply})

        # Logging (optional)
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/{st.session_state.user_id}.txt", "a", encoding="utf-8") as f:
            f.write(f"\nUser: {user_input}\nBot: {reply}\n")

        st.rerun()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# === Reset Chat ===
if st.button("🗑️ Reset Chat"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# === Upload PDF and extract ===
uploaded_file = st.file_uploader("📄 Upload a PDF", type=["pdf"])
if uploaded_file:
    file_name = uploaded_file.name
    if file_name not in st.session_state.uploaded_docs:
        reader = PdfReader(uploaded_file)
        extracted = "\n\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        short_text = extracted[:3000]
        st.session_state.chat_history.append({
            "role": "user",
            "text": f"📄 Extracted from '{file_name}':\n{short_text}"
        })
        st.session_state.uploaded_docs.append(file_name)
        st.session_state.uploaded_texts[file_name] = extracted
        st.rerun()

# === PDF preview on right ===
if st.session_state.uploaded_docs:
    preview_html = "<div id='right-panel'><h4>📄 Uploaded Docs</h4>"
    for doc in st.session_state.uploaded_docs:
        preview_html += f"<b>📘 {doc}</b><div class='pdf-preview'>{st.session_state.uploaded_texts[doc][:3000]}</div>"
    preview_html += "</div>"
    st.markdown("""
        <style>
            #right-panel {
                position: fixed;
                top: 75px;
                right: 0;
                width: 300px;
                height: 90%;
                background-color: #f9f9f9;
                border-left: 1px solid #ddd;
                padding: 15px;
                overflow-y: auto;
                z-index: 999;
            }
            .pdf-preview {
                white-space: pre-wrap;
                font-size: 0.85rem;
                max-height: 150px;
                overflow-y: auto;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)
    st.markdown(preview_html, unsafe_allow_html=True)

import streamlit as st
import google.generativeai as genai
import os
import uuid
from datetime import datetime
from PyPDF2 import PdfReader

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
if "view" not in st.session_state:
    st.session_state.view = "main"

# === Main Page ===
if st.session_state.view == "main":
    st.set_page_config(page_title="Legal Assistant", layout="wide")
    st.title("📚 VD - Compliance & Legal Assistant")
    st.markdown("#### Simplifying Regulations, One Chat at a Time.")
    st.markdown("""
    Welcome to VD Compliance & Legal Assistant – your AI-powered helper for navigating U.S. corporate regulations, drafting legal documents, and summarizing compliance materials.
    ---
    ### 💡 Key Features:
    - 📄 Summarize regulations like GDPR, HIPAA, SOX, PCI DSS
    - 🧾 Draft NDAs, Privacy Policies, and Terms of Service
    - 🧠 Answer compliance questions with U.S. legal context
    - 📂 Analyze and preview PDF documents
    - ✅ Provide clear, non-binding legal insights
    """)

    if st.button("Get Started"):
        st.session_state.view = "chat"
        st.rerun()

# === Chat Page ===
elif st.session_state.view == "chat":
    st.title("📚 VD - Compliance & Legal Assistant")

    onboarding_questions = [
        "Hi there! What's your company name?",
        "Great, and which sector or field are you in?",
        "Got it. Is your company new or established?",
        "When was the company established? (MM/DD/YYYY)",
        "✅ Thanks! Launching the assistant..."
    ]

    def display_chat():
        for message in st.session_state.chat_history:
            role = "🤖" if message["role"] == "model" else "🦁"
            st.markdown(f"{role}: {message['parts'][0]}")

    def handle_onboarding():
        display_chat()
        step = st.session_state.step

        if step < len(onboarding_questions):
            # Ask the current question
            if not st.session_state.chat_history or st.session_state.chat_history[-1]["role"] == "user":
                st.session_state.chat_history.append({"role": "model", "parts": [onboarding_questions[step]]})
                st.rerun()

            # Handle user input for each step
            if step == 0:
                company_name = st.text_input(onboarding_questions[step])
                if company_name:
                    st.session_state.chat_history.append({"role": "user", "parts": [company_name]})
                    st.session_state.company_data["company_name"] = company_name
                    st.session_state.step += 1
                    st.rerun()
            elif step == 1:
                sector = st.text_input(onboarding_questions[step])
                if sector:
                    st.session_state.chat_history.append({"role": "user", "parts": [sector]})
                    st.session_state.company_data["sector"] = sector
                    st.session_state.step += 1
                    st.rerun()
            elif step == 2:
                status = st.selectbox(onboarding_questions[step], ["Select an option", "New", "Established"])
                if status != "Select an option":
                    st.session_state.chat_history.append({"role": "user", "parts": [status]})
                    st.session_state.company_data["status"] = status
                    st.session_state.step += 1
                    st.rerun()
            elif step == 3:
                date_input = st.text_input(onboarding_questions[step])
                if date_input:
                    try:
                        parsed_date = datetime.strptime(date_input.strip(), "%m/%d/%Y")
                        st.session_state.chat_history.append({"role": "user", "parts": [date_input]})
                        st.session_state.company_data["established_date"] = parsed_date.strftime("%Y-%m-%d")
                        st.session_state.step += 1
                        st.rerun()
                    except ValueError:
                        st.error("❌ Please enter a valid date in MM/DD/YYYY format.")
            elif step == 4:
                st.session_state.chat_history.append({"role": "model", "parts": [onboarding_questions[step]]})
                st.session_state.onboarding_complete = True
                st.rerun()

    if not st.session_state.onboarding_complete:
        handle_onboarding()
        st.stop()

    # === System Prompt ===
    system_prompt = {
        "role": "user",
        "parts": ["""
You are a Compliance and Legal Assistant expert for U.S. businesses. Your responsibilities include:
- Explaining U.S. laws like GDPR, HIPAA, SOX, CCPA, PCI DSS.
- Drafting legal documents: NDAs, privacy policies, ToS, contracts.
- Identifying regulatory risks, suggesting mitigation.
- Helping with audits, due diligence, legal Q&A.

Speak clearly, use legal references, disclaim legal advice, and ask clarifying questions if needed. Default jurisdiction is the U.S.
"""]
    }

    if "messages" not in st.session_state:
        st.session_state.messages = [system_prompt]

    display_chat()

    user_input = st.text_input("💬 How can I assist you today?")
    if user_input:
        # Inject onboarding context BEFORE user query, only once after onboarding
        if len(st.session_state.messages) == 1 + len(st.session_state.chat_history) and st.session_state.onboarding_complete:
            context_message = {
                "role": "user",
                "parts": [f"""
My company details:
- Name: {st.session_state.company_data.get("company_name", "N/A")}
- Sector: {st.session_state.company_data.get("sector", "N/A")}
- Status: {st.session_state.company_data.get("status", "N/A")}
- Established: {st.session_state.company_data.get("established_date", "N/A")}
These details should help you give tailored legal and tax guidance.
"""]
            }
            st.session_state.messages.append(context_message)

        st.session_state.messages.append({"role": "user", "parts": [user_input]})
        st.session_state.chat_history.append({"role": "user", "parts": [user_input]})

        try:
            response = model.generate_content(st.session_state.messages)
            reply = response.text
            st.session_state.messages.append({"role": "model", "parts": [reply]})
            st.session_state.chat_history.append({"role": "model", "parts": [reply]})

            os.makedirs("logs", exist_ok=True)
            with open(f"logs/{st.session_state.user_id}.txt", "a", encoding="utf-8") as f:
                f.write(f"\nUser: {user_input}\nBot: {reply}\n")

            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    # === Reset Button ===
    if st.button("🗑️ Reset Chat"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # === PDF Upload ===
    uploaded_file = st.file_uploader("📄 Upload a PDF", type=["pdf"])
    if uploaded_file:
        file_name = uploaded_file.name
        if file_name not in st.session_state.uploaded_docs:
            reader = PdfReader(uploaded_file)
            extracted = "\n\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            short_text = extracted[:3000]
            st.session_state.chat_history.append({
                "role": "user",
                "parts": [f"📄 Extracted from '{file_name}':\n{short_text}"]
            })
            st.session_state.messages.append({
                "role": "user",
                "parts": [f"📄 Extracted from '{file_name}':\n{short_text}"]
            })
            st.session_state.uploaded_docs.append(file_name)
            st.session_state.uploaded_texts[file_name] = extracted
            st.rerun()

    # === PDF Preview Sidebar ===
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

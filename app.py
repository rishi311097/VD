import streamlit as st
import google.generativeai as genai
import os
import uuid
from PyPDF2 import PdfReader
from datetime import datetime

# Configure API
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "onboarding_step" not in st.session_state:
    st.session_state.onboarding_step = 0

if "company_data" not in st.session_state:
    st.session_state.company_data = {}

if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

if "uploaded_docs" not in st.session_state:
    st.session_state["uploaded_docs"] = []

if "uploaded_texts" not in st.session_state:
    st.session_state["uploaded_texts"] = {}

# Onboarding prompts
onboarding_questions = [
    {"question": "Hi! 👋 What's your company name?", "field": "company_name", "type": "text"},
    {"question": "Great, and which sector or field are you in?", "field": "sector", "type": "text"},
    {"question": "Got it. Is your company new or established?", "field": "status", "type": "select", "options": ["New", "Established"]},
    {"question": "When was the company established? (MM/DD/YYYY)", "field": "established_date", "type": "date_text"}
]

def render_chat():
    st.title("📚 VD - Compliance & Legal Assistant")

    # Show previous chat messages
    for msg in st.session_state.messages:
        role_icon = "🦁" if msg["role"] == "user" else "🤖"
        st.markdown(f"{role_icon} : {msg['content']}")

    # Onboarding flow
    if st.session_state.onboarding_step < len(onboarding_questions):
        q = onboarding_questions[st.session_state.onboarding_step]
        st.markdown(f"🤖 : {q['question']}")
        user_input = ""

        if q["type"] == "text":
            user_input = st.text_input("You:", key=f"onboard_input_{q['field']}")
        elif q["type"] == "select":
            user_input = st.selectbox("Select an option", q["options"], key=f"onboard_input_{q['field']}")
        elif q["type"] == "date_text":
            user_input = st.text_input("You (MM/DD/YYYY):", key="date_input")

        if st.button("Send"):
            if q["type"] == "date_text":
                try:
                    parsed_date = datetime.strptime(user_input.strip(), "%m/%d/%Y")
                    st.session_state.company_data[q["field"]] = parsed_date.strftime("%Y-%m-%d")
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.onboarding_step += 1
                except ValueError:
                    st.error("❌ Please enter a valid date in MM/DD/YYYY format.")
                    return
            elif user_input.strip():
                st.session_state.company_data[q["field"]] = user_input.strip()
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.onboarding_step += 1

                # Skip date step if user is 'New'
                if q["field"] == "status" and user_input.strip() == "New":
                    st.session_state.onboarding_step += 1
            st.rerun()
        return

    # Show assistant starting message
    if st.session_state.onboarding_step == len(onboarding_questions):
        st.session_state.messages.append({"role": "assistant", "content": "✅ Thanks! Launching the assistant..."})
        st.session_state.onboarding_step += 1
        st.rerun()

    # Assistant mode
    user_query = st.text_input("💬 How can I assist you today?", key=f"chat_input_{len(st.session_state.messages)}")
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        try:
            system_prompt = {
                "role": "user",
                "parts": f"""
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

Company info: {st.session_state.company_data}
Default jurisdiction: United States (unless the user specifies otherwise).
"""
            }
            conversation = [system_prompt] + [{"role": msg["role"], "parts": msg["content"]} for msg in st.session_state.messages if msg["role"] != "assistant"]
            response = model.generate_content(conversation)
            reply = response.text
            st.session_state.messages.append({"role": "assistant", "content": reply})

            os.makedirs("logs", exist_ok=True)
            with open(f"logs/{st.session_state['user_id']}.txt", "a", encoding="utf-8") as f:
                f.write(f"\nUser: {user_query}\nBot: {reply}\n")

            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")

# Run chat renderer
render_chat()

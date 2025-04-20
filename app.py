import streamlit as st
import google.generativeai as genai
import os
import uuid
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from datetime import datetime

# Configure API
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro")

# Initialize state
if "setup_step" not in st.session_state:
    st.session_state.setup_step = 1
    st.session_state.company_data = {}
    st.session_state.onboarding_messages = []

def onboarding_chat_display():
    st.title("📚 VD - Compliance & Legal Assistant")
    for msg in st.session_state.onboarding_messages:
        st.markdown(f"**🧑:** {msg['user']}")
        if "bot" in msg:
            st.markdown(f"**🤖:** {msg['bot']}")

    current_step = st.session_state.setup_step

    if current_step == 1:
        prompt = "What's your company name?"
        user_input = st.chat_input(prompt)
        if user_input:
            st.session_state.onboarding_messages.append({"user": user_input, "bot": "Great, and which sector or field are you in?"})
            st.session_state.company_data["company_name"] = user_input
            st.session_state.setup_step += 1
            st.rerun()

    elif current_step == 2:
        prompt = "Which sector or field is your company in?"
        user_input = st.chat_input(prompt)
        if user_input:
            st.session_state.onboarding_messages.append({"user": user_input, "bot": "Got it. Is your company new or established?"})
            st.session_state.company_data["sector"] = user_input
            st.session_state.setup_step += 1
            st.rerun()

    elif current_step == 3:
        prompt = "Type `New` or `Established` to describe your company status."
        user_input = st.chat_input(prompt)
        if user_input:
            status = user_input.strip().lower()
            if status in ["new", "established"]:
                formatted_status = "New" if status == "new" else "Established"
                st.session_state.company_data["status"] = formatted_status
                response = "When was it established? (MM/DD/YYYY)" if formatted_status == "Established" else "Awesome. Let's begin!"
                st.session_state.onboarding_messages.append({"user": user_input, "bot": response})
                st.session_state.setup_step += 1
                st.rerun()
            else:
                st.session_state.onboarding_messages.append({"user": user_input, "bot": "Please enter `New` or `Established`."})
                st.rerun()

    elif current_step == 4:
        if st.session_state.company_data["status"] == "Established":
            prompt = "When was your company established? (MM/DD/YYYY)"
            user_input = st.chat_input(prompt)
            if user_input:
                try:
                    parsed_date = datetime.strptime(user_input.strip(), "%m/%d/%Y")
                    st.session_state.company_data["established_date"] = parsed_date.strftime("%Y-%m-%d")
                    st.session_state.onboarding_messages.append({"user": user_input, "bot": "✅ Thanks! Launching the assistant..."})
                    st.session_state.setup_step += 1
                    st.rerun()
                except ValueError:
                    st.session_state.onboarding_messages.append({"user": user_input, "bot": "❌ Please enter a valid date in MM/DD/YYYY format."})
                    st.rerun()
        else:
            st.session_state.onboarding_messages.append({"user": "", "bot": "✅ Thanks! Launching the assistant..."})
            st.session_state.setup_step += 1
            st.rerun()

    elif current_step == 5:
        components.html(f"""
            <script>
                const data = {st.session_state.company_data};
                localStorage.setItem("companyData", JSON.stringify(data));
                window.parent.postMessage({{ type: 'streamlit:setComponentValue', value: true }}, '*');
            </script>
        """, height=0)
        st.session_state.onboarding_done = True
        st.rerun()

# Run onboarding if not done
if st.session_state.get("setup_step", 1) < 6:
    onboarding_chat_display()
    st.stop()

# ================= Main App =================

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

if "uploaded_docs" not in st.session_state:
    st.session_state["uploaded_docs"] = []

if "uploaded_texts" not in st.session_state:
    st.session_state["uploaded_texts"] = {}

# UI
st.title("📚 VD - Compliance & Legal Assistant")
st.markdown("💼 I can help with regulations, drafting documents, summaries, and more.")

if st.button("🗑️ Reset Chat"):
    st.session_state["messages"] = [system_prompt]
    st.session_state["uploaded_docs"] = []
    st.session_state["uploaded_texts"] = {}
    st.rerun()

# Chat history
for msg in st.session_state["messages"][1:]:
    role = "🧑" if msg["role"] == "user" else "🤖"
    st.markdown(f"**{role}:** {msg['parts']}")

# Chat input
user_input = st.chat_input("💬 How can I assist you today?")
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

if st.session_state["input_submitted"]:
    st.session_state["input_submitted"] = False

# PDF Upload
uploaded_file = st.file_uploader("📄 Upload a PDF", type=["pdf"])
if uploaded_file:
    file_name = uploaded_file.name
    if file_name not in st.session_state["uploaded_docs"]:
        reader = PdfReader(uploaded_file)
        extracted = "\n\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        short_text = extracted[:3000]
        st.session_state["messages"].append({
            "role": "user",
            "parts": f"Extracted from uploaded PDF '{file_name}':\n{short_text}"
        })
        st.session_state["uploaded_docs"].append(file_name)
        st.session_state["uploaded_texts"][file_name] = extracted
        st.rerun()

# Floating preview
if st.session_state["uploaded_docs"]:
    preview_html = "<div id='right-panel'><h4>📄 Uploaded Docs</h4>"
    for doc in st.session_state["uploaded_docs"]:
        preview_html += f"<b>📘 {doc}</b><div class='pdf-preview'>{st.session_state['uploaded_texts'][doc][:3000]}</div>"
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

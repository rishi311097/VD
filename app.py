import streamlit as st
import google.generativeai as genai
import os
import uuid
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from datetime import datetime

##
# Configure API
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro")

# Initialize session state
if "setup_step" not in st.session_state:
    st.session_state.setup_step = 1
    st.session_state.company_data = {}
    st.session_state.onboarding_messages = []

if "onboarding_messages" not in st.session_state:
    st.session_state.onboarding_messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "input_submitted" not in st.session_state:
    st.session_state.input_submitted = False

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []

if "uploaded_texts" not in st.session_state:
    st.session_state.uploaded_texts = {}

def next_step():
    st.session_state.setup_step += 1
    st.rerun()

def show_onboarding():
    st.title("📚 VD - Compliance & Legal Assistant")

    step = st.session_state.setup_step

    def show_chat_prompt(message, is_user=False):
        role = "🧑" if is_user else "🤖"
        st.chat_message(role).markdown(message)

    # Re-render all previous messages
    for msg in st.session_state.onboarding_messages:
        show_chat_prompt(msg["message"], is_user=msg["user"])

    # Step 1: Company Name
    if step == 1:
        prompt = "What's your company name?"
        show_chat_prompt(prompt)
        company_name = st.text_input("", key="company_name_input")
        if company_name:
            st.session_state.company_data["company_name"] = company_name
            st.session_state.onboarding_messages.append({"message": prompt, "user": False})
            st.session_state.onboarding_messages.append({"message": company_name, "user": True})
            next_step()

    # Step 2: Sector
    elif step == 2:
        prompt = "Which sector/field is your company in?"
        show_chat_prompt(prompt)
        sector = st.text_input("", key="sector_input")
        if sector:
            st.session_state.company_data["sector"] = sector
            st.session_state.onboarding_messages.append({"message": prompt, "user": False})
            st.session_state.onboarding_messages.append({"message": sector, "user": True})
            next_step()

    # Step 3: Status
    elif step == 3:
        prompt = "Is your company new or established?"
        show_chat_prompt(prompt)
        status = st.selectbox("", ["New", "Established"], key="status_select")
        if status:
            st.session_state.company_data["status"] = status
            st.session_state.onboarding_messages.append({"message": prompt, "user": False})
            st.session_state.onboarding_messages.append({"message": status, "user": True})
            next_step()

    # Step 4: Establishment Date
    elif step == 4:
        if st.session_state.company_data["status"] == "Established":
            prompt = "When was your company established? (MM/DD/YYYY)"
            show_chat_prompt(prompt)
            date_input = st.text_input("", key="established_date_input")
            if date_input:
                try:
                    parsed_date = datetime.strptime(date_input.strip(), "%m/%d/%Y")
                    st.session_state.company_data["established_date"] = parsed_date.strftime("%Y-%m-%d")
                    st.session_state.onboarding_messages.append({"message": prompt, "user": False})
                    st.session_state.onboarding_messages.append({"message": date_input, "user": True})
                    next_step()
                except ValueError:
                    st.error("❌ Please enter a valid date in MM/DD/YYYY format.")
        else:
            next_step()

    # Step 5: Done
    elif step == 5:
        st.session_state.onboarding_messages.append({"message": "✅ Onboarding complete! Launching assistant...", "user": False})
        components.html(f"""
            <script>
                const data = {st.session_state.company_data};
                localStorage.setItem("companyData", JSON.stringify(data));
                window.parent.postMessage({{ type: 'streamlit:setComponentValue', value: true }}, '*');
            </script>
        """, height=0)
        st.experimental_rerun()

# Run onboarding if not complete
if st.session_state.get("setup_step", 1) < 5:
    show_onboarding()
    st.stop()

# === Main App ===
system_prompt = {
    "role": "user",
    "parts": """
You are a Compliance and Legal Assistant expert, purpose-built to support legal professionals, compliance officers, and corporate teams in the United States... (shortened here)
"""
}

st.session_state.messages.append(system_prompt)

# Title + reset
st.title("📚 VD - Compliance & Legal Assistant")
st.markdown("💼 I can help with regulations, drafting documents, summaries, and more.")

if st.button("🗑️ Reset Chat"):
    st.session_state.messages = [system_prompt]
    st.session_state.uploaded_docs = []
    st.session_state.uploaded_texts = {}
    st.rerun()

# Display chat
for msg in st.session_state.messages[1:]:
    role = "🧑" if msg["role"] == "user" else "🤖"
    st.markdown(f"**{role}:** {msg['parts']}")

# Chat input
user_input = st.text_input("💬 How can I assist you today?", key=f"chat_input_{len(st.session_state['messages'])}")

if user_input and not st.session_state.input_submitted:
    st.session_state.messages.append({"role": "user", "parts": user_input})
    try:
        response = model.generate_content(st.session_state.messages)
        st.session_state.messages.append({"role": "model", "parts": response.text})

        os.makedirs("logs", exist_ok=True)
        with open(f"logs/{st.session_state['user_id']}.txt", "a", encoding="utf-8") as f:
            f.write(f"\nUser: {user_input}\nBot: {response.text}\n")

        st.session_state.input_submitted = True
        st.rerun()
    except Exception as e:
        st.error(f"Error: {str(e)}")

if st.session_state.input_submitted:
    st.session_state.input_submitted = False

# PDF upload
uploaded_file = st.file_uploader("📄 Upload a PDF", type=["pdf"])
if uploaded_file:
    file_name = uploaded_file.name
    if file_name not in st.session_state.uploaded_docs:
        reader = PdfReader(uploaded_file)
        extracted = "\n\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        short_text = extracted[:3000]
        st.session_state.messages.append({
            "role": "user",
            "parts": f"Extracted from uploaded PDF '{file_name}':\n{short_text}"
        })
        st.session_state.uploaded_docs.append(file_name)
        st.session_state.uploaded_texts[file_name] = extracted
        st.rerun()

# Floating panel preview
if st.session_state.uploaded_docs:
    preview_html = "<div id='right-panel'><h4>📄 Uploaded Docs</h4>"
    for doc in st.session_state.uploaded_docs:
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

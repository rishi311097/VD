import streamlit as st
import google.generativeai as genai
import os
import uuid
from PyPDF2 import PdfReader
from datetime import datetime
import streamlit.components.v1 as components

# Configure Gemini
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro")

# --- SESSION STATE INIT ---
if "setup_step" not in st.session_state:
    st.session_state.setup_step = 1
if "company_data" not in st.session_state:
    st.session_state.company_data = {}
if "onboarding_messages" not in st.session_state:
    st.session_state.onboarding_messages = []

# --- ONBOARDING LOGIC ---
def add_chat(role, message):
    st.session_state.onboarding_messages.append((role, message))

def onboarding_chat():
    st.title("📚 VD - Compliance & Legal Assistant")

    step = st.session_state.setup_step
    msgs = st.session_state.onboarding_messages
    company_data = st.session_state.company_data

    # Display chat history
    for role, message in msgs:
        emoji = "🦁" if role == "user" else "🤖"
        st.markdown(f"{emoji} : {message}")

    # Step-by-step logic
    if step == 1:
        user_input = st.text_input("Company name:", key="step1")
        if user_input:
            add_chat("user", user_input)
            company_data["company_name"] = user_input
            add_chat("bot", "Great, and which sector or field are you in?")
            st.session_state.setup_step += 1
            st.rerun()

    elif step == 2:
        user_input = st.text_input("Sector/field:", key="step2")
        if user_input:
            add_chat("user", user_input)
            company_data["sector"] = user_input
            add_chat("bot", "Got it. Is your company new or established?")
            st.session_state.setup_step += 1
            st.rerun()

    elif step == 3:
        status = st.selectbox("Company status", ["New", "Established"], key="step3")
        if status:
            add_chat("user", status)
            company_data["status"] = status
            if status == "Established":
                add_chat("bot", "When was it established? (MM/DD/YYYY)")
                st.session_state.setup_step += 1
            else:
                add_chat("bot", "Awesome. Let's begin!")
                st.session_state.setup_step += 2  # Skip date
            st.rerun()

    elif step == 4:
        user_input = st.text_input("Established date (MM/DD/YYYY):", key="step4")
        if user_input:
            try:
                parsed_date = datetime.strptime(user_input.strip(), "%m/%d/%Y")
                company_data["established_date"] = parsed_date.strftime("%Y-%m-%d")
                add_chat("user", user_input)
                add_chat("bot", "✅ Thanks! Launching the assistant...")
                st.session_state.setup_step += 1
                st.rerun()
            except ValueError:
                st.error("❌ Invalid format. Please use MM/DD/YYYY.")

    elif step == 5:
        # Store data in local storage
        components.html(f"""
            <script>
                const data = {company_data};
                localStorage.setItem("companyData", JSON.stringify(data));
                window.parent.postMessage({{ type: 'streamlit:setComponentValue', value: true }}, '*');
            </script>
        """, height=0)
        st.session_state.setup_step += 1
        st.rerun()

# --- SYSTEM PROMPT ---
system_prompt = {
    "role": "user",
    "parts": """
You are a Compliance and Legal Assistant expert, purpose-built to support legal professionals, compliance officers, and corporate teams in the United States...

(Truncated for brevity – keep full prompt as before)
"""
}

# --- START HERE ---
if st.session_state.setup_step <= 5:
    onboarding_chat()
    st.stop()

# --- MAIN ASSISTANT ---
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

st.title("📚 VD - Compliance & Legal Assistant")
st.markdown("💼 I can help with regulations, drafting documents, summaries, and more.")

if st.button("🗑️ Reset Chat"):
    st.session_state["messages"] = [system_prompt]
    st.session_state["uploaded_docs"] = []
    st.session_state["uploaded_texts"] = {}
    st.rerun()

# Display message history
for msg in st.session_state["messages"][1:]:
    role = "🧑" if msg["role"] == "user" else "🤖"
    st.markdown(f"**{role}:** {msg['parts']}")

# Chat input
user_input = st.text_input("💬 How can I assist you today?", key=f"chat_input_{len(st.session_state['messages'])}")
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

# Upload PDF
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

# --- Floating preview panel ---
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

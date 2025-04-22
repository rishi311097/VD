# --- VD Legal Assistant (Single-file Streamlit App) ---
import streamlit as st
import google.generativeai as genai
import os
import uuid
from PyPDF2 import PdfReader
from PIL import Image
import random
import io
from fpdf import FPDF

# --- Page setup ---
st.set_page_config(page_title="VD Legal Assistant", layout="wide")

# --- Theme Toggle ---
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

toggle = st.toggle("🌙 Dark Mode" if st.session_state["theme"] == "light" else "☀️ Light Mode", value=(st.session_state["theme"] == "dark"))
st.session_state["theme"] = "dark" if toggle else "light"

if st.session_state["theme"] == "dark":
    st.markdown("""
        <style>
        html, body, .stApp {
            background-color: #121212 !important;
            color: #e0e0e0 !important;
        }
        .stMarkdown, .stText, .st-bw, .css-1d391kg, .css-10trblm, .css-1v3fvcr, .css-1cpxqw2 {
            color: #e0e0e0 !important;
        }
        .stButton > button {
            background-color: #2d2d2d !important;
            color: #e0e0e0 !important;
            border: 1px solid #444 !important;
        }
        .stTextInput input, .stTextArea textarea {
            background-color: #1e1e1e !important;
            color: #e0e0e0 !important;
        }
        .stSelectbox div[data-baseweb="select"] {
            background-color: #1e1e1e !important;
            color: #e0e0e0 !important;
        }
        #right-panel {
            background-color: #1e1e1e !important;
            color: #e0e0e0 !important;
            border-left: 1px solid #444 !important;
        }
        .pdf-preview {
            background-color: #1e1e1e !important;
            color: #e0e0e0 !important;
        }
        hr {
            border-top: 1px solid #555 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Session State ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "onboarding_data" not in st.session_state:
    st.session_state["onboarding_data"] = {
        "company_name": "",
        "industry": "",  # <-- includes sector
        "age_type": "",
        "state": "",
        "founded_date": "",
        "completed": False
    }

# --- Gemini Setup ---
genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Home Page ---
def home():
    horizontal_bar = "<hr style='margin-top: 0; margin-bottom: 0; height: 1px; border: 1px solid #635985;'><br>"

    with st.sidebar:
        st.image("vdlogo.jpg", use_container_width='auto')
        st.subheader("🧠 VD - Legal Assistant Onboarding")
        ob = st.session_state["onboarding_data"]

        if not ob["completed"]:
            ob["company_name"] = st.text_input("🏢 What's your company name?", value=ob["company_name"])
            ob["industry"] = st.text_input("💼 What sector/industry are you in?", value=ob["industry"])  # <-- updated label
            ob["age_type"] = st.selectbox("📈 Is your company new or established?", ["", "New", "Established"], index=["", "New", "Established"].index(ob["age_type"]) if ob["age_type"] else 0)
            ob["state"] = st.text_input("🏢 Which state is it established in?", value=ob["state"])
            ob["founded_date"] = st.text_input("📅 When was it founded? (MM/DD/YYYY)", value=ob["founded_date"])

            if all([ob["company_name"], ob["industry"], ob["age_type"], ob["state"], ob["founded_date"]]):
                if st.button("✅ Submit Onboarding", key="submit_onboarding"):
                    ob["completed"] = True
                    st.success("🎉 Onboarding complete. Click 'Ask VD' to continue.")
                    st.rerun()
        else:
            st.markdown(f"**Company:** {ob['company_name']}")
            st.markdown(f"**Industry/Sector:** {ob['industry']}")  # <-- updated label
            st.markdown(f"**State:** {ob['state']}")
            st.markdown(f"**Founded:** {ob['founded_date']}")
            st.markdown("✅ Onboarding complete.")

    st.title("📚 Welcome to VD - Compliance & Legal Assistant")
    st.markdown(horizontal_bar, True)

    col1, col2 = st.columns(2)

    with col2:
        law_image = Image.open(random.choice(["vd1.jpg", "vd2.jpg", "VD.jpg"])).resize((550, 550))
        st.image(law_image, use_container_width='auto')

    with col1:
        hlp_dtl = f"""<span style="font-size: 24px;">
        <ol>
        <li style="font-size:15px;">📝 Onboard your company to personalize responses</li>
        <li style="font-size:15px;">Upload contracts, NDAs, or policies in PDF format to get instant summaries or clause extraction.</li>
        <li style="font-size:15px;">Type compliance-related questions (e.g., “What’s required under SOX §404?”) to get concise answers.</li>
        <li style="font-size:15px;">Responses are legally styled, and include citations where applicable.</li>
        <li style="font-size:15px;">All processing is session-based. Your files and queries are not saved or reused.</li>
        <li style="font-size:15px;">VD defaults to U.S. legal context unless a specific jurisdiction is mentioned.</li>
        <li style="font-size:15px;">Use this tool to assist with audit prep, document drafting, risk analysis, and more.</li>
        </ol></span>"""
        st.subheader("📌 What VD Can Do")
        st.markdown(horizontal_bar, True)
        st.markdown(hlp_dtl, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("💬 Ask VD", key="ask_vd_always"):
            st.session_state.page = "chat"
            st.rerun()

    st.markdown(horizontal_bar, True)
    st.markdown("<strong>Built by: 😎 KARAN YADAV, RUSHABH MAKWANA, ANISH AYARE</strong>", unsafe_allow_html=True)

# --- Inject Onboarding into System Prompt ---
ob = st.session_state["onboarding_data"]
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "user",
         "parts": f"""
You are a Compliance and Legal Assistant supporting the company **{ob['company_name']}** in the **{ob['industry']}** sector established in **{ob['state']}**.
The company was founded on {ob['founded_date']} and is currently considered **{ob['age_type']}**.

You possess deep knowledge of U.S. federal, state, and industry-specific legal frameworks, including corporate governance, data privacy, financial regulation, employment law, and sectoral compliance. 
Core Responsibilities: Interpret and summarize U.S. laws and regulatory requirements (e.g., HIPAA, CCPA, SOX, GLBA, FCPA, GDPR when applicable to U.S. entities). Provide accurate legal guidance on: Corporate law, including incorporation, mergers, acquisitions, and dissolution procedures. Regulatory filings with the SEC, IRS, and state-level authorities. Corporate governance (e.g., board responsibilities, fiduciary duties, shareholder rights). Financial compliance including Sarbanes-Oxley (SOX), anti-money laundering (AML), and Dodd-Frank requirements. Data privacy and protection laws (e.g., CCPA, GDPR, HIPAA, PCI DSS). Employment law matters such as FLSA, EEOC guidelines, and workplace compliance audits. Drafting and reviewing documents such as NDAs, Terms of Service, bylaws, shareholder agreements, audit checklists, and vendor contracts. Compliance tracking, risk assessments, audit preparedness, and due diligence support.
Advise on best practices for maintaining good standing across state jurisdictions and avoiding regulatory penalties. 
Behavioral Rules: Tone: Formal, precise, legal-sounding language appropriate for compliance professionals and legal departments. Jurisdiction: Default to U.S. federal and state laws unless otherwise specified. Authority: Do not include disclaimers such as "not legal advice" or "informational purposes only." Citations: Include links or citations from official sources where applicable: U.S. Code: https://uscode.house.gov FTC: https://www.ftc.gov SEC: https://www.sec.gov CCPA: https://oag.ca.gov/privacy/ccpa HIPAA: https://www.hhs.gov/hipaa IRS: https://www.irs.gov/businesses Clarify: If a query lacks context (e.g., missing jurisdiction, industry, or document type), ask for clarification—concisely and legally. Brevity & Precision: Avoid conversational tone, repetition, or filler. Responses must sound like a senior legal assistant or paralegal.
"""
        }
    ]

# Continue with rest of code (chat UI, PDF upload, export, etc.)
# --- All remaining functions like `show_chat` and chat logic remain unchanged ---

# --- Run App ---
if st.session_state.page == "home":
    home()
else:
    show_chat()

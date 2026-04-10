import streamlit as st
import google.generativeai as genai
from datetime import date

# --- 1. SYSTEM INSTRUCTIONS (The AI's DNA) ---
ACE_BEHAVIOR = """
You are 'Academic Ace', Victoria's elite AI academic strategist. 
CORE RULES:
1. USE UPLOADED FILES: Always prioritize information from the PDFs/Images Victoria uploads.
2. MODES:
   - STUDY: Deep dive explanations.
   - PRACTICE: Quiz Victoria on her materials.
   - EXAM SIM: Create high-pressure, realistic exam questions.
   - PANIC: Give the 20% of info that will get 80% of the marks.
3. PERSONALITY: Be encouraging, sharp, and highly organized.
"""

# --- 2. THEME & STYLE (Sunrise Palette) ---
st.set_page_config(page_title="Academic Ace", layout="wide", page_icon="📚")

st.markdown(f"""
    <style>
    /* Metric Cards */
    .metric-card {{ 
        background-color: rgba(255, 255, 255, 0.05); padding: 25px; border-radius: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;
    }}
    
    /* BIG BUTTONS: Wired for immediate response */
    div.stButton > button {{
        width: 100% !important; height: 110px !important;
        font-weight: 800 !important; font-size: 1.4rem !important;
        border-radius: 18px !important; border: 4px solid !important;
        background-color: transparent !important; transition: 0.3s ease !important;
    }}
    
    /* Yellow, Pink, Green, Red */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {{ border-color: #FFDB5A !important; color: #FFDB5A !important; }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {{ border-color: #E76BC8 !important; color: #E76BC8 !important; }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {{ border-color: #7EBD3E !important; color: #7EBD3E !important; }}
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) button {{ border-color: #FF4B4B !important; color: #FF4B4B !important; }}

    .status-banner {{
        padding: 15px; border-radius: 10px; font-weight: bold; border-left: 12px solid;
        background: rgba(128,128,128,0.1); margin: 20px 0;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE (The Vault) ---
if "courses" not in st.session_state: st.session_state.courses = {}
if "active_code" not in st.session_state: st.session_state.active_code = None
if "mode" not in st.session_state: st.session_state.mode = "Study"

# --- 4. AI ENGINE CONFIG ---
# Replace with your real API Key
API_KEY = "YAIzaSyAeAW5uxqQHquqzcDxVXCoObejTlKRFJsg"
try:
    genai.configure(api_key=API_KEY)
    # This attaches the System Instructions PERMANENTLY to the bot
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=ACE_BEHAVIOR
    )
except Exception as e:
    st.error(f"Brain Setup Error: {e}")

# --- 5. SIDEBAR: THE COMMAND CENTER ---
with st.sidebar:
    st.title("🎓 Ace Command")
    u_name = st.text_input("Student", value="Victoria")
    
    st.markdown("---")
    st.subheader("Add New Course")
    reg_c = st.text_input("Course Code").upper()
    reg_t = st.text_input("Topic")
    reg_d = st.date_input("Exam Date")
    
    if st.button("Register") and reg_c:
        st.session_state.courses[reg_c] = {
            "topic": reg_t, "date": reg_date, "history": [], "files": [], "chat_pts": 0, "e_score": 0
        }
        st.session_state.active_code = reg_c
        st.rerun()

    if st.session_state.courses:
        st.session_state.active_code = st.selectbox("Switch Active Course", options=list(st.session_state.courses.keys()))
        
        # FILE HANDLER: Saves into the course-specific memory
        ups = st.file_uploader(f"Upload for {st.session_state.active_code}", accept_multiple_files=True, key=f"up_{st.session_state.active_code}")
        if ups:
            st.session_state.courses[st.session_state.active_code]["files"] = ups

    if st.button("🗑️ Clear Hub"):
        st.session_state.clear()
        st.rerun()

# --- 6. MAIN DASHBOARD ---
if st.session_state.active_code:
    curr = st.session_state.courses[st.session_state.active_code]
    days = (curr["date"] - date.today()).days
    mastery = int(min(curr["chat_pts"], 30) + (curr["e_score"] * 0.7))

    st.title(f"{st.session_state.active_code}: {curr['topic']}")
    
    # METRICS
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card">Countdown<h2 style="color:#FFDB5A;">{days} Days</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card">Mastery<h2 style="color:#E76BC8;">{mastery}%</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card">Status<h2 style="color:#7EBD3E;">{"READY" if mastery >= 65 else "LOCKED"}</h2></div>', unsafe_allow_html=True)

    # MODE BUTTONS
    st.markdown("---")
    b1, b2, b3, b4 = st.columns(4)
    if b1.button("📖\nSTUDY"): st.session_state.mode = "Study"; st.rerun()
    if b2.button("✏️\nPRACTICE"): st.session_state.mode = "Practice"; st.rerun()
    if b3.button("📝\nEXAM SIM"): st.session_state.mode = "Exam Sim"; st.rerun()
    if b4.button("🚨\nPANIC"): st.session_state.mode = "Panic"; st.rerun()

    m_colors = {"Study": "#FFDB5A", "Practice": "#E76BC8", "Exam Sim": "#7EBD3E", "Panic": "#FF4B4B"}
    st.markdown(f'<div class="status-banner" style="border-left-color:{m_colors[st.session_state.mode]};">ACTIVE MODE: {st.session_state.mode.upper()}</div>', unsafe_allow_html=True)

    # --- 7. CHAT & ANALYTICS ---
    tab_chat, tab_files = st.tabs(["💬 AI Intelligence", "📂 Document Vault"])
    
    with tab_chat:
        for msg in curr["history"]:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Ask about your uploads..."):
            # 1. Log User Message
            curr["history"].append({"role": "user", "content": prompt})
            curr["chat_pts"] += 5
            with st.chat_message("user"): st.markdown(prompt)

            # 2. Get AI Response
            with st.chat_message("assistant"):
                with st.spinner("Processing documents..."):
                    try:
                        # Feed EVERYTHING to the model: System Instructions + Files + Prompt
                        content_payload = [f"User is currently in {st.session_state.mode} mode."]
                        
                        # Grab the actual files
                        if curr["files"]:
                            for f in curr["files"]:
                                content_payload.append({"mime_type": f.type, "data": f.getvalue()})
                        
                        content_payload.append(prompt)
                        
                        # Generate
                        response = model.generate_content(content_payload)
                        
                        if response.text:
                            st.markdown(response.text)
                            curr["history"].append({"role": "assistant", "content": response.text})
                        else:
                            st.error("The AI returned an empty response. Try re-uploading the file.")
                    except Exception as e:
                        st.error(f"Chat failed: {e}")
            st.rerun()
else:
    st.info("👈 Please add a course in the sidebar to unlock your Ace Hub.")
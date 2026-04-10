import streamlit as st
from google import genai
from google.genai import types
from datetime import date
import time

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Academic Ace", layout="wide", page_icon="📚")

# ─── STYLES ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px;
    border: 1px solid rgba(255,255,255,0.1); text-align: center;
}
div.stButton > button {
    width: 100% !important; height: 110px !important;
    font-weight: 800 !important; font-size: 1.4rem !important;
    border-radius: 18px !important; border: 4px solid !important;
    background-color: transparent !important; transition: 0.3s ease !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { border-color: #FFDB5A !important; color: #FFDB5A !important; }
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { border-color: #E76BC8 !important; color: #E76BC8 !important; }
div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { border-color: #FF4B4B !important; color: #FF4B4B !important; }
div[data-testid="stHorizontalBlock"] > div:nth-child(4) button { border-color: #7EBD3E !important; color: #7EBD3E !important; }
.status-banner {
    padding: 15px; border-radius: 10px; font-weight: bold; border-left: 12px solid;
    background: rgba(128,128,128,0.1); margin: 20px 0;
}
.timer-box {
    background: rgba(255,75,75,0.15); border: 2px solid #FF4B4B;
    border-radius: 10px; padding: 10px 20px; text-align: center;
    font-size: 2rem; font-weight: bold; color: #FF4B4B; margin-bottom: 10px;
}
.panic-banner {
    background: rgba(255,75,75,0.1); border: 2px dashed #FF4B4B;
    border-radius: 10px; padding: 12px; text-align: center;
    color: #FF4B4B; font-weight: bold; margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── AI SETUP ─────────────────────────────────────────────────────────────────
def get_system_prompt(name):
    return f"""You are Academic Ace, an elite AI academic strategist built for {name}.
RULES:
- Always address the student as {name}.
- ALWAYS base your responses on the uploaded files (PDFs/images). If no files are uploaded, say so.
- Be sharp, encouraging, and highly organized.
- Never make up content — only use what's in the documents."""

MODEL = "gemini-3-flash-preview"

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"AI Setup Error: {e}")
    client = None

# ─── MODE INTRO PROMPTS ────────────────────────────────────────────────────────
def get_mode_intro(mode, name):
    intros = {
        "Study": (
            f"{name} has just entered STUDY MODE. "
            f"Greet {name} briefly by name, then ask how they want to go through the material: "
            "(1) Full topic overview, (2) Chapter by chapter, (3) Slide by slide, (4) Key concepts only. "
            "Wait for their answer before starting."
        ),
        "Practice": (
            f"{name} has just entered PRACTICE MODE. "
            f"Greet {name} by name, then ask which format they want: "
            "(A) Flashcards — you show a term or concept, they answer; "
            "or (B) Multiple Choice — you give 4 options. "
            "Wait for their choice, then start generating questions strictly from the uploaded material."
        ),
        "Panic": (
            f"{name} has just entered PANIC MODE. They are cramming and need help fast. "
            f"Greet {name} by name with urgency, then generate a comprehensive Q&A sheet from ALL uploaded material. "
            "Format each item exactly like this:\n"
            "**Q: [question]**\nA: [clear, concise answer]\n\n"
            "Generate as many as the material supports (aim for 20–50). "
            "Cover every major topic. After the full list, add this exact line:\n"
            "---\n**Done reviewing? Type 'TEST ME' and I'll quiz you with similar questions (no answers shown).**"
        ),
        "Exam Sim": (
            f"{name} has just entered EXAM SIM MODE. This is a timed exam simulation. "
            f"Address {name} by name and state the rules: no hints, no help, they answer everything before getting feedback. "
            "Then immediately generate 10–15 realistic exam-style questions from the uploaded files, numbered. "
            "Tell them to answer all questions in the chat, then type SUBMIT for grading."
        ),
    }
    return intros[mode]

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {
    "courses": {},
    "active_code": None,
    "mode": "Study",
    "exam_start": None,
    "student_name": "Victoria",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── HELPER: Send message to Gemini with full history ─────────────────────────
def get_ai_response(history, new_message, files=None):
    """
    Sends new_message to Gemini with full history and optional files.
    Uses the new google-genai SDK with gemini-3-flash-preview.
    """
    # Build history in Gemini format (text only — files can't go in history)
    gemini_history = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append(
            types.Content(role=role, parts=[types.Part(text=msg["content"])])
        )

    # Must start with a user turn
    if gemini_history and gemini_history[0].role == "model":
        gemini_history = gemini_history[1:]

    # Build the new message parts: files first, then text
    new_parts = []
    if files:
        for f in files:
            f.seek(0)
            new_parts.append(types.Part.from_bytes(data=f.read(), mime_type=f.type))
    new_parts.append(types.Part(text=new_message))

    gemini_history.append(types.Content(role="user", parts=new_parts))

    response = client.models.generate_content(
        model=MODEL,
        contents=gemini_history,
        config=types.GenerateContentConfig(
            system_instruction=get_system_prompt(st.session_state.get("student_name", "Victoria"))
        ),
    )
    return response.text

# ─── HELPER: Trigger mode intro ───────────────────────────────────────────────
def activate_mode(new_mode, curr):
    """
    Called when a mode button is pressed.
    Fires the mode-specific intro prompt and stores the AI response.
    """
    st.session_state.mode = new_mode
    if new_mode == "Exam Sim":
        st.session_state.exam_start = time.time()
    else:
        st.session_state.exam_start = None

    if new_mode == "Panic":
        curr["panic_phase"] = "generate"

    intro = get_mode_intro(new_mode, st.session_state.student_name)
    # Store as internal so we can hide it from display
    curr["history"].append({"role": "user", "content": intro, "hidden": True})

    try:
        reply = get_ai_response(
            [m for m in curr["history"][:-1] if not m.get("hidden")],
            intro,
            curr["files"] if curr["files"] else None,
        )
        curr["history"].append({"role": "assistant", "content": reply})
    except Exception as e:
        curr["history"].append({"role": "assistant", "content": f"Mode error: {e}"})

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎓 Ace Command")
    name_input = st.text_input("Student", value=st.session_state.student_name)
    if name_input:
        st.session_state.student_name = name_input

    st.markdown("---")
    st.subheader("Add New Course")
    reg_c = st.text_input("Course Code").upper()
    reg_t = st.text_input("Topic")
    reg_d = st.date_input("Exam Date")

    if st.button("Register") and reg_c:
        if reg_c not in st.session_state.courses:
            st.session_state.courses[reg_c] = {
                "topic": reg_t,
                "date": reg_d,       # ← was reg_date (bug fix)
                "history": [],
                "files": [],
                "chat_pts": 0,
                "e_score": 0,
                "panic_phase": "generate",
            }
        st.session_state.active_code = reg_c
        st.rerun()

    if st.session_state.courses:
        st.session_state.active_code = st.selectbox(
            "Switch Active Course", options=list(st.session_state.courses.keys())
        )
        active = st.session_state.active_code
        ups = st.file_uploader(
            f"Upload for {active}",
            accept_multiple_files=True,
            key=f"up_{active}",
            type=["pdf", "png", "jpg", "jpeg"],
        )
        if ups:
            st.session_state.courses[active]["files"] = ups
            st.success(f"{len(ups)} file(s) loaded")

    if st.button("🗑️ Clear Hub"):
        st.session_state.clear()
        st.rerun()

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if not st.session_state.active_code:
    st.info("👈 Add a course in the sidebar to unlock your Ace Hub.")
    st.stop()

curr = st.session_state.courses[st.session_state.active_code]
days = (curr["date"] - date.today()).days
mastery = int(min(min(curr["chat_pts"], 30) + (curr["e_score"] * 0.7), 100))

st.title(f"{st.session_state.active_code}: {curr['topic']}")

# METRICS
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="metric-card">Countdown<h2 style="color:#FFDB5A;">{days} Days</h2></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card">Mastery<h2 style="color:#E76BC8;">{mastery}%</h2></div>', unsafe_allow_html=True)
with c3:
    status = "READY" if mastery >= 65 else "LOCKED IN"
    st.markdown(f'<div class="metric-card">Status<h2 style="color:#7EBD3E;">{status}</h2></div>', unsafe_allow_html=True)

# MODE BUTTONS
st.markdown("---")
b1, b2, b3, b4 = st.columns(4)
if b1.button("📖\nSTUDY"):    activate_mode("Study", curr);    st.rerun()
if b2.button("✏️\nPRACTICE"): activate_mode("Practice", curr); st.rerun()
if b3.button("🚨\nPANIC"):    activate_mode("Panic", curr);    st.rerun()
if b4.button("📝\nEXAM SIM"): activate_mode("Exam Sim", curr); st.rerun()

m_colors = {"Study": "#FFDB5A", "Practice": "#E76BC8", "Panic": "#FF4B4B", "Exam Sim": "#7EBD3E"}
st.markdown(
    f'<div class="status-banner" style="border-left-color:{m_colors[st.session_state.mode]};">'
    f'ACTIVE MODE: {st.session_state.mode.upper()}</div>',
    unsafe_allow_html=True,
)

# EXAM TIMER (counts up, shows time elapsed)
if st.session_state.mode == "Exam Sim" and st.session_state.exam_start:
    elapsed = int(time.time() - st.session_state.exam_start)
    mins, secs = divmod(elapsed, 60)
    st.markdown(f'<div class="timer-box">⏱ {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)

# PANIC PHASE INDICATOR
if st.session_state.mode == "Panic":
    phase = curr.get("panic_phase", "generate")
    if phase == "generate":
        st.markdown('<div class="panic-banner">📋 PHASE 1: Review the Q&A sheet below. Type TEST ME when ready.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="panic-banner">🔥 PHASE 2: Answer the questions — no answers shown!</div>', unsafe_allow_html=True)

# ─── CHAT ─────────────────────────────────────────────────────────────────────
tab_chat, tab_files = st.tabs(["💬 AI Intelligence", "📂 Document Vault"])

with tab_chat:
    # Render history — skip hidden internal prompts
    for msg in curr["history"]:
        if msg.get("hidden"):
            continue
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask Ace anything about your material..."):
        # Detect TEST ME to advance panic phase
        if st.session_state.mode == "Panic" and "test me" in prompt.lower():
            curr["panic_phase"] = "test"

        curr["history"].append({"role": "user", "content": prompt})
        curr["chat_pts"] += 5

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Build mode-aware context injected into the prompt
                    mode = st.session_state.mode
                    context_parts = [f"[MODE: {mode}]"]

                    if mode == "Panic":
                        phase = curr.get("panic_phase", "generate")
                        if phase == "test":
                            context_parts.append(
                                "[PANIC TEST PHASE: Generate similar questions with different wording. "
                                "Do NOT show answers. Grade only after student says DONE.]"
                            )

                    if mode == "Exam Sim":
                        elapsed = int(time.time() - st.session_state.exam_start) if st.session_state.exam_start else 0
                        context_parts.append(f"[Elapsed exam time: {elapsed//60}m {elapsed%60}s]")
                        if "submit" in prompt.lower():
                            context_parts.append("[Student has submitted. Grade their answers now, question by question.]")
                            curr["e_score"] = min(curr["e_score"] + 30, 100)

                    full_prompt = " ".join(context_parts) + "\n\n" + prompt

                    # Only pass visible history (no hidden mode-intro messages)
                    visible_history = [m for m in curr["history"][:-1] if not m.get("hidden")]

                    reply = get_ai_response(
                        visible_history,
                        full_prompt,
                        curr["files"] if curr["files"] else None,
                    )

                    st.markdown(reply)
                    curr["history"].append({"role": "assistant", "content": reply})

                except Exception as e:
                    err = str(e)
                    if "API_KEY" in err or "api key" in err.lower():
                        st.error("API key error. Check your Streamlit secrets.")
                    else:
                        st.error(f"Chat failed: {err}")

        st.rerun()

with tab_files:
    if curr["files"]:
        st.success(f"{len(curr['files'])} file(s) loaded into Ace")
        for f in curr["files"]:
            st.write(f"📄 {f.name} — {round(f.size / 1024, 1)} KB")
    else:
        st.info("No files uploaded yet. Use the sidebar to add PDFs or images.")

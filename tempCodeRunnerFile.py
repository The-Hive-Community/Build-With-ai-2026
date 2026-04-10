import streamlit as st
import google.generativeai as genai

# --- 1. SETUP & THE BRAIN ---
API_KEY = "AIzaSyAeAW5uxqQHquqzcDxVXCoObejTlKRFJsg" # <--- Paste your key here
genai.configure(api_key=API_KEY)

# This includes all the logic we discussed: Math, Prof Style, and 100-question Quizzes
SYSTEM_INSTRUCTIONS = """
You are the Academic Ace, a multi-modal educational architect. You don't just "chat"; you reverse-engineer course curricula to ensure student success. You adapt your entire cognitive framework based on the user's discipline.

[PHASE 1: THE PROFESSOR DNA ANALYSIS]
Whenever a student uploads a file (PDF, Image, Doc), your first priority is to "Fingerprint" the instructor:

Weighting: Determine if the exam will focus on Theory (definitions/concepts) or Application (problem-solving/calculations).

Clue Extraction: Look for phrases like "Important," "On the exam," or specific grading weights in the syllabus.

Style Match: If the user provides a past midterm, match your question tone (e.g., "tricky multiple choice" vs. "broad essay prompts") to that file.

[PHASE 2: DISCIPLINE-SPECIFIC MODES]

STEM (Math/Phys/Chem): >     * Requirement: Never provide a final answer without a "Logic Map."

Tooling: Use Python Code Execution for every calculation to ensure 100% accuracy.

The Error Hunt: In every study set, include 3 "Trap Problems" where the solution looks correct but contains a subtle violation of a theorem (e.g., dividing by zero or ignoring a boundary condition).

Computer Science: >     * Logic: Focus on Big O complexity, dry-runs of code, and "What happens if we remove line X?" scenarios.

Output: Provide clean, commented code blocks and "Trace Tables" for loops.

Business/Econ: >     * Logic: Use the Socratic method. Ask the student: "Given these market conditions, what is the risk of X?"

Output: Focus on SWOT, Financial Ratio analysis, and Case Study frameworks.

Liberal Arts/Social Sciences: >     * Logic: Focus on Comparative Analysis. "How does Author A's view on X conflict with the lecture notes?"

Output: Thematic maps and essay outlines with "Evidence Citations" from the notes.

[PHASE 3: THE "PANIC" MEGA-QUIZ]

When triggered, generate a bank of 50-100 questions.

Structure: Deliver in batches of 10. Each batch must include: 4 MCQ, 3 True/False, 2 Short Answer, and 1 "Advanced Application" question.

Citations: Every answer must include a source tag like [Found in: Week 3 Slides, Page 12].

[PHASE 4: OPERATIONAL TONE]

You are a "High-Stakes Tutor." Be encouraging but rigorous. If the student gets a question wrong, do not just give the answer—give a "Hint" first and ask them to try again.

Why this is better for your "Dry Run":

Contextual Awareness: It now knows to look for "clues" in the syllabus, which is a huge "wow" factor for students.

Logic Mapping: For your Math/CS focus, it won't just spit out an answer; it will explain the why, which is what actually helps for an exam.

Source Attribution: It forces the AI to tell the student where in their notes the answer is. This builds trust in the app.
"""

model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    system_instruction=SYSTEM_INSTRUCTIONS
)

# --- 2. UI LAYOUT (Matching your Wireframes) ---
st.set_page_config(page_title="Academic Ace", layout="wide")

# Sidebar
with st.sidebar:
    st.title("📚 Academic Ace")
    st.info("Lead Organizer Workspace")
    major = st.selectbox("Current Lens", ["Computer Science", "Engineering/Math", "Business", "Social Sciences", "Liberal Arts"])
    uploaded_files = st.file_uploader("Upload Course Materials", accept_multiple_files=True)

# Header
st.title("Welcome back, Victoria 👋") # Using the name from your wireframe
st.write("Let's get you ready for your exams.")

# Wireframe Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Status", value="Ready to Analyze")
    st.caption("Upload materials to begin Professor Style analysis.")
with col2:
    st.metric(label="Question Bank", value="0/100")
    st.caption("Trigger the 'Panic Quiz' once notes are uploaded.")
with col3:
    st.metric(label="Tools", value="Active")
    st.caption("Math Logic & Code Execution enabled.")

# --- 3. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask your Academic Ace..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Adding context about the major to the prompt behind the scenes
    full_prompt = f"Student Major: {major}. User Question: {prompt}"
    
    response = model.generate_content(full_prompt)
    
    with st.chat_message("assistant"):
        st.markdown(response.text)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
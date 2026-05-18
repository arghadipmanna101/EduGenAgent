import streamlit as st
import os
import io
from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import dimgrey

# 1. Define the Data Schema
class MCQ(BaseModel):
    question: str = Field(..., description="The multiple choice question text")
    options: List[str] = Field(..., description="A list of 4 possible answers")
    correct_answer: str = Field(..., description="The correct option (must match one of the options)")
    explanation: str = Field(..., description="A brief explanation of why the answer is correct")

class Quiz(BaseModel):
    questions: List[MCQ]

load_dotenv()

# Initialize Gemini 3.1 Flash-Lite
# (Optimization: Lower temperature (0.4) usually yields better factual MCQ accuracy)
gemini_flash = LLM(
    model="gemini/gemini-3.1-flash-lite-preview",
    temperature=0.4,
    api_key=os.getenv("GOOGLE_API_KEY")
)


def generate_pdf(quiz_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    flowables = []

    # Custom Text Styles
    title_style = styles['Title']
    q_style = ParagraphStyle('Question', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, spaceAfter=8,
                             spaceBefore=12)
    opt_style = ParagraphStyle('Option', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leftIndent=20,
                               spaceAfter=4)
    ans_style = ParagraphStyle('Answer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=10,
                               textColor=dimgrey, spaceBefore=6, spaceAfter=12)

    flowables.append(Paragraph("AI Generated Quiz (Teacher's Copy)", title_style))
    flowables.append(Spacer(1, 12))

    for i, q in enumerate(quiz_data.get('questions', [])):
        # 1. Add Question
        flowables.append(Paragraph(f"Q{i + 1}. {q['question']}", q_style))

        # 2. Add Options
        for j, opt in enumerate(q['options']):
            letter_choice = chr(65 + j)  # Converts 0->A, 1->B, etc.
            flowables.append(Paragraph(f"{letter_choice}. {opt}", opt_style))

        # 3. Add Answer & Explanation
        ans_text = f"<b>Correct Answer:</b> {q['correct_answer']}<br/><b>Explanation:</b> {q['explanation']}"
        flowables.append(Paragraph(ans_text, ans_style))

    doc.build(flowables)
    buffer.seek(0)
    return buffer

# --- Streamlit UI Setup ---
st.set_page_config(page_title="AI MCQ Generator", layout="centered")
st.title("🧠 Multi-Agent MCQ Generator")

with st.sidebar:
    st.header("Configuration")
    difficulty = st.slider("Difficulty Level (Bloom's Taxonomy)", 1, 10, 5)
    num_questions = st.number_input("Number of MCQs", min_value=1, max_value=200, value=5)

    if st.button("📝 New MCQ"):
        st.session_state.clear()
        st.rerun()

    st.info("""
    **Difficulty Logic:**
    - 1-3: Recall
    - 4-7: Application
    - 8-10: Synthesis
    """)

# Session State Initialization
if "generated_quiz" not in st.session_state:
    st.session_state.generated_quiz = None
if "answers_checked" not in st.session_state:
    st.session_state.answers_checked = {}

uploaded_file = st.file_uploader("Upload Source PDF", type=["pdf"])

# --- Execution Logic ---
if uploaded_file:
    if st.button("🚀 Generate Quiz"):
        with st.status("The Crew is analyzing the document...", expanded=True) as status:
            with open("temp_source.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.write("📖 Reading PDF...")
            loader = PyPDFLoader("temp_source.pdf")
            docs = loader.load()
            content = "\n".join([doc.page_content for doc in docs])

            st.write("🕵️ Agents are collaborating...")

            researcher = Agent(
                role='Senior Content Researcher',
                goal='Extract key concepts and facts from the text.',
                backstory="Expert at distilling academic documents into learning objectives.",
                llm=gemini_flash
            )

            designer = Agent(
                role='Assessment Psychometrician',
                goal=f'Create {num_questions} MCQs at difficulty {difficulty}/10.',
                backstory="Expert in Bloom's Taxonomy and distractor logic.",
                llm=gemini_flash
            )

            reviewer = Agent(
                role='Quality Assurance Editor',
                goal='Verify accuracy and ensure JSON formatting.',
                backstory="Final gatekeeper for technical and formatting integrity.",
                llm=gemini_flash
            )

            # Task 1: Use the full content now!
            extract_task = Task(
                description=f"Identify the top {num_questions * 2} concepts from this text: {content}",
                expected_output="A structured list of key concepts.",
                agent=researcher
            )

            design_task = Task(
                description=f"Generate {num_questions} MCQs (Difficulty: {difficulty}/10).",
                expected_output="A set of MCQs with 4 options each.",
                agent=designer,
                context=[extract_task]
            )

            review_task = Task(
                description="Final validation and JSON formatting.",
                expected_output="A validated JSON object containing the questions.",
                agent=reviewer,
                context=[design_task],
                output_json=Quiz
            )

            crew = Crew(
                agents=[researcher, designer, reviewer],
                tasks=[extract_task, design_task, review_task],
                process=Process.sequential
            )

            result = crew.kickoff()
            if os.path.exists("temp_source.pdf"):
                os.remove("temp_source.pdf")
            st.session_state.generated_quiz = result.to_dict()
            status.update(label="✅ Quiz Generated!", state="complete", expanded=False)

# --- Interactive Quiz Display ---
if st.session_state.generated_quiz:
    st.divider()
    st.subheader("📝 Practice Quiz")

    questions = st.session_state.generated_quiz.get('questions', [])

    for i, q in enumerate(questions):
        #st.write(f"**Q{i + 1}: {q['question']}**")

        user_choice = st.radio(
           f"**Q{i + 1}: {q['question']}**",
            q['options'],
            key=f"q_{i}_radio",
            index=None
        )

        if st.button(f"Submit Answer", key=f"btn_{i}"):
            st.session_state.answers_checked[i] = True

        if st.session_state.answers_checked.get(i):
            if user_choice == q['correct_answer']:
                st.success("Correct! 🎉")
            else:
                st.error(f"Incorrect. The correct answer was: {q['correct_answer']}")
            st.info(f"**Explanation:** {q['explanation']}")
        st.divider()

    # --- NEW: PDF DOWNLOAD BUTTON ---
    # Generate the PDF in memory
    pdf_buffer = generate_pdf(st.session_state.generated_quiz)

    st.download_button(
        label="📄 Download Quiz as PDF",
        data=pdf_buffer,
        file_name="ai_generated_quiz.pdf",
        mime="application/pdf"
    )
elif not uploaded_file:
    st.info("Please upload a PDF to begin.")
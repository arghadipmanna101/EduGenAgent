import pandas as pd
from database import get_connection
from components.style import load_css
import json
import streamlit as st
import os
import io
import plotly.graph_objects as go
from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import dimgrey


load_css()

# 🔒 Authentication Protection (MOVE TO TOP)
'''if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/1_Login.py")

if st.session_state.get("role") != "Student":
    st.error("Access Denied.")
    st.stop()'''

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.image("assets/logo4.png", width=150)
    st.markdown("## 🎓 Student Panel")

    menu = st.radio("Navigation", [
        "Dashboard",
        "Generate MCQs",
        "Generate Long Questions",
        "Take Test",
        "Analytics",
    ])

    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("app.py")

# ---------------- HEADER ----------------
header_col1, header_col2 = st.columns([8, 1])

with header_col1:
    student_name = st.session_state.get("user_name", "Student")
    st.title(f"Welcome {student_name} 👋")

with header_col2:
    st.image("assets/student.png", width=80)

st.divider()

# ================= DASHBOARD =================
if menu == "Dashboard":

    # ---------------- Skill Verification ----------------
    st.subheader("💻 Verify Your Programming Skills")

    languages = [
        "Python",
        "Java",
        "C++",
        "C",
        "JavaScript",
        "SQL"
    ]

    selected_language = st.selectbox("Select Language", languages)

    if st.button("Start Skill Test"):
        st.session_state["selected_language"] = selected_language
        st.switch_page("pages/6_Skill_Test.py")

    st.divider()

    # ---------------- Best Skill Scores (Bar Chart) ----------------
    st.subheader("📊 Your Verified Skills")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT language, MAX(score) as best_score
        FROM skill_tests
        WHERE student_id=%s
        GROUP BY language
    """, (st.session_state["user_id"],))

    skills = cursor.fetchall()

    cursor.close()
    conn.close()

    if skills:
        df = pd.DataFrame(skills, columns=["Language", "Best Score"])
        st.bar_chart(df.set_index("Language"))
    else:
        st.info("No skill tests taken yet.")

    st.divider()

    # ---------------- Subject Knowledge Level ----------------
    st.subheader("📘 Subject Knowledge Level")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subject, AVG(score) as avg_score
        FROM tests
        WHERE student_id=%s
        GROUP BY subject
    """, (st.session_state["user_id"],))

    subject_data = cursor.fetchall()

    cursor.close()
    conn.close()

    if subject_data:
        for subject, avg_score in subject_data:
            avg_score = round(avg_score, 2)

            if avg_score >= 80:
                level = "Advanced"
            elif avg_score >= 50:
                level = "Intermediate"
            else:
                level = "Beginner"

            st.markdown(f"### {subject} — {level} ({avg_score}%)")
            st.progress(avg_score / 100)
    else:
        st.info("No test data available yet.")

# ================= OTHER MENUS =================
elif menu == "Generate MCQs":
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
        q_style = ParagraphStyle('Question', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14,
                                 spaceAfter=8,
                                 spaceBefore=12)
        opt_style = ParagraphStyle('Option', parent=styles['Normal'], fontName='Helvetica', fontSize=13, leftIndent=20,
                                   spaceAfter=4)
        ans_style = ParagraphStyle('Answer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=13,
                                   textColor=dimgrey, spaceBefore=6, spaceAfter=12)

        flowables.append(Paragraph("AI Generated Quiz", title_style))
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
        num_questions = st.number_input("Number of MCQs", min_value=1, max_value=20, value=5)

        if st.button("📝 New MCQ"):
            st.session_state.clear()
            st.rerun()

        st.info("""
        **Difficulty Logic:**
        - 1-3: Recall
        - 4-7: Application
        - 8-10: Synthesis
        """)

    # --- Session State Initialization ---
    if "generated_quiz" not in st.session_state:
        st.session_state.generated_quiz = None
    if "answers_checked" not in st.session_state:
        st.session_state.answers_checked = {}
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}  # Tracks what the user selected
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "analysis_report" not in st.session_state:
        st.session_state.analysis_report = None

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
            # st.write(f"**Q{i + 1}: {q['question']}**")

            # Disable radio buttons if already answered to prevent changing answers
            is_answered = st.session_state.answers_checked.get(i, False)

            user_choice = st.radio(
                f"**Q{i + 1}: {q['question']}**",
                q['options'],
                key=f"q_{i}_radio",
                index=None if not is_answered else q['options'].index(
                    st.session_state.user_answers[i]) if st.session_state.user_answers.get(i) in q['options'] else None,
                disabled=is_answered
            )

            if st.button(f"Submit Answer", key=f"btn_{i}", disabled=is_answered):
                if user_choice:  # Ensure they selected something
                    st.session_state.answers_checked[i] = True
                    st.session_state.user_answers[i] = user_choice

                    # Scoring Logic
                    if user_choice == q['correct_answer']:
                        st.session_state.score += 1
                    st.rerun()  # Refresh to update score at top and disable UI
                else:
                    st.warning("Please select an answer before submitting.")

            # Display result if answered
            if st.session_state.answers_checked.get(i):
                if st.session_state.user_answers[i] == q['correct_answer']:
                    st.success("Correct! 🎉")
                else:
                    st.error(f"Incorrect. The correct answer was: {q['correct_answer']}")
                st.info(f"**Explanation:** {q['explanation']}")
            st.divider()

        # --- NEW: VISUAL SCOREBOARD ---
        st.subheader("📈 Performance Overview")

        # Calculate Data
        total_qs = len(questions)
        correct = st.session_state.score
        answered = len(st.session_state.answers_checked)
        incorrect = answered - correct
        remaining = total_qs - answered

        # Create Columns for Metrics and Chart
        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric("Total Score", f"{correct}/{total_qs}")
            st.metric("Accuracy", f"{(correct / answered * 100 if answered > 0 else 0):.1f}%")
            st.write(f"✅ Correct: {correct}")
            st.write(f"❌ Incorrect: {incorrect}")
            if remaining > 0:
                st.write(f"⏳ Remaining: {remaining}")

        with col2:
            # Donut Chart Logic
            labels = ['Correct', 'Incorrect', 'Remaining']
            values = [correct, incorrect, remaining]
            # Professional color palette: Emerald Green, Soft Red, Light Grey
            colors = ['#2ecc71', '#e74c3c', '#f0f2f6']

            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.6,
                marker_colors=colors,
                textinfo='label+percent' if answered > 0 else 'none',
                showlegend=False
            )])

            fig.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                height=250,
                annotations=[dict(text=f'{int(correct / total_qs * 100) if total_qs > 0 else 0}%',
                                  x=0.5, y=0.5, font_size=20, showarrow=False)]
            )

            st.plotly_chart(fig, use_container_width=True)
        # --- AI Analysis Section ---
        st.subheader("📊 Post-Quiz AI Analysis")

        # Only allow analysis if at least one question was answered
        if len(st.session_state.answers_checked) > 0:
            if st.button("🧠 Analyze My Performance & Get Tips"):
                with st.status("The AI Tutor is analyzing your answers...", expanded=True) as status:

                    # 1. Gather wrong answers
                    wrong_answers_data = ""
                    for i, q in enumerate(questions):
                        if st.session_state.answers_checked.get(i):
                            user_ans = st.session_state.user_answers.get(i)
                            if user_ans != q['correct_answer']:
                                wrong_answers_data += f"- Question: {q['question']}\n  Your Answer: {user_ans}\n  Correct Answer: {q['correct_answer']}\n  Concept Explanation: {q['explanation']}\n\n"

                    # 2. Trigger Analysis Agent
                    if not wrong_answers_data:
                        st.session_state.analysis_report = "### 🏆 Flawless Victory!\nYou answered all attempted questions perfectly! You have a strong grasp of these concepts. Keep up the great work!"
                        status.update(label="Analysis Complete", state="complete")
                    else:
                        tutor_agent = Agent(
                            role='Academic Performance Tutor',
                            goal='Analyze incorrect quiz answers to identify conceptual misunderstandings and provide actionable study tips.',
                            backstory="You are an empathetic, world-class private tutor. You don't just give answers; you identify the underlying 'why' behind a student's mistakes.",
                            llm=gemini_flash
                        )

                        analysis_task = Task(
                            description=f"A student got the following questions wrong on a quiz:\n\n{wrong_answers_data}\n\nReview the explanations and the student's choices. Write a brief, encouraging report (using Markdown) that identifies the specific core concepts the student is struggling with, and provide 3 actionable study tips to improve.",
                            expected_output="A structured markdown report with 'Areas for Improvement' and 'Actionable Study Tips'.",
                            agent=tutor_agent
                        )

                        analysis_crew = Crew(agents=[tutor_agent], tasks=[analysis_task])
                        report_result = analysis_crew.kickoff()
                        st.session_state.analysis_report = report_result.raw  # Store the raw markdown output
                        status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

        # Display the report if it exists
        if st.session_state.analysis_report:
            st.info(st.session_state.analysis_report)
        # --- NEW: PDF DOWNLOAD BUTTON ---
        # Generate the PDF in memory
        st.divider()
        pdf_buffer = generate_pdf(st.session_state.generated_quiz)

        with st.sidebar:
            st.download_button(
                label="📄 Download Quiz as PDF",
                data=pdf_buffer,
                file_name="ai_generated_quiz.pdf",
                mime="application/pdf"
            )
    elif not uploaded_file:
        st.info("Please upload a PDF to begin.")

elif menu == "Generate Long Questions":
    # --- 1. Data Schemas ---
    class LongAnswerQuestion(BaseModel):
        question: str = Field(..., description="The descriptive question text")
        mark_value: int = Field(..., description="The marks assigned to this question")
        key_points: List[str] = Field(..., description="The essential facts or points that must be in the answer")
        difficulty: str = Field(..., description="Difficulty level evaluation")


    class DescriptiveExam(BaseModel):
        questions: List[LongAnswerQuestion]


    class GradingReport(BaseModel):
        score_awarded: int = Field(..., description="Numeric marks awarded for the answer")
        feedback: str = Field(..., description="Detailed feedback on the student's answer")
        accuracy_score: int = Field(..., description="How complete and correct the answer is (1-10)")
        relevance_score: int = Field(...,
                                     description="Is the answer to the point without extra stuff or being too verbose (1-10)")
        structure_score: int = Field(..., description="The logical structure of the answer (1-10)")
        completeness_score: int = Field(..., description="Whether a full answer to the question was provided (1-10)")
        grammar_score: int = Field(..., description="Grammar and spelling quality (1-10)")


    load_dotenv()

    # Initialize Model
    gemini_flash = LLM(
        model="gemini/gemini-3.1-flash-lite-preview",
        temperature=0.5,
        api_key=os.getenv("GOOGLE_API_KEY")
    )


    def generate_question_paper_pdf(exam_data):
        buffer = io.BytesIO()
        # Reduced margins for a cleaner look
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        flowables = []

        title_style = styles['Title']
        # Slightly smaller space after question text
        q_style = ParagraphStyle('Question', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11,
                                 spaceAfter=8)

        flowables.append(Paragraph("Examination Paper", title_style))
        flowables.append(Spacer(1, 15))

        for i, q in enumerate(exam_data['questions']):
            text = f"Q{i + 1}. {q['question']} <b>[{q['mark_value']} Marks]</b>"
            flowables.append(Paragraph(text, q_style))

            # Reduced from 140 to 30 for a much tighter look
            flowables.append(Spacer(1, 30))

        doc.build(flowables)
        buffer.seek(0)
        return buffer


    # --- 3. Streamlit UI Setup ---
    st.set_page_config(page_title="AI LAQ Suite", layout="centered")
    st.title("📑 AI Long Answer Suite")

    # Persistent state for results
    if "descriptive_exam" not in st.session_state:
        st.session_state.descriptive_exam = None
    if "grades" not in st.session_state:
        st.session_state.grades = {}
    if "final_report" not in st.session_state:
        st.session_state.final_report = None
    if "source_content" not in st.session_state:
        st.session_state.source_content = ""

    with st.sidebar:
        st.header("📝 Exam Configuration")
        difficulty_val = st.slider("Difficulty Level", 1, 10, 5)

        st.divider()
        st.subheader("Marks Weightage")
        st.write("Specify how many questions you want for each mark category.")

        mark_distribution = {}
        with st.expander("Assign Question Counts (1-20 Marks)", expanded=True):
            for m in range(1, 21):
                count = st.number_input(f"{m} Mark Questions:", min_value=0, value=0, key=f"mark_{m}")
                if count > 0:
                    mark_distribution[m] = count

        # Derived Stats
        total_q = sum(mark_distribution.values())
        total_m = sum(m * count for m, count in mark_distribution.items())

        if total_q > 0:
            st.success(f"Blueprint: {total_q} Questions | {total_m} Total Marks")

        if st.button("📝 New LAQ"):
            st.session_state.clear()
            st.rerun()

    uploaded_file = st.file_uploader("Upload Source PDF", type=["pdf"])

    # --- 4. Generation Logic ---
    if uploaded_file and total_q > 0:
        if st.button("🚀 Generate Exam"):
            with st.status("Analyzing PDF & Drafting Questions...", expanded=True) as status:
                with open("temp_source.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())

                loader = PyPDFLoader("temp_source.pdf")
                docs = loader.load()
                content = "\n".join([doc.page_content for doc in docs])
                st.session_state.source_content = content

                researcher = Agent(role='Researcher', goal='Extract core academic themes.',
                                   backstory="Expert in academic synthesis.", llm=gemini_flash)
                examiner = Agent(role='Examiner', goal=f'Draft {total_q} questions.',
                                 backstory="Academic rigor specialist.", llm=gemini_flash)

                t1 = Task(description=f"Analyze themes: {content}", expected_output="List of themes.", agent=researcher)
                t2 = Task(
                    description=f"""
                    Create a descriptive exam with this mark distribution: {json.dumps(mark_distribution)}.
                    Difficulty Level: {difficulty_val}/10. 

                    CRITICAL RULES FOR KEY POINTS:
                    1. The number of 'key_points' MUST scale with the 'mark_value'. 
                    2. A 1-mark question should have exactly 1-2 key points.
                    3. A 5-mark question should have 4-6 distinct, detailed key points.
                    4. Never provide more key points than the mark value allows for a 'point-per-mark' grading system.
                    """,
                    expected_output="JSON DescriptiveExam object.",
                    agent=examiner, context=[t1], output_json=DescriptiveExam
                )

                result = Crew(agents=[researcher, examiner], tasks=[t1, t2]).kickoff()
                st.session_state.descriptive_exam = result.to_dict()
                status.update(label="✅ Exam Ready!", state="complete")

    # --- 5. Grading & Interaction (REFINED FOR SYNTHESIS & GROUNDING) ---
    if st.session_state.descriptive_exam:
        st.divider()
        st.subheader("📄 Practice & Grading")

        for i, q in enumerate(st.session_state.descriptive_exam['questions']):
            with st.expander(f"Question {i + 1} ({q['mark_value']} Marks)"):
                st.write(f"### {q['question']}")
                if st.toggle("💡 Show Hint", key=f"hint_toggle_{i}"):
                    st.info("**Required Concepts:**\n" + "\n".join([f"- {p}" for p in q['key_points']]))

                user_ans = st.text_area("Your Answer", key=f"ans_area_{i}", height=150)

                if st.button(f"Grade Answer {i + 1}", key=f"grade_btn_{i}"):
                    with st.spinner("Analyzing depth and accuracy..."):
                        # REFINED AGENT: Focuses on synthesis, not just keywords
                        grader = Agent(
                            role='Nuanced Academic Professor',
                            goal='Evaluate answers for conceptual depth, synthesis, and strict adherence to source material.',
                            backstory="""You are a veteran professor who despises 'keyword stuffing'. 
                            You look for answers that explain HOW and WHY concepts connect. 
                            You penalize answers that are just a list of keywords without proper sentence structure or context.""",
                            llm=gemini_flash
                        )

                        grading_task = Task(
                            description=f"""
                            --- SOURCE MATERIAL (The ONLY Source of Truth) ---
                            {st.session_state.source_content}

                            --- GRADING TARGETS ---
                            Question: {q['question']}
                            Maximum Marks: {q['mark_value']}
                            Required Key Points: {q['key_points']}

                            --- STUDENT SUBMISSION ---
                            "{user_ans}"

                            --- EVALUATION RULES ---
                            1. GROUNDING: If the student includes facts NOT found in the Source Material, ignore them or penalize if they contradict the source.
                            2. ANTI-KEYWORD STUFFING: If the student simply lists the 'Key Points' without explaining them in full sentences or providing context, award NO MORE than 30% of the total marks.
                            3. SYNTHESIS: Award full marks only if the student uses the keywords to build a coherent, logical narrative that directly answers the prompt.
                            4. PENALTIES: Deduct marks for repetition, being overly verbose without adding value, or failing to provide a clear structure (Introduction -> Explanation -> Conclusion).

                            The 'score_awarded' must be between 0 and {q['mark_value']}.
                            The 5 metrics (Accuracy, Relevance, Structure, Completeness, Grammar) are on a scale of 1-10.
                            """,
                            expected_output="JSON GradingReport object.",
                            agent=grader,
                            output_json=GradingReport
                        )
                        grade_result = Crew(agents=[grader], tasks=[grading_task]).kickoff()
                        st.session_state.grades[i] = grade_result.to_dict()

                if i in st.session_state.grades:
                    rep = st.session_state.grades[i]
                    clamped_score = min(rep['score_awarded'], q['mark_value'])
                    st.markdown(f"#### Score: **{clamped_score} / {q['mark_value']}**")
                    st.write(f"**Feedback:** {rep['feedback']}")
        # --- 6. Final Performance & Radar Graph ---
        if len(st.session_state.grades) > 0:
            st.divider()
            if st.button("🏁 Finalize Exam & See Analytics"):
                # Calculate Clamped Sums
                total_obtained = sum(
                    min(g['score_awarded'], st.session_state.descriptive_exam['questions'][idx]['mark_value'])
                    for idx, g in st.session_state.grades.items())
                total_possible = sum(q['mark_value'] for q in st.session_state.descriptive_exam['questions'])

                with st.status("Generating Performance Analytics...", expanded=True):
                    auditor = Agent(role='Auditor', goal='Summarize performance patterns.',
                                    backstory="Academic Mentor.",
                                    llm=gemini_flash)
                    analysis_task = Task(
                        description=f"Analyze these results: {json.dumps(list(st.session_state.grades.values()))}",
                        expected_output="Overall summary of strengths and areas for improvement.",
                        agent=auditor
                    )
                    final_analysis = Crew(agents=[auditor], tasks=[analysis_task]).kickoff()
                    st.session_state.final_report = {"score": f"{total_obtained} / {total_possible}",
                                                     "analysis": final_analysis.raw}

            if st.session_state.final_report:
                st.header("📊 Final Performance Report")
                st.metric("Aggregate Exam Score", st.session_state.final_report['score'])

                # --- Radar Chart Calculation ---
                metrics = ['Accuracy', 'Relevance', 'Structure', 'Completeness', 'Grammar']

                avg_accuracy = sum(g['accuracy_score'] for g in st.session_state.grades.values()) / len(
                    st.session_state.grades)
                avg_relevance = sum(g['relevance_score'] for g in st.session_state.grades.values()) / len(
                    st.session_state.grades)
                avg_structure = sum(g['structure_score'] for g in st.session_state.grades.values()) / len(
                    st.session_state.grades)
                avg_completeness = sum(g['completeness_score'] for g in st.session_state.grades.values()) / len(
                    st.session_state.grades)
                avg_grammar = sum(g['grammar_score'] for g in st.session_state.grades.values()) / len(
                    st.session_state.grades)

                values = [avg_accuracy, avg_relevance, avg_structure, avg_completeness, avg_grammar]

                fig = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=metrics,
                    fill='toself',
                    marker=dict(color='#3498db'),
                    line=dict(color='#2980b9')
                ))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False,
                                  title="Skill Competency Radar")
                st.plotly_chart(fig)

                # --- ADDED: Evaluation Metrics as Text Breakdown ---
                st.markdown("### 📈 Metric Score Breakdown")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric(label="Accuracy", value=f"{avg_accuracy:.1f}/10")
                with col2:
                    st.metric(label="Relevance", value=f"{avg_relevance:.1f}/10")
                with col3:
                    st.metric(label="Structure", value=f"{avg_structure:.1f}/10")
                with col4:
                    st.metric(label="Completeness", value=f"{avg_completeness:.1f}/10")
                with col5:
                    st.metric(label="Grammar", value=f"{avg_grammar:.1f}/10")
                st.divider()

                st.markdown("### 💡 Academic Mentorship Summary")
                st.info(st.session_state.final_report['analysis'])

        # --- 7. Export ---
        st.divider()
        pdf_buf = generate_question_paper_pdf(st.session_state.descriptive_exam)
        st.download_button(label="📥 Download Question Paper (PDF)", data=pdf_buf, file_name="ai_descriptive_exam.pdf",
                           mime="application/pdf")
    elif not uploaded_file:
        st.info("Please upload a PDF to begin.")

elif menu == "Take Test":
    st.header("🧪 Take Test")

elif menu == "Analytics":
    st.header("📊 Performance Analytics")
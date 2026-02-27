import streamlit as st
import pandas as pd
from database import get_connection
from components.style import load_css

load_css()

# 🔒 Authentication Protection (MOVE TO TOP)
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/1_Login.py")

if st.session_state.get("role") != "Student":
    st.error("Access Denied.")
    st.stop()

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
    st.header("📘 Generate MCQs")

elif menu == "Generate Long Questions":
    st.header("📝 Generate Long Questions")

elif menu == "Take Test":
    st.header("🧪 Take Test")

elif menu == "Analytics":
    st.header("📊 Performance Analytics")
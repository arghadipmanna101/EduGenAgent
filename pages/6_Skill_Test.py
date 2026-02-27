import streamlit as st
from database import get_connection

# 🔒 Login protection
if "authenticated" not in st.session_state:
    st.switch_page("pages/1_Login.py")

language = st.session_state.get("selected_language")

if not language:
    st.switch_page("pages/3_Student_Dashboard.py")

st.title(f"{language} Skill Test")

st.info("Here 50 MCQs will be generated later.")

# Temporary score simulation
score = st.slider("Simulate Your Score (%)", 0, 100, 50)

if st.button("Submit Test"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO skill_tests (student_id, language, score)
        VALUES (%s, %s, %s)
    """, (
        st.session_state["user_id"],
        language,
        score
    ))

    conn.commit()
    cursor.close()
    conn.close()

    st.success("Test Submitted Successfully!")
    st.switch_page("pages/3_Student_Dashboard.py")
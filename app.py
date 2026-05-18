import os
import time
import streamlit as st
from datetime import timedelta
from database import get_connection

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="EduGenAgent",
    page_icon="🎓",
    layout="wide"
)

# ------------------ LOAD CSS ------------------
from components.style import load_css
load_css()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "assets", "logo4.png")

# ------------------ HERO SECTION ------------------

st.markdown("<br><br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=260)

with col2:
    st.markdown("""
    <h1 style='font-size:48px;'>EduGenAgent</h1>
    <h3 style='color:gray;'>AI-Powered Intelligent Learning Ecosystem</h3>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        if st.button("🚀 Get Started"):
            st.switch_page("pages/1_Login.py")

    with c2:
        if st.button("📘 Learn More"):
            st.toast("Multi-Agent AI driven assessment platform")

st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

# ------------------ FEATURES SECTION ------------------

st.markdown("## ⚡ Why EduGenAgent?")

f1, f2, f3 = st.columns(3)

with f1:
    st.markdown("""
    ### 🤖 AI Question Generation
    Generate unlimited MCQs and long questions 
    with difficulty control.
    """)

with f2:
    st.markdown("""
    ### 📊 Smart Analytics
    Track performance, weak topics, 
    and improvement trends.
    """)

with f3:
    st.markdown("""
    ### 🧠 Multi-Agent Architecture
    Separate AI agents for generation, 
    grading, and recommendations.
    """)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

st.markdown("## 📈 Platform Statistics")

@st.cache_data(ttl=timedelta(seconds=30))
def get_statistics():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    students = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM questions")
    questions = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM test_results")
    tests = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return students, questions, tests

# Display
col1, col2, col3 = st.columns(3)
students, questions, tests = get_statistics()

col1.metric("Active Students", f"{students}+")
col2.metric("Questions Generated", f"{questions}+")
col3.metric("Tests Completed", f"{tests}+")

st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

# ------------------ FOOTER ------------------

st.markdown("""
<div style='text-align:center; color:gray; font-size:14px;'>
    © 2026 EduGenAgent | Built with Streamlit & Agentic AI  
    Academy of Technology - Final Year Project
</div>
""", unsafe_allow_html=True)




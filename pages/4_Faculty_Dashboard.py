import streamlit as st
from components.style import load_css

load_css()

with st.sidebar:
    st.image("assets/logo.png", width=150)
    st.markdown("## 👨‍🏫 Faculty Panel")
    menu = st.radio("Navigation", [
        "Dashboard",
        "Upload Resources",
        "Generate Question Bank",
        "View Student Performance",
        "Logout"
    ])

st.title("Faculty Dashboard")

if menu == "Upload Resources":
    st.header("📂 Upload Study Material")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    
    if uploaded_file:
        st.success("File uploaded successfully!")

elif menu == "View Student Performance":
    st.header("📊 Class Performance")
    st.dataframe({
        "Student": ["Arghadip", "Sneha", "Vishal"],
        "Tests Taken": [5, 6, 4],
        "Average Score": ["82%", "75%", "88%"]
    })
    
# 🚫 Block direct access
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please login first.")
    st.switch_page("pages/1_Login.py")

# 🚫 Role protection
if st.session_state.get("role") != "Faculty":
    st.error("Access Denied.")
    st.stop()
    
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.switch_page("app.py")
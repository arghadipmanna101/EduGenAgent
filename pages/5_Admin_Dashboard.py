import streamlit as st
from components.style import load_css

load_css()
st.title("🛠 Admin Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Total Users", "120")
col2.metric("Total Tests Generated", "560")
col3.metric("API Calls Today", "1,240")
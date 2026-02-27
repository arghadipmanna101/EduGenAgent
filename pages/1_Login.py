import streamlit as st
import bcrypt
from database import get_connection
from components.style import load_css
load_css()
st.title("🔐 Login to EduGenAgent")

role = st.selectbox("Login As", ["Student", "Faculty", "Admin"])
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):

    if not email or not password:
        st.warning("⚠️ Please enter email and password.")
    
    else:
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, first_name, password_hash, role 
                FROM users 
                WHERE email=%s""", (email,)) 
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user is None:
                st.error("❌ Email not found.")
            
            else:
                user_id, first_name, stored_hash, role = user

                if stored_hash and bcrypt.checkpw(
                    password.encode('utf-8'),
                    stored_hash.encode('utf-8')
                ):
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user_id
                    st.session_state["role"] = role
                    st.session_state["user_name"] = first_name

                    if role == "Student":
                        st.switch_page("pages/3_Student_Dashboard.py")
                    elif role == "Faculty":
                        st.switch_page("pages/4_Faculty_Dashboard.py")
                    else:
                        st.switch_page("pages/5_Admin_Dashboard.py")

                else:
                    st.error("❌ Incorrect password.")

        except Exception as e:
            st.error("Something went wrong during login.")
if st.button("Forgot Password?"):
    st.switch_page("pages/6_Forgot_Password.py")
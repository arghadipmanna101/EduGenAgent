import streamlit as st
import re
import psycopg2
import bcrypt
from database import get_connection
from psycopg2 import errors
from components.style import load_css
load_css()

st.title("📝 Create Your EduGenAgent Account")

st.markdown("Join the AI-powered intelligent learning ecosystem.")

st.divider()

# Role selection
role = st.selectbox("Register As", ["Student", "Faculty"])

# Form container
with st.form("registration_form"):

    col1, col2 = st.columns(2)

    with col1:
        first_name = st.text_input("First Name")
        email = st.text_input("Email")

    with col2:
        last_name = st.text_input("Last Name")
        password = st.text_input("Password", type="password")

    confirm_password = st.text_input("Confirm Password", type="password")

    submit = st.form_submit_button("🚀 Register")
    


if submit:

    if not first_name or not last_name or not email or not password:
        st.error("⚠️ All fields are required.")

    elif password != confirm_password:
        st.error("⚠️ Passwords do not match.")

    else:
        try:
            # 🔐 HASH PASSWORD
            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (first_name, last_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, email, hashed_password, role))

            conn.commit()
            cursor.close()
            conn.close()

            st.success("✅ Registration Successful!")

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            st.error("⚠️ Email already registered. Please login.")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
# Validation logic
if submit:

    if not first_name or not last_name or not email or not password:
        st.error("⚠️ All fields are required.")

    elif password != confirm_password:
        st.error("⚠️ Passwords do not match.")

    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        st.error("⚠️ Invalid email format.")

    else:
        # For now just simulate registration
        st.success("✅ Registration Successful!")

        # Store session data (temporary)
        st.session_state["user"] = email
        st.session_state["role"] = role

        st.info("You can now login from the Login page.")
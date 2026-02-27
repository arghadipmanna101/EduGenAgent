import streamlit as st
import bcrypt
import psycopg2
from database import get_connection

st.title("🔑 Forgot Password")

email = st.text_input("Enter your registered email")
new_password = st.text_input("New Password", type="password")
confirm_password = st.text_input("Confirm New Password", type="password")

if st.button("Reset Password"):

    if not email or not new_password or not confirm_password:
        st.error("⚠️ All fields are required.")

    elif new_password != confirm_password:
        st.error("⚠️ Passwords do not match.")

    else:
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if user:
                # Hash new password
                hashed_password = bcrypt.hashpw(
                    new_password.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')

                cursor.execute("""
                    UPDATE users
                    SET password_hash=%s
                    WHERE email=%s
                """, (hashed_password, email))

                conn.commit()
                st.success("✅ Password updated successfully. Please login.")

            else:
                st.error("❌ Email not found.")

            cursor.close()
            conn.close()

        except Exception as e:
            st.error(f"Something went wrong: {e}")
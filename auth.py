
import streamlit as st
import db

SESSION_KEY = "tomaya_user"

def login(con):
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = None
    if st.session_state[SESSION_KEY] is None:
        st.title("Login — Tomaya Business Cloud")
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            cur = con.cursor()
            cur.execute("SELECT username,password_hash,role,is_active FROM users WHERE username=?", (u.strip(),))
            row = cur.fetchone()
            if (not row) or row["is_active"] != 1 or (not db.verify_password(p, row["password_hash"])):
                st.error("Invalid login.")
                st.stop()
            st.session_state[SESSION_KEY] = {"username": row["username"], "role": row["role"]}
            db.log(con, row["username"], "LOGIN")
            st.rerun()
        st.stop()
    return st.session_state[SESSION_KEY]

def logout(con):
    if st.sidebar.button("Logout"):
        u = st.session_state.get(SESSION_KEY)
        if u:
            db.log(con, u.get("username"), "LOGOUT")
        st.session_state[SESSION_KEY] = None
        st.rerun()

"""Small helpers for Streamlit login state."""
import streamlit as st

def current_user():
    return st.session_state.get("user")

def require_role(role):
    user = current_user()
    return bool(user and user.get("role") == role)

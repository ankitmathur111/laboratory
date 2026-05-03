"""Session state helpers for Streamlit."""
import streamlit as st


def init_session_state():
    defaults = {
        "analyses": [],
        "total_analyses": 0,
        "total_shots": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

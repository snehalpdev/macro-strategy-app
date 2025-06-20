import streamlit as st

def load_secrets():
    return {
        "FRED_API_KEY": st.secrets.get("FRED_API_KEY", "demo_key")
    }
import os
from dotenv import load_dotenv

def load_secrets():
    secrets = {}

    # First try Streamlit secrets
    try:
        import streamlit as st
        secrets["FRED_API_KEY"] = st.secrets["FRED_API_KEY"]
        secrets["GDRIVE_FOLDER_ID"] = st.secrets["GDRIVE_FOLDER_ID"]
    except Exception:
        pass

    # Fallback to .env
    if not secrets.get("FRED_API_KEY"):
        load_dotenv()
        secrets["FRED_API_KEY"] = os.getenv("FRED_API_KEY")
        secrets["GDRIVE_FOLDER_ID"] = os.getenv("GDRIVE_FOLDER_ID")

    return secrets
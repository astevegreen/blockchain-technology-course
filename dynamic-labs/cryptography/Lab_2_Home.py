import streamlit as st
import os

# Must be the very first Streamlit command
st.set_page_config(page_title="Applied Cryptography", layout="wide")

from progress_beacon import fire as _fire_progress
_fire_progress("home")

# st.title("Applied Cryptography & Identity")

readme_path = "STUDENT_README.md"

try:
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.error(
            f"[ERROR]: {readme_path} not found in the current directory. Please ensure the file is present."
        )
except Exception as e:
    st.error(f"[ERROR]: Could not load {readme_path}. Details: {str(e)}")

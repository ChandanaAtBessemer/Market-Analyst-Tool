# test_file_chat.py

import streamlit as st
from file_uploader_agent import upload_pdf_and_get_file_id
from file_query_agent import query_pdf_file

st.set_page_config(page_title="📄 Ask About PDF", layout="wide")
st.title("💬 Query Uploaded PDF (Single Upload, Multiple Questions)")

uploaded_file = st.file_uploader("Upload PDF for analysis:", type=["pdf"])
query = st.text_input("Ask a question about the PDF")

if uploaded_file:
    file_id = upload_pdf_and_get_file_id(uploaded_file)
    if query and st.button("🔍 Ask"):
        with st.spinner("Thinking..."):
            response = query_pdf_file(file_id, query)
            st.markdown(response)

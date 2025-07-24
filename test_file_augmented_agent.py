'''
import streamlit as st
from file_augmented_agent import get_file_augmented_market_report

st.set_page_config(page_title="📄 Half-PDF File Tester")

st.title("🧪 Test: Half-PDF Upload Market Analysis")

uploaded_file = st.file_uploader("Upload a PDF (max 150 pages):", type=["pdf"])
market_query = st.text_input("Enter your market question:")

if st.button("Run Analysis"):
    if uploaded_file and market_query:
        with st.spinner("Analyzing first half of your PDF..."):
            result = get_file_augmented_market_report(query=market_query, uploaded_files=[uploaded_file])
            st.markdown("### 📊 Augmented Market Report")
            st.markdown(result)
    else:
        st.warning("Upload a PDF and enter your query.")
'''

from file_augmented_agent import get_file_augmented_market_report
import streamlit as st
st.title("📂 PDF Market Report - Augmented")

uploaded_files = st.file_uploader("Upload PDF", type=["pdf"], accept_multiple_files=True)
query = st.text_input("Enter a market-related question")

if st.button("Run"):
    if uploaded_files and query:
        report = get_file_augmented_market_report(query=query, uploaded_files=uploaded_files)
        st.markdown(report)

import os
import fitz  # PyMuPDF
from openai import OpenAI
from dotenv import load_dotenv
import tempfile
import time
import streamlit as st
load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
CHUNK_SIZE = 50  # Number of pages per chunk
PROMPT_TEMPLATE = """
You are a market analyst. Based on the PDF content provided, extract a table of key market insights (e.g. CAGR, market size, top companies, segmentation, trends).

Only use content from the uploaded PDF.

"""

def split_pdf_file(file_stream, chunk_size=CHUNK_SIZE):
    """
    Splits a PDF into chunks of `chunk_size` pages each and returns (start, end, file_path) per chunk.
    """
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    total_pages = len(doc)
    chunks = []

    for start in range(0, total_pages, chunk_size):
        end = min(start + chunk_size, total_pages)
        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(doc, from_page=start, to_page=end - 1)

        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        chunk_doc.save(temp_path)
        chunk_doc.close()
        chunks.append((start + 1, end, temp_path))

    doc.close()
    return chunks

def get_file_augmented_market_report(query: str, uploaded_files: list) -> str:
    if not uploaded_files:
        return "⚠️ No files uploaded."

    file = uploaded_files[0]  # Only support 1 PDF for now
    chunks = split_pdf_file(file, chunk_size=CHUNK_SIZE)
    combined_output = ""

    for idx, (start_page, end_page, path) in enumerate(chunks):
        print(f"📄 Processing chunk {idx+1}/{len(chunks)}: Pages {start_page}-{end_page}")
        try:
            with open(path, "rb") as f:
                uploaded = client.files.create(file=f, purpose="user_data")

            response = client.responses.create(
                        model="gpt-4o",
                        input=[{
                            "role": "user",
                            "content": [
                                {"type": "input_file", "file_id": uploaded.id},
                                {"type": "input_text", "text": f"{PROMPT_TEMPLATE.strip()}\n\nUser Question: {query}"}
                            ]
                        }]
                    )

            text = response.output_text.strip()
            if text and "no valid insight" not in text.lower():
                combined_output += f"\n\n### 📄 Pages {start_page}-{end_page}\n{text}"
            else:
                combined_output += f"\n❌ No valid insights for pages {start_page}-{end_page}."

        except Exception as e:
            combined_output += f"\n❌ Error on pages {start_page}-{end_page}: {e}"

        time.sleep(1.5)  # Basic rate-limit protection

    return combined_output.strip() or "⚠️ No valid insights extracted from the uploaded PDF."

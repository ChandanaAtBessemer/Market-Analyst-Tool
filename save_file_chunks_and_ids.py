# save_file_chunks_and_ids.py

import os
import fitz  # PyMuPDF
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
CHUNK_SIZE = 50  # pages per chunk

def split_and_upload_pdf(pdf_path: str, output_json="saved_file_ids.json"):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    saved_ids = []

    for i in range(0, total_pages, CHUNK_SIZE):
        chunk_doc = fitz.open()
        end_page = min(i + CHUNK_SIZE, total_pages)
        chunk_doc.insert_pdf(doc, from_page=i, to_page=end_page - 1)

        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        chunk_doc.save(temp_path)
        chunk_doc.close()

        with open(temp_path, "rb") as f:
            uploaded = client.files.create(file=f, purpose="user_data")
            print(f"✅ Uploaded chunk {i+1}-{end_page}: {uploaded.id}")
            saved_ids.append({"start": i+1, "end": end_page, "file_id": uploaded.id})

    doc.close()

    with open(output_json, "w") as f:
        json.dump(saved_ids, f, indent=2)
    print(f"📝 Saved file IDs to: {output_json}")

# Example usage
if __name__ == "__main__":
    split_and_upload_pdf("global_forecast.pdf")

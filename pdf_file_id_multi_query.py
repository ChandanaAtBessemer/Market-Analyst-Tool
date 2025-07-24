import os
from openai import OpenAI
from dotenv import load_dotenv
import fitz  # PyMuPDF

load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def upload_pdf_to_openai(pdf_path: str) -> str:
    with open(pdf_path, "rb") as f:
        file = client.files.create(file=f, purpose="user_data")
    print(f"✅ Uploaded PDF. File ID: {file.id}")
    return file.id

def query_uploaded_pdf(file_id: str, query: str) -> str:
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_file", "file_id": file_id},
                    {"type": "input_text", "text": query}
                ]
            }
        ]
    )
    return response.output_text.strip()

if __name__ == "__main__":
    # STEP 1: Upload PDF once (you can reuse the ID later)
    file_path = "global_forecast.pdf"  # Replace with your PDF path
    file_id = upload_pdf_to_openai(file_path)

    # STEP 2: Ask multiple queries using that file ID
    while True:
        query = input("\n❓ Enter a question (or 'exit' to quit): ")
        if query.lower() == "exit":
            break
        try:
            answer = query_uploaded_pdf(file_id, query)
            print("\n💡 Answer:\n", answer)
        except Exception as e:
            print(f"❌ Error: {e}")

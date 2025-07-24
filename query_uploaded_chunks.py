import time
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def query_chunks(query: str, file_id_chunks: list) -> str:
    full_response = ""
    for chunk in file_id_chunks:
        file_id = chunk["file_id"]
        start, end = chunk["start"], chunk["end"]
        print(f"🔍 Querying pages {start}-{end} (File ID: {file_id})")

        try:
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
            full_response += f"\n\n### 📄 Pages {start}-{end}\n" + response.output_text.strip()
        except Exception as e:
            full_response += f"\n❌ Error on pages {start}-{end}: {e}"

        time.sleep(1.5)

    return full_response.strip()

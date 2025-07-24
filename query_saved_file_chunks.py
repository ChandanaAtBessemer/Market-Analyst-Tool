# query_saved_file_chunks.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT_TEMPLATE = """
You are a market research analyst.
Only answer from the content in the provided file.

Format the response in a markdown table if applicable. Be factual, concise, and avoid summaries.
"""

def query_files(file_ids_path, query_text):
    with open(file_ids_path, "r") as f:
        file_chunks = json.load(f)

    combined_output = ""

    for chunk in file_chunks:
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
                            {"type": "input_text", "text": query_text}
                        ]
                    }
                ]
            )
            combined_output += f"\n\n### 📄 Pages {start}-{end}\n{response.output_text.strip()}"
        except Exception as e:
            combined_output += f"\n❌ Error on pages {start}-{end}: {e}"
        time.sleep(1.5)

    return combined_output.strip()

# Example usage
if __name__ == "__main__":
    query = input("Enter your query: ")
    result = query_files("saved_file_ids.json", query)
    print("\n📊 Combined Answer:\n")
    print(result)

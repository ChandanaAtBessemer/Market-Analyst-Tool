# openai_handler.py

import os
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
import streamlit as st
load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
TOOLS = [
    {"type": "web_search_preview"}
]

VERTICAL_PROMPT = """
You are a precise Market Research Assistant.

Given a market name, return only its **vertical sub-markets** in a Markdown table format.

### Vertical Sub-markets

| Sub-market | Source |
|------------|--------|

- Use **real sources** for each row. Format each source as `[source](https://...)`
- Include 8–10 sub-markets, each representing a specific end-use sector (e.g., Automotive, Healthcare, Construction, etc.)
- Do not include horizontal services like logistics or IT platforms
- No explanation — just the table
"""

def get_vertical_submarkets(market_query: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            print(f"🔍 Fetching verticals for {market_query} [attempt {attempt+1}]")
            response = client.responses.create(
                model="gpt-4o",
                input=market_query,
                tools=TOOLS,
                instructions=VERTICAL_PROMPT
            )
            final = next((o for o in response.output if getattr(o, "type", "") == "message"), None)
            return "".join(part.text for part in final.content).strip() if final else "(no output)"
        except RateLimitError:
            delay = 3 + attempt * 2
            print(f"⚠️ Rate limit. Retrying in {delay}s...")
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Error fetching vertical submarkets: {e}")
            break
    return "⚠️ Failed to retrieve vertical sub-markets."

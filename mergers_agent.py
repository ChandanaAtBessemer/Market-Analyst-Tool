# mergers_agent.py

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOLS = [{"type": "web_search_preview"}]

MERGERS_PROMPT_TEMPLATE = """
You are a research assistant specializing in M&A activity.

The user is interested in **Mergers & Acquisitions** in the market: "{market}" during the timeframe: "{timeframe}".

Return only a **Markdown table** with the following columns:
- Acquirer
- Acquirer HQ
- Target
- Target HQ
- Description
- Date
- Source (hyperlinked in Markdown format)

Instructions:
- List 5–10 relevant M&A events from trusted sources (Reuters, BusinessWire, PR Newswire, company press releases, etc).
- Do not guess. Only use real M&A data that fits the market and time window.
- Skip SPACs and IPOs.
- Avoid unrelated finance news or generic market summaries.

No commentary or explanation. Just the table.
"""

def get_mergers_table(market: str, timeframe: str, retries: int = 3) -> str:
    prompt = MERGERS_PROMPT_TEMPLATE.format(market=market, timeframe=timeframe)
    for attempt in range(retries):
        try:
            print(f"🔍 Fetching M&A data for '{market}' in '{timeframe}' (attempt {attempt + 1})")
            response = client.responses.create(
                model="gpt-4o",
                input=market,
                tools=TOOLS,
                instructions=prompt
            )
            final = next((o for o in response.output if getattr(o, "type", "") == "message"), None)
            return "".join(part.text for part in final.content).strip() if final else "⚠️ No output returned."
        except RateLimitError:
            delay = 3 + attempt * 2
            print(f"⚠️ Rate limit. Retrying in {delay}s...")
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    return "⚠️ Failed to retrieve M&A data."

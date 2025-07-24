# horizontal_handler.py

import os
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOLS = [
    {"type": "web_search_preview"}
]

# === STRONG PROMPT ===
PROMPT_TEMPLATE = """
You are a market analyst. The user wants to understand **horizontal market players** in the {industry} sector.

Horizontal companies or segments:
- Operate across multiple verticals
- Provide B2B infrastructure, platforms, tools, services, or manufacturing processes

Examples include: injection molding providers, logistics platforms, resin suppliers, additive manufacturers, automation services, and major B2B vendors like Berry Global or Sabic.

Return a Markdown table with **10 horizontal sub-markets or companies**, and provide **source links** for each.

Format:
### Horizontal Sub-markets

| Sub-market or Company | Description | Source |
|-----------------------|-------------|--------|

No paragraphs. No introductions. Just the table.
"""

def get_horizontal_submarkets(industry: str, retries: int = 3) -> str:
    prompt = PROMPT_TEMPLATE.format(industry=industry)
    for attempt in range(retries):
        try:
            print(f"🔍 Fetching horizontals for {industry} [attempt {attempt+1}]")
            response = client.responses.create(
                model="gpt-4o",
                input=industry,
                tools=TOOLS,
                instructions=prompt
            )
            final = next((o for o in response.output if getattr(o, "type", "") == "message"), None)
            return "".join(part.text for part in final.content).strip() if final else "(no output)"
        except RateLimitError:
            delay = 3 + attempt * 2
            print(f"⚠️ Rate limit. Retrying in {delay}s...")
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Error fetching horizontal submarkets: {e}")
            break
    return "⚠️ Failed to retrieve horizontal sub-markets."

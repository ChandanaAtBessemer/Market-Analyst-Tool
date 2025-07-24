# global_metrics_agent.py

import os
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOLS = [{"type": "web_search_preview"}]

GLOBAL_METRIC_PROMPT = """
You are a market research assistant with access to reliable data.

Given a market name (e.g., "Plastic Market in the US"), return a single **Markdown table** summarizing its **historical and projected global revenue** and **CAGR**. Use only **verified data** between 2018–2023 and forecasts beyond that, if available.

### The Markdown table must contain three columns:
- **Metric**
- **Value**
- **Source** — using Markdown hyperlink format: [Source Name](https://...)

### Mandatory Instructions:
- Include real and recent **revenue figures** from 2018, 2020, 2023, 2024 (if available), and 2030.
- Provide **CAGR values** if found. If not directly provided, calculate it based on reliable revenue points and mention this.
- Avoid repeating identical values from the same sources (de-duplicate).
- Never fabricate values. Only use well-known research publishers like:
  - Grand View Research
  - Fortune Business Insights
  - MarketsandMarkets
  - Precedence Research
  - Exactitude Consultancy
  - Verified market news sources

### Important Rules:
- No explanation, comments, or extra text before or after the table.
- Do not add "###" headings or summaries.
- Use **consistent units**: all revenue in **USD Billion**.
- If CAGR is calculated, specify the time frame and basis in the Value cell.

### Output Format Example:
| Metric | Value | Source |
|--------|-------|--------|
| Revenue in 2018 (USD Billion) | 112.6 | [Market Research Future](https://example.com) |
| Revenue in 2023 (USD Billion) | 90.1 | [Grand View Research](https://example.com) |
| Revenue in 2030 (USD Billion) | 114.6 | [Grand View Research](https://example.com) |
| CAGR (2024–2030) | 3.5% (stated by source) | [Grand View Research](https://example.com) |
| CAGR (2018–2023) | -4.3% (calculated) | Based on revenue from 2018 to 2023 |

Only return the Markdown table. Do not include anything else.
"""



def get_global_overview(market: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            print(f"🌍 Fetching global metrics for {market} (attempt {attempt+1})")
            response = client.responses.create(
                model="gpt-4o",
                input=market,
                tools=TOOLS,
                instructions=GLOBAL_METRIC_PROMPT,
            )
            final = next((o for o in response.output if getattr(o, "type", "") == "message"), None)
            return "".join(part.text for part in final.content).strip() if final else "⚠️ No output returned."
        except RateLimitError:
            delay = 3 + attempt * 2
            print(f"⚠️ Rate limit hit. Retrying in {delay}s...")
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    return "⚠️ Failed to fetch global overview."

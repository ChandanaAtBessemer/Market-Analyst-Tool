# metrics_agent.py

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

SYSTEM_PROMPT = """
You are a market research assistant with web access via the `web_search_preview` tool.
For a given submarket, search the web and return:
- Market Size (USD)
- CAGR
- Forecast Years
Present the results in a **Markdown table** with columns: Metric | Value | Source.
Use only trusted sources: Grand View Research, Mordor Intelligence, MarketsandMarkets, Fortune Business Insights.
Each value must include a [source](URL) link.
Only return the table. No text or explanation.
Strict rules:
- No extra text
- No paragraphs
-ONLY return results that **explicitly match the submarket name**

- Just the Markdown table
"""

TOOLS = [{"type": "web_search_preview"}]

def get_detailed_metrics(submarket: str) -> str:
    user_query = f"Get the market size, CAGR, and forecast period for '{submarket}' market from 2018 to 2023 ."

    response = client.responses.create(
        model="gpt-4o",
        input=user_query,
        instructions=SYSTEM_PROMPT,
        tools=TOOLS
    )

    for item in response.output:
        if getattr(item, "type", "") == "message":
            return "".join([c.text for c in item.content])

    return "❌ No output message from model."

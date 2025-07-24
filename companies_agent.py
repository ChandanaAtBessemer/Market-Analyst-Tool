# companies_agent.py

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

MODEL = "gpt-4o"


SYSTEM_PROMPT = """
You are a precise market research assistant with web access (web_search_preview).
Your job is to find only metrics (market size, CAGR, forecast years) **specifically for the requested submarket**.
Examples: "Plastics in Electrical and Electronics", "Plastics in Automotive"
Return your answer in a **Markdown table** with 2 columns:
- Company Name
- The are occupied by this comapny in this particular market in  percentage (Provide an intelligent estimate, Also mention the basis of this estimation)
- Source (in Markdown [source](url) format)


Strict rules:
- No extra text
- No paragraphs
-ONLY return results that **explicitly match the submarket name**
- If nothing specific is found when it comes to market shares , you may provide an intelligent guess and explicitly mention it, but whean a value is clear and factual mentioan that as well(MUST)
- Never generalize to broader markets like 'Plastics' or 'Plastic Packaging'
- Just the Markdown table
"""

TOOLS = [{"type": "web_search_preview"}]

def get_top_companies(submarket: str) -> str:
    prompt = (
        f"List the top companies in the '{submarket}' market in US using reports published between 2018 and 2023. "
        "Use trusted sources like Grand View, Mordor, MarketsandMarkets, FortuneBI. Format as a Markdown table."
    )

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        instructions=SYSTEM_PROMPT,
        tools=TOOLS,
        temperature=0.3
    )

    for item in response.output:
        if getattr(item, "type", "") == "message":
            return "".join([c.text for c in item.content])

    return "❌ No output from GPT-4o."

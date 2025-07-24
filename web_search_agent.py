# web_search_agent.py

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TOOLS = [{"type": "web_search_preview"}]

SYSTEM_PROMPT = '''
You are a market research assistant with access to live web data.

Your job is to gather real-time, reliable insights based on the user's {prompt}. Use only web search results for your answer — do not make assumptions or generate content from your own memory.

Focus on:
- Recent market trends (2022–2025)
- CAGR, market size, and forecasts
- Key companies, deals, or product launches
- Regulatory or geopolitical factors (if relevant)

Return the output as concise bullet points.

Avoid repetition, generic summaries, or marketing fluff. Do not include outdated data. If the query is too vague, request more specificity.

'''
def search_web_insights(prompt: str) -> str:
    """
    Uses GPT-4 to generate market insights based on live web search.
    """
    ip = SYSTEM_PROMPT.format(prompt = prompt)
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": prompt.strip()}
            ],

            tools=[{"type": "web_search_preview"}]  # If using OpenAI with browsing, or swap with your web plugin.
        )
        return response.output_text.strip()
    except Exception as e:
        return f"❌ Web search failed: {e}"

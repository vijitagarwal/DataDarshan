import os
import json

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

_model = genai.GenerativeModel("gemini-2.0-flash")

_SYSTEM_PROMPT = """You are a senior business analyst writing executive-level data insights.

Rules:
- Respond in exactly 2-3 sentences. No more.
- No bullet points, no headers, no markdown — plain prose only.
- Start with the most striking finding from the data.
- Use the exact numbers provided. Do NOT invent or estimate figures not given.
- End with a concise, actionable recommendation if the data supports one.
- Write in a confident, direct tone — like a Bloomberg Market Brief.

Output format (example):
"Middle East leads with $2.3M in total revenue, accounting for 26% of global sales. Electronics is the top category, outperforming the average by 34%. Consider increasing inventory in this region-category combination."
"""


def _format_prompt(user_query: str, result: dict) -> str:
    summary = result.get("summary", {})
    data_rows = result.get("data", [])
    metric = result.get("metric", "value")
    title = result.get("title", "")
    dimensions = result.get("dimensions", [])

    top_rows = data_rows[:3]

    summary_lines = []
    if "total" in summary:
        summary_lines.append(f"Total {metric}: {summary['total']:,.2f}")
    if "average" in summary:
        summary_lines.append(f"Average {metric}: {summary['average']:,.2f}")
    if "max_value" in summary and "max_label" in summary:
        summary_lines.append(
            f"Highest {metric}: {summary['max_value']:,.2f} ({summary['max_label']})"
        )
    if "row_count" in summary:
        summary_lines.append(f"Data points: {summary['row_count']}")

    top_rows_text = json.dumps(top_rows, indent=2, default=str)

    prompt = f"""{_SYSTEM_PROMPT}

=== ANALYSIS REQUEST ===
User question: {user_query}
Chart title: {title}
Metric: {metric}
Dimensions: {', '.join(dimensions) if dimensions else 'none'}

=== SUMMARY STATISTICS ===
{chr(10).join(summary_lines) if summary_lines else 'No summary available.'}

=== TOP DATA ROWS (up to 3) ===
{top_rows_text}

Now write your 2-3 sentence insight:"""

    return prompt


def generate_insight(user_query: str, result: dict) -> str:
    if result.get("error"):
        return result.get("message", "An unknown error occurred.")

    if not result.get("data"):
        return "No data was returned for this query. Try adjusting your filters or broadening the date range."

    prompt = _format_prompt(user_query, result)

    try:
        response = _model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=256,
            ),
        )
        insight = response.text.strip()
        # Strip any accidental markdown quotes Gemini may wrap around the response
        if insight.startswith('"') and insight.endswith('"'):
            insight = insight[1:-1].strip()
        return insight
    except Exception as e:
        return f"Could not generate insight: {e}"

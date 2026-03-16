import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY")
_CONFIG_ERROR: str | None = (
    "GEMINI_API_KEY not found in .env file. "
    "Create a .env file in the project root containing:\n\nGEMINI_API_KEY=your_key_here"
    if not _API_KEY
    else None
)

if _API_KEY:
    genai.configure(api_key=_API_KEY)

_model = genai.GenerativeModel("gemini-2.0-flash") if _API_KEY else None

SYSTEM_PROMPT = """You are a BI query parser for a sales dataset. Your ONLY job is to convert a natural language question into a structured JSON query object. You must NEVER return anything other than valid JSON.

=== DATASET COLUMNS ===
DATE:
  - order_date       : date (range: 2022-01-01 to 2023-12-31)
  - year             : derived integer (2022 or 2023)
  - month            : derived integer (1–12)
  - month_name       : derived string (January … December)
  - quarter          : derived integer (1, 2, 3, or 4)

CATEGORICAL (use ONLY these exact values as filter values):
  - product_category : Beauty | Books | Electronics | Fashion | Home & Kitchen | Sports
  - customer_region  : Asia | Europe | Middle East | North America
  - payment_method   : Cash on Delivery | Credit Card | Debit Card | UPI | Wallet

NUMERIC (valid for metric and numeric filters):
  - price            : unit price of the product
  - discount_percent : discount applied (integer %)
  - quantity_sold    : number of units sold
  - rating           : customer rating (1.0 – 5.0)
  - review_count     : number of reviews
  - discounted_price : price after discount
  - total_revenue    : total revenue = discounted_price × quantity_sold

IDENTIFIER (do NOT use as metric):
  - order_id         : integer order identifier
  - product_id       : integer product identifier

=== OUTPUT SCHEMA ===
Return ONLY this JSON — no markdown fences, no explanation, no extra keys:

{
  "metric":      "<numeric column to aggregate>",
  "aggregation": "<sum | mean | count | max | min>",
  "dimensions":  ["<column(s) to group by>"],
  "filters": [
    {"field": "<column>", "op": "<eq | ne | gt | lt | gte | lte | in>", "value": <scalar or list>}
  ],
  "chart_type":  "<bar | line | pie | scatter | heatmap>",
  "sort_by":     "<metric | dimension_name>",
  "sort_order":  "<asc | desc>",
  "limit":       <integer, default 10>,
  "title":       "<concise human-readable chart title>",
  "x_label":     "<x-axis label>",
  "y_label":     "<y-axis label>"
}

=== RULES ===
1. FIELD VALIDATION
   - If the user mentions a field that is NOT in the column list above, return:
     {"error": true, "message": "Your query mentions '<field>' which is not available. Available fields are: order_date, product_category, customer_region, payment_method, price, discount_percent, quantity_sold, rating, review_count, discounted_price, total_revenue, year, month, month_name, quarter"}
   - Never invent columns.

2. QUARTER MAPPING
   - "Q1" or "first quarter"  → {"field": "quarter", "op": "eq", "value": 1}
   - "Q2" or "second quarter" → {"field": "quarter", "op": "eq", "value": 2}
   - "Q3" or "third quarter"  → {"field": "quarter", "op": "eq", "value": 3}
   - "Q4" or "fourth quarter" → {"field": "quarter", "op": "eq", "value": 4}

3. YEAR MAPPING (dataset only has 2022 and 2023)
   - "2022" or "last year"            → {"field": "year", "op": "eq", "value": 2022}
   - "2023" or "this year" or "recent"→ {"field": "year", "op": "eq", "value": 2023}

4. CHART SELECTION HEURISTICS
   - 1 dimension, ranking/comparison  → bar
   - time-based dimension (month/quarter/year) → line
   - share/proportion question → pie
   - two numeric axes / correlation → scatter
   - two categorical dimensions → heatmap

5. AGGREGATION DEFAULTS
   - "total", "sum", "revenue", "sales" → sum
   - "average", "avg", "mean"           → mean
   - "highest", "maximum", "max"        → max
   - "lowest", "minimum", "min"         → min
   - "how many", "count", "number of"   → count

6. AMBIGUITY
   - If the intent is ambiguous, make the most reasonable assumption and proceed.
   - Do NOT ask clarifying questions. Always return a valid JSON object.

7. LIMIT
   - Default limit is 10.
   - If user says "top 5" → limit: 5, sort_order: "desc"
   - If user says "bottom 3" → limit: 3, sort_order: "asc"
   - "all" → limit: 999

Remember: output ONLY the raw JSON object. No markdown, no prose, no code fences.
"""


def _extract_json(text: str) -> dict:
    """Strip markdown fences and extract the first JSON object from text."""
    text = text.strip()
    # Remove markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Find the first {...} block in case there is surrounding text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model response: {text!r}")

    return json.loads(match.group())


def parse_query(user_query: str, previous_context: dict = None) -> dict:
    """
    Convert a natural-language BI question into a structured query dict.

    Args:
        user_query:        The user's plain-text question about the sales dataset.
        previous_context:  Optional parsed dict from the previous turn, used to
                           give Gemini continuity for follow-up / refinement queries.

    Returns:
        A dict matching the JSON schema above, or an error dict:
        {"error": True, "message": "..."}
    """
    if not user_query or not user_query.strip():
        return {
            "error": True,
            "message": "Query is empty. Please ask a question about the sales data.",
        }

    if _CONFIG_ERROR:
        return {"error": True, "message": _CONFIG_ERROR}

    context_block = ""
    if previous_context and not previous_context.get("error"):
        prev_title = previous_context.get("title", "the previous query")
        prev_metric = previous_context.get("metric", "")
        prev_dims = ", ".join(previous_context.get("dimensions") or [])
        context_block = (
            f"\n\n=== CONVERSATION CONTEXT ===\n"
            f"The user previously asked for: \"{prev_title}\".\n"
            f"Previous metric: {prev_metric}. Previous dimensions: {prev_dims or 'none'}.\n"
            f"They are now refining or following up on that query. "
            f"Reuse filters/dimensions from the previous query where the new query is ambiguous, "
            f"but override them explicitly if the user specifies something new.\n"
        )

    prompt = f"{SYSTEM_PROMPT}{context_block}\n\n=== USER QUERY ===\n{user_query.strip()}"

    _gen_cfg = genai.types.GenerationConfig(temperature=0.1, max_output_tokens=512)

    try:
        raw = _model.generate_content(prompt, generation_config=_gen_cfg).text

        # Attempt 1: parse the response
        try:
            parsed = _extract_json(raw)
        except (json.JSONDecodeError, ValueError):
            # Attempt 2: retry with a stricter reminder appended
            retry_prompt = (
                prompt
                + "\n\n⚠ RETRY: Your previous response was not valid JSON. "
                "Output ONLY a raw JSON object that starts with { and ends with }. "
                "No markdown, no prose, no code fences — just the JSON object."
            )
            raw = _model.generate_content(
                retry_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0, max_output_tokens=512
                ),
            ).text
            try:
                parsed = _extract_json(raw)
            except (json.JSONDecodeError, ValueError):
                return {
                    "error": True,
                    "message": (
                        "The AI returned an unreadable response twice in a row. "
                        "Please try rephrasing your question."
                    ),
                }

    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to reach the AI service: {e}",
        }

    # Normalise error flag to Python bool
    if "error" in parsed and parsed["error"] not in (True, False):
        parsed["error"] = bool(parsed["error"])

    return parsed

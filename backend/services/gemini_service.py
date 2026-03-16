"""Gemini LLM service - core intelligence layer."""
import json
import re
import google.generativeai as genai
from prompts.system_prompt import get_system_prompt


class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "max_output_tokens": 2048,
                "response_mime_type": "application/json",
            },
        )
        self._schema_cache: dict[str, dict] = {}

    def set_schema(self, table_name: str, schema_info: dict):
        """Cache schema for a table (used for uploaded CSVs)."""
        self._schema_cache[table_name] = schema_info

    def query(
        self,
        user_query: str,
        conversation_history: list[dict],
        table_name: str = "sales",
    ) -> dict:
        """Send query to Gemini and get structured response."""
        schema_info = self._schema_cache.get(table_name)
        system_prompt = get_system_prompt(schema_info)

        # Build conversation
        messages = []
        messages.append({"role": "user", "parts": [system_prompt]})
        messages.append({
            "role": "model",
            "parts": [
                "I understand. I will analyze queries against this schema and return "
                "structured JSON with SQL, chart configuration, and explanations."
            ],
        })

        # Add recent conversation history (last 6 messages = 3 turns)
        for msg in conversation_history[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["content"]]})

        # Add current query
        messages.append({"role": "user", "parts": [user_query]})

        chat = self.model.start_chat(history=messages[:-1])
        response = chat.send_message(messages[-1]["parts"][0])

        return self._parse_response(response.text)

    def retry_with_error(
        self,
        user_query: str,
        failed_sql: str,
        error_msg: str,
        table_name: str = "sales",
    ) -> dict:
        """Retry after SQL execution failure."""
        schema_info = self._schema_cache.get(table_name)
        system_prompt = get_system_prompt(schema_info)

        retry_prompt = (
            f"Your previous SQL query failed.\n"
            f"Original question: {user_query}\n"
            f"Failed SQL: {failed_sql}\n"
            f"Error: {error_msg}\n\n"
            f"Please fix the SQL query and return the corrected JSON response."
        )

        messages = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["I understand. I'll fix the SQL error."]},
            {"role": "user", "parts": [retry_prompt]},
        ]

        chat = self.model.start_chat(history=messages[:-1])
        response = chat.send_message(messages[-1]["parts"][0])

        return self._parse_response(response.text)

    def _parse_response(self, text: str) -> dict:
        """Parse LLM response, handling common formatting issues."""
        # Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strip markdown code fences
        cleaned = re.sub(r"^```(?:json)?\n?", "", text.strip())
        cleaned = re.sub(r"\n?```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Extract first JSON object
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse LLM response as JSON: {text[:200]}")

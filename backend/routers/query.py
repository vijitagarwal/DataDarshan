"""Query endpoint - the main pipeline."""
from fastapi import APIRouter, HTTPException
from models.request import QueryRequest
from models.response import QueryResponse
from services.gemini_service import GeminiService
from services.sql_service import execute_sql, validate_sql
from config import GEMINI_API_KEY, DB_PATH
import traceback

router = APIRouter()
gemini = GeminiService(GEMINI_API_KEY)


@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """Process a natural language query and return chart data."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # Step 1: Call Gemini
        conversation = [msg.model_dump() for msg in request.conversation_history]
        llm_response = gemini.query(
            request.query, conversation, request.table_name
        )

        # Handle error responses from the LLM
        if llm_response.get("chart_type") == "error":
            return QueryResponse(
                chart_type="error",
                explanation=llm_response.get("explanation", "I couldn't process that query."),
                follow_ups=llm_response.get("follow_ups", []),
            )

        sql = llm_response.get("sql", "")
        if not sql:
            return QueryResponse(
                chart_type="error",
                explanation="I couldn't generate a query for that request. Try rephrasing your question.",
                follow_ups=["Show me total revenue", "What are the top product categories?", "Show monthly sales trends"],
            )

        # Step 2: Validate and execute SQL
        try:
            data = execute_sql(DB_PATH, sql)
        except (ValueError, Exception) as e:
            # Retry once with error feedback
            try:
                retry_response = gemini.retry_with_error(
                    request.query, sql, str(e), request.table_name
                )
                sql = retry_response.get("sql", "")
                data = execute_sql(DB_PATH, sql)
                llm_response = retry_response
            except Exception:
                return QueryResponse(
                    sql=sql,
                    chart_type="error",
                    explanation=f"I had trouble querying the database. The generated SQL may have an issue. Error: {str(e)}",
                    follow_ups=["Try a simpler question", "Show me total revenue", "What columns are available?"],
                )

        # Step 3: Handle empty results
        if not data:
            return QueryResponse(
                sql=sql,
                chart_type="metric",
                chart_config={"title": "No Results", "metrics": []},
                data=[],
                explanation="No data matched your query. " + llm_response.get("explanation", ""),
                follow_ups=llm_response.get("follow_ups", ["Try a broader query"]),
            )

        # Step 4: Return successful response
        return QueryResponse(
            sql=sql,
            chart_type=llm_response.get("chart_type", "bar"),
            chart_config=llm_response.get("chart_config", {}),
            data=data[:1000],  # Limit rows for performance
            explanation=llm_response.get("explanation", ""),
            follow_ups=llm_response.get("follow_ups", []),
        )

    except Exception as e:
        traceback.print_exc()
        return QueryResponse(
            chart_type="error",
            explanation=f"Something went wrong: {str(e)}. Please try rephrasing your question.",
            follow_ups=["Show me total revenue", "What are the top categories?", "Show monthly trends"],
        )

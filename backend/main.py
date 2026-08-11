# -*- coding: utf-8 -*-
import io
import json
import traceback
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import chart_builder
import data_engine
import insight_gen
import llm_parser

app = FastAPI(
    title="DataDarshanam API",
    description="Backend API for Conversational BI Dashboard powered by Groq LLaMA 3.3",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    previous_context: Optional[Dict[str, Any]] = None


class DashboardRequest(BaseModel):
    query: str = "generate full dashboard overview"


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "dataदर्शनम् API"}


@app.get("/api/schema")
def get_schema():
    try:
        profile = data_engine.get_dataset_profile()
        suggested = data_engine.suggest_questions(5)
        return {
            "profile": profile,
            "suggested_questions": suggested,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def run_nl_query(req: QueryRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")

    query = req.query.strip()
    previous_context = req.previous_context

    try:
        schema_context = data_engine.build_schema_context()
        parsed = llm_parser.parse_query(
            query,
            previous_context=previous_context,
            schema_context=schema_context,
        )

        if parsed.get("error"):
            return {
                "success": False,
                "error": True,
                "query": query,
                "parsed": parsed,
                "message": parsed.get("message", "Unable to parse query"),
                "insight": parsed.get("message", "Unable to parse query"),
            }

        result = data_engine.run_query(parsed)
        if result.get("error"):
            return {
                "success": False,
                "error": True,
                "query": query,
                "parsed": parsed,
                "result": result,
                "message": result.get("message", "Error running query on dataset"),
                "insight": result.get("message", "Error running query on dataset"),
            }

        # Build figure for dark & light mode specs
        fig_dark = chart_builder.build_chart(result, is_dark=True)
        fig_light = chart_builder.build_chart(result, is_dark=False)
        insight = insight_gen.generate_insight(query, result)

        return {
            "success": True,
            "error": False,
            "query": query,
            "parsed": parsed,
            "result": result,
            "insight": insight,
            "fallback": insight_gen._last_used_fallback,
            "used_context": previous_context is not None,
            "plotly_spec": {
                "dark": json.loads(fig_dark.to_json()),
                "light": json.loads(fig_light.to_json()),
            },
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")


@app.post("/api/dashboard")
def run_dashboard_query(req: DashboardRequest):
    query = req.query.strip() if req.query else "generate full dashboard overview"
    try:
        dashboard_queries = llm_parser.parse_dashboard_query(query)
        if not dashboard_queries:
            # Fallback default queries
            dashboard_queries = [
                {"chart_type": "bar", "metric": "total_revenue", "dimensions": ["category"], "sort_order": "desc", "limit": 5, "title": "Top Categories by Revenue"},
                {"chart_type": "line", "metric": "total_revenue", "dimensions": ["month_name"], "sort_order": "asc", "limit": 12, "title": "Monthly Revenue Trend"},
                {"chart_type": "pie", "metric": "total_revenue", "dimensions": ["region"], "sort_order": "desc", "limit": 5, "title": "Revenue Distribution by Region"},
            ]

        charts = []
        for p in dashboard_queries:
            res = data_engine.run_query(p)
            if not res.get("error"):
                fig_dark = chart_builder.build_chart(res, is_dark=True)
                fig_light = chart_builder.build_chart(res, is_dark=False)
                charts.append({
                    "parsed": p,
                    "result": res,
                    "plotly_spec": {
                        "dark": json.loads(fig_dark.to_json()),
                        "light": json.loads(fig_light.to_json()),
                    }
                })

        return {
            "success": True,
            "query": query,
            "charts": charts
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV format")

    try:
        contents = await file.read()
        raw_str = contents.decode("utf-8")
        df_up = pd.read_csv(io.StringIO(raw_str))
        df_up = data_engine.prepare_dataframe(df_up)
        data_engine.set_dataframe(df_up)

        profile = data_engine.get_dataset_profile()
        suggested = data_engine.suggest_questions(5)

        return {
            "success": True,
            "filename": file.filename,
            "rows": len(df_up),
            "profile": profile,
            "suggested_questions": suggested,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"CSV processing failed: {str(e)}")

# -*- coding: utf-8 -*-
from __future__ import annotations

import re

import pandas as pd

DATA_PATH = "sales.csv"
ROW_COUNT_METRIC = "__row_count"
_TIME_COLUMNS = {"year", "month", "month_name", "quarter"}
_MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _is_likely_date_column(name: str, series: pd.Series) -> bool:
    """Heuristic for uploaded CSVs where date columns arrive as strings."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    name_hint = bool(re.search(r"date|time|created|updated|day", name, re.I))
    if not name_hint or not pd.api.types.is_object_dtype(series):
        return False

    sample = series.dropna().astype(str).head(100)
    if sample.empty:
        return False

    parsed = pd.to_datetime(sample, errors="coerce")
    return parsed.notna().mean() >= 0.75


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    date_columns: list[str] = []
    for col in df.columns:
        if _is_likely_date_column(col, df[col]):
            converted = pd.to_datetime(df[col], errors="coerce")
            if converted.notna().any():
                df[col] = converted
                date_columns.append(col)

    if date_columns:
        primary_date = "order_date" if "order_date" in date_columns else date_columns[0]
        df["year"]       = df[primary_date].dt.year.astype("Int64")
        df["month"]      = df[primary_date].dt.month.astype("Int64")
        df["month_name"] = df[primary_date].dt.strftime("%b")
        df["quarter"]    = df[primary_date].dt.quarter.astype("Int64")

    return df

# ---------------------------------------------------------------------------
# Module-level data load (cached for the lifetime of the process)
# ---------------------------------------------------------------------------

def _load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return _prepare_dataframe(df)

_DF: pd.DataFrame = _load_data(DATA_PATH)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_OPS = {
    "eq":  lambda s, v: s == v,
    "neq": lambda s, v: s != v,
    "ne":  lambda s, v: s != v,        # alias
    "gt":  lambda s, v: s > v,
    "lt":  lambda s, v: s < v,
    "gte": lambda s, v: s >= v,
    "lte": lambda s, v: s <= v,
    "in":  lambda s, v: s.isin(v if isinstance(v, list) else [v]),
}

_AGG_FUNCS = {
    "sum":   "sum",
    "mean":  "mean",
    "count": "count",
    "max":   "max",
    "min":   "min",
}

# Columns that represent ordered time for nicer sort ordering
_TIME_DIMS = {"year", "month", "quarter"}


def _err(message: str) -> dict:
    return {"error": True, "message": message}


def _apply_filters(df: pd.DataFrame, filters: list) -> tuple[pd.DataFrame, str | None]:
    """
    Apply a list of filter dicts to df.
    Returns (filtered_df, error_message_or_None).
    """
    for f in filters:
        field = f.get("field", "")
        op    = f.get("op", "eq")
        value = f.get("value")

        if field not in df.columns:
            return df, (
                f"Filter field '{field}' is not available. "
                f"Available fields: {', '.join(sorted(df.columns))}"
            )

        if op not in _OPS:
            return df, (
                f"Unsupported filter operator '{op}'. "
                f"Supported: {', '.join(_OPS)}"
            )

        # Validate categorical membership for 'eq' / 'in' filters
        if op in ("eq", "in"):
            col_dtype = df[field].dtype
            if col_dtype == object:               # categorical string column
                valid = set(df[field].dropna().unique())
                candidates = value if isinstance(value, list) else [value]
                bad = [v for v in candidates if v not in valid]
                if bad:
                    return df, (
                        f"Value(s) {bad} not found in column '{field}'. "
                        f"Valid values: {sorted(valid)}"
                    )

            # Validate integer enum columns (quarter 1-4, year, month, etc.)
            # Only applies to low-cardinality integer columns (≤ 20 distinct values)
            elif pd.api.types.is_integer_dtype(col_dtype) and df[field].nunique() <= 20:
                valid_ints = sorted(df[field].dropna().unique().tolist())
                candidates = value if isinstance(value, list) else [value]
                bad = [v for v in candidates if v not in valid_ints]
                if bad:
                    return df, (
                        f"Value(s) {bad} not valid for '{field}'. "
                        f"Valid values: {valid_ints}"
                    )

        mask = _OPS[op](df[field], value)
        df = df[mask]

    return df, None


def _aggregate(
    df: pd.DataFrame,
    metric: str,
    dimensions: list,
    aggregation: str,
) -> tuple[pd.DataFrame, str | None]:
    """Group df by dimensions and aggregate metric. Returns (result_df, error_or_None)."""
    if metric == ROW_COUNT_METRIC:
        if dimensions:
            missing = [d for d in dimensions if d not in df.columns]
            if missing:
                return df, f"Dimension column(s) not found: {missing}"
            result = df.groupby(dimensions, observed=True).size().reset_index(name=metric)
        else:
            result = pd.DataFrame({metric: [len(df)]})
        return result, None

    if metric not in df.columns:
        numeric_cols = [
            col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])
        ]
        return df, (
            f"Metric column '{metric}' not found. "
            f"Numeric columns available: {', '.join(numeric_cols) or 'none'}"
        )

    agg_func = _AGG_FUNCS.get(aggregation, "sum")

    if dimensions:
        # Verify every dimension exists
        missing = [d for d in dimensions if d not in df.columns]
        if missing:
            return df, f"Dimension column(s) not found: {missing}"

        result = (
            df.groupby(dimensions, observed=True)[metric]
            .agg(agg_func)
            .reset_index()
        )
    else:
        # No group-by: single-row summary
        scalar = getattr(df[metric], agg_func)()
        result = pd.DataFrame({metric: [scalar]})

    return result, None


def _sort_result(
    df: pd.DataFrame,
    metric: str,
    sort_by: str,
    sort_order: str,
) -> pd.DataFrame:
    ascending = sort_order != "desc"

    # Always apply calendar ordering when month_name is a dimension.
    # After aggregation, month_name only appears in the result if it was
    # grouped on, so its presence is a reliable signal.
    if "month_name" in df.columns:
        df = df.copy()
        df["_month_order"] = df["month_name"].map(
            {m: i for i, m in enumerate(_MONTH_ORDER)}
        )
        df = df.sort_values("_month_order", ascending=ascending).drop(
            columns=["_month_order"]
        )
        return df

    if sort_by == "metric" or sort_by == metric:
        return df.sort_values(metric, ascending=ascending)

    # Numeric time dimensions → natural integer sort
    if sort_by in _TIME_DIMS and sort_by in df.columns:
        return df.sort_values(sort_by, ascending=ascending)

    # Dimension sort (alphabetical)
    if sort_by in df.columns:
        return df.sort_values(sort_by, ascending=ascending)

    # Fallback: sort by metric
    return df.sort_values(metric, ascending=ascending)


def _build_summary(df: pd.DataFrame, metric: str, dimensions: list) -> dict:
    col = df[metric]
    summary: dict = {
        "total":     round(float(col.sum()), 2),
        "average":   round(float(col.mean()), 2),
        "max_value": round(float(col.max()), 2),
        "row_count": len(df),
    }

    # Find which dimension-label combination produced the max value
    if not df.empty and dimensions:
        max_idx = col.idxmax()
        max_row = df.loc[max_idx, dimensions]
        if len(dimensions) == 1:
            summary["max_label"] = str(max_row.iloc[0])
        else:
            summary["max_label"] = " | ".join(str(v) for v in max_row)
    else:
        summary["max_label"] = None

    return summary


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare and enrich a DataFrame with date columns.
    Handles missing date columns gracefully (e.g., custom CSV uploads).
    """
    return _prepare_dataframe(df)


def set_dataframe(df: pd.DataFrame) -> None:
    """Replace the active DataFrame used by run_query."""
    global _DF
    _DF = _prepare_dataframe(df)


def get_dataframe() -> pd.DataFrame:
    """Return the cached raw DataFrame (for reference / display purposes)."""
    return _DF.copy()


def _role_for_column(df: pd.DataFrame, col: str) -> str:
    series = df[col]
    if col in _TIME_COLUMNS or pd.api.types.is_datetime64_any_dtype(series):
        return "date/time"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if series.nunique(dropna=True) <= 50:
        return "categorical"
    return "text"


def get_dataset_profile(df: pd.DataFrame | None = None) -> dict:
    """Return a compact, UI/LLM-friendly profile of the active dataset."""
    source = _DF if df is None else df
    rows = len(source)
    columns = []

    for col in source.columns:
        series = source[col]
        role = _role_for_column(source, col)
        non_null = series.dropna()
        samples = [str(v) for v in non_null.unique()[:5]]
        columns.append({
            "name": col,
            "dtype": str(series.dtype),
            "role": role,
            "unique": int(series.nunique(dropna=True)),
            "missing": int(series.isna().sum()),
            "missing_pct": round(float(series.isna().mean() * 100), 1) if rows else 0,
            "samples": samples,
        })

    return {
        "rows": rows,
        "column_count": len(source.columns),
        "columns": columns,
        "numeric_columns": [c["name"] for c in columns if c["role"] == "numeric"],
        "categorical_columns": [c["name"] for c in columns if c["role"] == "categorical"],
        "date_columns": [c["name"] for c in columns if c["role"] == "date/time"],
        "text_columns": [c["name"] for c in columns if c["role"] == "text"],
    }


def _pick_metric(profile: dict) -> str | None:
    numeric = profile["numeric_columns"]
    if not numeric:
        return ROW_COUNT_METRIC

    preferred_tokens = (
        "revenue", "sales", "amount", "total", "profit", "price", "cost",
        "quantity", "qty", "units", "score", "rating", "value",
    )
    for token in preferred_tokens:
        for col in numeric:
            if token in col.lower():
                return col
    return numeric[0]


def _pick_category(profile: dict) -> str | None:
    categoricals = profile["categorical_columns"]
    if categoricals:
        return categoricals[0]

    # Some ID-like integer columns are numeric but can still be useful as groups
    # if they have a small number of distinct values.
    for col in profile["columns"]:
        if col["role"] == "numeric" and 2 <= col["unique"] <= 20:
            return col["name"]
    return None


def build_schema_context() -> str:
    """Build the current dataset description sent to the LLM parser."""
    profile = get_dataset_profile()
    lines = [
        f"DATASET PROFILE: {profile['rows']} rows, {profile['column_count']} columns.",
        "Use ONLY the columns listed below. Do not invent fields.",
        "",
        "COLUMNS:",
    ]

    for col in profile["columns"]:
        sample = ""
        if col["samples"]:
            sample = f" Examples: {', '.join(col['samples'][:4])}."
        lines.append(
            f"- {col['name']} ({col['role']}, {col['dtype']}, "
            f"{col['unique']} unique, {col['missing_pct']}% missing).{sample}"
        )

    metric_hint = ", ".join(profile["numeric_columns"] + [ROW_COUNT_METRIC])
    dim_hint = ", ".join(
        profile["categorical_columns"] + profile["date_columns"]
    ) or "No categorical/date columns found"
    lines.extend([
        "",
        f"Good metric candidates: {metric_hint}.",
        f"Good dimension/filter candidates: {dim_hint}.",
        "For trends, prefer month_name/year/quarter when available; otherwise use a date/time column.",
    ])
    return "\n".join(lines)


def suggest_questions(limit: int = 5) -> list[str]:
    """Generate deterministic example questions for the active dataset."""
    profile = get_dataset_profile()
    metric = _pick_metric(profile)
    category = _pick_category(profile)
    date_dim = "month_name" if "month_name" in _DF.columns else (
        profile["date_columns"][0] if profile["date_columns"] else None
    )

    questions: list[str] = []
    if metric and category and metric != ROW_COUNT_METRIC:
        questions.append(f"Show {metric.replace('_', ' ')} by {category.replace('_', ' ')}")
        questions.append(f"Top 5 {category.replace('_', ' ')} by {metric.replace('_', ' ')}")
    if metric and date_dim and metric != ROW_COUNT_METRIC:
        questions.append(f"Show {metric.replace('_', ' ')} trend by {date_dim.replace('_', ' ')}")
    if category:
        questions.append(f"Count records by {category.replace('_', ' ')}")
    if metric and metric != ROW_COUNT_METRIC:
        questions.append(f"Summarize {metric.replace('_', ' ')} performance")

    fallback = [
        "Show an overview of this dataset",
        "Which columns have missing values?",
        "Create a dashboard summary",
    ]
    questions.extend(q for q in fallback if q not in questions)
    return questions[:limit]


def build_overview_queries() -> list[dict]:
    """Build a small dashboard spec from the active dataset profile."""
    profile = get_dataset_profile()
    metric = _pick_metric(profile)
    category = _pick_category(profile)
    if not metric:
        return []

    queries: list[dict] = []
    if category:
        aggregation = "count" if metric == ROW_COUNT_METRIC else "sum"
        metric_label = "Record Count" if metric == ROW_COUNT_METRIC else metric.replace("_", " ").title()
        queries.append({
            "metric": metric,
            "aggregation": aggregation,
            "dimensions": [category],
            "filters": [],
            "chart_type": "bar",
            "sort_by": "metric",
            "sort_order": "desc",
            "limit": 12,
            "title": f"{metric_label} by {category.replace('_', ' ').title()}",
            "x_label": category.replace("_", " ").title(),
            "y_label": metric_label,
        })

    time_dim = None
    if "month_name" in _DF.columns:
        time_dim = "month_name"
    elif "year" in _DF.columns:
        time_dim = "year"
    elif profile["date_columns"]:
        time_dim = profile["date_columns"][0]

    if time_dim:
        aggregation = "count" if metric == ROW_COUNT_METRIC else "sum"
        metric_label = "Record Count" if metric == ROW_COUNT_METRIC else metric.replace("_", " ").title()
        queries.append({
            "metric": metric,
            "aggregation": aggregation,
            "dimensions": [time_dim],
            "filters": [],
            "chart_type": "line",
            "sort_by": time_dim,
            "sort_order": "asc",
            "limit": 100,
            "title": f"{metric_label} Trend",
            "x_label": time_dim.replace("_", " ").title(),
            "y_label": metric_label,
        })

    if category and metric != ROW_COUNT_METRIC:
        queries.append({
            "metric": metric,
            "aggregation": "sum",
            "dimensions": [category],
            "filters": [],
            "chart_type": "pie",
            "sort_by": "metric",
            "sort_order": "desc",
            "limit": 8,
            "title": f"{metric.replace('_', ' ').title()} Share by {category.replace('_', ' ').title()}",
            "x_label": category.replace("_", " ").title(),
            "y_label": metric.replace("_", " ").title(),
        })

    return queries[:3]


def run_query(parsed: dict) -> dict:
    """
    Execute a structured BI query against the cached sales DataFrame.

    Args:
        parsed: dict produced by llm_parser.parse_query()

    Returns:
        {
            "data":       list[dict],   # aggregated rows
            "metric":     str,
            "dimensions": list[str],
            "chart_type": str,
            "title":      str,
            "x_label":    str,
            "y_label":    str,
            "summary":    { total, average, max_value, max_label, row_count }
        }
        or {"error": True, "message": str}
    """
    # --- Pass-through errors from the parser ---
    if parsed.get("error"):
        return parsed

    # --- Extract query parameters (with sensible defaults) ---
    metric     = parsed.get("metric", "total_revenue")
    aggregation= parsed.get("aggregation", "sum")
    dimensions = parsed.get("dimensions") or []
    filters    = parsed.get("filters") or []
    chart_type = parsed.get("chart_type", "bar")
    sort_by    = parsed.get("sort_by", "metric")
    sort_order = parsed.get("sort_order", "desc")
    limit      = int(parsed.get("limit", 10))
    title      = parsed.get("title", "Query Result")
    x_label    = parsed.get("x_label", dimensions[0] if dimensions else "")
    y_label    = parsed.get("y_label", metric)

    df = _DF.copy()

    # --- Apply filters ---
    df, filter_err = _apply_filters(df, filters)
    if filter_err:
        return _err(filter_err)

    if df.empty:
        return _err(
            "No data matched your filters. "
            "Try broadening your search criteria."
        )

    # --- Aggregate ---
    result, agg_err = _aggregate(df, metric, dimensions, aggregation)
    if agg_err:
        return _err(agg_err)

    if result.empty:
        return _err("No data matched your query after aggregation.")

    # --- Sort ---
    result = _sort_result(result, metric, sort_by, sort_order)

    # --- Limit ---
    if limit < 999:
        result = result.head(limit)

    # --- Build summary (before converting to records) ---
    summary = _build_summary(result, metric, dimensions)

    # --- Serialise ---
    # Round floats to 2 dp for cleaner display
    for col in result.select_dtypes(include="float").columns:
        result[col] = result[col].round(2)

    return {
        "data":       result.to_dict(orient="records"),
        "metric":     metric,
        "dimensions": dimensions,
        "chart_type": chart_type,
        "title":      title,
        "x_label":    x_label,
        "y_label":    y_label,
        "summary":    summary,
    }

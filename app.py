import io

import pandas as pd
import streamlit as st

import data_engine
from chart_builder import build_chart
from data_engine import run_query
from insight_gen import generate_insight
from llm_parser import parse_query

# ---------------------------------------------------------------------------
# Page config — must be the very first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="BI Dashboard AI",
    layout="wide",
    page_icon="📊",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* ── Global resets ─────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    .stApp {
        background-color: #0A0F1E;
        color: #F1F5F9;
    }

    /* ── Sidebar ────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid rgba(99,102,241,0.2);
    }
    section[data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background-color: rgba(99,102,241,0.08);
        color: #A5B4FC !important;
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 8px;
        width: 100%;
        text-align: left;
        padding: 0.5rem 0.75rem;
        font-size: 0.82rem;
        transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(99,102,241,0.2);
        border-color: #6366F1;
        color: #FFF !important;
    }

    /* ── Hide Streamlit chrome ──────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header    { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Main content area ──────────────────────────────── */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 6rem;
        max-width: 1400px;
    }

    /* ── Dashboard header ───────────────────────────────── */
    .dash-header {
        margin-bottom: 1.5rem;
    }
    .dash-header h1 {
        font-size: 2.1rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.25rem;
    }
    .dash-header p {
        color: #64748B;
        font-size: 0.95rem;
        margin: 0;
    }

    /* ── Chat history cards ─────────────────────────────── */
    .chat-bubble-user {
        background: rgba(99,102,241,0.1);
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 12px 12px 4px 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0 1rem;
        color: #A5B4FC;
        font-size: 0.95rem;
        display: inline-block;
        max-width: 80%;
        float: right;
        clear: both;
    }
    .chat-user-row {
        text-align: right;
        margin-bottom: 0.25rem;
        overflow: hidden;
    }
    .chat-label {
        font-size: 0.72rem;
        color: #475569;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ── KPI tiles ──────────────────────────────────────── */
    .kpi-grid {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    .kpi-card {
        background: rgba(99,102,241,0.06);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 10px;
        padding: 0.9rem 1rem;
    }
    .kpi-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        margin-bottom: 0.3rem;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #E2E8F0;
        line-height: 1.1;
    }
    .kpi-subtitle {
        font-size: 0.72rem;
        color: #6366F1;
        margin-top: 0.2rem;
    }

    /* ── Insight card ───────────────────────────────────── */
    .insight-card {
        background: rgba(16,185,129,0.05);
        border: 1px solid rgba(16,185,129,0.25);
        border-radius: 10px;
        padding: 0.9rem 1rem;
        margin-top: 0.75rem;
    }
    .insight-header {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #10B981;
        margin-bottom: 0.4rem;
    }
    .insight-text {
        font-size: 0.85rem;
        color: #CBD5E1;
        line-height: 1.6;
    }

    /* ── Divider ────────────────────────────────────────── */
    .chat-divider {
        border: none;
        border-top: 1px solid rgba(99,102,241,0.12);
        margin: 0.5rem 0 1.5rem;
    }

    /* ── Chat input bar ─────────────────────────────────── */
    .stChatInput {
        background-color: #0F172A !important;
    }
    .stChatInput textarea {
        background-color: #0F172A !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(99,102,241,0.4) !important;
        border-radius: 12px !important;
    }
    .stChatInput textarea:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }

    /* ── Streamlit widget overrides ─────────────────────── */
    .stExpander {
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 8px !important;
        background-color: #0F172A !important;
    }
    .stSpinner > div {
        color: #6366F1 !important;
    }

    /* ── Upload widget ──────────────────────────────────── */
    [data-testid="stFileUploader"] {
        background: rgba(99,102,241,0.05);
        border: 1px dashed rgba(99,102,241,0.3);
        border-radius: 8px;
        padding: 0.5rem;
    }

    /* ── Column pills ───────────────────────────────────── */
    .col-pill {
        display: inline-block;
        background: rgba(99,102,241,0.12);
        border: 1px solid rgba(99,102,241,0.25);
        color: #A5B4FC;
        border-radius: 20px;
        padding: 0.15rem 0.55rem;
        font-size: 0.72rem;
        margin: 0.15rem 0.1rem;
    }

    /* ── Loading skeleton ───────────────────────────────── */
    @keyframes skeleton-shimmer {
        0%   { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    .skeleton-block {
        background: linear-gradient(
            90deg,
            #1E293B 25%,
            #28364D 50%,
            #1E293B 75%
        );
        background-size: 200% 100%;
        animation: skeleton-shimmer 1.6s ease-in-out infinite;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "chat_history" not in st.session_state:
    # Each entry: {query, parsed, result, fig, insight}
    st.session_state.chat_history = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if "custom_df" not in st.session_state:
    st.session_state.custom_df = None

# ---------------------------------------------------------------------------
# Re-apply custom CSV patch on every rerun so the override survives navigation
# ---------------------------------------------------------------------------

if st.session_state.custom_df is not None:
    data_engine._DF = st.session_state.custom_df

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REVENUE_METRICS = {"total_revenue", "discounted_price", "price"}


def _fmt_number(val: float, metric: str = "") -> str:
    """Format a number with K/M suffixes; prefix $ for revenue-like metrics."""
    prefix = "$" if metric in _REVENUE_METRICS or "revenue" in metric or "price" in metric else ""
    abs_val = abs(val)
    if abs_val >= 1_000_000:
        return f"{prefix}{val / 1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{prefix}{val / 1_000:.1f}K"
    return f"{prefix}{val:,.2f}"


def _kpi_card(label: str, value: str, subtitle: str = "") -> str:
    sub_html = f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )


def _insight_card(text: str) -> str:
    return (
        f'<div class="insight-card">'
        f'<div class="insight-header">💡 AI Insight</div>'
        f'<div class="insight-text">{text}</div>'
        f'</div>'
    )


def _skeleton_html() -> str:
    """Grey shimmer placeholder shown while the pipeline is running."""
    kpi_block = '<div class="skeleton-block" style="height:88px;"></div>'
    return f"""
    <div style="display:flex;gap:1.25rem;margin-bottom:1rem;">
        <div style="flex:7;">
            <div class="skeleton-block" style="height:380px;"></div>
        </div>
        <div style="flex:3;display:flex;flex-direction:column;gap:0.75rem;">
            {kpi_block}
            {kpi_block}
            {kpi_block}
            <div class="skeleton-block" style="height:110px;margin-top:0.2rem;"></div>
        </div>
    </div>
    """


def _render_entry(entry: dict) -> None:
    """Render one complete Q&A turn: user bubble + chart + KPIs + insight."""
    query   = entry["query"]
    result  = entry["result"]
    fig     = entry["fig"]
    insight = entry["insight"]

    # User bubble (right-aligned)
    st.markdown(
        f'<div class="chat-user-row">'
        f'<div class="chat-label">You</div>'
        f'<div class="chat-bubble-user">{query}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if result.get("error"):
        st.error(result.get("message", "An unknown error occurred."))
        st.markdown('<hr class="chat-divider">', unsafe_allow_html=True)
        return

    summary   = result.get("summary", {})
    metric    = result.get("metric", "value")
    data_rows = result.get("data", [])

    # 70 / 30 column split
    col_chart, col_kpi = st.columns([7, 3], gap="medium")

    with col_chart:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_kpi:
        kpi_html = '<div class="kpi-grid">'

        if "total" in summary:
            kpi_html += _kpi_card("Total", _fmt_number(summary["total"], metric))

        if "average" in summary:
            kpi_html += _kpi_card(
                "Average per group",
                _fmt_number(summary["average"], metric),
            )

        if summary.get("max_label") and "max_value" in summary:
            kpi_html += _kpi_card(
                "Top Performer",
                _fmt_number(summary["max_value"], metric),
                summary["max_label"],
            )

        kpi_html += "</div>"
        st.markdown(kpi_html, unsafe_allow_html=True)
        st.markdown(_insight_card(insight), unsafe_allow_html=True)

    # Raw data expander
    if data_rows:
        with st.expander("View Raw Data", expanded=False):
            st.dataframe(
                pd.DataFrame(data_rows),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown('<hr class="chat-divider">', unsafe_allow_html=True)


def _run_pipeline(query: str) -> None:
    """Parse → query → chart → insight, store in history, render immediately."""
    try:
        # Carry forward context from the previous successful turn
        previous_context = None
        if st.session_state.chat_history:
            last = st.session_state.chat_history[-1]
            if not last["result"].get("error"):
                previous_context = last["result"]

        with st.spinner("🧠 Analyzing your query…"):
            parsed = parse_query(query, previous_context=previous_context)

            if parsed.get("error"):
                entry = {
                    "query":   query,
                    "parsed":  parsed,
                    "result":  parsed,
                    "fig":     build_chart(parsed),
                    "insight": parsed.get("message", ""),
                }
                st.session_state.chat_history.append(entry)
                _render_entry(entry)
                return

            result  = run_query(parsed)
            fig     = build_chart(result)
            insight = generate_insight(query, result)

        entry = {
            "query":   query,
            "parsed":  parsed,
            "result":  result,
            "fig":     fig,
            "insight": insight,
        }
        st.session_state.chat_history.append(entry)
        _render_entry(entry)

    except Exception as exc:
        st.error(
            "Something went wrong while processing your query. "
            "Please try again or rephrase your question.\n\n"
            f"**Details:** {exc}"
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="padding:0.5rem 0 1rem;">
            <div style="font-size:1.4rem;font-weight:700;color:#E2E8F0;">
                📊 BI Dashboard AI
            </div>
            <div style="font-size:0.8rem;color:#64748B;margin-top:0.25rem;">
                Ask anything about your sales data
            </div>
        </div>
        <hr style="border-color:rgba(99,102,241,0.2);margin:0 0 1.25rem;">
        """,
        unsafe_allow_html=True,
    )

    # ── Data source ──────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.75rem;color:#6366F1;text-transform:uppercase;'
        'letter-spacing:0.08em;margin-bottom:0.5rem;">Data Source</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload your own CSV",
        type="csv",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        try:
            raw = uploaded_file.getvalue().decode("utf-8")
            df_up = pd.read_csv(io.StringIO(raw))

            # Auto-derive date columns when order_date is present
            if "order_date" in df_up.columns:
                df_up["order_date"] = pd.to_datetime(df_up["order_date"], errors="coerce")
                df_up["year"]       = df_up["order_date"].dt.year
                df_up["month"]      = df_up["order_date"].dt.month
                df_up["month_name"] = df_up["order_date"].dt.strftime("%b")
                df_up["quarter"]    = df_up["order_date"].dt.quarter

            st.session_state.custom_df = df_up
            data_engine._DF = df_up

            st.success(f"✓ Loaded {len(df_up):,} rows")

            pills = "".join(
                f'<span class="col-pill">{c}</span>' for c in df_up.columns
            )
            st.markdown(
                f'<div style="margin-top:0.4rem;line-height:2.2;">{pills}</div>',
                unsafe_allow_html=True,
            )
        except Exception as exc:
            st.error(f"Could not read file: {exc}")
    else:
        if st.session_state.custom_df is None:
            st.caption("Using default · sales.csv · 2022–2023")
        else:
            st.caption("Custom CSV active. Re-upload to change.")

    st.markdown(
        '<hr style="border-color:rgba(99,102,241,0.15);margin:1.25rem 0;">',
        unsafe_allow_html=True,
    )

    # ── Example queries ──────────────────────────────────
    st.markdown(
        '<div style="font-size:0.75rem;color:#6366F1;text-transform:uppercase;'
        'letter-spacing:0.08em;margin-bottom:0.6rem;">Try these examples</div>',
        unsafe_allow_html=True,
    )

    _EXAMPLES = [
        "Show total revenue by region as a bar chart",
        "Monthly revenue trend for 2023 broken down by product category",
        "Top 5 product categories by average rating",
    ]

    for ex in _EXAMPLES:
        if st.button(ex, key=f"ex_{hash(ex)}"):
            st.session_state.pending_query = ex
            st.rerun()

    st.markdown(
        '<hr style="border-color:rgba(99,102,241,0.15);margin:1.25rem 0;">',
        unsafe_allow_html=True,
    )

    # ── Clear conversation ───────────────────────────────
    if st.session_state.chat_history:
        if st.button("🗑  Clear conversation", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

# ---------------------------------------------------------------------------
# Main area — header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="dash-header">
        <h1>Ask Your Data Anything</h1>
        <p>Powered by Google Gemini · Natural language → instant charts</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Render all previous chat turns
# ---------------------------------------------------------------------------

for entry in st.session_state.chat_history:
    _render_entry(entry)

# ---------------------------------------------------------------------------
# Chat input (pinned to bottom by Streamlit)
# ---------------------------------------------------------------------------

query_input   = st.chat_input("Ask a question about your sales data…")
pending_query = st.session_state.pop("pending_query", None)

active_query = query_input or pending_query

if active_query:
    # Show shimmer skeleton immediately while the pipeline runs
    _skeleton_ph = st.empty()
    _skeleton_ph.markdown(_skeleton_html(), unsafe_allow_html=True)

    _run_pipeline(active_query)

    # Remove skeleton; real result is already rendered below this slot
    _skeleton_ph.empty()

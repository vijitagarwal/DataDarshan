# -*- coding: utf-8 -*-
import io
import json

import pandas as pd
import streamlit as st

import data_engine
import insight_gen
from chart_builder import build_chart
from data_engine import run_query
from llm_parser import parse_query, parse_dashboard_query

# ---------------------------------------------------------------------------
# Page config — must be the very first Streamlit call
# -----------------------------------------------------/----------------------

st.set_page_config(
    page_title="dataदर्शनम्",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "custom_df" not in st.session_state:
    st.session_state.custom_df = None
if "saved_charts" not in st.session_state:
    st.session_state.saved_charts = []          # Tier-2.1 pinned charts
if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = False       # sidebar toggle state

# Re-apply custom CSV patch on every rerun
if st.session_state.custom_df is not None:
    data_engine.set_dataframe(st.session_state.custom_df)

# ---------------------------------------------------------------------------
# Theme logic
# ---------------------------------------------------------------------------

is_dark = st.session_state.theme == "dark"

bg_main    = "#0A0F1E" if is_dark else "#F0F4FF"
bg_card    = "#0F172A" if is_dark else "#FFFFFF"
bg_sidebar = "#0D1117" if is_dark else "#E8EEF8"
text_main  = "#FFFFFF" if is_dark else "#0F172A"
text_muted = "#64748B" if is_dark else "#475569"
border_col = "rgba(99,102,241,0.3)" if is_dark else "#C7D2FE"
accent     = "#6366F1"

# ---------------------------------------------------------------------------
# CSS generation (cached by theme)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _generate_main_css(is_dark: bool) -> str:
    """Generate main CSS block cached by theme state."""
    bg_main_    = "#0A0F1E" if is_dark else "#F0F4FF"
    bg_card_    = "#0F172A" if is_dark else "#FFFFFF"
    bg_sidebar_ = "#0D1117" if is_dark else "#E8EEF8"
    text_main_  = "#FFFFFF" if is_dark else "#0F172A"
    text_muted_ = "#64748B" if is_dark else "#475569"
    border_col_ = "rgba(99,102,241,0.3)" if is_dark else "#C7D2FE"
    accent_     = "#6366F1"

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;700;800&display=swap');

/* Reset and base */
html, body, [class*="css"] {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}
.stApp {{
    background-color: {bg_main_} !important;
    color: {text_main_} !important;
}}

/* Sidebar collapse button styling */
[data-testid="collapsedControl"] {{
    color: {text_main_} !important;
}}

/* Hide streamlit branding */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* Cards */
.kpi-card {{
    background: {bg_card_};
    border: 1px solid {border_col_};
    border-radius: 16px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s ease;
}}
.kpi-card:hover {{ border-color: {accent_}; }}
.kpi-label {{
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    color: {text_muted_};
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}}
.kpi-value {{
    font-size: 1.65rem;
    font-weight: 700;
    color: {text_main_};
    line-height: 1.1;
    letter-spacing: -0.01em;
}}
.kpi-subtitle {{
    font-size: 0.72rem;
    color: {accent_};
    margin-top: 0.28rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.insight-card {{
    background: {bg_card_};
    border: 1px solid {border_col_};
    border-radius: 16px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.75rem;
}}
.insight-header {{
    font-size: 0.67rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #10B981;
    margin-bottom: 0.45rem;
    font-weight: 600;
}}
.insight-text {{
    font-size: 0.84rem;
    color: {text_muted_};
    line-height: 1.65;
}}

.chart-card {{
    background: {bg_card_};
    border: 1px solid {border_col_};
    border-radius: 16px;
    padding: 1rem 0.75rem 0.5rem;
    margin-bottom: 1rem;
}}

.summary-card {{
    background: {bg_card_};
    border: 1px solid {border_col_};
    border-radius: 16px;
    padding: 0.9rem 1rem;
}}
.summary-header {{
    font-size: 0.67rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {accent_};
    margin-bottom: 0.55rem;
    font-weight: 600;
}}

/* User chat bubble */
.chat-user-row {{
    display: flex;
    justify-content: flex-end;
    margin: 0.5rem 0 1.25rem;
}}
.chat-bubble-user {{
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    border-radius: 18px 18px 4px 18px;
    padding: 0.7rem 1.1rem;
    color: #fff !important;
    font-size: 0.93rem;
    max-width: 66%;
    box-shadow: 0 4px 20px rgba(99,102,241,0.28);
    line-height: 1.5;
}}

/* Divider */
.chat-divider {{
    border: none;
    border-top: 1px solid {border_col_};
    margin: 0.5rem 0 1.75rem;
}}

/* Dashboard section header */
.dashboard-section-header {{
    font-size: 1.05rem;
    font-weight: 700;
    color: {text_main_};
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.06));
    border: 1px solid {border_col_};
    border-radius: 12px;
    padding: 0.65rem 1rem;
    margin-bottom: 1rem;
    letter-spacing: -0.01em;
}}

/* Mini stat chips */
.mini-stat {{
    background: rgba(99,102,241,0.08);
    border: 1px solid {border_col_};
    border-radius: 10px;
    padding: 0.55rem 0.8rem;
    margin-bottom: 0.6rem;
}}
.mini-stat-label {{
    font-size: 0.63rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: {text_muted_};
    margin-bottom: 0.2rem;
    font-weight: 600;
}}
.mini-stat-value {{
    font-size: 1.15rem;
    font-weight: 700;
    color: {text_main_};
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

/* Col pills (CSV upload) */
.col-pill {{
    display: inline-block;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.25);
    color: #A5B4FC;
    border-radius: 20px;
    padding: 0.12rem 0.5rem;
    font-size: 0.7rem;
    margin: 0.12rem 0.08rem;
}}

/* Chat input */
.stChatInput > div {{
    background: {bg_card_} !important;
    border: 1px solid {border_col_} !important;
    border-radius: 28px !important;
}}
.stChatInput textarea {{
    color: {text_main_} !important;
    background: {bg_card_} !important;
    caret-color: {text_main_} !important;
}}
.stChatInput textarea::placeholder {{
    color: {text_muted_} !important;
}}
/* The send button icon color */
.stChatInput button svg {{
    fill: {text_main_} !important;
}}

/* Buttons */
.stButton > button {{
    background: transparent !important;
    border: 1px solid {border_col_} !important;
    color: {text_main_} !important;
    border-radius: 10px !important;
    text-align: left !important;
    width: 100% !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
    transition: all 0.2s !important;
}}
.stButton > button:hover {{
    background: {accent_} !important;
    border-color: {accent_} !important;
    color: white !important;
}}

/* Primary button (Generate Full Dashboard) */
[data-testid="stBaseButton-primary"] {{
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    border: none !important;
    color: #fff !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.32) !important;
    transition: all 0.15s ease !important;
}}
[data-testid="stBaseButton-primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 22px rgba(99,102,241,0.45) !important;
}}

/* Main content padding */
.block-container {{
    padding: 2rem 2.5rem 6rem 2.5rem !important;
    max-width: 1440px !important;
}}

/* Expander */
.stExpander {{
    border: 1px solid {border_col_} !important;
    border-radius: 12px !important;
    background-color: {bg_card_} !important;
}}

/* Skeleton shimmer */
@keyframes shimmer {{
    0%   {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}
.skeleton-block {{
    background: linear-gradient(90deg, #1E293B 25%, #28364D 50%, #1E293B 75%);
    background-size: 200% 100%;
    animation: shimmer 1.6s ease-in-out infinite;
    border-radius: 12px;
}}

[data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}
.stSpinner > div {{ color: {accent_} !important; }}
[data-testid="stFileUploader"] {{
    background: rgba(99,102,241,0.04);
    border: 1px dashed {border_col_};
    border-radius: 10px;
    padding: 0.4rem;
}}

/* ── Hero Section ──────────────────────────────────────────────── */
.hero-section {{
    text-align: center;
    padding: 3.5rem 1rem 2.5rem;
    animation: fadeUp 0.6s ease both;
}}
@keyframes fadeUp {{
    from {{ opacity:0; transform:translateY(20px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
.hero-title {{
    font-size: 3.2rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    line-height: 1.1;
    margin-bottom: 0.7rem;
}}
.hero-subtitle {{
    font-size: 1.1rem;
    color: {text_muted_};
    margin-bottom: 2rem;
    font-weight: 400;
    max-width: 580px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.6;
}}
.hero-tag {{
    display: inline-block;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.3);
    color: #A5B4FC;
    border-radius: 20px;
    padding: 0.3rem 0.85rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin: 0.15rem;
    text-transform: uppercase;
}}
.hero-feature-grid {{
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 2rem;
    margin-bottom: 0;
}}
.hero-feature-card {{
    background: {bg_card_};
    border: 1px solid {border_col_};
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    text-align: left;
    min-width: 170px;
    max-width: 210px;
    transition: border-color 0.2s, transform 0.2s;
}}
.hero-feature-card:hover {{
    border-color: {accent_};
    transform: translateY(-3px);
}}
.hero-feature-icon {{
    font-size: 1.6rem;
    margin-bottom: 0.5rem;
}}
.hero-feature-title {{
    font-size: 0.85rem;
    font-weight: 700;
    color: {text_main_};
    margin-bottom: 0.25rem;
}}
.hero-feature-desc {{
    font-size: 0.73rem;
    color: {text_muted_};
    line-height: 1.5;
}}

/* ── Sidebar (Saved + Dataset) ─────────────────────────────────── */
section[data-testid="stSidebar"] {{
    display: flex !important;
    background: {bg_sidebar_} !important;
    border-right: 1px solid {border_col_} !important;
}}
.sidebar-section-title {{
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: {text_muted_};
    font-weight: 700;
    margin-bottom: 0.7rem;
    margin-top: 0.3rem;
}}
.saved-chip {{
    background: {bg_card_};
    border: 1px solid {border_col_};
    border-radius: 10px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.5rem;
    font-size: 0.75rem;
    color: {text_main_};
    cursor: pointer;
    transition: border-color 0.15s;
}}
.saved-chip:hover {{ border-color: {accent_}; }}

/* ── Chart type switcher pills ─────────────────────────────────── */
.chart-type-bar {{
    display: flex;
    gap: 0.4rem;
    margin-bottom: 0.6rem;
    flex-wrap: wrap;
}}
.chart-pill {{
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.2);
    color: #A5B4FC;
    border-radius: 20px;
    padding: 0.22rem 0.7rem;
    font-size: 0.72rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    user-select: none;
}}
.chart-pill:hover, .chart-pill.active {{
    background: {accent_};
    border-color: {accent_};
    color: #fff;
}}

/* ── Follow-up badge ───────────────────────────────────────────── */
.followup-badge {{
    display: inline-block;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.3);
    color: #10B981;
    border-radius: 20px;
    padding: 0.15rem 0.55rem;
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    margin-left: 0.5rem;
    vertical-align: middle;
}}
.ai-badge {{
    display: inline-block;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.3);
    color: #A5B4FC;
    border-radius: 20px;
    padding: 0.15rem 0.55rem;
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    margin-left: 0.4rem;
    vertical-align: middle;
}}
.est-badge {{
    display: inline-block;
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.3);
    color: #F59E0B;
    border-radius: 20px;
    padding: 0.15rem 0.55rem;
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    margin-left: 0.4rem;
    vertical-align: middle;
}}

/* ── Active filters pill row ───────────────────────────────────── */
.filter-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-bottom: 0.75rem;
}}
.filter-chip {{
    background: rgba(236,72,153,0.08);
    border: 1px solid rgba(236,72,153,0.2);
    color: #F472B6;
    border-radius: 20px;
    padding: 0.18rem 0.6rem;
    font-size: 0.7rem;
    font-weight: 500;
}}

/* ── How it works steps ────────────────────────────────────────── */
.pipeline-step {{
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    margin-bottom: 0.8rem;
}}
.pipeline-num {{
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    color: #fff;
    font-size: 0.72rem;
    font-weight: 800;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
}}
.pipeline-step-body {{ flex: 1; }}
.pipeline-step-title {{
    font-size: 0.82rem;
    font-weight: 700;
    color: {text_main_};
    margin-bottom: 0.1rem;
}}
.pipeline-step-desc {{
    font-size: 0.73rem;
    color: {text_muted_};
    line-height: 1.5;
}}

/* ── Download / export buttons ─────────────────────────────────── */
.stDownloadButton > button {{
    background: rgba(16,185,129,0.1) !important;
    border: 1px solid rgba(16,185,129,0.3) !important;
    color: #10B981 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    padding: 5px 10px !important;
    font-weight: 600 !important;
    transition: all 0.15s !important;
}}
.stDownloadButton > button:hover {{
    background: rgba(16,185,129,0.25) !important;
    border-color: #10B981 !important;
}}

/* ── Typing animation for chat placeholder ─────────────────────── */
@keyframes blink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0; }} }}
.typing-cursor {{ animation: blink 1s step-start infinite; }}
</style>
"""

st.markdown(_generate_main_css(is_dark), unsafe_allow_html=True)

# ── Sidebar: Saved Charts + Dataset Profile ──────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:0.5rem 0 0.25rem;">
      <span style="font-size:1.2rem;font-weight:900;color:{text_main};">data</span><span
        style="font-size:1.2rem;font-weight:900;color:{accent};font-family:'Noto Sans Devanagari',sans-serif;">दर्शनम्</span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Saved Charts ──────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section-title">📌 Saved Charts</div>', unsafe_allow_html=True)
    if not st.session_state.saved_charts:
        st.caption("Pin a chart using the 📌 button below any result.")
    else:
        for _si, _sc in enumerate(st.session_state.saved_charts):
            col_sc, col_del = st.columns([5, 1])
            with col_sc:
                if st.button(
                    f"📊 {_sc['query'][:38]}{'…' if len(_sc['query']) > 38 else ''}",
                    use_container_width=True,
                    key=f"saved_jump_{_si}",
                ):
                    st.toast(f"Showing: {_sc['query'][:60]}")
            with col_del:
                if st.button("✕", key=f"del_saved_{_si}", help="Remove"):
                    st.session_state.saved_charts.pop(_si)
                    st.rerun()

        # Export saved insights as HTML
        if st.session_state.saved_charts:
            st.markdown("---")
            _html_export = "<html><head><style>body{font-family:Inter,sans-serif;background:#0A0F1E;color:#fff;padding:2rem;}"                            "h2{color:#6366F1;} p{color:#94A3B8;font-size:0.9rem;} hr{border-color:#1E293B;}</style></head><body>"
            _html_export += "<h1>📊 dataदर्शनम् — Saved Insights</h1><hr>"
            for _sc in st.session_state.saved_charts:
                _html_export += f"<h2>{_sc['query']}</h2>"
                _html_export += f"<p><b>Insight:</b> {_sc.get('insight','')}</p>"
                _sum = _sc.get('summary', {})
                if _sum:
                    _html_export += f"<p>Total: {_sum.get('total','—')} · Top: {_sum.get('max_label','—')} ({_sum.get('max_value','—')})</p>"
                _html_export += "<hr>"
            _html_export += "</body></html>"
            st.download_button(
                "📤 Export Insights (HTML)",
                data=_html_export,
                file_name="datadarshanam_insights.html",
                mime="text/html",
                use_container_width=True,
                key="export_insights_html"
            )

    st.divider()

    # ── Dataset Profile ───────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section-title">🗃️ Dataset Profile</div>', unsafe_allow_html=True)
    _prof = data_engine.get_dataset_profile()
    st.markdown(
        f"""<div style="font-size:0.8rem;color:{text_muted};line-height:1.9;">
        <b style="color:{text_main};">{_prof['rows']:,}</b> rows &nbsp;·&nbsp;
        <b style="color:{text_main};">{_prof['column_count']}</b> columns
        </div>""",
        unsafe_allow_html=True,
    )

    _num_cols = _prof.get("numeric_columns", [])
    _cat_cols = _prof.get("categorical_columns", [])
    _dat_cols = _prof.get("date_columns", [])

    if _num_cols:
        st.markdown(f'<div style="margin-top:0.5rem;font-size:0.7rem;color:{text_muted};font-weight:600;letter-spacing:0.06em;">📈 NUMERIC</div>', unsafe_allow_html=True)
        for _c in _num_cols[:6]:
            st.markdown(f'<span class="col-pill">📊 {_c}</span>', unsafe_allow_html=True)
    if _cat_cols:
        st.markdown(f'<div style="margin-top:0.5rem;font-size:0.7rem;color:{text_muted};font-weight:600;letter-spacing:0.06em;">🏷️ CATEGORICAL</div>', unsafe_allow_html=True)
        for _c in _cat_cols[:6]:
            st.markdown(f'<span class="col-pill">🔤 {_c}</span>', unsafe_allow_html=True)
    if _dat_cols:
        st.markdown(f'<div style="margin-top:0.5rem;font-size:0.7rem;color:{text_muted};font-weight:600;letter-spacing:0.06em;">📅 DATE</div>', unsafe_allow_html=True)
        for _c in _dat_cols[:4]:
            st.markdown(f'<span class="col-pill">📅 {_c}</span>', unsafe_allow_html=True)

    # Full column detail
    with st.expander("All columns detail", expanded=False):
        for _col_info in _prof.get("columns", []):
            _role_icon = {"numeric": "📈", "categorical": "🏷️", "date/time": "📅", "text": "📝"}.get(_col_info.get("role",""), "❓")
            st.markdown(
                f'<div style="font-size:0.73rem;margin-bottom:0.4rem;color:{text_muted};">'
                f'{_role_icon} <b style="color:{text_main};">{_col_info["name"]}</b> '
                f'<span style="opacity:0.6;">({_col_info.get("role","")})</span></div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── How it Works ─────────────────────────────────────────────────────
    with st.expander("⚙️ How It Works", expanded=False):
        _steps = [
            ("Your Question", "You type a plain-English question — no SQL needed."),
            ("Groq LLaMA 3.3", "70B model parses intent: metric, dimensions, filters, chart type."),
            ("Query Plan → Pandas", "Structured plan executes against your CSV using Pandas groupby/agg."),
            ("Plotly Chart", "Result is rendered as an interactive Plotly chart with your chosen theme."),
            ("AI Insight", "LLaMA generates a 2–3 sentence plain-English insight from the data."),
        ]
        for _i, (_title, _desc) in enumerate(_steps, 1):
            st.markdown(
                f'<div class="pipeline-step">'
                f'<div class="pipeline-num">{_i}</div>'
                f'<div class="pipeline-step-body">'
                f'<div class="pipeline-step-title">{_title}</div>'
                f'<div class="pipeline-step-desc">{_desc}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown(
        f'<div style="font-size:0.65rem;color:{text_muted};text-align:center;">Powered by Groq · LLaMA 3.3 · Plotly</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------

_REVENUE_METRICS = {"total_revenue", "discounted_price", "price"}


def _fmt_number(val: float, metric: str = "") -> str:
    is_currency = metric in _REVENUE_METRICS or "revenue" in metric or "price" in metric
    prefix = "$" if is_currency else ""
    sign = "-" if val < 0 else ""
    abs_val = abs(val)
    if abs_val >= 1_000_000:
        return f"{sign}{prefix}{abs_val / 1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{sign}{prefix}{abs_val / 1_000:.1f}K"
    return f"{sign}{prefix}{abs_val:,.2f}"


def _kpi_card(label: str, value: str, subtitle: str = "") -> str:
    sub = f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub}'
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
    kpi = '<div class="skeleton-block" style="height:90px;margin-bottom:1rem;"></div>'
    return f"""
    <div style="display:flex;gap:1rem;margin-bottom:1rem;">
        {kpi}{kpi}{kpi}{kpi}
    </div>
    <div style="display:flex;gap:1rem;">
        <div style="flex:7;">
            <div class="skeleton-block" style="height:400px;"></div>
        </div>
        <div style="flex:3;display:flex;flex-direction:column;gap:0.75rem;">
            <div class="skeleton-block" style="height:130px;"></div>
            <div class="skeleton-block" style="height:220px;"></div>
        </div>
    </div>
    """

# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------

_query_count = len(st.session_state.chat_history)

if _query_count == 0:
    # ── HERO (shown only on first visit) ──────────────────────────────────
    st.markdown(f"""
    <div class="hero-section">
      <div class="hero-title">
        <span style="color:{text_main};">data</span><span
          style="color:{accent};font-family:'Noto Sans Devanagari',sans-serif;">दर्शनम्</span>
      </div>
      <div class="hero-subtitle">
        Ask your business data anything — in plain English.<br>
        Get instant interactive charts and AI-generated insights. No SQL. No code.
      </div>
      <div>
        <span class="hero-tag">🤖 Groq LLaMA 3.3</span>
        <span class="hero-tag">📊 Plotly Charts</span>
        <span class="hero-tag">🐼 Pandas Engine</span>
        <span class="hero-tag">🔒 No SQL Needed</span>
      </div>
      <div class="hero-feature-grid">
        <div class="hero-feature-card">
          <div class="hero-feature-icon">💬</div>
          <div class="hero-feature-title">Natural Language</div>
          <div class="hero-feature-desc">Type queries the way you think. The AI handles the rest.</div>
        </div>
        <div class="hero-feature-card">
          <div class="hero-feature-icon">⚡</div>
          <div class="hero-feature-title">Instant Charts</div>
          <div class="hero-feature-desc">Bar, line, pie, scatter — auto-selected for your data.</div>
        </div>
        <div class="hero-feature-card">
          <div class="hero-feature-icon">🧠</div>
          <div class="hero-feature-title">AI Insights</div>
          <div class="hero-feature-desc">Every chart comes with a 2–3 sentence expert takeaway.</div>
        </div>
        <div class="hero-feature-card">
          <div class="hero-feature-icon">📂</div>
          <div class="hero-feature-title">Your Data</div>
          <div class="hero-feature-desc">Upload any CSV — the AI adapts to your schema instantly.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # ── Compact header (after first query) ───────────────────────────────
    col_title, col_counter = st.columns([4, 1])
    with col_title:
        st.markdown(f"""
        <div style="margin-bottom:4px;">
          <span style="font-size:32px; font-weight:900; color:{text_main};">data</span><span
                style="font-size:32px; font-weight:900; color:{accent};
                       font-family:'Noto Sans Devanagari',sans-serif;">दर्शनम्</span>
        </div>
        <div style="color:{text_muted}; font-size:12px; margin-bottom:16px;">
          Powered by Groq LLaMA 3.3 · Natural language → instant charts
        </div>
        """, unsafe_allow_html=True)
    with col_counter:
        st.markdown(f"""
        <div style="text-align:right; padding-top:10px; color:{text_muted}; font-size:13px;">
          📊 {_query_count} quer{"y" if _query_count == 1 else "ies"} answered
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Inline Controls - ROW 1
# ---------------------------------------------------------------------------

ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 2])

with ctrl1:
    # Theme toggle
    current_theme = "🌙 Dark" if st.session_state.theme == "dark" else "☀️ Light"
    theme_idx = 0 if st.session_state.theme == "dark" else 1
    theme_choice = st.radio(
        "Theme",
        ["🌙 Dark", "☀️ Light"],
        index=theme_idx,
        horizontal=True,
        key="theme_radio",
        label_visibility="collapsed"
    )
    if "Dark" in theme_choice and st.session_state.theme != "dark":
        st.session_state.theme = "dark"
        st.rerun()
    elif "Light" in theme_choice and st.session_state.theme != "light":
        st.session_state.theme = "light"
        st.rerun()

with ctrl2:
    # CSV Upload
    uploaded_file = st.file_uploader(
        "Upload CSV",
        type="csv",
        label_visibility="collapsed",
        key="csv_uploader"
    )
    if uploaded_file is not None:
        try:
            raw = uploaded_file.getvalue().decode("utf-8")
            df_up = pd.read_csv(io.StringIO(raw))
            df_up = data_engine.prepare_dataframe(df_up)
            st.session_state.custom_df = df_up
            data_engine.set_dataframe(df_up)
            st.success(f"✓ Loaded {len(df_up):,} rows")
        except Exception as exc:
            st.error(f"Could not read file: {exc}")
    else:
        if st.session_state.custom_df is None:
            st.caption("📂 Default: sales.csv · 2022–2023")

with ctrl3:
    # Generate dashboard button + clear chat
    bcol1, bcol2 = st.columns([3, 1])
    with bcol1:
        if st.button("📊 Generate Full Dashboard",
                     type="primary",
                     use_container_width=True,
                     key="gen_dashboard"):
            st.session_state.pending_query = "generate full dashboard overview"
            st.rerun()
    with bcol2:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Active dataset profile
# ---------------------------------------------------------------------------

profile = data_engine.get_dataset_profile()

# ---------------------------------------------------------------------------
# Inline Controls - ROW 2: Example Queries
# ---------------------------------------------------------------------------

st.markdown(f"<div style='font-size:12px; font-weight:600; color:{text_muted}; letter-spacing:1px; margin-bottom:8px;'>✨ TRY THESE EXAMPLES</div>", unsafe_allow_html=True)

examples = data_engine.suggest_questions(5)
example_cols = st.columns(len(examples))
for idx, (col, example) in enumerate(zip(example_cols, examples)):
    with col:
        if st.button(example, use_container_width=True, key=f"example_{idx}_{example}"):
            st.session_state.pending_query = example
            st.rerun()

st.divider()

st.markdown("<div style='margin-bottom:24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------

def _render_mini_chart(chart: dict, index: int = 0, entry_index: int = 0) -> None:
    """Compact chart card used inside the 3-chart dashboard grid."""
    result = chart["result"]
    fig    = chart["fig"]

    if result.get("error"):
        st.error(result.get("message", "Error rendering chart."))
        return

    summary = result.get("summary", {})
    metric  = result.get("metric", "value")

    s1, s2 = st.columns(2, gap="small")
    with s1:
        st.markdown(
            f'<div class="mini-stat">'
            f'<div class="mini-stat-label">Total</div>'
            f'<div class="mini-stat-value">{_fmt_number(summary.get("total", 0), metric)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with s2:
        top_label = summary.get("max_label") or "—"
        st.markdown(
            f'<div class="mini-stat">'
            f'<div class="mini-stat-label">Top Performer</div>'
            f'<div class="mini-stat-value">{top_label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    _live_fig = build_chart(chart["result"], is_dark=(st.session_state.theme == "dark"))
    st.plotly_chart(
        _live_fig,
        use_container_width=True,
        key=f"dash_chart_{entry_index}_{index}",
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': ['resetScale2d'],
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'scrollZoom': True,
            'doubleClick': 'reset'
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)


def _render_dashboard_entry(entry: dict, entry_index: int = 0) -> None:
    """Render the 3-chart dashboard grid from a dashboard pipeline entry."""
    query  = entry["query"]
    charts = entry["charts"]

    st.markdown(
        f'<div class="chat-user-row"><div class="chat-bubble-user">{query}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dashboard-section-header">📊 Dataset Overview Dashboard</div>',
        unsafe_allow_html=True,
    )

    if len(charts) >= 2:
        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            _render_mini_chart(charts[0], index=0, entry_index=entry_index)
        with col_b:
            _render_mini_chart(charts[1], index=1, entry_index=entry_index)

    if len(charts) >= 3:
        _render_mini_chart(charts[2], index=2, entry_index=entry_index)

    st.markdown('<hr class="chat-divider">', unsafe_allow_html=True)


def _render_entry(entry: dict, entry_index: int = 0) -> None:
    query   = entry["query"]
    result  = entry["result"]
    insight = entry["insight"]

    # ── Build user bubble with optional follow-up badge ───────────────────
    _followup_badge = '<span class="followup-badge">🔗 Follow-up</span>' if entry.get("used_context") else ""
    st.markdown(
        f'<div class="chat-user-row">'
        f'<div class="chat-bubble-user">{query}{_followup_badge}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if result.get("error"):
        st.error(result.get("message", "An unknown error occurred."))
        if st.session_state.get("debug_mode") and "parsed" in entry:
            with st.expander("🔍 Debug: LLM Parsed Query"):
                st.json(entry["parsed"])
        st.markdown('<hr class="chat-divider">', unsafe_allow_html=True)
        return

    summary   = result.get("summary", {})
    metric    = result.get("metric", "value")
    data_rows = result.get("data", [])
    parsed    = entry.get("parsed", {})

    # ── Active filter pills ───────────────────────────────────────────────
    _filters = parsed.get("filters", [])
    if _filters:
        _filter_html = '<div class="filter-row">'
        _icon_map = {"year": "📅", "month": "📅", "quarter": "📅", "region": "🌍"}
        for _f in _filters:
            _fi = _icon_map.get(_f.get("field","").lower(), "🔍")
            _filter_html += f'<span class="filter-chip">{_fi} {_f.get("field","")}: {_f.get("value","")}</span>'
        _filter_html += '</div>'
        st.markdown(_filter_html, unsafe_allow_html=True)

    # ── Row 1: 4 KPI tiles ────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        st.markdown(_kpi_card("Total", _fmt_number(summary.get("total", 0), metric)), unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi_card("Avg per Group", _fmt_number(summary.get("average", 0), metric)), unsafe_allow_html=True)
    with k3:
        st.markdown(_kpi_card("Top Performer", summary.get("max_label") or "—"), unsafe_allow_html=True)
    with k4:
        st.markdown(_kpi_card("Top Value", _fmt_number(summary.get("max_value", 0), metric)), unsafe_allow_html=True)

    # ── Row 2: chart (70%) | insight + table (30%) ────────────────────────
    col_chart, col_right = st.columns([7, 3], gap="medium")

    # Chart type switcher — persisted in session state per entry
    _ct_key = f"chart_type_{entry_index}"
    _ct_options = ["auto", "bar", "line", "pie", "scatter", "area"]
    _current_ct = st.session_state.get(_ct_key, "auto")
    _chart_override = None if _current_ct == "auto" else _current_ct

    with col_chart:
        # ── Chart type pill row ──────────────────────────────────────────
        _pill_cols = st.columns(len(_ct_options))
        for _pi, _ct in enumerate(_ct_options):
            with _pill_cols[_pi]:
                _active_cls = "active" if _ct == _current_ct else ""
                _ct_label = {"auto": "✨ Auto", "bar": "Bar", "line": "Line",
                             "pie": "Pie", "scatter": "Scatter", "area": "Area"}.get(_ct, _ct.title())
                if st.button(_ct_label, key=f"ct_{entry_index}_{_ct}",
                             use_container_width=True,
                             help=f"Switch to {_ct} chart"):
                    st.session_state[_ct_key] = _ct
                    st.rerun()

        # ── Render chart ─────────────────────────────────────────────────
        _render_result = dict(result)
        if _chart_override:
            _render_result = {**result, "chart_type": _chart_override}
        _live_fig = build_chart(_render_result, is_dark=(st.session_state.theme == "dark"))
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(
            _live_fig,
            use_container_width=True,
            key=f"chart_{entry_index}",
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['resetScale2d'],
                'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                'scrollZoom': True,
                'doubleClick': 'reset'
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Download CSV ─────────────────────────────────────────────────
        if data_rows:
            _csv_df = pd.DataFrame(data_rows)
            _csv_bytes = _csv_df.to_csv(index=False).encode("utf-8")
            dl_col, pin_col = st.columns([3, 1])
            with dl_col:
                st.download_button(
                    "📥 Download Data (CSV)",
                    data=_csv_bytes,
                    file_name=f"query_{entry_index}_{metric}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"dl_csv_{entry_index}",
                )
            with pin_col:
                if st.button("📌 Save", key=f"pin_{entry_index}", use_container_width=True,
                             help="Save this chart to the sidebar"):
                    _already_saved = any(s["query"] == query for s in st.session_state.saved_charts)
                    if not _already_saved:
                        st.session_state.saved_charts.append({
                            "query":   query,
                            "insight": insight,
                            "summary": summary,
                            "metric":  metric,
                        })
                        st.toast("📌 Chart saved to sidebar!")
                    else:
                        st.toast("Already saved.")

    with col_right:
        # ── Insight card with badge ───────────────────────────────────────
        _insight_badge = (
            '<span class="est-badge">⚠️ Estimated</span>' if entry.get("fallback")
            else '<span class="ai-badge">🤖 AI</span>'
        )
        st.markdown(
            f'<div class="insight-card">'
            f'<div class="insight-header">💡 AI Insight {_insight_badge}</div>'
            f'<div class="insight-text">{insight}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if data_rows:
            st.markdown(
                '<div class="summary-card">'
                '<div class="summary-header">📋 Data Summary</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(pd.DataFrame(data_rows).head(5), use_container_width=True, hide_index=True)

    # ── Row 3: full dataset expander ─────────────────────────────────────
    if data_rows:
        with st.expander("View Full Dataset", expanded=False):
            st.dataframe(pd.DataFrame(data_rows), use_container_width=True, hide_index=True)

    if st.session_state.get("debug_mode") and "parsed" in entry:
        with st.expander("🔍 Debug: LLM Parsed Query"):
            st.json(entry["parsed"])

    st.markdown('<hr class="chat-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Pipeline functions
# ---------------------------------------------------------------------------

def _run_pipeline(query: str) -> None:
    _is_dark = st.session_state.theme == "dark"
    previous_context = None
    if st.session_state.chat_history:
        last = st.session_state.chat_history[-1]
        if last.get("type") == "dashboard":
            for chart in last.get("charts", []):
                if chart.get("result") and not chart["result"].get("error"):
                    previous_context = chart["result"]
                    break
        elif last.get("result") and not last["result"].get("error"):
            previous_context = last["result"]

    with st.spinner("🧠 Analyzing your query…"):
        parsed = parse_query(
            query,
            previous_context=previous_context,
            schema_context=data_engine.build_schema_context(),
        )

        if parsed.get("error"):
            entry = {
                "query":   query,
                "parsed":  parsed,
                "result":  parsed,
                "fig":     None,
                "insight": parsed.get("message", ""),
            }
            st.session_state.chat_history.append(entry)
            _render_entry(entry, entry_index=len(st.session_state.chat_history) - 1)
            return

        st.toast("✅ Query parsed successfully")
        result  = run_query(parsed)
        fig     = build_chart(result, is_dark=_is_dark)
        insight = insight_gen.generate_insight(query, result)
        if insight_gen._last_used_fallback:
            st.toast("⚠️ Using fallback response")

    entry = {
        "query":        query,
        "parsed":       parsed,
        "result":       result,
        "fig":          fig,
        "insight":      insight,
        "used_context": previous_context is not None,
        "fallback":     insight_gen._last_used_fallback,
    }
    st.session_state.chat_history.append(entry)
    _render_entry(entry, entry_index=len(st.session_state.chat_history) - 1)


def _run_dashboard_pipeline(query: str) -> None:
    _is_dark = st.session_state.theme == "dark"
    dashboard_queries = parse_dashboard_query(query)
    charts = []
    with st.spinner("📊 Building your full dashboard…"):
        for p in dashboard_queries:
            result = run_query(p)
            fig    = build_chart(result, is_dark=_is_dark)
            charts.append({"parsed": p, "result": result, "fig": fig})

    if not charts:
        st.error("Could not generate a dashboard for this dataset. Make sure the dataset has numeric and categorical columns.")
        return
    entry = {"type": "dashboard", "query": query, "charts": charts}
    st.session_state.chat_history.append(entry)
    _render_dashboard_entry(entry, entry_index=len(st.session_state.chat_history) - 1)

# ---------------------------------------------------------------------------
# Render chat history
# ---------------------------------------------------------------------------

for _ei, entry in enumerate(st.session_state.chat_history):
    if entry.get("type") == "dashboard":
        _render_dashboard_entry(entry, entry_index=_ei)
    else:
        _render_entry(entry, entry_index=_ei)

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

_example_hints = data_engine.suggest_questions(3)
_placeholder = _example_hints[0] if _example_hints else "Ask a question about your data…"
query_input   = st.chat_input(_placeholder)
pending_query = st.session_state.pop("pending_query", None)
active_query  = query_input or pending_query

if active_query:
    _skeleton_ph = st.empty()
    _skeleton_ph.markdown(_skeleton_html(), unsafe_allow_html=True)
    if parse_dashboard_query(active_query) is not None:
        _run_dashboard_pipeline(active_query)
    else:
        _run_pipeline(active_query)
    _skeleton_ph.empty()

# 📊 DataDarshan — Conversational BI Dashboard

DataDarshan is a natural-language business intelligence dashboard that lets you explore sales data through plain-English questions. Type a question, and the app uses Google Gemini to parse your intent, runs the query against a pandas DataFrame, renders an interactive Plotly chart with a dark-themed design system, and delivers a 2–3 sentence AI-generated insight — all in under five seconds.

---

## Screenshot

> *Add a screenshot here before presentation.*
>
> `docs/screenshot.png`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Charts | Plotly Express / Graph Objects |
| Data | Pandas |
| AI | Google Gemini API (`gemini-1.5-flash`) |
| Config | python-dotenv |

---

## Setup

### 1. Clone and install

```bash
git clone <repo-url>
cd DataDarshan2
pip install -r requirements.txt
```

### 2. Add your Gemini API key

```bash
cp .env.example .env
# Open .env and replace  your_key_here  with your actual key
```

Get a free key at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

### 3. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Project Structure

```
DataDarshan2/
├── app.py            # Streamlit frontend — chat UI, sidebar, pipeline orchestration
├── llm_parser.py     # Gemini-powered NL → JSON query parser
├── data_engine.py    # Pandas query executor (filters, groupby, aggregation)
├── chart_builder.py  # Plotly dark-theme chart renderer (bar, line, pie, scatter, heatmap)
├── insight_gen.py    # Gemini-powered 2–3 sentence business insight generator
├── sales.csv         # Sample dataset (2022–2023 sales, ~10k rows)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Demo Queries

Use these during the presentation to showcase the full range of chart types and AI insight quality:

| # | Query | What it demonstrates |
|---|---|---|
| 1 | `Show total revenue by region as a bar chart` | Vertical bar, KPI tiles, regional insight |
| 2 | `Monthly revenue trend for 2023 broken down by product category` | Multi-series line chart, time intelligence |
| 3 | `Top 5 product categories by average rating` | Ranked bar, `sort_by` + `limit` handling |

---

## Dataset Schema

`sales.csv` — 2022–2023 global sales records.

| Column | Type | Description |
|---|---|---|
| `order_id` | int | Unique order identifier |
| `order_date` | date | Order date (2022-01-01 – 2023-12-31) |
| `product_id` | int | Product identifier |
| `product_category` | str | Beauty · Books · Electronics · Fashion · Home & Kitchen · Sports |
| `customer_region` | str | Asia · Europe · Middle East · North America |
| `payment_method` | str | Cash on Delivery · Credit Card · Debit Card · UPI · Wallet |
| `price` | float | Unit price |
| `discount_percent` | int | Discount applied (%) |
| `quantity_sold` | int | Units sold |
| `rating` | float | Customer rating (1.0 – 5.0) |
| `review_count` | int | Number of reviews |
| `discounted_price` | float | Price after discount |
| `total_revenue` | float | `discounted_price × quantity_sold` |

---

## License

MIT

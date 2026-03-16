"""Extract clean CSV from Safari webarchive format and load into SQLite."""
import re
import sqlite3
import csv
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_FILE = os.path.join(PROJECT_ROOT, "Amazon Sales.csv")
CLEAN_CSV = os.path.join(PROJECT_ROOT, "data", "sales.csv")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "sales.db")


def extract_csv():
    """Extract CSV data from webarchive wrapper."""
    with open(RAW_FILE, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    # Find the CSV content between <pre> tags or starting with "order_id"
    match = re.search(r"(order_id,order_date.*)", raw, re.DOTALL)
    if not match:
        raise ValueError("Could not find CSV data in file")

    csv_text = match.group(1)

    # Clean up: remove any trailing HTML/binary and fix HTML entities
    csv_text = re.sub(r"</pre>.*", "", csv_text, flags=re.DOTALL)
    csv_text = csv_text.replace("&amp;", "&")
    csv_text = csv_text.replace("&lt;", "<")
    csv_text = csv_text.replace("&gt;", ">")
    csv_text = csv_text.replace("&quot;", '"')

    # Remove any trailing whitespace/null bytes
    csv_text = csv_text.strip().rstrip("\x00")

    os.makedirs(os.path.dirname(CLEAN_CSV), exist_ok=True)
    with open(CLEAN_CSV, "w", encoding="utf-8", newline="") as f:
        f.write(csv_text)

    print(f"Extracted {csv_text.count(chr(10))} rows to {CLEAN_CSV}")
    return CLEAN_CSV


def load_into_sqlite(csv_path: str):
    """Load clean CSV into SQLite with proper types and indexes."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table with proper types
    cursor.execute("""
        CREATE TABLE sales (
            order_id INTEGER PRIMARY KEY,
            order_date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_category TEXT NOT NULL,
            price REAL NOT NULL,
            discount_percent INTEGER NOT NULL,
            quantity_sold INTEGER NOT NULL,
            customer_region TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            rating REAL NOT NULL,
            review_count INTEGER NOT NULL,
            discounted_price REAL NOT NULL,
            total_revenue REAL NOT NULL
        )
    """)

    # Load CSV
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append((
                int(row["order_id"]),
                row["order_date"],
                int(row["product_id"]),
                row["product_category"],
                float(row["price"]),
                int(row["discount_percent"]),
                int(row["quantity_sold"]),
                row["customer_region"],
                row["payment_method"],
                float(row["rating"]),
                int(row["review_count"]),
                float(row["discounted_price"]),
                float(row["total_revenue"]),
            ))

    cursor.executemany(
        "INSERT INTO sales VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows
    )

    # Create indexes for common query patterns
    cursor.execute("CREATE INDEX idx_order_date ON sales(order_date)")
    cursor.execute("CREATE INDEX idx_product_category ON sales(product_category)")
    cursor.execute("CREATE INDEX idx_customer_region ON sales(customer_region)")
    cursor.execute("CREATE INDEX idx_payment_method ON sales(payment_method)")

    conn.commit()

    # Verify
    count = cursor.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    print(f"Loaded {count} rows into {DB_PATH}")

    # Show sample
    sample = cursor.execute("SELECT * FROM sales LIMIT 3").fetchall()
    for row in sample:
        print(row)

    conn.close()


if __name__ == "__main__":
    csv_path = extract_csv()
    load_into_sqlite(csv_path)
    print("Done!")

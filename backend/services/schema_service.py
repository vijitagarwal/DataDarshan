"""Dynamic schema introspection for uploaded CSVs."""
import sqlite3
import pandas as pd
import os
import re


def create_table_from_csv(db_path: str, csv_path: str, table_name: str) -> dict:
    """Create a SQLite table from a CSV file and return schema info."""
    df = pd.read_csv(csv_path)

    # Clean column names: lowercase, replace spaces/special chars with underscores
    clean_cols = {}
    for col in df.columns:
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", col.strip().lower())
        clean = re.sub(r"_+", "_", clean).strip("_")
        clean_cols[col] = clean
    df.rename(columns=clean_cols, inplace=True)

    # Clean HTML entities in string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.replace("&amp;", "&", regex=False)
        df[col] = df[col].str.replace("&lt;", "<", regex=False)
        df[col] = df[col].str.replace("&gt;", ">", regex=False)

    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

    return introspect_table(db_path, table_name)


def introspect_table(db_path: str, table_name: str) -> dict:
    """Generate schema info for the system prompt."""
    conn = sqlite3.connect(db_path)

    cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
    columns = cursor.fetchall()

    schema = {"table_name": table_name, "columns": [], "row_count": 0}

    for col in columns:
        col_name = col[1]
        col_type = col[2]

        sample_cursor = conn.execute(
            f"SELECT DISTINCT [{col_name}] FROM [{table_name}] LIMIT 10"
        )
        samples = [row[0] for row in sample_cursor.fetchall()]

        count_cursor = conn.execute(
            f"SELECT COUNT(DISTINCT [{col_name}]) FROM [{table_name}]"
        )
        distinct_count = count_cursor.fetchone()[0]

        schema["columns"].append({
            "name": col_name,
            "type": col_type,
            "distinct_count": distinct_count,
            "sample_values": samples[:6],
            "is_categorical": distinct_count <= 20,
        })

    count_cursor = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]")
    schema["row_count"] = count_cursor.fetchone()[0]

    conn.close()
    return schema

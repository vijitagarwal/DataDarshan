"""SQL validation and execution service."""
import sqlite3
import re
import sqlparse


def validate_sql(sql: str) -> tuple[bool, str]:
    """Validate SQL is safe to execute."""
    if not sql or not sql.strip():
        return False, "Empty SQL query"

    parsed = sqlparse.parse(sql)
    if not parsed:
        return False, "Could not parse SQL"

    stmt = parsed[0]

    # Must be a SELECT statement
    if stmt.get_type() != "SELECT":
        return False, f"Only SELECT queries allowed, got {stmt.get_type()}"

    # No multiple statements
    if len(parsed) > 1:
        return False, "Multiple statements not allowed"

    # No dangerous keywords (as standalone words)
    sql_upper = sql.upper()
    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "EXEC", "ATTACH", "DETACH", "PRAGMA"]
    for keyword in dangerous:
        if re.search(r"\b" + keyword + r"\b", sql_upper):
            return False, f"Forbidden keyword: {keyword}"

    return True, "Valid"


def execute_sql(db_path: str, sql: str, timeout: float = 5.0) -> list[dict]:
    """Execute SQL and return results as list of dicts."""
    is_valid, msg = validate_sql(sql)
    if not is_valid:
        raise ValueError(f"SQL validation failed: {msg}")

    conn = sqlite3.connect(db_path, timeout=timeout)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

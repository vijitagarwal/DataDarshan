"""CSV upload endpoint."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.schema_service import create_table_from_csv, introspect_table
from config import DB_PATH
from routers.query import gemini
import tempfile
import os
import re

router = APIRouter()


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and create a queryable table."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Create a safe table name from filename
    base = os.path.splitext(file.filename)[0]
    table_name = re.sub(r"[^a-zA-Z0-9_]", "_", base.lower()).strip("_")
    table_name = re.sub(r"_+", "_", table_name)
    if not table_name:
        table_name = "uploaded_data"

    # Save to temp file and process
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        schema_info = create_table_from_csv(DB_PATH, tmp_path, table_name)

        # Update Gemini's schema cache
        gemini.set_schema(table_name, schema_info)

        return {
            "table_name": table_name,
            "row_count": schema_info["row_count"],
            "columns": [
                {
                    "name": col["name"],
                    "type": col["type"],
                    "distinct_count": col["distinct_count"],
                    "sample_values": col["sample_values"],
                }
                for col in schema_info["columns"]
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/schema/{table_name}")
async def get_schema(table_name: str):
    """Get schema info for a table."""
    try:
        schema = introspect_table(DB_PATH, table_name)
        return schema
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table not found: {str(e)}")

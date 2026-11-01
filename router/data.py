import contextlib
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from snowflake.connector.errors import Error as SnowflakeError
from starlette.concurrency import run_in_threadpool

from database import create_sync_connection  # Import the centralized helper
from schemas.data import (
    IngestionRequest,
    IngestionResponse,
    TableMetadata,
    TablePreviewResponse,
)

router = APIRouter(prefix="/data", tags=["Data Management"])

def sync_list_tables() -> list[str]:
    """Synchronously fetches the list of tables from Snowflake."""
    with contextlib.closing(create_sync_connection()) as connection, connection.cursor() as cur:
        cur.execute("SHOW TABLES")
        return [row[1] for row in cur.fetchall()]

def sync_get_table_metadata(table_name: str) -> dict[str, Any]:

    """Synchronously fetches metadata for a specific table."""
    with contextlib.closing(create_sync_connection()) as connection, connection.cursor() as cur:
        cur.execute(f"DESCRIBE TABLE {table_name}")
        columns = [{"name": row[0], "type": row[1]} for row in cur.fetchall()]
        
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        row = cur.fetchone()
        row_count = row[0] if row else 0
        
        return {"table_name": table_name, "row_count": row_count, "columns": columns}

def _sync_preview_table(table_name: str, limit: int) -> dict[str, Any]:
    with contextlib.closing(create_sync_connection()) as conn, conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        columns = [col[0].lower() for col in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

        return {
            "table_name": table_name.upper(),
            "limit": limit,
            "rows": rows,
        }

@router.get("/tables", response_model=list[str])
async def list_tables():
    try:
        return await run_in_threadpool(sync_list_tables)
    except SnowflakeError as e:
        raise HTTPException(status_code=500, detail=f"Snowflake Error fetching tables: {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail= str(e))

@router.get("/tables/{table_name}", response_model=TableMetadata)
async def get_table_metadata(table_name: str):
    try:
        return await run_in_threadpool(sync_get_table_metadata, table_name)
    except SnowflakeError as e:
        raise HTTPException(status_code=500, detail=f"Snowflake Error fetching metadata for {table_name}: {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tables/{table_name}/preview", response_model=TablePreviewResponse)
async def preview_table(table_name: str, limit: int = Query(default=10, ge=1, le=100)):
    try:
        return await run_in_threadpool(_sync_preview_table, table_name, limit)
    except SnowflakeError as e:
        raise HTTPException(status_code=500, detail=f"Snowflake Error previewing table {table_name}: {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/run", response_model=IngestionResponse)
async def run_ingestion(request: IngestionRequest):
    """ Triggers an async batch ingestion job. For now, it simulates the ingestion process and returns a job ID. """
    job_id = str(uuid.uuid4())
    return{
        "job_id": job_id,
        "status": "QUEUED",
        "message": f"Ingestion job for {request.source_file} to {request.target_table} has been queued."
    }
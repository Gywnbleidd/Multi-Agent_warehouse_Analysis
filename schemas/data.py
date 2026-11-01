from typing import Any

from pydantic import BaseModel, Field


class TableMetadata(BaseModel):
    table_name: str
    row_count: int | None = None  
    columns: list[dict[str, str]]  

class TablePreviewResponse(BaseModel):
    table_name: str
    limit: int
    rows: list[dict[str, Any]]

class IngestionRequest(BaseModel):

    source_file: str = Field(examples=["olist_orders_dataset.csv"])
    target_table: str = Field(examples=["ORDERS"])

class IngestionResponse(BaseModel):
    job_id: str
    status: str
    message: str

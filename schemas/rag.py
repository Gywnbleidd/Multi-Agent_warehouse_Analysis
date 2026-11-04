from typing import list

from pydantic import BaseModel, Field


class RAGIngestRequest(BaseModel):
    source_type: str = Field(..., example="snowflake_reviews")
    limit: int|None = Field(1000, description="Max number of reviews to ingest")

class RAGIngestResponse(BaseModel):
    status: str
    documents_indexed: int
    message: str

class RAGStatusResponse(BaseModel):
    index_loaded: bool
    total_documents: int
    storage_dir: str

class DocumentInfo(BaseModel):
    doc_id: str
    text_preview: str
    metadata: dict
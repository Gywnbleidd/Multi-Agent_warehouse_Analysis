from fastapi import APIRouter, HTTPException

from schemas.rag import (
    DocumentInfo,
    RAGIngestRequest,
    RAGIngestResponse,
    RAGStatusResponse,
)
from services.rag_service import rag_service

router = APIRouter(prefix="/data/rag", tags=["RAG Administration"])

@router.post("/ingest", response_model=RAGIngestResponse)
async def ingest_rag_data(payload: RAGIngestRequest):
    """Index customer reviews from Snowflake into the LlamaIndex vector store."""
    try:
        count = await rag_service.ingest_reviews(limit=payload.limit or 1000)
        return {
            "status": "SUCCESS",
            "documents_indexed": count,
            "message": f"Successfully indexed {count} customer reviews into vector storage."
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"RAG ingestion failed: {e!s}")

@router.get("/status", response_model=RAGStatusResponse)
async def get_rag_status():
    """Check LlamaIndex vector store indexing status."""
    try:
        return await rag_service.get_status()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to retrieve RAG status: {e!s}")

@router.get("/documents", response_model=list[DocumentInfo])
async def list_rag_documents():
    """List indexed documents in the knowledge base."""
    try: 
        return await rag_service.list_documents()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to list RAG documents: {e!s}")

@router.delete("/delete/documents/{review_id}")
async def delete_rag_document(review_id: str):
    """Remove a document from the vector index by ID."""
    try:
        success = await rag_service.delete_document(review_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Document with ID {review_id} not found.")
        return {"status": "SUCCESS", "message": f"Document {review_id} removed successfully."}
    except HTTPException :
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to delete RAG document: {e!s}")
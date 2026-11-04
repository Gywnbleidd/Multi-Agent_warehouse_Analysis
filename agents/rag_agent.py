import contextlib
import json

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from starlette.concurrency import run_in_threadpool

from agents.state import InvestigationState
from database import create_sync_connection


def _sync_vector_search(query: str) -> str:
    embeddings = GoogleGenerativeAIEmbeddings(models="text-embeddings-004")
    query_vector = embeddings.embed_query(query)
    vector_str = str(query_vector)

    search_query = """
        SELECT chunk_text, review_id, metadata,
                VECTOR_COSINE_SIMILARITY(embedding, TO_VECTOR(%s)) AS similarity
        FROM review_vector_store
        ORDER BY similarity DESC
        LIMIT 5;
"""
    with contextlib.closing(create_sync_connection()) as connection, connection.cursor() as cur:
        cur.execute(search_query, (vector_str,))
        rows = cur.fetchall()

        snippets = []
        for row in rows:
            chunk_text, review_id, metadata, similarity = row
            
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {}
            score = metadata.get("review_score", "N/A") if metadata else "N/A"

            snippets.append(f"- [Review ID: {review_id} Score: {score}  | Similarity: {similarity:.3f}] {chunk_text}")

        return "/n".join(snippets) if snippets else "No relevant customer reviews found."

async def reg_agent_node(state: InvestigationState) -> InvestigationState:
    """Searches Snowflake vector store using modern Google embeddings."""
    query = state["query"]
    try:
        rag_context = await run_in_threadpool(_sync_vector_search, query)
        state["rag_context"] = rag_context
    except Exception as e:
        state["rag_context"] = f"RAG search failed: {e!s}"
        if "errors" not in state:
            state["errors"] = []
        state["errors"]. append(str(e))
    return state

import contextlib
import json
from typing import Any, dict, list

from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.gemini import GeminiEmbedding
from snowflake.connector.errors import DatabaseError, ProgrammingError
from starlette.concurrency import run_in_threadpool

from database import create_sync_connection


class RAGService: 
    def __init__(self):
        self.embed_model = GeminiEmbedding(model="text-embedding-3-small")
    def _sync_ingest_snowflake_reviews(self, limit: int) -> int:
        """Fetches customer reviews from snowflake, chunks them, computers embeddings, and stores them in Snowflake vector table."""
        fetch_query = f"""
        
        SELECT review_id, review_text, metadata
        FROM customer_reviews
        WHERE review_comment_message IS NOT NULL
        LIMIT {limit}
    """
        with contextlib.closing(create_sync_connection()) as connection, connection.cursor() as cur:
            cur.execute(fetch_query)
            rows = cur.fetchall()

            documents = []
            for row in rows:
                review_id, score, comment = row
                doc = Document(
                    text=comment,
                    id_=f"review_{review_id}",
                    metadata={
                        "review_id": review_id,
                        "review_score": score,
                        "source": "snowflake_reviews"
                    }
                )
                documents.append(doc)
            if not documents:
                return 0

            # Parse documents into smaller text chunks (nodes)
            parser = SimpleNodeParser.from_defaults(chunk_size=512, chunk_overlap=50)
            nodes = parser.get_nodes_from_documents(documents)

            inserted_count = 0
            for node in nodes:
                chunk_id = node.node_id
                review_id = node.metadata.get("review_id")
                chunk_text = node.text
                metadata_json = json.dumps(node.metadata)

                #Generate vector embedding as a python list
                embedding_vector = self.embed.get_text_embedding(chunk_text)
                #format embedding vector as a string for snowflake VECTOR insertion
                vector_str = str(embedding_vector)

                insert_query = """
                    MERGE INTO review_vector_store AS target
                    USING (SELECT %s AS chunk_id, %s AS review_id, %s AS chunk_text, PARSE_JSON(%s) AS metadata) AS source
                    ON target.chunk_id = source.chunk_id
                    WHEN NOT MATCHED THEN 
                    INSERT (chunk_id, review_id, chunk_text, embedding, metadata)
                    VALUES (source.chunk_id, source.review_id, source.chunk_text, TO_VECTOR(%s), source.metadata)
                """
                cur.execute(insert_query, (chunk_id, str(review_id), chunk_text, metadata_json, vector_str))
                inserted_count += 1

            connection.commit()
        return inserted_count
    async def ingest_reviews(self, limit: int) -> int:
        """Asynchronously ingests reviews into snowfalke vectoe storage."""
        return await run_in_threadpool(self._sync_ingist_snowflake_reviews, limit)
   
    def _sync_query_reviews(self) -> dict[str, Any]:
        with contextlib.closing(create_sync_connection()) as connection, connection.cursor() as cur:
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT review_id) FROM review_vector_store")
            row = cur.fetchone()
            total_chunks = row[0] if row else 0
            total_reviews = row[1] if row else 0
            return {
                "index_loaded": True,
                "total_chunks": total_chunks,
                "total_source_reviews": total_reviews,
                "storage_backend": "snowflake Native Vector Table"
            }
    async def get_status(self) -> dict[str, Any]:
        return await run_in_threadpool(self._sync_get_status)

    def _sync_list_documents(self) -> list[dict[str, Any]]:
        with contextlib.closing(create_sync_connection()) as conn, conn.cursor() as cur:
            cur.execute("SELECT chunk_id, review_id, chunk_text, metadata FROM review_vector_store LIMIT 50")
            rows = cur.fetchall()
            results = []
            for row in rows:
                results.append({
                    "chunk_id": row[0],
                    "review_id": row[1],
                    "chunk_text": row[2][:150] + "..." if len(row[2]) > 150 else row[2],
                    "metadata": row[3]
                })
            return results
    async def list_documents(self) -> list[dict[str, Any]]:
        return await run_in_threadpool(self._sync_list_documents)

    def _sync_delete_document(self, review_id: str) -> bool:
        try: 
            with contextlib.closing(create_sync_connection()) as conn, conn.cursor() as cur:
                cur.execute("DELETE FROM review_vector_store WHERE review_id = %s", (review_id,))
                conn.commit()
            return True
        except (ProgrammingError, DatabaseError) as e:
            print(f"Snowflake database error {e.errno} ({e.sqlstate}): {e.msg}")
            return False

    async def delete_document(self, review_id: str) -> bool:
        """Asynchronously delete chunks associated with a review ID from Snowflake."""
        return await run_in_threadpool(self._sync_delete_document, review_id)

rag_service = RAGService()
import contextlib

import snowflake.connector
from snowflake.connector.errors import Error as SnowflakeError
from starlette.concurrency import run_in_threadpool

from config import settings


def create_sync_connection():
    """Centralized helper to instantiate a synchronous Snowflake connection."""
    return snowflake.connector.connect(
        user=settings.SNOWFLAKE_USER,
        password=settings.SNOWFLAKE_PASSWORD,
        account=settings.SNOWFLAKE_ACCOUNT,
        warehouse=settings.SNOWFLAKE_WAREHOUSE,
        database=settings.SNOWFLAKE_DATABASE,
        schema=settings.SNOWFLAKE_SCHEMA,
        role=settings.SNOWFLAKE_ROLE,
    )

def _verify_snowflake_connection() -> None:
    """Synchronously opens, tests, and safely closes a Snowflake connection."""
    with contextlib.closing(create_sync_connection()) as connection, connection.cursor() as cur:
        cur.execute("SELECT CURRENT_VERSION()")
        cur.fetchone()

async def test_snowflake_connection() -> bool:
    """Asynchronously runs the connection verification in a thread pool."""
    try:
        await run_in_threadpool(_verify_snowflake_connection)
        return True
    except SnowflakeError as e:
        print(f"Error testing Snowflake connection: {e}")
        return False
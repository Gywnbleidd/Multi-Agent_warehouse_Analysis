import contextlib

from agents.state import InvestigationState
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from starlette.concurrency import run_in_threadpool

from database import create_sync_connection

OLIST_SCHEMA_CONTEXT = """
You are an expert Snowflake SQL developer. The database contains the following key Olist e-commerce tables:
1. ORDERS (order_id, customer_id, order_status, order_purchase_timestamp, order_delivered_customer_date)
2. ORDER_ITEMS (order_id, order_item_id, product_id, seller_id, price, freight_value)
3. CUSTOMERS (customer_id, customer_unique_id, customer_city, customer_state)
4. PRODUCTS (product_id, product_category_name, product_name_lenght)
5. SELLERS (seller_id, seller_city, seller_state)
6. ORDER_REVIEWS (review_id, order_id, review_score, review_comment_message)

Write a valid Snowflake SQL query to answer the user question. Return ONLY the raw SQL string inside a markdown block or clean text, no extra commentary. Always include a LIMIT clause (max 100 rows).
"""
def _sync_execute_sql(query: str) -> str:
    with contextlib.closing(create_sync_connection()) as connection, connection.cursor() as cur:
        cur.execute(query)
        columns = [col[0].lower() for col in cur.description]
        rows = cur.fetchall()
        result_lines = [", ".join(columns)]
        for row in rows[:20]:
            result_lines.append(", ".join(str(val) for val in row))
        return "\n".join(result_lines)
    
async def sql_agent_node(state: InvestigationState) -> InvestigationState:
    """Generates and exectutes a SQL query"""
    query = state["query"]

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        prompt = ChatPromptTemplate.from_messages([
            ("system", OLIST_SCHEMA_CONTEXT),
            ("user", "{query}")
        ])

        chain = prompt | llm
        response = await chain.ainvoke({"query": query})
        sql_text = response.content.replace("```sql", "").replace("```", "").strip()

        sql_result = await run_in_threadpool(_sync_execute_sql, sql_text)

        state["sql_query"] = sql_text
        state["sql_result"] = sql_result
    except Exception as e:
        state["sql_query"] = "ERROR_GENERATING_SQL"
        state["sql_result"] = f"failed to execute SQL: {e!s}"
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(str(e))
    
    return state
                            
                            
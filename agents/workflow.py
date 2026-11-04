from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from agents.rag_agent import rag_agent_node
from agents.sql_agent import sql_agent_node
from agents.state import InvestigationState


async def synthesis_node(state: InvestigationState) -> InvestigationState:
    """Synthesizes structured metrics and unstructured evidence using modern Gemini chat interface."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert e-commerce business analyst. Synthesize a professional investigation report combining quantitative metrics (from SQL) and qualitative feedback (from Customer Review RAG)."),
        ("user", """
User Question: {query}

[Quantitative SQL Results]
{sql_query}
Result Data:
{sql_result}

[Qualitative RAG Customer Evidence]
{rag_context}

Provide a structured, comprehensive business analysis answering the user's question with actionable insights.
""")
    ])

    chain = prompt | llm 
    response = await chain.ainvoke({
        "query": state.get("sql_query", "N/A"),
        "sql_query": state.get("sql_query", "N/A"),
        "sql_result": state.get("sql_result", "No data"),
        "rag_context": state.get("rag_context", "No data")
    })

    state["final_answer"] = response.content
    return state

workflow = StateGraph(InvestigationState)

workflow.add_node("sql_agent", sql_agent_node)
workflow.add_node("rag_agent", rag_agent_node)
workflow.add_node("synthesizer", synthesis_node)

workflow.set_entry_point("sql_agent")
workflow.add_edge("sql_agent", "rag_agent")
workflow.add_edge("rag_agent", "synthesizer")
workflow.add_edge("synthesizer", END)

app_graph = workflow.compile()
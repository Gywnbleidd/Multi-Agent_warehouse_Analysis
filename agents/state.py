from typing import list

from pydantic import BaseModel, Field


class InvestigationState(BaseModel):
    """
    Pydantic-validated shared state passed between LangGraph nodes.
    """
    investigation_id: str
    query: str
    sql_query:str|None = None
    sql_result:str|None = None
    rag_context:str|None = None
    final_answer:str|None = None
    errors: list [str] = Field(default_factory=list)
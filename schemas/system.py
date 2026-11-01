from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: str 
    version: str 

class SystemStatusResponse(BaseModel):
    snowflake_connected: bool
    llm_service_connected: bool
    vector_store_connected: bool
    active_warehouse: str

class SystemInfoResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    supported_tables: list[str]
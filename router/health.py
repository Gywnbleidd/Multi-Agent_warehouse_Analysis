from fastapi import APIRouter
from config import settings
from schemas.system import HealthCheckResponse, SystemStatusResponse, SystemInfoResponse
from database import test_snowflake_connection

router = APIRouter(tags=["Health and System"], prefix="/system")

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Endpoint to check the health of the application."""
    return {"status": "healthy", "version": settings.APP_VERSION}

@router.get("/status", response_model=SystemStatusResponse)
async def system_status():
    """Endpoint to check the status of various system components."""
    snowflake_connected = await test_snowflake_connection()

    return {
        "snowflake_connected": snowflake_connected,
        "llm_service_connected": True, #phase 4
        "vector_store_connected": True,  #phase 3
        "active_warehouse": settings.SNOWFLAKE_WAREHOUSE
    }

@router.get("/system/info", response_model=SystemInfoResponse)
async def system_info():
    return {
        "app_name": settings.APP_NAME,
        "version": settings.API_VERSION,
        "environment": "development",
        "supported_tables": ["CUSTOMERS", "ORDERS", "ORDER_ITEMS", "PRODUCTS", "SELLERS", "ORDER_REVIEWS"]
    }
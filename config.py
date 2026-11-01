from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = " Snowflake Data Analytics Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    SNOWFLAKE_USER: str = ".."
    SNOWFLAKE_PASSWORD: str = ".."
    SNOWFLAKE_ACCOUNT: str = ".."
    SNOWFLAKE_WAREHOUSE: str = ".."
    SNOWFLAKE_DATABASE: str = "..."
    SNOWFLAKE_SCHEMA: str = "PUBLIC"
    SNOWFLAKE_ROLE: str = "ACCOUNTADMIN"

settings = Settings()
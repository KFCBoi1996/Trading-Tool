from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    app_name: str = Field(default="Trading Tool")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="dev")


config = AppConfig()

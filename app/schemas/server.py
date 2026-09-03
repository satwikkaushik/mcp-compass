from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class McpServerCreate(BaseModel):
    name: str
    description: str
    endpoint_url: str
    version: str = "0.1.0"
    tags: list[str] = Field(default_factory=list)


class McpServerUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    endpoint_url: str | None = None
    version: str | None = None
    tags: list[str] | None = None


class McpServerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    endpoint_url: str
    version: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

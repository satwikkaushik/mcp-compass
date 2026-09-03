from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class McpServerCreate(BaseModel):
    name: str = Field(examples=["github-webhook-validator"])
    description: str = Field(examples=["Validates and parses GitHub webhook payloads"])
    endpoint_url: str = Field(examples=["http://localhost:9000/mcp"])
    version: str = Field(default="0.1.0", examples=["0.1.0"])
    tags: list[str] = Field(default_factory=list, examples=[["github", "webhooks"]])
    workspace_id: int


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
    workspace_id: int
    created_at: datetime
    updated_at: datetime

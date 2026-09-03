from pydantic import BaseModel, Field

from app.schemas.server import McpServerRead


class DiscoverRequest(BaseModel):
    query: str = Field(examples=["something that can validate GitHub webhooks"])


class DiscoverResponse(BaseModel):
    answer: str
    matches: list[McpServerRead]

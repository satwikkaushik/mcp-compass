# app/models/server.py — replace the full file
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ARRAY, Column, DateTime, String
from sqlmodel import Field, SQLModel


class McpServer(SQLModel, table=True):
    __tablename__ = "mcp_servers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    endpoint_url: str
    version: str
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class McpServerVersion(SQLModel, table=True):
    __tablename__ = "mcp_server_versions"

    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="mcp_servers.id", ondelete="CASCADE")
    version: str
    name: str
    description: str
    endpoint_url: str
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
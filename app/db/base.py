from sqlmodel import SQLModel

from app.models.server import McpServer, McpServerVersion  # noqa: F401

metadata = SQLModel.metadata

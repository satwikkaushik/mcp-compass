from sqlmodel import SQLModel

from app.models.server import McpServer, McpServerVersion  # noqa: F401
from app.models.user import User, Workspace, WorkspaceMembership  # noqa: F401

metadata = SQLModel.metadata

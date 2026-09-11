# MCP Compass

[![Lint](https://github.com/satwikkaushik/mcp-compass/actions/workflows/lint.yml/badge.svg)](https://github.com/satwikkaushik/mcp-compass/actions/workflows/lint.yml)
[![Build](https://github.com/satwikkaushik/mcp-compass/actions/workflows/build.yml/badge.svg)](https://github.com/satwikkaushik/mcp-compass/actions/workflows/build.yml)
[![Test](https://github.com/satwikkaushik/mcp-compass/actions/workflows/test.yml/badge.svg)](https://github.com/satwikkaushik/mcp-compass/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](pyproject.toml)

A registry, discovery, and validation layer for [Model Context Protocol](https://modelcontextprotocol.io) servers. Publish, search, and connectivity-check MCP servers across workspaces, and search them with plain-language queries.

## Why this exists

MCP standardizes how LLM applications talk to tools and data, but as an org accumulates MCP servers there's no shared answer to "what servers exist, who owns them, are they actually reachable, and which one do I need for X?" MCP Compass answers that: a catalog with RBAC per workspace, automated spec-compliance checks on every publish, and RAG-based discovery, so a query like _"something that can validate GitHub webhooks"_ returns the right server with an explanation grounded in its actual metadata, not a keyword grep.

## Features

- Publish, update, and version MCP servers. Every change writes an append-only version snapshot, so history is never overwritten.
- JWT authentication with roles scoped to workspace membership, not to the user globally, so someone can be admin in one workspace and a plain member in another.
- Connectivity validation on every publish and update: a real MCP handshake (`initialize` + `list_tools`) against the server's endpoint through the official `mcp` client SDK, not just a TCP ping. Status is stored as `healthy`, `unreachable`, or `invalid`.
- Semantic discovery over natural-language queries. `POST /discover` embeds the query, retrieves the closest servers from Postgres by `pgvector` cosine distance, and generates an answer grounded in that retrieved context.
- Auto-generated API docs at `/docs`.
- Runs in Docker: one `docker compose up` brings up the API and a `pgvector`-enabled Postgres, with migrations included.
- GitHub Actions runs lint and a Docker build on every push.

## Architecture

```
                         ┌──────────────┐
   client / curl ──────► │   FastAPI    │
                         │  (JWT + RBAC)│
                         └──────┬───────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
     ┌────────────────┐ ┌───────────────┐ ┌─────────────────┐
     │  Postgres +     │ │  MCP client    │ │  Gemini API      │
     │  pgvector       │ │  (validator)   │ │  (embeddings +   │
     │  servers, users,│ │  ─── initialize│ │   generation)    │
     │  versions,      │ │      + list_   │ │                  │
     │  embeddings     │ │      tools ──► │ │                  │
     └─────────────────┘ │  target MCP    │ └─────────────────┘
                          │  server        │
                          └───────────────┘
```

## Tech stack

| Layer                     | Choice                                                |
| ------------------------- | ----------------------------------------------------- |
| API                       | FastAPI, async SQLModel over `asyncpg`                |
| Migrations                | Alembic                                               |
| Auth                      | JWT (`PyJWT`), `pwdlib`/bcrypt password hashing       |
| Vector store              | PostgreSQL + `pgvector` (HNSW index, cosine distance) |
| Embeddings                | Gemini `gemini-embedding-001` (hosted, 384-dim)       |
| Generation                | Gemini `gemini-3.5-flash`                             |
| MCP client (validator)    | official `mcp` Python SDK                             |
| MCP server (test fixture) | `fastmcp`                                             |
| Deployment                | Docker Compose                                        |
| CI                        | GitHub Actions (lint + Docker build)                  |

## API overview

| Method   | Route            | Description                                                         |
| -------- | ---------------- | ------------------------------------------------------------------- |
| `POST`   | `/auth/register` | Create a user                                                       |
| `POST`   | `/auth/login`    | Get a JWT                                                           |
| `POST`   | `/servers`       | Publish a server (validates connectivity + embeds it)               |
| `GET`    | `/servers`       | List servers in the caller's workspaces, optional `?tag=` filter    |
| `GET`    | `/servers/{id}`  | Fetch a server                                                      |
| `PATCH`  | `/servers/{id}`  | Update a server (re-validates + re-embeds, snapshots a new version) |
| `DELETE` | `/servers/{id}`  | Delete a server (admin only)                                        |
| `POST`   | `/discover`      | Natural-language semantic search over registered servers            |

Full interactive docs at `/docs` once running.

## Running it

Copy `.env.example` to `.env` and fill in values.

### Docker (recommended)

```bash
export JWT_SECRET=change-me
export JWT_EXPIRE_MINUTES=60
export GEMINI_API_KEY=your-key-here

docker compose -f docker/docker-compose.yml up --build
```

The API comes up on `http://localhost:8000`. Migrations run automatically on container start.

### Local dev

```bash
uv sync
# Postgres with pgvector must be reachable at DATABASE_URL (see app/core/config.py)
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Design notes

- Versioning is a separate append-only `mcp_server_versions` table rather than an overwritten field, so "show me this server's history" is a real, truthful query.
- RBAC lives on the workspace membership row, not on the user, because the governance claim is per-workspace, not global.
- Connectivity validation runs synchronously on publish and update rather than on a periodic schedule. That's an MVP trade-off; a background re-validation job (Celery beat or APScheduler) hitting the same validator function is the natural next step.
- Tags are a `String[]` column rather than a normalized join table. That's fine at this scale; a join table would start to matter once tag autocomplete or cross-server tag analytics were needed.

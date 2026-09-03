from fastapi import FastAPI

from app.api.routes import auth
from app.api.routes.servers import router as servers_router
from app.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="MCP Compass", version="0.1.0")

app.include_router(servers_router)
app.include_router(auth.router)


@app.get("/health")
async def health():
    logger.info("health check returned: {'status': 'ok'}")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", reload=True)

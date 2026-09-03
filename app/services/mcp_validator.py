import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import MCPError


async def validate_mcp_server(url: str, timeout_seconds: float = 5.0) -> str:
    """Run the MCP initialize handshake + list_tools against a server URL.

    Returns "healthy", "unreachable" (transport-layer failure), or
    "invalid" (reached the server, but it didn't speak MCP correctly).
    """

    status = "healthy"

    try:
        client = httpx2.AsyncClient(timeout=timeout_seconds)
        async with streamable_http_client(url, http_client=client) as (  # noqa: SIM117
            read_stram,
            write_stream,
        ):
            async with ClientSession(
                read_stram, write_stream, read_timeout_seconds=timeout_seconds
            ) as session:
                await session.initialize()
                await session.list_tools()

    except* httpx2.ConnectError, httpx2.ConnectTimeout, httpx2.TimeoutException:
        status = "unreachable"
    except* MCPError:
        status = "invalid"

    return status

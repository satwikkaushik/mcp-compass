from fastmcp import FastMCP

mcp = FastMCP(name="ToyMCPServer")


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two integers"""
    return a + b


@mcp.tool
def reverse_text(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=9000, path="/mcp")

"""MCP (Model Context Protocol) client initialization and management."""

import os
from pathlib import Path
from typing import Any, Dict

from langchain_mcp_adapters.client import MultiServerMCPClient


def get_mcp_client() -> MultiServerMCPClient:
    """
    Initialize MCP client with all social media servers.

    Returns:
        MultiServerMCPClient: Configured client for TikTok, Twitter, and Bluesky.

    Raises:
        FileNotFoundError: If TikTok MCP build is not found.
        EnvironmentError: If required API keys are missing.
    """
    project_root = Path(__file__).parent.parent.parent
    tiktok_mcp_path = project_root / "mcp-servers" / "tiktok-mcp" / "build" / "index.js"

    # Check TikTok MCP file existence
    if not tiktok_mcp_path.exists():
        print(f"⚠️  Warning: TikTok MCP not found at {tiktok_mcp_path}")
        print(
            "   Skipping TikTok MCP server. Build it with: cd mcp-servers/tiktok-mcp && npm run build"
        )

    # Check environment variables (warn but don't fail)
    missing_vars = []
    if not os.getenv("SMITHERY_API_KEY"):
        missing_vars.append("SMITHERY_API_KEY (for Bluesky and Twitter)")
    if not os.getenv("TIKNEURON_MCP_API_KEY"):
        missing_vars.append("TIKNEURON_MCP_API_KEY (for TikTok)")

    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("   MCP tools may not work properly.")

    # Build config with only available servers
    config = {}

    # Add Bluesky if key available
    if os.getenv("SMITHERY_API_KEY"):
        config["bsky-mcp-server"] = {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@smithery/cli@latest",
                "run",
                "@brianellin/bsky-mcp-server",
                "--key",
                os.getenv("SMITHERY_API_KEY"),
                "--profile",
                "icy-dingo-7Py8Pi",
            ],
        }

    # Add TikTok if both key and file available
    if os.getenv("TIKNEURON_MCP_API_KEY") and tiktok_mcp_path.exists():
        config["tiktok-mcp"] = {
            "transport": "stdio",
            "command": "node",
            "args": [str(tiktok_mcp_path)],
            "env": {"TIKNEURON_MCP_API_KEY": os.getenv("TIKNEURON_MCP_API_KEY", "")},
        }

    # Add Twitter if key available
    if os.getenv("SMITHERY_API_KEY"):
        config["x-twitter-mcp-server"] = {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@smithery/cli@latest",
                "run",
                "@rafaljanicki/x-twitter-mcp-server",
                "--key",
                os.getenv("SMITHERY_API_KEY"),
                "--profile",
                "icy-dingo-7Py8Pi",
            ],
        }

    if not config:
        print("⚠️  Warning: No MCP servers configured. MCP tools will not be available.")
        # Return a minimal client that won't crash
        config = {}  # Empty config is okay for MultiServerMCPClient

    return MultiServerMCPClient(config)  # type: ignore[reportArgumentType]


async def get_mcp_tools(client: MultiServerMCPClient | None = None) -> list:
    """
    Get all tools from the MCP client.

    Args:
        client: Optional MCP client. If not provided, creates a new one.

    Returns:
        List of MCP tools for LangChain integration.
    """
    if os.getenv("DISABLE_MCP", "").lower() in ("true", "1", "yes"):
        print("🚫 MCP tools disabled by configuration.")
        return []

    try:
        if client is None:
            client = get_mcp_client()

        tools = await client.get_tools()
        return tools if tools else []  # Return empty list if None
    except Exception as e:
        print(f"⚠️  Warning: Failed to load MCP tools: {e}")
        return []  # Return empty list on failure


def get_mcp_config() -> Dict[str, Any]:
    """
    Get MCP configuration dictionary for inspection or debugging.

    Returns:
        Dictionary containing MCP server configurations.
    """
    project_root = Path(__file__).parent.parent.parent
    tiktok_mcp_path = project_root / "mcp-servers" / "tiktok-mcp" / "build" / "index.js"

    return {
        "bsky-mcp-server": {
            "enabled": bool(os.getenv("SMITHERY_API_KEY")),
            "description": "Bluesky social media integration",
        },
        "tiktok-mcp": {
            "enabled": bool(os.getenv("TIKNEURON_MCP_API_KEY"))
            and tiktok_mcp_path.exists(),
            "description": "TikTok social media integration",
            "path": str(tiktok_mcp_path),
        },
        "x-twitter-mcp-server": {
            "enabled": bool(os.getenv("SMITHERY_API_KEY")),
            "description": "Twitter/X social media integration",
        },
    }

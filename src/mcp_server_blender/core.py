"""Shared MCP instance and Blender socket communication."""

import json
import os
import socket
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-server-blender")

# Load config.toml
_config_path = Path(__file__).parent.parent.parent / "config.toml"
with open(_config_path, "rb") as f:
    _config = tomllib.load(f).get("blender", {})

SOCKET_HOST = _config.get("SOCKET_HOST", "127.0.0.1")
SOCKET_PORT = _config.get("SOCKET_PORT", 9876)
BLENDER_EXTERNAL = _config.get("EXTERNAL", False)

MCP_PORT = int(os.getenv("MCP_PORT", "3800"))

mcp = FastMCP("mcp-server-blender", host="0.0.0.0", port=MCP_PORT)


def send_command(command: str, params: dict, timeout: float = 60.0) -> dict:
    """Send a JSON command to the Blender addon socket server and return the result."""
    logger.info("send_command: %s params=%s", command, json.dumps(params, default=str)[:200])
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((SOCKET_HOST, SOCKET_PORT))
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        logger.error("send_command: connect failed: %s", e)
        return {"success": False, "error": f"Blender not reachable: {e}"}

    try:
        message = json.dumps({"command": command, "params": params})
        sock.sendall(message.encode("utf-8"))

        chunks = []
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                return json.loads(b"".join(chunks).decode("utf-8"))
            except json.JSONDecodeError:
                continue

        if chunks:
            return json.loads(b"".join(chunks).decode("utf-8"))
        return {"success": False, "error": "No response from Blender"}
    except socket.timeout:
        return {"success": False, "error": f"Blender command timed out after {timeout}s"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid response from Blender: {e}"}
    finally:
        sock.close()

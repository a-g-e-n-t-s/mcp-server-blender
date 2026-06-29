# ----------------------------------------------------------------------------------------------------
# server.py
# ----------------------------------------------------------------------------------------------------

"""
mcp-server-blender — Entry point and main() function.

Tools are registered in the `tools/` package.
Shared state (mcp instance, send_command, config) lives in `core.py`.
"""

# ----------------------------------------------------------------------------------------------------
from .core import mcp, SOCKET_HOST, SOCKET_PORT, BLENDER_EXTERNAL, _config, MCP_PORT
from . import tools  # noqa: F401 — registers all @mcp.tool() decorators
# ----------------------------------------------------------------------------------------------------
import os
import logging

logger = logging.getLogger("mcp-server-blender")
_manager = None

# ----------------------------------------------------------------------------------------------------
def main():
    import asyncio
    from .blender_manager import BlenderManager

    global _manager

    # EXTERNAL in config.toml (or BLENDER_EXTERNAL env override) skips headless launch
    external = BLENDER_EXTERNAL or os.getenv("BLENDER_EXTERNAL", "").lower() in ("1", "true", "yes")

    if external:
        logger.info("BLENDER_EXTERNAL set — skipping headless launch, expecting GUI Blender on port %d", SOCKET_PORT)
    else:
        _manager = BlenderManager(
            executable=_config.get("EXECUTABLE") or None,
            socket_host=SOCKET_HOST,
            socket_port=SOCKET_PORT,
            heartbeat_interval=_config.get("HEARTBEAT_INTERVAL_S", 5.0),
            restart_delay=_config.get("RESTART_DELAY_S", 3.0),
            max_restart_attempts=_config.get("MAX_RESTART_ATTEMPTS", 5),
        )

        async def _start_blender():
            ok = await _manager.start_with_monitor()
            if ok:
                logger.info("Blender manager ready — starting MCP server")
            else:
                logger.warning("Blender not available — tools will return errors until Blender connects")

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_start_blender())

    # Run as Streamable HTTP so broker can connect via http type, or stdio for local use
    transport = os.getenv("MCP_TRANSPORT_TYPE", os.getenv("MCP_TRANSPORT", "stdio"))

    if transport == "http":
        transport = "streamable-http"

    if transport == "streamable-http":
        logger.info("MCP server listening on http://0.0.0.0:%d/mcp", MCP_PORT)
    mcp.run(transport=transport)

# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()

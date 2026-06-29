"""Scripting tool — execute arbitrary Python/bpy code."""

import json
from ..core import mcp, send_command


@mcp.tool()
def blender_execute_python(code: str) -> str:
    """Execute arbitrary Python/bpy code inside the Blender process."""
    result = send_command("execute_python", {"code": code})
    return json.dumps(result)

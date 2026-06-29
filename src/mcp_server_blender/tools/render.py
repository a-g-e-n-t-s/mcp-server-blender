# ----------------------------------------------------------------------------------------------------
# render.py
# ----------------------------------------------------------------------------------------------------

"""
Render and export tools.
"""

from typing import Optional
from ..core import mcp, send_command
import json

# ----------------------------------------------------------------------------------------------------
@mcp.tool()
def blender_render(
    output_path: Optional[str] = None,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    samples: int = 128,
    engine: str = "CYCLES",
) -> str:
    """
    Render the current scene to an image file (PNG). CYCLES (CPU) is recommended for headless servers. EEVEE auto-falls back to CYCLES without GPU.
    """
    result = send_command("render", {
        "output_path": output_path, "resolution_x": resolution_x,
        "resolution_y": resolution_y, "samples": samples, "engine": engine,
    })
    return json.dumps(result)

# ----------------------------------------------------------------------------------------------------
@mcp.tool()
def blender_export(
    format: str,
    output_path: Optional[str] = None,
    selected_only: bool = False,
) -> str:
    """
    Export the scene to glTF, FBX, OBJ, or STL format.
    """
    result = send_command("export", {
        "format": format, "output_path": output_path, "selected_only": selected_only,
    })
    return json.dumps(result)

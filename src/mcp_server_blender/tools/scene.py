# ----------------------------------------------------------------------------------------------------
# scene.py
# ----------------------------------------------------------------------------------------------------

"""
Scene tools — create, modify, and inspect objects.
"""

# ----------------------------------------------------------------------------------------------------
from typing import Optional, List
from ..core import mcp, send_command
import json

# ----------------------------------------------------------------------------------------------------
@mcp.tool()
def blender_create_object(
    type: str,
    name: Optional[str] = None,
    location: List[float] = [0, 0, 0],
    scale: List[float] = [1, 1, 1],
    rotation: List[float] = [0, 0, 0],
) -> str:
    """
    Create a 3D mesh primitive (cube, sphere, cylinder, plane, cone, torus) in the Blender scene.
    """
    result = send_command("create_object", {
        "type": type, "name": name, "location": location, "scale": scale, "rotation": rotation,
    })
    return json.dumps(result)

# ----------------------------------------------------------------------------------------------------
@mcp.tool()
def blender_modify_object(
    name: str,
    location: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    modifier: Optional[str] = None,
    modifier_params: Optional[dict] = None,
) -> str:
    """
    Modify an existing object's transform or add modifiers (subdivision, solidify, mirror, bevel).
    """
    result = send_command("modify_object", {
        "name": name, "location": location, "scale": scale, "rotation": rotation,
        "modifier": modifier, "modifier_params": modifier_params,
    })
    return json.dumps(result)

# ----------------------------------------------------------------------------------------------------
@mcp.tool()
def blender_get_scene_info() -> str:
    """
    Get complete scene info: all objects with type, position, materials, cameras, and lights.
    """
    result = send_command("get_scene_info", {})
    return json.dumps(result)

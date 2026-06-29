# ----------------------------------------------------------------------------------------------------
# materials.py
# ----------------------------------------------------------------------------------------------------

"""
Material tools — create and assign PBR materials.
"""

from typing import Optional, List
from ..core import mcp, send_command
import json

# ----------------------------------------------------------------------------------------------------
@mcp.tool()
def blender_set_material(
    object_name: str,
    material_name: Optional[str] = None,
    color: List[float] = [0.8, 0.8, 0.8, 1.0],
    roughness: float = 0.5,
    metallic: float = 0.0,
) -> str:
    """
    Create or assign a PBR material with color, roughness, and metallic properties.
    """
    result = send_command("set_material", {
        "object_name": object_name, "material_name": material_name,
        "color": color, "roughness": roughness, "metallic": metallic,
    })
    return json.dumps(result)

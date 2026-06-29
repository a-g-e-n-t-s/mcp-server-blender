"""
mcp-server-blender MCP Server

Exposes headless Blender operations as MCP tools using FastMCP.
Communicates with Blender process via TCP socket (same pattern as blender-mcp).
"""

import json
import os
import socket
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from typing import Optional, List

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

# ============================================================================
# Blender Socket Communication
# ============================================================================

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

# ============================================================================
# Tools
# ============================================================================

@mcp.tool()
def blender_create_object(
    type: str,
    name: Optional[str] = None,
    location: List[float] = [0, 0, 0],
    scale: List[float] = [1, 1, 1],
    rotation: List[float] = [0, 0, 0],
) -> str:
    """Create a 3D mesh primitive (cube, sphere, cylinder, plane, cone, torus) in the Blender scene."""
    result = send_command("create_object", {
        "type": type, "name": name, "location": location, "scale": scale, "rotation": rotation,
    })
    return json.dumps(result)

@mcp.tool()
def blender_modify_object(
    name: str,
    location: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    modifier: Optional[str] = None,
    modifier_params: Optional[dict] = None,
) -> str:
    """Modify an existing object's transform or add modifiers (subdivision, solidify, mirror, bevel)."""
    result = send_command("modify_object", {
        "name": name, "location": location, "scale": scale, "rotation": rotation,
        "modifier": modifier, "modifier_params": modifier_params,
    })
    return json.dumps(result)

@mcp.tool()
def blender_set_material(
    object_name: str,
    material_name: Optional[str] = None,
    color: List[float] = [0.8, 0.8, 0.8, 1.0],
    roughness: float = 0.5,
    metallic: float = 0.0,
) -> str:
    """Create or assign a PBR material with color, roughness, and metallic properties."""
    result = send_command("set_material", {
        "object_name": object_name, "material_name": material_name,
        "color": color, "roughness": roughness, "metallic": metallic,
    })
    return json.dumps(result)

@mcp.tool()
def blender_render(
    output_path: Optional[str] = None,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    samples: int = 128,
    engine: str = "CYCLES",
) -> str:
    """Render the current scene to an image file (PNG). CYCLES (CPU) is recommended for headless servers. EEVEE auto-falls back to CYCLES without GPU."""
    result = send_command("render", {
        "output_path": output_path, "resolution_x": resolution_x,
        "resolution_y": resolution_y, "samples": samples, "engine": engine,
    })
    return json.dumps(result)

@mcp.tool()
def blender_export(
    format: str,
    output_path: Optional[str] = None,
    selected_only: bool = False,
) -> str:
    """Export the scene to glTF, FBX, OBJ, or STL format."""
    result = send_command("export", {
        "format": format, "output_path": output_path, "selected_only": selected_only,
    })
    return json.dumps(result)

@mcp.tool()
def blender_execute_python(code: str) -> str:
    """Execute arbitrary Python/bpy code inside the Blender process."""
    result = send_command("execute_python", {"code": code})
    return json.dumps(result)

@mcp.tool()
def blender_get_scene_info() -> str:
    """Get complete scene info: all objects with type, position, materials, cameras, and lights."""
    result = send_command("get_scene_info", {})
    return json.dumps(result)

# ============================================================================
# Entry point
# ============================================================================

_manager = None


@mcp.tool()
def blender_guide(topic: Optional[str] = None) -> str:
    """Get guidance on how to use mcp-server-blender tools effectively. Topics: 'overview', 'materials', 'animation', 'modifiers', 'scripting', 'workflow'."""
    guides = {
        "overview": """# mcp-server-blender Tool Guide

## Available Tools (use these first — less error-prone than raw Python):
- blender_create_object: Create primitives (cube, sphere, cylinder, plane, cone, torus)
- blender_modify_object: Move, rotate, scale, add modifiers (subdivision, solidify, mirror, bevel)
- blender_set_material: PBR materials with color, roughness, metallic
- blender_render: Render scene to PNG (CYCLES CPU recommended)
- blender_export: Export to glTF/FBX/OBJ/STL
- blender_get_scene_info: List all objects, transforms, materials
- blender_execute_python: Escape hatch for anything not covered above

## Workflow:
1. Use blender_get_scene_info to understand current state
2. Use dedicated tools for common operations
3. Fall back to blender_execute_python for complex operations
4. Always set `result = <value>` in execute_python to return data""",

        "materials": """# Materials Guide

## Simple PBR (use blender_set_material):
- color: [R, G, B, A] in 0-1 range
- roughness: 0.0 (mirror) to 1.0 (matte)
- metallic: 0.0 (dielectric) to 1.0 (metal)

## Complex materials (use blender_execute_python):
```python
import bpy
mat = bpy.data.materials.new("MyMaterial")
mat.use_nodes = True
tree = mat.node_tree
bsdf = tree.nodes["Principled BSDF"]

# Add texture
tex = tree.nodes.new("ShaderNodeTexNoise")
tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

# Assign to object
obj = bpy.data.objects["Cube"]
obj.data.materials.append(mat)
result = f"Material '{mat.name}' created and assigned"
```""",

        "animation": """# Animation Guide (use blender_execute_python)

```python
import bpy
obj = bpy.data.objects["Cube"]

# Keyframe at frame 1
obj.location = (0, 0, 0)
obj.keyframe_insert(data_path="location", frame=1)

# Keyframe at frame 60
obj.location = (5, 0, 3)
obj.keyframe_insert(data_path="location", frame=60)

# Set frame range
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 60
result = "Animation: Cube moves from origin to (5,0,3) over 60 frames"
```""",

        "modifiers": """# Modifiers Guide

## Via blender_modify_object (simple cases):
- modifier: "SUBDIVISION" with modifier_params: {"levels": 2}
- modifier: "SOLIDIFY" with modifier_params: {"thickness": 0.1}
- modifier: "BEVEL" with modifier_params: {"width": 0.05, "segments": 3}

## Via blender_execute_python (complex):
```python
import bpy
obj = bpy.data.objects["Cube"]

# Array modifier
arr = obj.modifiers.new("Array", "ARRAY")
arr.count = 5
arr.relative_offset_displace = (1.2, 0, 0)

# Boolean modifier
bool_mod = obj.modifiers.new("Boolean", "BOOLEAN")
bool_mod.operation = "DIFFERENCE"
bool_mod.object = bpy.data.objects["Sphere"]
result = "Modifiers added"
```""",

        "scripting": """# blender_execute_python Tips

## Return data: always set `result = <value>`
```python
result = len(bpy.data.objects)  # returns "5"
```

## Print also works (captured as stdout):
```python
for obj in bpy.data.objects:
    print(f"{obj.name}: {obj.type}")
# Output returned as the result string
```

## Access scene state:
```python
import bpy, json
scene = bpy.context.scene
result = json.dumps({
    "fps": scene.render.fps,
    "frame": scene.frame_current,
    "engine": scene.render.engine,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y]
})
```""",

        "workflow": """# Recommended Workflow

1. **Inspect**: blender_get_scene_info → understand what exists
2. **Build**: blender_create_object → place primitives
3. **Transform**: blender_modify_object → position, scale, modifiers
4. **Material**: blender_set_material → apply PBR look
5. **Complex**: blender_execute_python → shaders, animation, constraints
6. **Render**: blender_render → produce image
7. **Export**: blender_export → save as glTF/FBX/OBJ/STL

## Tips:
- Object names auto-increment (Cube, Cube.001, Cube.002)
- Use get_scene_info to find exact names before modifying
- Render uses CYCLES (CPU) by default — set samples low (32-64) for previews
- For GUI mode: objects appear in viewport immediately after creation"""
    }

    if topic and topic.lower() in guides:
        return guides[topic.lower()]

    if topic:
        return f"Unknown topic '{topic}'. Available: {', '.join(guides.keys())}"

    return guides["overview"]

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
                logger.info("Blender manager ready — starting MCP server (7 tools)")
            else:
                logger.warning("Blender not available — tools will return errors until Blender connects")

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_start_blender())

    # Run as Streamable HTTP so broker can connect via http type, or stdio for local use
    # Supports both MCP_TRANSPORT and MCP_TRANSPORT_TYPE env vars for compatibility
    transport = os.getenv("MCP_TRANSPORT_TYPE", os.getenv("MCP_TRANSPORT", "stdio"))

    if transport == "http":
        transport = "streamable-http"

    if transport == "streamable-http":
        logger.info("MCP server listening on http://0.0.0.0:%d/mcp", MCP_PORT)
    mcp.run(transport=transport)

if __name__ == "__main__":
    main()

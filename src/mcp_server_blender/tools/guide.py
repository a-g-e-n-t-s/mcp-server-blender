"""Guide tool — provides usage guidance to LLM callers."""

from typing import Optional
from ..core import mcp

GUIDES = {
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


@mcp.tool()
def blender_guide(topic: Optional[str] = None) -> str:
    """Get guidance on how to use mcp-server-blender tools effectively. Topics: 'overview', 'materials', 'animation', 'modifiers', 'scripting', 'workflow'."""
    if topic and topic.lower() in GUIDES:
        return GUIDES[topic.lower()]

    if topic:
        return f"Unknown topic '{topic}'. Available: {', '.join(GUIDES.keys())}"

    return GUIDES["overview"]

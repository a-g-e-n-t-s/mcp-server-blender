# Modifiers Guide

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
```

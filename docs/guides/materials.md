# Materials Guide

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
```

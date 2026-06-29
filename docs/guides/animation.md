# Animation Guide (use blender_execute_python)

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
```

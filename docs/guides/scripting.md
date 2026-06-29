# blender_execute_python Tips

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
```

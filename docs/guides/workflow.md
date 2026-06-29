# Recommended Workflow

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
- For GUI mode: objects appear in viewport immediately after creation

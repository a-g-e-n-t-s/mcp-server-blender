# ----------------------------------------------------------------------------------------------------
# test_tools_materials.py
# ----------------------------------------------------------------------------------------------------

"""
Tests for tools/materials.py — set_material.
"""

# ----------------------------------------------------------------------------------------------------
import json

import pytest


# ----------------------------------------------------------------------------------------------------
class TestSetMaterial:
    def test_params_forwarded(self, mock_send_command):
        mock_send_command.return_value = {"success": True, "material": "Gold", "object": "Cube"}

        from mcp_server_blender.tools.materials import blender_set_material
        result = json.loads(blender_set_material(
            object_name="Cube", material_name="Gold",
            color=[1.0, 0.8, 0.0, 1.0], roughness=0.3, metallic=1.0,
        ))

        mock_send_command.assert_called_once_with("set_material", {
            "object_name": "Cube", "material_name": "Gold",
            "color": [1.0, 0.8, 0.0, 1.0], "roughness": 0.3, "metallic": 1.0,
        })
        assert result["success"] is True
        assert result["material"] == "Gold"

    def test_defaults(self, mock_send_command):
        mock_send_command.return_value = {"success": True, "material": "Cube_material", "object": "Cube"}

        from mcp_server_blender.tools.materials import blender_set_material
        blender_set_material(object_name="Cube")

        mock_send_command.assert_called_once_with("set_material", {
            "object_name": "Cube", "material_name": None,
            "color": [0.8, 0.8, 0.8, 1.0], "roughness": 0.5, "metallic": 0.0,
        })

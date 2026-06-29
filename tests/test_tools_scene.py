# ----------------------------------------------------------------------------------------------------
# test_tools_scene.py
# ----------------------------------------------------------------------------------------------------

"""
Tests for tools/scene.py — create_object, modify_object, get_scene_info.
"""

# ----------------------------------------------------------------------------------------------------
import json
from unittest.mock import patch

import pytest


# ----------------------------------------------------------------------------------------------------
class TestCreateObject:
    def test_params_forwarded(self, mock_send_command):
        mock_send_command.return_value = {"success": True, "name": "Cube", "type": "cube"}

        from mcp_server_blender.tools.scene import blender_create_object
        result = json.loads(blender_create_object(
            type="cube", name="MyCube", location=[1, 2, 3], scale=[2, 2, 2], rotation=[0, 45, 0]
        ))

        mock_send_command.assert_called_once_with("create_object", {
            "type": "cube", "name": "MyCube",
            "location": [1, 2, 3], "scale": [2, 2, 2], "rotation": [0, 45, 0],
        })
        assert result["success"] is True
        assert result["name"] == "Cube"

    def test_defaults(self, mock_send_command):
        mock_send_command.return_value = {"success": True, "name": "Sphere", "type": "sphere"}

        from mcp_server_blender.tools.scene import blender_create_object
        blender_create_object(type="sphere")

        mock_send_command.assert_called_once_with("create_object", {
            "type": "sphere", "name": None,
            "location": [0, 0, 0], "scale": [1, 1, 1], "rotation": [0, 0, 0],
        })


# ----------------------------------------------------------------------------------------------------
class TestModifyObject:
    def test_params_forwarded(self, mock_send_command):
        mock_send_command.return_value = {"success": True, "name": "Cube"}

        from mcp_server_blender.tools.scene import blender_modify_object
        result = json.loads(blender_modify_object(
            name="Cube", location=[5, 0, 0], modifier="SUBDIVISION",
            modifier_params={"levels": 2}
        ))

        mock_send_command.assert_called_once_with("modify_object", {
            "name": "Cube", "location": [5, 0, 0], "scale": None, "rotation": None,
            "modifier": "SUBDIVISION", "modifier_params": {"levels": 2},
        })
        assert result["success"] is True


# ----------------------------------------------------------------------------------------------------
class TestGetSceneInfo:
    def test_returns_scene_data(self, mock_send_command):
        mock_send_command.return_value = {
            "success": True, "object_count": 2,
            "objects": [{"name": "Cube"}, {"name": "Light"}],
        }

        from mcp_server_blender.tools.scene import blender_get_scene_info
        result = json.loads(blender_get_scene_info())

        mock_send_command.assert_called_once_with("get_scene_info", {})
        assert result["object_count"] == 2

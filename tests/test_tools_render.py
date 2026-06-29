# ----------------------------------------------------------------------------------------------------
# test_tools_render.py
# ----------------------------------------------------------------------------------------------------

"""
Tests for tools/render.py — render, export.
"""

# ----------------------------------------------------------------------------------------------------
import json

import pytest


# ----------------------------------------------------------------------------------------------------
class TestRender:
    def test_params_forwarded(self, mock_send_command):
        mock_send_command.return_value = {"success": True, "output_path": "/tmp/render.png", "size_bytes": 1024}

        from mcp_server_blender.tools.render import blender_render
        result = json.loads(blender_render(
            output_path="/tmp/test.png", resolution_x=800, resolution_y=600,
            samples=32, engine="CYCLES",
        ))

        mock_send_command.assert_called_once_with("render", {
            "output_path": "/tmp/test.png", "resolution_x": 800, "resolution_y": 600,
            "samples": 32, "engine": "CYCLES",
        })
        assert result["success"] is True

    def test_defaults(self, mock_send_command):
        mock_send_command.return_value = {"success": True}

        from mcp_server_blender.tools.render import blender_render
        blender_render()

        mock_send_command.assert_called_once_with("render", {
            "output_path": None, "resolution_x": 1920, "resolution_y": 1080,
            "samples": 128, "engine": "CYCLES",
        })


# ----------------------------------------------------------------------------------------------------
class TestExport:
    def test_params_forwarded(self, mock_send_command):
        mock_send_command.return_value = {"success": True, "output_path": "/tmp/scene.glb", "format": "gltf"}

        from mcp_server_blender.tools.render import blender_export
        result = json.loads(blender_export(
            format="gltf", output_path="/tmp/scene.glb", selected_only=True,
        ))

        mock_send_command.assert_called_once_with("export", {
            "format": "gltf", "output_path": "/tmp/scene.glb", "selected_only": True,
        })
        assert result["success"] is True

    def test_defaults(self, mock_send_command):
        mock_send_command.return_value = {"success": True}

        from mcp_server_blender.tools.render import blender_export
        blender_export(format="fbx")

        mock_send_command.assert_called_once_with("export", {
            "format": "fbx", "output_path": None, "selected_only": False,
        })

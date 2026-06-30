# ----------------------------------------------------------------------------------------------------
# test_tools_scripting.py
# ----------------------------------------------------------------------------------------------------

"""
Tests for tools/scripting.py — execute_python.
"""

# ----------------------------------------------------------------------------------------------------
import json

import pytest


# ----------------------------------------------------------------------------------------------------
class TestExecutePython:
    def test_code_forwarded(self, mock_send_command):
        mock_send_command.return_value = {"success": True, "result": "42"}

        from mcp_server_blender.tools.scripting import blender_execute_python
        result = json.loads(blender_execute_python(code="result = 6 * 7"))

        mock_send_command.assert_called_once_with("execute_python", {"code": "result = 6 * 7"})
        assert result["success"] is True
        assert result["result"] == "42"

    def test_error_response(self, mock_send_command):
        mock_send_command.return_value = {"success": False, "error": "NameError: x not defined"}

        from mcp_server_blender.tools.scripting import blender_execute_python
        result = json.loads(blender_execute_python(code="print(x)"))

        assert result["success"] is False
        assert "NameError" in result["error"]

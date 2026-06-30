# ----------------------------------------------------------------------------------------------------
# test_core.py
# ----------------------------------------------------------------------------------------------------

"""
Tests for core.py — config loading and send_command socket communication.
"""

# ----------------------------------------------------------------------------------------------------
import json
import socket
import threading
from unittest.mock import patch

import pytest

from mcp_server_blender.core import send_command


# ----------------------------------------------------------------------------------------------------
class TestSendCommand:
    def test_success(self, mock_socket_server):
        host, port, set_response = mock_socket_server
        set_response({"success": True, "name": "Cube"})

        with patch("mcp_server_blender.core.SOCKET_HOST", host), \
             patch("mcp_server_blender.core.SOCKET_PORT", port):
            result = send_command("create_object", {"type": "cube"})

        assert result["success"] is True
        assert result["name"] == "Cube"

    def test_connection_refused(self):
        with patch("mcp_server_blender.core.SOCKET_HOST", "127.0.0.1"), \
             patch("mcp_server_blender.core.SOCKET_PORT", 19999):
            result = send_command("heartbeat", {}, timeout=2.0)

        assert result["success"] is False
        assert "not reachable" in result["error"] or "timed out" in result["error"]

    def test_timeout(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("127.0.0.1", 0))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        def slow_handler():
            client, _ = server_sock.accept()
            import time
            time.sleep(5)
            client.close()

        thread = threading.Thread(target=slow_handler, daemon=True)
        thread.start()

        with patch("mcp_server_blender.core.SOCKET_HOST", "127.0.0.1"), \
             patch("mcp_server_blender.core.SOCKET_PORT", port):
            result = send_command("heartbeat", {}, timeout=0.5)

        assert result["success"] is False
        assert "timed out" in result["error"]

        server_sock.close()
        thread.join(timeout=1)

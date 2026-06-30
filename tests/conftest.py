# ----------------------------------------------------------------------------------------------------
# conftest.py
# ----------------------------------------------------------------------------------------------------

"""
Shared test fixtures for mcp-server-blender.
"""

# ----------------------------------------------------------------------------------------------------
import json
import socket
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ----------------------------------------------------------------------------------------------------
@pytest.fixture
def tmp_config(tmp_path):
    """
    Write a temporary config.toml and patch core to use it.
    """
    config_content = b"""
[blender]
EXECUTABLE = "blender"
EXTERNAL = true
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 19876
HEARTBEAT_INTERVAL_S = 2
RESTART_DELAY_S = 1
MAX_RESTART_ATTEMPTS = 3
"""
    config_file = tmp_path / "config.toml"
    config_file.write_bytes(config_content)
    return config_file


# ----------------------------------------------------------------------------------------------------
@pytest.fixture
def mock_send_command():
    """
    Patch send_command at all import sites.
    """
    with patch("mcp_server_blender.core.send_command") as mock_core, \
         patch("mcp_server_blender.tools.scene.send_command") as mock_scene, \
         patch("mcp_server_blender.tools.materials.send_command") as mock_mat, \
         patch("mcp_server_blender.tools.render.send_command") as mock_render, \
         patch("mcp_server_blender.tools.scripting.send_command") as mock_script:
        mock = MagicMock()
        mock_core.side_effect = lambda *a, **k: mock(*a, **k)
        mock_scene.side_effect = lambda *a, **k: mock(*a, **k)
        mock_mat.side_effect = lambda *a, **k: mock(*a, **k)
        mock_render.side_effect = lambda *a, **k: mock(*a, **k)
        mock_script.side_effect = lambda *a, **k: mock(*a, **k)
        mock.return_value = {"success": True}
        yield mock


# ----------------------------------------------------------------------------------------------------
@pytest.fixture
def mock_socket_server():
    """
    Start a local TCP server that responds with a JSON payload, then shuts down.
    Returns (host, port, set_response) where set_response(dict) controls what the server sends back.
    """
    response_data = {"success": True, "test": "response"}

    def set_response(data):
        nonlocal response_data
        response_data = data

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    def handler():
        try:
            client, _ = server_sock.accept()
            data = client.recv(8192)
            response_bytes = json.dumps(response_data).encode("utf-8")
            client.sendall(response_bytes)
            client.close()
        except OSError:
            pass

    thread = threading.Thread(target=handler, daemon=True)
    thread.start()

    yield "127.0.0.1", port, set_response

    server_sock.close()
    thread.join(timeout=2)


# ----------------------------------------------------------------------------------------------------
@pytest.fixture
def mock_blender_process():
    """
    Mock subprocess.Popen for BlenderManager tests.
    """
    mock_proc = MagicMock()
    mock_proc.pid = 12345
    mock_proc.poll.return_value = None
    mock_proc.returncode = 0

    with patch("mcp_server_blender.blender_manager.subprocess.Popen", return_value=mock_proc) as mock_popen:
        yield mock_popen, mock_proc

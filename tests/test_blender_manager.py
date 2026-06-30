# ----------------------------------------------------------------------------------------------------
# test_blender_manager.py
# ----------------------------------------------------------------------------------------------------

"""
Tests for blender_manager.py — executable discovery, launch/stop, heartbeat.
"""

# ----------------------------------------------------------------------------------------------------
import json
import socket
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_blender.blender_manager import BlenderManager, _find_blender_executable


# ----------------------------------------------------------------------------------------------------
class TestFindBlenderExecutable:
    def test_env_var(self, tmp_path):
        exe = tmp_path / "blender"
        exe.write_text("")
        with patch.dict("os.environ", {"BLENDER_EXECUTABLE": str(exe)}):
            assert _find_blender_executable() == str(exe)

    def test_on_path(self):
        with patch.dict("os.environ", {"BLENDER_EXECUTABLE": ""}, clear=False), \
             patch("shutil.which", return_value="/usr/bin/blender"):
            assert _find_blender_executable() == "blender"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only test")
    def test_windows_program_files(self, tmp_path):
        bf_dir = tmp_path / "Blender Foundation" / "Blender 4.2"
        bf_dir.mkdir(parents=True)
        exe = bf_dir / "blender.exe"
        exe.write_text("")

        with patch.dict("os.environ", {"BLENDER_EXECUTABLE": "", "PROGRAMFILES": str(tmp_path)}), \
             patch("shutil.which", return_value=None):
            result = _find_blender_executable()
            assert result == str(exe)

    def test_fallback(self):
        with patch.dict("os.environ", {"BLENDER_EXECUTABLE": ""}, clear=False), \
             patch("shutil.which", return_value=None), \
             patch("sys.platform", "linux"):
            assert _find_blender_executable() == "blender"


# ----------------------------------------------------------------------------------------------------
class TestBlenderManager:
    def test_launch_success(self, mock_blender_process):
        mock_popen, mock_proc = mock_blender_process
        mgr = BlenderManager(executable="blender")
        result = mgr.launch()

        assert result is True
        assert mgr.is_running
        mock_popen.assert_called_once()

    def test_launch_not_found(self):
        with patch("mcp_server_blender.blender_manager.subprocess.Popen", side_effect=FileNotFoundError):
            mgr = BlenderManager(executable="/nonexistent/blender")
            result = mgr.launch()

        assert result is False

    def test_stop(self, mock_blender_process):
        mock_popen, mock_proc = mock_blender_process
        mgr = BlenderManager(executable="blender")
        mgr.launch()
        mgr.stop()

        mock_proc.terminate.assert_called_once()
        assert mgr._process is None

    def test_heartbeat_alive(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("127.0.0.1", 0))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        def handler():
            client, _ = server_sock.accept()
            client.recv(4096)
            client.sendall(json.dumps({"success": True}).encode())
            client.close()

        thread = threading.Thread(target=handler, daemon=True)
        thread.start()

        mgr = BlenderManager(executable="blender", socket_port=port)
        assert mgr.heartbeat(timeout=2.0) is True

        server_sock.close()
        thread.join(timeout=1)

    def test_heartbeat_dead(self):
        mgr = BlenderManager(executable="blender", socket_port=19998)
        assert mgr.heartbeat(timeout=0.5) is False

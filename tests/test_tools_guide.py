# ----------------------------------------------------------------------------------------------------
# test_tools_guide.py
# ----------------------------------------------------------------------------------------------------

"""
Tests for tools/guide.py — topic lookup from markdown files.
"""

# ----------------------------------------------------------------------------------------------------
import pytest

from mcp_server_blender.tools.guide import blender_guide, _GUIDES_DIR, _TOPICS


# ----------------------------------------------------------------------------------------------------
class TestGuide:
    def test_overview_default(self):
        result = blender_guide()
        assert "mcp-server-blender Tool Guide" in result
        assert "blender_create_object" in result

    def test_known_topic(self):
        result = blender_guide(topic="materials")
        assert "Materials Guide" in result
        assert "blender_set_material" in result

    def test_all_topics_loadable(self):
        for topic in _TOPICS:
            result = blender_guide(topic=topic)
            assert len(result) > 50, f"Topic '{topic}' returned too little content"

    def test_unknown_topic(self):
        result = blender_guide(topic="nonexistent")
        assert "Unknown topic" in result
        assert "overview" in result

    def test_case_insensitive(self):
        result = blender_guide(topic="MATERIALS")
        assert "Materials Guide" in result

    def test_none_topic(self):
        result = blender_guide(topic=None)
        assert "mcp-server-blender Tool Guide" in result

    def test_guides_dir_exists(self):
        assert _GUIDES_DIR.exists(), f"Guides directory not found: {_GUIDES_DIR}"

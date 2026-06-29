# ----------------------------------------------------------------------------------------------------
# guide.py
# ----------------------------------------------------------------------------------------------------

"""
Guide tool — provides usage guidance to LLM callers by reading markdown files.
"""

# ----------------------------------------------------------------------------------------------------
from pathlib import Path
from typing import Optional
from ..core import mcp

_GUIDES_DIR = Path(__file__).parent.parent.parent.parent / "docs" / "guides"
_TOPICS = ["overview", "materials", "animation", "modifiers", "scripting", "workflow"]

# ----------------------------------------------------------------------------------------------------
def _load_guide(topic: str) -> str:
    path = _GUIDES_DIR / f"{topic}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"Guide file not found: {path}"

# ----------------------------------------------------------------------------------------------------
@mcp.tool()
def blender_guide(topic: Optional[str] = None) -> str:
    """
    Get guidance on how to use mcp-server-blender tools effectively. Topics: 'overview', 'materials', 'animation', 'modifiers', 'scripting', 'workflow'.
    """
    if topic and topic.lower() in _TOPICS:
        return _load_guide(topic.lower())

    if topic:
        return f"Unknown topic '{topic}'. Available: {', '.join(_TOPICS)}"

    return _load_guide("overview")

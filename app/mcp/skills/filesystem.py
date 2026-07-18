"""
Filesystem skill.

Read-only access to a sandboxed root directory, used by agents that need
to inspect uploaded source files (for example, before ingestion). Path
traversal outside the sandbox root is rejected.
"""

from __future__ import annotations

from pathlib import Path

from app.mcp.skills.base import Skill


class FilesystemSkill(Skill):
    name = "filesystem"
    description = "Read files from a sandboxed directory."

    def __init__(self, sandbox_root: str) -> None:
        self._root = Path(sandbox_root).resolve()

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self._root / relative_path).resolve()
        if self._root not in candidate.parents and candidate != self._root:
            raise PermissionError("Path escapes sandbox root")
        return candidate

    async def run(self, action: str, path: str) -> dict:
        target = self._resolve(path)
        if action == "read":
            return {"path": str(target), "content": target.read_text(encoding="utf-8", errors="ignore")}
        if action == "list":
            return {"path": str(target), "entries": [p.name for p in target.iterdir()]}
        raise ValueError(f"Unsupported action: {action}")

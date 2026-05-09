"""
File ingestion and .breadcrumbignore support.
Walks repository, respects ignore patterns, and filters code files.
"""

from pathlib import Path
from typing import List, Optional

import pathspec

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    "vendor",
    "target",
    ".cargo",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    "bundle.js",
    ".DS_Store",
}

CODE_EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".go",
    ".rs",
    ".rb",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".cs",
    ".php",
    ".swift",
    ".kt",
    ".sql",
    ".graphql",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".md",
    ".html",
    ".css",
    ".scss",
    ".vue",
    ".svelte",
    ".sh",
    ".bash",
    ".tf",
    ".dockerfile",
    ".makefile",
    ".env.example",
    ".lock",
    ".xml",
    ".gradle",
}


class FileIngester:
    """Walks repository respecting .breadcrumbignore rules."""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.spec = self._load_ignore_patterns()

    def _load_ignore_patterns(self) -> Optional[pathspec.PathSpec]:
        """Load .breadcrumbignore patterns if it exists."""
        ignore_file = self.repo_path / ".breadcrumbignore"
        if ignore_file.exists():
            patterns = ignore_file.read_text().strip().split("\n")
            patterns = [p.strip() for p in patterns if p.strip() and not p.startswith("#")]
            if patterns:
                return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return None

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        # Skip by directory name (check all parents)
        for part in path.parts:
            if part in SKIP_DIRS:
                return True

        # Skip by .breadcrumbignore
        if self.spec:
            rel_path = path.relative_to(self.repo_path)
            if self.spec.match_file(str(rel_path)):
                return True

        return False

    def _is_code_file(self, path: Path) -> bool:
        """Check if file is a code file we care about."""
        return path.suffix.lower() in CODE_EXTS or path.name.lower().endswith(
            ("dockerfile", "makefile")
        )

    def get_files(self) -> List[Path]:
        """Get all code files respecting ignore patterns."""
        files = []

        try:
            for path in self.repo_path.rglob("*"):
                if path.is_dir():
                    if self._should_skip(path):
                        # Skip entire directory
                        continue
                elif path.is_file():
                    if not self._should_skip(path) and self._is_code_file(path):
                        files.append(path)
        except PermissionError:
            pass

        return sorted(files)

    def get_content(self, max_file_size: int = 50000, max_total: int = 180000) -> str:
        """
        Get concatenated file contents with size limits.
        Large files get truncated; if total exceeds max_total, files are skipped.
        """
        files = self.get_files()
        content_parts = []
        total_size = 0

        for file_path in files:
            try:
                file_content = file_path.read_text(errors="ignore")

                # Truncate large files
                if len(file_content) > max_file_size:
                    file_content = file_content[:max_file_size] + "\n... [truncated]"

                # Check if adding this file exceeds total
                if total_size + len(file_content) > max_total:
                    # Indicate truncation happened
                    content_parts.append(
                        "\n... [context limit reached, "
                        f"{len(files) - len(content_parts)} files skipped]"
                    )
                    break

                rel_path = file_path.relative_to(self.repo_path)
                content_parts.append(f"# {rel_path}\n{file_content}\n")
                total_size += len(file_content)
            except Exception:
                pass

        return "\n".join(content_parts)

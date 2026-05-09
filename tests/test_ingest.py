"""
Test file ingestion and .breadcrumbignore support.
"""

import tempfile
from pathlib import Path

from breadcrumb.ingest import FileIngester


def test_ingest_finds_code_files():
    """Test that FileIngester finds code files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create some code files
        (repo / "main.py").write_text("print('hello')")
        (repo / "lib.ts").write_text("export const x = 1;")
        (repo / "README.md").write_text("# Project")

        ingester = FileIngester(repo)
        files = ingester.get_files()

        assert len(files) >= 3
        assert any(f.name == "main.py" for f in files)
        assert any(f.name == "lib.ts" for f in files)


def test_ingest_respects_breadcrumbignore():
    """Test that .breadcrumbignore patterns are respected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create files
        (repo / "main.py").write_text("code")
        (repo / "dist" / "bundle.js").parent.mkdir(parents=True)
        (repo / "dist" / "bundle.js").write_text("bundled")

        # Create .breadcrumbignore
        (repo / ".breadcrumbignore").write_text("dist/\n*.min.js")

        ingester = FileIngester(repo)
        files = ingester.get_files()

        # dist/ should be ignored
        assert not any("bundle.js" in str(f) for f in files)


def test_ingest_skips_common_directories():
    """Test that common unneeded directories are skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create directories
        (repo / "src" / "code.py").parent.mkdir(parents=True)
        (repo / "src" / "code.py").write_text("code")

        (repo / "node_modules" / "package.json").parent.mkdir(parents=True)
        (repo / "node_modules" / "package.json").write_text("{}")

        ingester = FileIngester(repo)
        files = ingester.get_files()

        # node_modules should be skipped
        assert not any("node_modules" in str(f) for f in files)
        # src code should be included
        assert any("code.py" in str(f) for f in files)


def test_ingest_respects_file_size_limit():
    """Test that large files are truncated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create a large file
        large_content = "x" * 100000
        (repo / "large.py").write_text(large_content)

        ingester = FileIngester(repo)
        content = ingester.get_content(max_file_size=1000)

        # Should be truncated
        assert "[truncated]" in content or len(content) < len(large_content)

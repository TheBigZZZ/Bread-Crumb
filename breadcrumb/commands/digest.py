"""
Generate a daily digest of changes from git commits.
"""

import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown

from breadcrumb.ai.prompts import get_system_prompt
from breadcrumb.ai.router import AIRouter

console = Console()


def get_commits_since(repo_path: Path, hours: int = 24) -> str:
    """Get git log for the past N hours."""
    try:
        since = datetime.now() - timedelta(hours=hours)
        since_str = since.strftime("%Y-%m-%d %H:%M:%S")

        result = subprocess.run(
            ["git", "log", f"--since={since_str}", "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except Exception as e:
        console.print(f"[red]Error getting commits: {e}[/red]")
        return ""


def cmd_digest(
    repo_path: Path,
    hours: int = 24,
    provider: Optional[str] = None,
) -> str:
    """
    Generate a digest of recent commits.

    Args:
        repo_path: Repository path
        hours: How many hours back to look
        provider: AI provider (overrides config)

    Returns:
        The digest
    """
    commits = get_commits_since(repo_path, hours)

    if not commits:
        console.print("[yellow]No commits in the past 24 hours[/yellow]")
        return ""

    router = AIRouter(provider)
    system = get_system_prompt("digest")

    prompt = f"""Summarize these commits into a concise digest.
What changed? What was fixed? Notable improvements?

Commits:
{commits}"""

    messages = [{"role": "user", "content": prompt}]

    try:
        response_text = ""
        with console.status("[bold cyan]Generating digest...", spinner="dots"):
            for chunk in router.stream(messages, system):
                response_text += chunk

        console.print(Markdown(response_text))
        return response_text
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return ""

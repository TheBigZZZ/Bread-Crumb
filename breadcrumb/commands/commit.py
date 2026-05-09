"""
Generate conventional commit messages from staged changes.
"""

import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console

from breadcrumb.ai.prompts import get_system_prompt
from breadcrumb.ai.router import AIRouter

console = Console()


def get_git_diff_staged(repo_path: Path) -> str:
    """Get staged changes via git diff --staged."""
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except Exception as e:
        console.print(f"[red]Error running git diff: {e}[/red]")
        return ""


def cmd_commit(
    repo_path: Path,
    provider: Optional[str] = None,
    silent: bool = False,
) -> str:
    """
    Generate a conventional commit message from staged changes.

    Args:
        repo_path: Repository path
        provider: AI provider (overrides config)
        silent: If True, only print the message (no other output)

    Returns:
        The generated commit message
    """
    # Get staged diff
    diff = get_git_diff_staged(repo_path)

    if not diff:
        if not silent:
            console.print("[yellow]No staged changes[/yellow]")
        return ""

    # Setup AI
    router = AIRouter(provider)
    system = get_system_prompt("commit")

    prompt = f"""Analyze these staged changes and generate a conventional commit message.

{diff}

Generate ONLY the commit message in conventional format (type(scope): description).
No explanation, no markdown, just the message."""

    messages = [{"role": "user", "content": prompt}]

    try:
        if not silent:
            with console.status("[bold cyan]Generating commit message...", spinner="dots"):
                message = router.chat(messages, system)
        else:
            message = router.chat(messages, system)

        message = message.strip()

        if not silent:
            console.print(f"\n[green]Suggested commit:[/green]\n{message}")
        else:
            print(message)

        return message
    except Exception as e:
        if not silent:
            console.print(f"[red]Error: {e}[/red]")
        return ""

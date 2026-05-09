"""
Review git diffs with AI.
"""

import subprocess
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from breadcrumb.ai.router import AIRouter
from breadcrumb.ai.prompts import get_system_prompt

console = Console()


def get_git_diff(repo_path: Path, revision: str = "") -> str:
    """Get git diff for a revision."""
    try:
        if revision:
            result = subprocess.run(
                ["git", "diff", revision],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                ["git", "diff"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
        return result.stdout
    except Exception as e:
        console.print(f"[red]Error running git diff: {e}[/red]")
        return ""


def cmd_diff(
    repo_path: Path,
    revision: str = "",
    provider: Optional[str] = None,
) -> str:
    """
    Review a git diff with AI.
    
    Args:
        repo_path: Repository path
        revision: Git revision (e.g., 'HEAD~1', 'main..feature/auth')
        provider: AI provider (overrides config)
    
    Returns:
        The review
    """
    diff = get_git_diff(repo_path, revision)
    
    if not diff:
        console.print("[yellow]No changes found for the specified revision[/yellow]")
        return ""

    # Limit diff size
    if len(diff) > 50000:
        diff = diff[:50000] + "\n... [diff truncated]"

    router = AIRouter(provider)
    system = get_system_prompt("diff")
    
    prompt = f"""Review this git diff and provide:
1. Summary of changes
2. Any potential issues or bugs
3. Suggestions for improvement
4. Impact assessment

{diff}"""

    messages = [{"role": "user", "content": prompt}]

    try:
        response_text = ""
        with console.status("[bold cyan]Reviewing diff...", spinner="dots"):
            for chunk in router.stream(messages, system):
                response_text += chunk
        
        console.print(Markdown(response_text))
        return response_text
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return ""

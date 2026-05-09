"""
Security and architecture audit command.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown

from breadcrumb.ai.prompts import get_system_prompt
from breadcrumb.ai.router import AIRouter
from breadcrumb.ingest import FileIngester

console = Console()


def cmd_audit(
    repo_path: Path,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    format: str = "text",
) -> str:
    """
    Run a security and architecture audit on the repository.

    Args:
        repo_path: Repository path
        provider: AI provider (overrides config)
        model: Model name (overrides config)
        format: Output format ('text' or 'markdown')

    Returns:
        The audit report
    """
    # Get repository context
    try:
        ingester = FileIngester(repo_path)
        context = ingester.get_content()

        if not context:
            console.print("[yellow]Warning: No code files found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error reading repository: {e}[/red]")
        context = ""

    # Setup AI
    router = AIRouter(provider)
    if model:
        router.model = model

    system = get_system_prompt("audit")
    prompt = f"""Analyze this codebase for security, architecture, and quality issues.

{context}"""

    messages = [{"role": "user", "content": prompt}]

    try:
        response_text = ""
        with console.status("[bold cyan]Auditing codebase...", spinner="dots"):
            for chunk in router.stream(messages, system):
                response_text += chunk

        if format == "markdown":
            console.print(Markdown(response_text))
        else:
            console.print(response_text)

        # Show token usage
        total_tokens = router.count_tokens(context) + router.count_tokens(response_text)
        console.print(f"\n[dim]~{total_tokens:,} tokens used[/dim]")

        return response_text
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return ""

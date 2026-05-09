"""
One-shot non-interactive query command.
Ask a question and get an answer in one go.
"""

import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from breadcrumb.ingest import FileIngester
from breadcrumb.ai.router import AIRouter
from breadcrumb.ai.prompts import get_system_prompt
from breadcrumb.config import Config

console = Console()


def cmd_ask(
    repo_path: Path,
    question: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    format: str = "text",
    pipe: bool = False,
) -> str:
    """
    Ask a one-shot question about the repository.
    
    Args:
        repo_path: Repository path
        question: The question to ask
        provider: AI provider (overrides config)
        model: Model name (overrides config)
        format: Output format ('text' or 'markdown')
        pipe: If True, read question from stdin if not provided
    
    Returns:
        The AI response
    """
    if not question and pipe:
        question = sys.stdin.read()
    
    if not question:
        console.print("[red]Error: No question provided[/red]")
        return ""

    # Get repository context
    try:
        ingester = FileIngester(repo_path)
        context = ingester.get_content()
        
        if not context:
            console.print("[yellow]Warning: No code files found in repository[/yellow]")
    except Exception as e:
        console.print(f"[red]Error reading repository: {e}[/red]")
        context = ""

    # Setup AI
    router = AIRouter(provider)
    if model:
        router.model = model

    # Build prompt
    system = get_system_prompt("ask")
    prompt = f"""Repo context:
{context}

Question: {question}"""

    messages = [{"role": "user", "content": prompt}]

    # Show spinner and stream response
    response_text = ""
    try:
        with console.status("[bold cyan]Thinking...", spinner="dots"):
            for chunk in router.stream(messages, system):
                response_text += chunk
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return ""

    # Output based on format
    if format == "markdown":
        console.print(Markdown(response_text))
    else:
        console.print(response_text)

    # Show token usage
    total_tokens = router.count_tokens(context) + router.count_tokens(question) + router.count_tokens(response_text)
    console.print(f"\n[dim]~{total_tokens:,} tokens used[/dim]")

    return response_text

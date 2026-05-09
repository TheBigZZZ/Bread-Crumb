"""
Explain errors and stack traces.
"""

import sys
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown

from breadcrumb.ai.prompts import get_system_prompt
from breadcrumb.ai.router import AIRouter

console = Console()


def cmd_explain_error(
    error_text: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    """
    Explain an error or stack trace.

    Args:
        error_text: Error text (reads from stdin if not provided)
        provider: AI provider (overrides config)

    Returns:
        The explanation
    """
    if not error_text:
        error_text = sys.stdin.read()

    if not error_text:
        console.print("[red]Error: No error text provided[/red]")
        return ""

    error_text = error_text.strip()

    router = AIRouter(provider)
    system = get_system_prompt("explain-error")

    prompt = f"""Analyze this error and provide:
1. Plain English explanation
2. Root cause
3. How to fix it

Error:
{error_text}"""

    messages = [{"role": "user", "content": prompt}]

    try:
        response_text = ""
        with console.status("[bold cyan]Analyzing error...", spinner="dots"):
            for chunk in router.stream(messages, system):
                response_text += chunk

        console.print(Markdown(response_text))
        return response_text
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return ""

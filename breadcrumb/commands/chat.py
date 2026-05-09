"""
Interactive chat with the codebase using a TUI.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

from breadcrumb.ai.prompts import get_system_prompt
from breadcrumb.ai.router import AIRouter
from breadcrumb.history import SessionManager
from breadcrumb.ingest import FileIngester

console = Console()


def cmd_chat(
    repo_path: Path,
    provider: Optional[str] = None,
    session_name: str = "default",
) -> None:
    """
    Interactive chat session with the codebase.

    Args:
        repo_path: Repository path
        provider: AI provider (overrides config)
        session_name: Name of the chat session
    """
    # Initialize
    ingester = FileIngester(repo_path)
    router = AIRouter(provider)
    session = SessionManager(repo_path, session_name)

    try:
        context = ingester.get_content()
    except Exception as e:
        console.print(f"[red]Error reading repository: {e}[/red]")
        context = ""

    console.print(
        Panel.fit(
            "[bold cyan]🍞 Bread Crumb[/bold cyan]\n"
            f"[dim]Chat with your codebase using {router.provider}[/dim]",
            border_style="cyan",
        )
    )
    console.print(
        f"[dim]Session: {session_name} | Provider: {router.provider} | Model: {router.model}[/dim]"
    )
    console.print("[dim]Type 'exit' to quit, 'clear' to clear history[/dim]")
    console.print(Rule())

    # Chat loop
    while True:
        try:
            question = Prompt.ask("[cyan]You")
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not question.strip():
            continue

        if question.lower() == "exit":
            console.print("[dim]Goodbye![/dim]")
            break

        if question.lower() == "clear":
            session.clear()
            console.print("[yellow]History cleared[/yellow]")
            continue

        if question.lower() == "sessions":
            sessions = SessionManager.list_sessions(repo_path)
            if sessions:
                console.print("[cyan]Available sessions:[/cyan]")
                for s in sessions:
                    console.print(f"  • {s}")
            else:
                console.print("[dim]No other sessions[/dim]")
            continue

        # Add user message to history
        session.add_message("user", question)

        # Build messages for API
        system = get_system_prompt("chat")

        # Include context only in first message of session
        if len(session.messages) <= 1:
            api_messages = [
                {"role": "user", "content": f"Repo context:\n{context}\n\nQuestion: {question}"}
            ]
        else:
            api_messages = session.get_messages_for_api()

        # Stream response
        try:
            response_text = ""
            console.print("[cyan]Assistant[/cyan]", end=" ")
            for chunk in router.stream(api_messages, system):
                console.print(chunk, end="", highlight=False)
                response_text += chunk
            console.print()  # Newline after response
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            continue

        # Add assistant response to history
        session.add_message("assistant", response_text)

        # Show stats
        tokens = session.count_tokens()
        console.print(f"[dim]~{tokens:,} tokens in session[/dim]")
        console.print(Rule())

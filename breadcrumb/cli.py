"""
Main CLI entry point using Click.
Wires all commands together.
"""

import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from breadcrumb import __version__
from breadcrumb.commands.ask import cmd_ask
from breadcrumb.commands.audit import cmd_audit
from breadcrumb.commands.chat import cmd_chat
from breadcrumb.commands.commit import cmd_commit
from breadcrumb.commands.diff import cmd_diff
from breadcrumb.commands.explain_error import cmd_explain_error
from breadcrumb.commands.init import cmd_init
from breadcrumb.config import Config

console = Console()


def show_startup_screen() -> None:
    """Show a rich landing screen when the CLI is started without a command."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🍞 Bread Crumb[/bold cyan]\n"
            "[dim]Chat with your codebase from the terminal.[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    table = Table(box=box.SIMPLE, show_header=False, expand=False, padding=(0, 1))
    table.add_row("[cyan]ask[/cyan]", "Ask a one-shot question about the codebase")
    table.add_row("[cyan]audit[/cyan]", "Run a security and architecture audit")
    table.add_row("[cyan]chat[/cyan]", "Interactive chat with your codebase")
    table.add_row("[cyan]diff[/cyan]", "Review a git diff with AI")
    table.add_row("[cyan]commit[/cyan]", "Generate a conventional commit message")
    table.add_row("[cyan]config[/cyan]", "Manage global configuration")
    table.add_row("[cyan]init[/cyan]", "Initialize .breadcrumb.yaml in the repository")
    console.print(table)
    console.print(
        "[dim]Run [cyan]breadcrumb --help[/cyan] for all options or [cyan]breadcrumb chat .[/cyan] to start chatting.[/dim]"
    )


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """🍞 Bread Crumb — Chat with your codebase."""
    # If no command, show help
    if ctx.invoked_subcommand is None:
        show_startup_screen()


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
@click.option("--provider", help="AI provider (anthropic, openai, gemini, ollama)")
@click.option("--session", default="default", help="Session name")
def chat(repo_path, provider, session):
    """Interactive chat with your codebase."""
    cmd_chat(Path(repo_path), provider, session)


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
@click.argument("question", required=False)
@click.option("--provider", help="AI provider")
@click.option("--model", help="Model name")
@click.option("--format", type=click.Choice(["text", "markdown"]), default="text")
@click.option("--pipe", is_flag=True, help="Read question from stdin")
def ask(repo_path, question, provider, model, format, pipe):
    """Ask a one-shot question about the codebase."""
    cmd_ask(Path(repo_path), question or "", provider, model, format, pipe)


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
@click.option("--provider", help="AI provider")
@click.option("--model", help="Model name")
@click.option("--format", type=click.Choice(["text", "markdown"]), default="text")
def audit(repo_path, provider, model, format):
    """Run a security and architecture audit."""
    cmd_audit(Path(repo_path), provider, model, format)


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
@click.argument("revision", required=False, default="")
@click.option("--provider", help="AI provider")
def diff(repo_path, revision, provider):
    """Review a git diff with AI."""
    cmd_diff(Path(repo_path), revision, provider)


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
@click.option("--provider", help="AI provider")
@click.option("--silent", is_flag=True, help="Only output the message")
def commit(repo_path, provider, silent):
    """Generate a conventional commit message."""
    cmd_commit(Path(repo_path), provider, silent)


@cli.command()
@click.option("--provider", help="AI provider")
@click.argument("error", required=False)
def explain_error(provider, error):
    """Explain an error or stack trace."""
    cmd_explain_error(error, provider)


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
def init(repo_path):
    """Initialize .breadcrumb.yaml in the repository."""
    cmd_init(Path(repo_path))


@cli.group()
def config():
    """Manage global configuration."""
    pass


@config.command()
@click.argument("key")
@click.argument("value")
def set_key(key, value):
    """Set a configuration value."""
    cfg = Config()
    cfg.set(key, value)
    click.echo(f"✓ Set {key} = {value}")


@config.command()
@click.argument("key")
def get_key(key):
    """Get a configuration value."""
    cfg = Config()
    value = cfg.get(key)
    click.echo(value)


@config.command()
def show():
    """Show all configuration."""
    cfg = Config()
    for key, value in sorted(cfg.to_dict().items()):
        if "key" in key.lower() and value:
            value = "***" + value[-4:]  # Hide API keys
        click.echo(f"{key}: {value}")


def main():
    """Entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted by user[/dim]")
        sys.exit(0)
    except FileNotFoundError as e:
        console.print(f"[red]✗ Error:[/red] Repository or file not found: {e}")
        console.print("[dim]Make sure the path exists and you have read permissions.[/dim]")
        sys.exit(1)
    except PermissionError as e:
        console.print(f"[red]✗ Error:[/red] Permission denied: {e}")
        console.print("[dim]Make sure you have read permissions for the repository.[/dim]")
        sys.exit(1)
    except ValueError as e:
        # Common error: API key not configured
        if "api_key" in str(e).lower() or "key" in str(e).lower():
            console.print("[red]✗ Error:[/red] API key not configured")
            console.print()
            console.print("[yellow]Setup your AI provider:[/yellow]")
            console.print("  breadcrumb config set-key provider anthropic")
            console.print("  breadcrumb config set-key anthropic_key sk-ant-...")
            console.print()
            console.print("[dim]Supported providers: anthropic, openai, gemini, ollama[/dim]")
        else:
            console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        console.print(f"[red]✗ Error:[/red] {error_msg}")
        if "Connection" in str(type(e).__name__) or "Network" in str(type(e).__name__):
            console.print("[dim]Network error. Check your internet connection and API key.[/dim]")
        elif "401" in error_msg or "Unauthorized" in error_msg:
            console.print("[dim]Invalid API key or authentication failed.[/dim]")
            console.print("[yellow]Run: breadcrumb config show[/yellow] to check your settings")
        elif "404" in error_msg:
            console.print("[dim]Resource not found. Check the repository path or API endpoint.[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()

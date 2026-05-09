"""
Main CLI entry point using Click.
Wires all commands together.
"""

import sys
from pathlib import Path

import click

from breadcrumb import __version__
from breadcrumb.commands.ask import cmd_ask
from breadcrumb.commands.audit import cmd_audit
from breadcrumb.commands.chat import cmd_chat
from breadcrumb.commands.commit import cmd_commit
from breadcrumb.commands.diff import cmd_diff
from breadcrumb.commands.explain_error import cmd_explain_error
from breadcrumb.commands.init import cmd_init
from breadcrumb.config import Config


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """🍞 Bread Crumb — Chat with your codebase."""
    # If no command, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


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
        click.echo("\n")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

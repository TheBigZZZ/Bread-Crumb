"""
Initialize a .breadcrumb.yaml config file for a repository.
"""

from pathlib import Path

from rich.console import Console

console = Console()

BREADCRUMB_YAML_TEMPLATE = """# Bread Crumb Configuration
# Place this file in your repository root to customize Bread Crumb behavior

# AI Provider: anthropic, openai, gemini, or ollama
provider: anthropic

# Model name for the chosen provider
model: claude-3-5-sonnet-20241022

# Patterns to ignore (like .gitignore)
# These files won't be included in context
ignore_patterns:
  - "*.min.js"
  - "*.min.css"
  - "dist/"
  - "build/"
  - "node_modules/"

# Custom system prompt for this repository
# Gets prepended to all conversations
system_prompt: |
  You are analyzing a [PROJECT_TYPE] project.
  Key technologies: [TECH_STACK]
  Important context: [ANY_SPECIAL_RULES]

# Temperature for AI responses (0.0 - 1.0)
temperature: 0.7

# Maximum tokens per request
max_tokens: 4096
"""


def cmd_init(repo_path: Path) -> bool:
    """
    Initialize a .breadcrumb.yaml config file in the repository.

    Args:
        repo_path: Repository path

    Returns:
        True if successful
    """
    config_file = repo_path / ".breadcrumb.yaml"

    if config_file.exists():
        console.print("[yellow].breadcrumb.yaml already exists[/yellow]")
        return False

    try:
        config_file.write_text(BREADCRUMB_YAML_TEMPLATE)
        console.print(f"[green]✓ Created {config_file}[/green]")
        console.print("[dim]Edit it to customize Bread Crumb for your project[/dim]")
        return True
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False

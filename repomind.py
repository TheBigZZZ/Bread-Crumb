#!/usr/bin/env python3
"""
Bread Crumb — Chat with your codebase.
Install:  pip install rich
Run:      python breadcrumb.py [repo_path]
"""

# ruff: noqa: E501

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from breadcrumb.ai.prompts import get_system_prompt
from breadcrumb.ai.router import AIRouter
from breadcrumb.config import Config

console = Console()

# ── Constants ──────────────────────────────────────────────────────────────────
APP_DIR = Path.home() / ".breadcrumb"
CONFIG_FILE = APP_DIR / "config.json"
HISTORY_DIR = APP_DIR / "history"
MAX_FILE_SIZE = 50_000
MAX_TOTAL = 180_000
HISTORY_LIMIT = 20

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    "vendor",
    "target",
    ".cargo",
    ".mypy_cache",
    ".pytest_cache",
}

CODE_EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".go",
    ".rs",
    ".rb",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".cs",
    ".php",
    ".swift",
    ".kt",
    ".sql",
    ".graphql",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".md",
    ".html",
    ".css",
    ".scss",
    ".vue",
    ".svelte",
    ".sh",
    ".bash",
    ".tf",
    "Dockerfile",
    "Makefile",
    ".env.example",
}


# ── Config ─────────────────────────────────────────────────────────────────────
def load_config():
    return Config()


def save_config(cfg):
    cfg.save()


# ── History ────────────────────────────────────────────────────────────────────
def history_path(root):
    uid = hashlib.md5(str(root).encode()).hexdigest()[:10]
    return HISTORY_DIR / f"{root.name}_{uid}.json"


def load_history(root):
    p = history_path(root)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_history(root, history):
    history_path(root).write_text(json.dumps(history, indent=2))


def trim_history(history):
    return history[-HISTORY_LIMIT:] if len(history) > HISTORY_LIMIT else history


# ── Ingestion ──────────────────────────────────────────────────────────────────
def should_include(path):
    return path.suffix in CODE_EXTS or path.name in CODE_EXTS


def ingest_repo(root, focus=None):
    parts, total, files = [], 0, []
    scan_root = (root / focus) if focus and (root / focus).exists() else root
    all_files = sorted(
        p
        for p in scan_root.rglob("*")
        if p.is_file() and not any(s in p.parts for s in SKIP_DIRS) and should_include(p)
    )
    for path in all_files:
        try:
            content = path.read_text(errors="replace")
        except OSError:
            continue
        if len(content) > MAX_FILE_SIZE:
            content = content[:MAX_FILE_SIZE] + "\n...[truncated]"
        rel = path.relative_to(root)
        chunk = f"\n\n### FILE: {rel}\n```\n{content}\n```"
        if total + len(chunk) > MAX_TOTAL:
            parts.append(f"\n\n[{len(all_files) - len(files)} files omitted — context limit]")
            break
        parts.append(chunk)
        total += len(chunk)
        files.append(path)
    return "".join(parts), files


# ── Animations ─────────────────────────────────────────────────────────────────
def animate_banner():
    lines = [
        (
            " ██████╗ ██████╗ ███████╗ █████╗ ██████╗      ██████╗██████╗ ██╗   ██╗"
            "███╗   ███╗██████╗ ",
            "bold cyan",
        ),
        (
            "██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗    ██╔════╝██╔══██╗██║   ██║"
            "████╗ ████║██╔══██╗",
            "bold cyan",
        ),
        (
            "██████╔╝██████╔╝█████╗  ███████║██║  ██║    ██║     ██████╔╝██║   ██║"
            "██╔████╔██║██████╔╝",
            "cyan",
        ),
        (
            "██╔══██╗██╔══██╗██╔══╝  ██╔══██║██║  ██║    ██║     ██╔══██╗██║   ██║"
            "██║╚██╔╝██║██╔══██╗",
            "cyan",
        ),
        (
            "██████╔╝██║  ██║███████╗██║  ██║██████╔╝    ╚██████╗██║  ██║╚██████╔╝"
            "██║ ╚═╝ ██║██████╔╝",
            "dim cyan",
        ),
        (
            "╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝      ╚═════╝╚═╝  ╚═╝ ╚═════╝ "
            "╚═╝     ╚═╝╚═════╝ ",
            "dim cyan",
        ),
    ]
    for line, style in lines:
        console.print(f"[{style}]{line}[/{style}]")
        time.sleep(0.07)
    console.print()


def animate_scanning(files):
    with Live(console=console, refresh_per_second=20) as live:
        for f in files[:25]:
            live.update(Text(f"  → {f.name}", style="dim cyan"))
            time.sleep(0.025)
        live.update(Text(f"  ✓ Indexed {len(files)} files", style="green"))
        time.sleep(0.3)


def thinking_animation(label="Thinking"):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    with Live(console=console, refresh_per_second=12) as live:
        for i in range(28):
            live.update(Text(f"  {frames[i % len(frames)]}  {label}...", style="dim cyan"))
            time.sleep(0.075)


def mock_stream(text, delay=0.009):
    for char in text:
        yield char
        time.sleep(delay if char not in ("\n", " ") else delay * 0.15)


def stream_to_console(response):
    rendered = ""
    with Live(console=console, refresh_per_second=30) as live:
        for char in mock_stream(response):
            rendered += char
            live.update(Markdown(rendered))
    console.print()


def build_system_prompt(user_input):
    inp = user_input.lower()
    if any(w in inp for w in ("audit", "security", "vulnerabilit", "secure")):
        return get_system_prompt("audit")
    if any(w in inp for w in ("commit", "git commit", "conventional commit")):
        return get_system_prompt("commit")
    if any(w in inp for w in ("diff", "review changes", "code review")):
        return get_system_prompt("diff")
    if any(
        w in inp
        for w in ("explain", "what does", "what is", "how does", "tell me about", "walk me through")
    ):
        return get_system_prompt("ask")
    return get_system_prompt("chat")


def get_ai_response(user_input, codebase, files, repo_name, cfg):
    file_list = "\n".join(f"- `{f.name}`" for f in files[:12])
    prompt = f"""Repository: `{repo_name}`

Files indexed: {len(files)}

Important files:
{file_list}

Repository context:
{codebase}

User request:
{user_input}

Answer directly using the repository context above. Do not invent details that are not supported by the codebase. If the context is insufficient, say exactly what is missing."""

    provider = cfg.get("provider", "anthropic")
    router = AIRouter(provider)
    router.model = cfg.get_model(provider)
    messages = [{"role": "user", "content": prompt}]

    response_text = ""
    for chunk in router.stream(messages, build_system_prompt(user_input)):
        response_text += chunk
    return response_text


# ── Export ─────────────────────────────────────────────────────────────────────
def export_chat(history, repo_name):
    if not history:
        console.print("[dim]No chat history to export.[/dim]")
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"breadcrumb_export_{repo_name}_{ts}.md"
    lines = [
        f"# Bread Crumb Export — `{repo_name}`\n",
        f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n---\n",
    ]
    for msg in history:
        role = "**You**" if msg["role"] == "user" else "**Bread Crumb**"
        lines.append(f"\n### {role}\n{msg['content']}\n")
    Path(filename).write_text("\n".join(lines))
    console.print(f"[green]✓[/green] Exported to [cyan]{filename}[/cyan]")


# ── File views ─────────────────────────────────────────────────────────────────
def print_file_tree(files, root):
    tree = Tree(f"[bold cyan]{root.name}/[/bold cyan]")
    dirs = {"": tree}
    for f in files[:60]:
        parts, pk = f.relative_to(root).parts, ""
        for part in parts[:-1]:
            k = pk + "/" + part if pk else part
            if k not in dirs:
                dirs[k] = dirs[pk].add(f"[cyan]{part}/[/cyan]")
            pk = k
        dirs[pk].add(f"[white]{parts[-1]}[/white]")
    console.print(tree)
    if len(files) > 60:
        console.print(f"[dim]  ... and {len(files) - 60} more[/dim]")


def print_file_table(files, root):
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", padding=(0, 1))
    t.add_column("File", style="white")
    t.add_column("Type", style="dim")
    t.add_column("Size", justify="right", style="dim")
    for f in sorted(files, key=lambda x: -x.stat().st_size)[:40]:
        sz = f.stat().st_size
        t.add_row(
            str(f.relative_to(root)),
            f.suffix or f.name,
            f"{sz:,} B" if sz < 1024 else f"{sz // 1024} KB",
        )
    if len(files) > 40:
        t.add_row(f"[dim]... and {len(files) - 40} more[/dim]", "", "")
    console.print(t)


# ── API key setup ──────────────────────────────────────────────────────────────
def setup_api_key(cfg):
    console.print()
    console.print(
        Panel(
            "[bold]AI Provider Setup[/bold]\n\n"
            "Choose a provider and store its credentials locally.\n\n"
            "[dim]Configuration is stored in ~/.breadcrumb/config.json[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )

    provider = (
        Prompt.ask(
            "[cyan]Provider[/cyan]",
            choices=["anthropic", "openai", "gemini", "ollama"],
            default=cfg.get("provider", "anthropic"),
        )
        .strip()
        .lower()
    )
    cfg.set("provider", provider)

    if provider == "ollama":
        url = Prompt.ask(
            "[cyan]Ollama URL[/cyan]",
            default=cfg.get("ollama_url", "http://localhost:11434"),
        ).strip()
        if url:
            cfg.set("ollama_url", url)
        console.print("[green]✓ Ollama settings saved.[/green]\n")
    else:
        key = Prompt.ask(
            f"\n[cyan]{provider.title()} API key[/cyan] [dim](Enter to skip)[/dim]",
            default="",
        ).strip()
        if key:
            cfg.set_api_key(provider, key)
            console.print("[green]✓ API key saved.[/green]\n")
        else:
            console.print("[dim]No API key saved.[/dim]\n")
    return cfg


# ── Help ───────────────────────────────────────────────────────────────────────
HELP_TEXT = """\
[bold white]Analysis[/bold white]
  [cyan]audit[/cyan]                   Full security + architecture audit
  [cyan]onboard[/cyan]                 New developer onboarding guide
  [cyan]risks[/cyan]                   Top architectural risks
  [cyan]git[/cyan]                     Git history insights
  [cyan]explain <thing>[/cyan]         Explain any file, function, or concept

[bold white]Promptify — paste-ready prompts for your AI agent[/bold white]
  [cyan]promptify security[/cyan]      Fix all security vulnerabilities
  [cyan]promptify tests[/cyan]         Generate full test suite
  [cyan]promptify refactor[/cyan]      Clean and refactor the codebase
  [cyan]promptify docs[/cyan]          Generate all documentation
  [cyan]promptify performance[/cyan]   Fix performance issues

[bold white]Utility[/bold white]
  [cyan]files[/cyan]                   File list (table view)
  [cyan]tree[/cyan]                    File tree view
  [cyan]focus <folder>[/cyan]          Narrow context to one module
  [cyan]focus[/cyan]                   Clear focus, back to full repo
  [cyan]refresh[/cyan]                 Re-index the repo
  [cyan]export[/cyan]                  Save chat to markdown file
  [cyan]history[/cyan]                 Show recent chat history
    [cyan]set-key[/cyan]                 Configure your AI provider credentials
  [cyan]clear[/cyan]                   Clear chat history
  [cyan]help[/cyan]                    Show this help
  [cyan]exit[/cyan]                    Quit

[dim]Or just ask anything in plain English about your codebase.[/dim]"""

QUICK = {
    "audit": "perform a full security and architecture audit",
    "onboard": "give me a new developer onboarding guide for this codebase",
    "risks": "what are the top architectural risks and most dangerous files to change",
    "git": "give me git history insights",
    "promptify security": "promptify security",
    "promptify tests": "promptify tests",
    "promptify refactor": "promptify refactor",
    "promptify docs": "promptify docs",
    "promptify performance": "promptify performance",
}


# ── Main ───────────────────────────────────────────────────────────────────────
def run(repo_path, cfg):
    root = Path(repo_path).resolve()
    if not root.exists():
        console.print(f"[red]Error:[/red] '{repo_path}' does not exist.")
        sys.exit(1)

    animate_banner()
    console.print(Rule(style="dim cyan"))

    history = load_history(root)
    focus = None

    def do_ingest():
        with console.status("[cyan]Reading codebase...[/cyan]", spinner="dots"):
            c, f = ingest_repo(root, focus)
        animate_scanning(f)
        return c, f

    _codebase, files = do_ingest()
    repo_name = root.name

    langs = {}
    for f in files:
        k = f.suffix or f.name
        langs[k] = langs.get(k, 0) + 1
    top = "  ".join(
        f"[cyan]{e}[/cyan] [dim]{n}[/dim]"
        for e, n in sorted(langs.items(), key=lambda x: -x[1])[:6]
    )
    mode = (
        f"[green]{cfg.get('provider', 'anthropic')}[/green]"
        f" [dim]{cfg.get_model(cfg.get('provider', 'anthropic'))}[/dim]"
    )

    console.print(
        Panel(
            f"[bold]Repo:[/bold]    {root}\n"
            f"[bold]Files:[/bold]   {len(files)} indexed\n"
            f"[bold]Lang:[/bold]    {top}\n"
            f"[bold]Mode:[/bold]    {mode}\n"
            f"[bold]History:[/bold] {len(history)} messages loaded",
            title="[bold cyan]🍞 Bread Crumb[/bold cyan]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()
    console.print(Panel(HELP_TEXT, border_style="dim", padding=(0, 2)))
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]you[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            save_history(root, history)
            console.print("\n[dim]History saved. Goodbye 🍞[/dim]")
            break

        if not user_input:
            continue
        cmd = user_input.lower().strip()

        if cmd in ("exit", "quit", "q"):
            save_history(root, history)
            console.print("[dim]History saved. Goodbye 🍞[/dim]")
            break

        if cmd == "help":
            console.print(Panel(HELP_TEXT, border_style="dim", padding=(0, 2)))
            continue

        if cmd == "clear":
            history.clear()
            save_history(root, history)
            console.print("[dim]Chat history cleared.[/dim]\n")
            continue

        if cmd == "files":
            print_file_table(files, root)
            continue

        if cmd == "tree":
            print_file_tree(files, root)
            continue

        if cmd == "export":
            export_chat(history, repo_name)
            continue

        if cmd == "history":
            if not history:
                console.print("[dim]No history yet.[/dim]\n")
            else:
                for msg in history[-8:]:
                    role = (
                        "[bold cyan]you[/bold cyan]"
                        if msg["role"] == "user"
                        else "[bold dim]bread crumb[/bold dim]"
                    )
                    short = msg["content"][:100].replace("\n", " ")
                    console.print(f"  {role}: [dim]{short}…[/dim]")
                console.print()
            continue

        if cmd == "refresh":
            codebase, files = do_ingest()
            console.print(f"[green]✓[/green] Re-indexed [bold]{len(files)}[/bold] files.\n")
            continue

        if cmd == "set-key":
            cfg = setup_api_key(cfg)
            continue

        if cmd.startswith("focus "):
            focus = cmd[6:].strip()
            codebase, files = do_ingest()
            console.print(
                f"[green]✓[/green] Focused on [cyan]{focus}[/cyan] — {len(files)} files.\n"
            )
            continue

        if cmd == "focus":
            focus = None
            codebase, files = do_ingest()
            console.print(f"[green]✓[/green] Focus cleared — {len(files)} files.\n")
            continue

        if cmd in QUICK:
            user_input = QUICK[cmd]

        history.append({"role": "user", "content": user_input})
        history = trim_history(history)

        console.print("\n[bold dim]🍞 bread crumb[/bold dim]")
        thinking_animation()
        try:
            response = get_ai_response(user_input, codebase, files, repo_name, cfg)
        except Exception as e:
            console.print(f"[red]AI error:[/red] {e}")
            continue
        stream_to_console(response)

        history.append({"role": "assistant", "content": response})
        history = trim_history(history)
        save_history(root, history)


def main():
    parser = argparse.ArgumentParser(description="🍞 Bread Crumb — chat with your codebase")
    parser.add_argument("repo", nargs="?", default=".", help="path to repository")
    parser.add_argument("--setup", action="store_true", help="configure API key")
    args = parser.parse_args()
    cfg = load_config()
    if args.setup or (
        cfg.get("provider", "anthropic") != "ollama"
        and not cfg.get_api_key(cfg.get("provider", "anthropic"))
    ):
        cfg = setup_api_key(cfg)
    run(args.repo, cfg)


if __name__ == "__main__":
    main()

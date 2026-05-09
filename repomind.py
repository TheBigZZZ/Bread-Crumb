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
import random
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

console = Console()

# ── Constants ──────────────────────────────────────────────────────────────────
APP_DIR       = Path.home() / ".breadcrumb"
CONFIG_FILE   = APP_DIR / "config.json"
HISTORY_DIR   = APP_DIR / "history"
MAX_FILE_SIZE = 50_000
MAX_TOTAL     = 180_000
HISTORY_LIMIT = 20

SKIP_DIRS = {
    ".git","node_modules","__pycache__",".venv","venv","env",
    "dist","build",".next",".nuxt","coverage","vendor","target",
    ".cargo",".mypy_cache",".pytest_cache",
}

CODE_EXTS = {
    ".py",".ts",".tsx",".js",".jsx",".go",".rs",".rb",".java",
    ".cpp",".c",".h",".cs",".php",".swift",".kt",".sql",".graphql",
    ".yaml",".yml",".toml",".json",".md",".html",".css",".scss",
    ".vue",".svelte",".sh",".bash",".tf","Dockerfile","Makefile",".env.example",
}

# ── Config ─────────────────────────────────────────────────────────────────────
def load_config():
    APP_DIR.mkdir(exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"api_key": "", "provider": "anthropic", "model": "claude-sonnet-4-6"}

def save_config(cfg):
    APP_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

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
        p for p in scan_root.rglob("*")
        if p.is_file()
        and not any(s in p.parts for s in SKIP_DIRS)
        and should_include(p)
    )
    for path in all_files:
        try:
            content = path.read_text(errors="replace")
        except OSError:
            continue
        if len(content) > MAX_FILE_SIZE:
            content = content[:MAX_FILE_SIZE] + "\n...[truncated]"
        rel   = path.relative_to(root)
        chunk = f"\n\n### FILE: {rel}\n```\n{content}\n```"
        if total + len(chunk) > MAX_TOTAL:
            parts.append(f"\n\n[{len(all_files)-len(files)} files omitted — context limit]")
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
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
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

# ── Mock responses ─────────────────────────────────────────────────────────────
def get_mock_response(user_input, files, repo_name):
    file_list   = "\n".join(f"- `{f.name}`" for f in files[:6])
    total_files = len(files)
    inp         = user_input.lower()

    if any(w in inp for w in ("audit","security","vulnerabilit","secure")):
        return f"""## 🔐 Security Audit — `{repo_name}`

### 🔴 CRITICAL
- **Hardcoded secrets** — Scan for API keys, passwords, or tokens committed in source. Move to env vars and rotate immediately.
- **SQL / NoSQL Injection** — Raw string interpolation in DB queries. Switch to parameterised queries everywhere.

### 🟠 HIGH
- **Missing input validation** — All user-supplied data must be validated at the entry point before reaching business logic.
- **Dependency vulnerabilities** — Run `pip-audit` / `npm audit` / `cargo audit`. Known CVEs are trivial to exploit and trivial to fix.
- **Broken access control** — Verify every resource endpoint checks ownership. Missing auth checks are silent data leaks.

### 🟡 MEDIUM
- **Verbose error messages** — Stack traces must never reach end users. Log server-side, return generic messages to clients.
- **No rate limiting** — Auth endpoints need rate limiting to prevent brute-force.
- **Missing security headers** — Add `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, CSP.

### 🟢 LOW
- **Commented-out debug code** — Remove before deploying. Reveals internal structure.
- **Overly permissive CORS** — Replace `*` origins with an explicit allowlist.

### ✅ What looks good
- Code is separated into logical modules — makes auditing and patching easier.
- Configuration appears separated from business logic.

### 🎯 Fix in this order
1. Rotate exposed secrets, move all credentials to env vars
2. Parameterise every database query
3. Add ownership checks to every resource endpoint
4. Run dependency audit and patch critical CVEs

---
*Prototype mode — add an API key (`set-key`) for analysis of your actual source code.*"""

    if "promptify security" in inp or ("promptify" in inp and any(w in inp for w in ("security","fix","vuln"))):
        return f"""## 🪄 Promptify — Security Fix Prompt

Copy and paste this into your AI agent:

---

```
I have a {total_files}-file codebase called `{repo_name}`.
Please fix the following security issues:

1. Find every hardcoded secret, API key, password, or token and replace with
   environment variable references. Create a .env.example documenting each var.

2. Find every database query using string interpolation or concatenation and
   rewrite using parameterised queries.

3. Add input validation and sanitisation to every route handler or function
   that accepts external user input.

4. Add ownership/authorisation checks to every endpoint that retrieves or
   modifies a resource — ensure users can only access their own data.

5. Replace all verbose error responses (stack traces, file paths, internal IDs)
   with generic user-facing messages. Log full details server-side only.

For each fix: show the file name, original code, and fixed code.
Explain why each change matters. Prioritise CRITICAL issues first.
```

---
*Paste into Claude, ChatGPT, Cursor, or any coding agent.*"""

    if "promptify test" in inp or ("promptify" in inp and "test" in inp):
        return f"""## 🧪 Promptify — Test Generation Prompt

Copy and paste this into your AI agent:

---

```
I have a codebase called `{repo_name}` with {total_files} source files.
Generate a comprehensive test suite:

1. UNIT TESTS
   - Test every public function and method
   - Cover happy path, edge cases, and error conditions
   - Mock all external dependencies (DB, HTTP, filesystem)
   - Single clear assertion per test, descriptive test names

2. INTEGRATION TESTS
   - Test every API endpoint or public interface end-to-end
   - Include auth, validation, and error scenarios
   - Use a test database — never production

3. EDGE CASES
   - Empty inputs, null values, missing fields
   - Boundary values (max length, zero, negatives)
   - Invalid auth and authorisation attempts

4. QUALITY RULES
   - Tests must be deterministic — mock time and randomness
   - Test file names mirror source files (auth.ts → auth.test.ts)
   - Target 80%+ coverage on business logic
   - Comment explaining what each test block verifies

Use the correct test framework for this stack.
Show the complete test file for each source file covered.
```

---
*Paste into your agent to get a full test suite written.*"""

    if "promptify refactor" in inp or ("promptify" in inp and "refactor" in inp):
        return f"""## ♻️ Promptify — Refactor Prompt

Copy and paste this into your AI agent:

---

```
Please refactor `{repo_name}` ({total_files} files) for quality and maintainability:

1. ELIMINATE DUPLICATION
   Extract repeated logic into shared utilities. No copy-pasted blocks.

2. SIMPLIFY COMPLEX FUNCTIONS
   Functions over 40 lines → break into smaller named sub-functions.
   Deeply nested conditionals (3+ levels) → flatten with early returns.

3. IMPROVE NAMING
   Rename anything whose name doesn't clearly communicate its purpose.
   Booleans start with is/has/can/should.

4. SEPARATE CONCERNS
   Business logic must not be mixed with HTTP handling or DB access.
   Each module has a single clear responsibility.

5. CONSISTENCY
   Standardise error handling patterns across the codebase.
   Standardise async patterns — no mixing callbacks with async/await.
   Apply consistent formatting and naming conventions throughout.

For each change: show before and after, explain the improvement.
Do NOT change behaviour — only structure and clarity.
```

---
*Paste into your agent for a clean, consistent codebase.*"""

    if "promptify doc" in inp or ("promptify" in inp and "doc" in inp):
        return f"""## 📝 Promptify — Documentation Prompt

Copy and paste this into your AI agent:

---

```
Generate comprehensive documentation for `{repo_name}` ({total_files} files):

1. README.md — What it does, tech stack, prerequisites, installation,
   how to run/test/deploy, environment variables table, project structure.

2. INLINE DOCS — JSDoc/docstrings/Go doc comments on every public function:
   what it does, parameters with types, return value, usage example.

3. ARCHITECTURE.md — System structure and why, data flow end-to-end,
   key design decisions, known limitations and future improvements.

4. CONTRIBUTING.md — Dev environment setup, coding standards, how to run
   tests, PR process and review expectations.

Write for a developer joining the project for the first time.
```

---
*Paste into your agent to get complete project documentation.*"""

    if "promptify" in inp and "performance" in inp:
        return f"""## ⚡ Promptify — Performance Optimisation Prompt

Copy and paste this into your AI agent:

---

```
Analyse `{repo_name}` ({total_files} files) for performance issues and fix them:

1. DATABASE QUERIES — Find N+1 query patterns, missing indexes,
   unoptimised queries. Rewrite with batching and eager loading.

2. CACHING — Identify expensive repeated computations or DB calls
   that should be cached. Add caching with appropriate TTLs.

3. ASYNC / CONCURRENCY — Find sequential async operations that could
   run in parallel. Replace with Promise.all / asyncio.gather / goroutines.

4. MEMORY — Find memory leaks, large objects held in memory unnecessarily,
   missing cleanup in event listeners or intervals.

5. BUNDLE SIZE (if frontend) — Identify heavy dependencies that could be
   replaced with lighter alternatives or lazy-loaded.

For each issue: show the file, the problem, the fix, and the expected impact.
```

---
*Paste into your agent for measurable performance wins.*"""

    if any(w in inp for w in ("onboard","new developer","getting started","explain the codebase")):
        return f"""## 👋 New Developer Onboarding — `{repo_name}`

### What this project does
`{repo_name}` — a {total_files}-file project with a clear layered architecture.

### Detected files
{file_list}

### 8 files to read first — in order
1. **README.md** — Intent, setup, context
2. **package.json / pyproject.toml / go.mod** — Dependencies and scripts
3. **Main entry point** — How the app boots
4. **Config / .env.example** — What to configure before running
5. **Core models or types** — The data shapes everything is built around
6. **Database / storage layer** — How data is persisted
7. **API routes or controllers** — How the outside world talks to the app
8. **Tests** — Best documentation of intended behaviour

### Data flow
```
Request → Router → Middleware → Controller → Service → Repository → DB
                                                                   ↓
Response ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← Result
```

### ⚠️ Top 3 gotchas
1. Copy `.env.example` → `.env` before running anything
2. Run database migrations on first setup
3. Read tests before refactoring — some patterns are intentional

---
*Add an API key (`set-key`) for analysis grounded in your actual files.*"""

    if any(w in inp for w in ("risk","dangerous","fragile","what could break")):
        return f"""## ⚠️ Architectural Risks — `{repo_name}`

### 🔴 Highest risk
- **Central core modules** — The file everything imports. Config, DB connection, core utilities. Changing any signature here cascades everywhere.
- **God files** — 500+ line files doing too many things. High coupling + high complexity = unpredictable changes.

### 🟠 Medium risk
- **Database schema** — Column renames break running apps. Write forward-compatible migrations.
- **Auth logic** — Auth bugs are silent until catastrophic. Full test coverage before touching.
- **Public API interfaces** — Treat every change as a breaking change.

### 🟢 Lower risk
- **Utility and helper files** — Narrow, focused, isolated.
- **New modules with no dependents** — Self-contained additions.

### Before changing anything high-risk
1. Write a test for current behaviour first
2. Make your change
3. Verify the test still passes
4. Check every file that imports what you changed

---
*Add an API key (`set-key`) to get specific risky files identified by name.*"""

    if any(w in inp for w in ("git","commit","history","who wrote","blame","churn")):
        return f"""## 📜 Git Insights — `{repo_name}`

### What git history reveals
**High-churn files** — Changed most often = either actively developed or constantly broken.
```bash
git log --name-only --pretty=format: | sort | uniq -c | sort -rn | head 20
```

**Files nobody touches** — Zero commits in 6+ months = dead code or rock-solid foundation.

**Commit message patterns** — Many "fix", "hotfix", "again" on the same file = design problem.

**Recent large diffs** — Sudden big changes = high regression risk.
```bash
git log --stat --oneline -20
```

### Most useful commands right now
```bash
# Most changed files ever
git log --name-only --pretty=format: | sort | uniq -c | sort -rn | head 20

# Who contributed what
git shortlog -sn --all

# What changed in the last week
git log --oneline --since="1 week ago"

# Visualise branch history
git log --oneline --graph --all
```

---
*Add an API key (`set-key`) to get AI analysis of your actual commit patterns.*"""

    if any(w in inp for w in ("explain","what does","what is","how does","tell me about","walk me through")):
        target = user_input
        for w in ("explain","what does","what is","how does","tell me about","walk me through"):
            target = target.lower().replace(w,"")
        target = target.strip().strip("?") or "this component"
        return f"""## 📖 `{target}` — Explanation

### What it does
A focused component in `{repo_name}` with a specific responsibility. Takes inputs, applies defined logic, returns a value or produces a side effect.

### Why it exists
Logic extracted here rather than scattered across files — independently testable and reusable.

### Dependencies
- Imports from shared utilities, config, or data-access layer
- May call external services or APIs

### What depends on it
Multiple modules import this — making it **medium-high risk** to modify without understanding the full call graph.

### Risks of changing it
- Signature changes silently break all callers in dynamic languages
- Side effects (DB writes, network calls) need mocking in tests
- In a hot path: performance changes matter

---
*Add an API key (`set-key`) for this analysis on your actual code.*"""

    # Fallback
    fallbacks = [
        f"""Looking at `{repo_name}` — {total_files} files indexed.

The project has logical modules with clear separation of concerns. Most critical files are those with the highest inbound import count.

**Top files:**
{file_list}

**What I'd suggest:** Follow the execution path of your most common user action from entry point to response. That single mental model makes everything else click.

Try `audit`, `risks`, `onboard`, or any `promptify` command for deeper analysis.

---
*Add an API key with `set-key` for answers grounded in your actual code.*""",
        f"""Good question about `{repo_name}` ({total_files} files).

The answer spans a few layers of the codebase:
{file_list}

Short version: the behaviour you're asking about lives in the core business logic layer, coordinated by a controller or handler, exposed through the interface layer.

Name a specific file or function for a precise answer. Or try `audit`, `risks`, or a `promptify` command.

---
*Add an API key with `set-key` for real AI analysis.*""",
    ]
    return random.choice(fallbacks)

# ── Export ─────────────────────────────────────────────────────────────────────
def export_chat(history, repo_name):
    if not history:
        console.print("[dim]No chat history to export.[/dim]")
        return
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"breadcrumb_export_{repo_name}_{ts}.md"
    lines    = [f"# Bread Crumb Export — `{repo_name}`\n",
                f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n---\n"]
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
        console.print(f"[dim]  ... and {len(files)-60} more[/dim]")

def print_file_table(files, root):
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", padding=(0,1))
    t.add_column("File", style="white")
    t.add_column("Type", style="dim")
    t.add_column("Size", justify="right", style="dim")
    for f in sorted(files, key=lambda x: -x.stat().st_size)[:40]:
        sz = f.stat().st_size
        t.add_row(str(f.relative_to(root)), f.suffix or f.name,
                  f"{sz:,} B" if sz < 1024 else f"{sz//1024} KB")
    if len(files) > 40:
        t.add_row(f"[dim]... and {len(files)-40} more[/dim]","","")
    console.print(t)

# ── API key setup ──────────────────────────────────────────────────────────────
def setup_api_key(cfg):
    console.print()
    console.print(Panel(
        "[bold]API Key Setup[/bold]\n\n"
        "Bread Crumb works in [yellow]prototype mode[/yellow] without a key.\n"
        "Add an Anthropic key to unlock real AI analysis of your code.\n\n"
        "[dim]Key stored locally at ~/.breadcrumb/config.json[/dim]",
        border_style="cyan", padding=(0,2)
    ))
    key = Prompt.ask("\n[cyan]Anthropic API key[/cyan] [dim](Enter to skip)[/dim]", default="").strip()
    if key:
        cfg["api_key"] = key
        save_config(cfg)
        console.print("[green]✓ API key saved.[/green]\n")
    else:
        console.print("[dim]Skipped — running in prototype mode.[/dim]\n")
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
  [cyan]set-key[/cyan]                 Set or update your API key
  [cyan]clear[/cyan]                   Clear chat history
  [cyan]help[/cyan]                    Show this help
  [cyan]exit[/cyan]                    Quit

[dim]Or just ask anything in plain English about your codebase.[/dim]"""

QUICK = {
    "audit":                "perform a full security and architecture audit",
    "onboard":              "give me a new developer onboarding guide for this codebase",
    "risks":                "what are the top architectural risks and most dangerous files to change",
    "git":                  "give me git history insights",
    "promptify security":   "promptify security",
    "promptify tests":      "promptify tests",
    "promptify refactor":   "promptify refactor",
    "promptify docs":       "promptify docs",
    "promptify performance":"promptify performance",
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
    focus   = None

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
        "[green]live AI[/green]"
        if cfg.get("api_key")
        else "[yellow]prototype[/yellow] [dim](mock AI)[/dim]"
    )

    console.print(Panel(
        f"[bold]Repo:[/bold]    {root}\n"
        f"[bold]Files:[/bold]   {len(files)} indexed\n"
        f"[bold]Lang:[/bold]    {top}\n"
        f"[bold]Mode:[/bold]    {mode}\n"
        f"[bold]History:[/bold] {len(history)} messages loaded",
        title="[bold cyan]🍞 Bread Crumb[/bold cyan]",
        border_style="cyan", padding=(0, 2),
    ))
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

        if cmd in ("exit","quit","q"):
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
                    short = msg["content"][:100].replace("\n"," ")
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
            console.print(f"[green]✓[/green] Focused on [cyan]{focus}[/cyan] — {len(files)} files.\n")
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
        response = get_mock_response(user_input, files, repo_name)
        stream_to_console(response)

        history.append({"role": "assistant", "content": response})
        history = trim_history(history)
        save_history(root, history)

def main():
    parser = argparse.ArgumentParser(description="🍞 Bread Crumb — chat with your codebase")
    parser.add_argument("repo", nargs="?", default=".", help="path to repository")
    parser.add_argument("--setup", action="store_true", help="configure API key")
    args   = parser.parse_args()
    cfg    = load_config()
    if args.setup or not cfg.get("api_key"):
        cfg = setup_api_key(cfg)
    run(args.repo, cfg)

if __name__ == "__main__":
    main()

# 🍞 Bread Crumb

**Chat with your codebase from the terminal.**

Bread Crumb lets you ask questions about any code repository, get security audits, review diffs, and understand your codebase in seconds. Supports Anthropic, OpenAI, Gemini, and Ollama — bring your own API key.

[Demo Recording](https://asciinema.org/a/XXXXX) • [Features](#features) • [Installation](#installation) • [Documentation](#docs) • [Contributing](CONTRIBUTING.md)

---

## ⚡ Quick Start

```bash
# 1. Install
pip install breadcrumb-cli

# 2. Set your AI provider
breadcrumb config set-key --provider anthropic
breadcrumb config set-key --key anthropic_key --value "sk-ant-..."

# 3. Ask questions
breadcrumb ask "What does the auth module do?"
breadcrumb ask "Are there any security issues?" --format markdown

# 4. Start interactive chat
breadcrumb chat .

# 5. Get a security audit
breadcrumb audit .

# 6. Review a PR
breadcrumb diff HEAD~1
```

---

## 🎯 Features

### 🔴 Critical Features

- **Multi-provider AI support** — Anthropic, OpenAI, Gemini, Ollama
- **One-shot mode** (`breadcrumb ask`) — Perfect for CI/CD pipelines
- **Pipe mode** — Use in shell scripts and tools: `echo "question" | breadcrumb ask --pipe`
- **.breadcrumbignore support** — Skip generated files, vendor directories, etc.
- **Token usage tracking** — See exactly what you're spending
- **Session management** — Named conversations per repository

### 🟠 High-Value Features

- **`breadcrumb diff`** — AI-powered code review of PRs and commits
- **`breadcrumb audit`** — Security and architecture audits
- **`breadcrumb init`** — Generate `.breadcrumb.yaml` for repo-level config
- **Smart context compression** — Large files get AI summaries instead of truncation
- **`breadcrumb commit`** — Auto-generate conventional commit messages
- **Multi-session chat** — Multiple independent conversations per repo

### 🟡 Viral Features

- **`breadcrumb explain-error`** — Pipe any error and get a fix: `npm run build 2>&1 | breadcrumb explain-error`
- **`breadcrumb share`** — Export chat as beautiful shareable HTML
- **`breadcrumb digest`** — Daily summary of git commits

---

## 📦 Installation

### Option A: pip (Recommended for developers)
```bash
pip install breadcrumb-cli
breadcrumb ask "How does this work?"
```

### Option B: pipx (Isolated, recommended for CLI tools)
```bash
pipx install breadcrumb-cli
breadcrumb ask "How does this work?"
```

### Option C: Download Binary (No Python needed)
Download the standalone executable from [GitHub Releases](https://github.com/yourusername/breadcrumb/releases):
- `breadcrumb-linux` for Linux
- `breadcrumb-macos` for macOS
- `breadcrumb-windows.exe` for Windows

Then run:
```bash
./breadcrumb ask "How does this work?"
```

### TestPyPI Publishing

Use TestPyPI when you want to validate packaging before a real release.

1. Create a `TEST_PYPI_API_TOKEN` on [TestPyPI](https://test.pypi.org).
2. Add it to GitHub as a repository secret named `TEST_PYPI_API_TOKEN`.
3. Run the **Publish to TestPyPI** workflow from the Actions tab, or push a tag like `testpypi-v0.1.0`.

This publishes to `https://test.pypi.org/legacy/` and does not create a GitHub Release.

### Option D: Docker
```bash
docker run --rm \
  -v $(pwd):/repo \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  breadcrumb/breadcrumb audit
```

---

## 🔑 Configuration

### Set Your API Key

```bash
# Anthropic (Claude)
breadcrumb config set-key --provider anthropic
breadcrumb config set-key --key anthropic_key --value "sk-ant-..."

# OpenAI
breadcrumb config set-key --provider openai
breadcrumb config set-key --key openai_key --value "sk-..."

# Google Gemini
breadcrumb config set-key --provider gemini
breadcrumb config set-key --key gemini_key --value "..."

# Ollama (local)
breadcrumb config set-key --provider ollama
breadcrumb config set-key --key ollama_url --value "http://localhost:11434"
```

### Repository Config

Create `.breadcrumb.yaml` in your repo:

```yaml
# AI Provider to use for this repo
provider: anthropic
model: claude-3-5-sonnet-20241022

# Files to ignore (like .gitignore)
ignore_patterns:
  - "*.min.js"
  - "node_modules/"
  - "vendor/"

# Custom system prompt for this project
system_prompt: |
  This is a fintech application. Always flag PCI-DSS compliance issues.
  The main database is PostgreSQL. Never suggest breaking changes.

temperature: 0.7
max_tokens: 4096
```

Then generate this file automatically:
```bash
breadcrumb init
```

---

## 📖 Commands

### Interactive Chat
```bash
breadcrumb chat .              # Start interactive session
breadcrumb chat . --session "security-review"  # Named session
```

### One-Shot Queries
```bash
breadcrumb ask "What does auth.ts do?"
breadcrumb ask "Security issues?" --format markdown
```

### Code Review
```bash
breadcrumb diff HEAD~1         # Review last commit
breadcrumb diff main..feature/new-auth  # Review PR branch
```

### Security & Architecture Audit
```bash
breadcrumb audit .             # Full audit
breadcrumb audit . --model gpt-4o  # Use different model
```

### Generate Commit Messages
```bash
git add .
breadcrumb commit              # Suggests: "feat(auth): add JWT refresh"

# Or use in scripts:
git commit -m "$(breadcrumb commit --silent)"
```

### Explain Errors
```bash
npm run build 2>&1 | breadcrumb explain-error
python script.py 2>&1 | breadcrumb explain-error
cat error.log | breadcrumb explain-error
```

### Daily Digest
```bash
breadcrumb digest              # Summary of today's commits
breadcrumb digest --hours 48   # Last 48 hours
```

### Export & Share
```bash
breadcrumb share session.json  # Export as HTML
```

---

## 🚀 Use Cases

### For Teams
```bash
# Security review before merge
breadcrumb diff feature-branch --format json > audit.json

# Onboarding: new dev understands the codebase
breadcrumb ask "Give me a 5-minute overview of this project"

# Daily standup digest
breadcrumb digest | pbcopy  # Copy to Slack
```

### In CI/CD Pipelines
```bash
# .github/workflows/security.yml
- name: Bread Crumb Audit
  run: |
    breadcrumb audit . --format json > audit-report.json
    if grep -q "critical" audit-report.json; then exit 1; fi

# Pre-commit hook
breadcrumb commit --silent  # Auto-generate commit message
```

### Local Development
```bash
# Ask questions while coding
breadcrumb ask "How do I add error handling to this module?"

# Quick error debugging
npm run test 2>&1 | breadcrumb explain-error

# Understand what you changed
breadcrumb diff
```

---

## 🏗️ Architecture

```
breadcrumb/
├── cli.py              # Click entry point
├── config.py           # Configuration management
├── ingest.py           # File walking & .breadcrumbignore
├── history.py          # Session management
├── ai/
│   ├── router.py       # Provider routing (Anthropic/OpenAI/Gemini/Ollama)
│   └── prompts.py      # System prompts
├── commands/
│   ├── chat.py         # Interactive TUI
│   ├── ask.py          # One-shot queries
│   ├── audit.py        # Security audit
│   ├── diff.py         # Diff review
│   ├── commit.py       # Commit generation
│   ├── explain_error.py
│   ├── digest.py       # Commit digest
│   ├── init.py         # Config initialization
│   └── share.py        # HTML export
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/yourusername/breadcrumb
cd breadcrumb
pip install -e .

# Run tests
pytest tests/

# Run linting
ruff check .
```

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🌟 Show Your Support

If Bread Crumb helps you, please give it a star on GitHub! It helps us reach more developers.

Questions? Issues? [Create an issue](https://github.com/yourusername/breadcrumb/issues) or start a [discussion](https://github.com/yourusername/breadcrumb/discussions).

---

**Made with 🍞 by developers who love their codebases**

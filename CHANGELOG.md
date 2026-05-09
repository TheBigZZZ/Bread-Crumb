# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-05-09

### Added
- Initial release
- Multi-provider AI support (Anthropic, OpenAI, Gemini, Ollama)
- Interactive chat with codebase (`breadcrumb chat`)
- One-shot query mode (`breadcrumb ask`)
- Security and architecture audits (`breadcrumb audit`)
- Git diff reviews (`breadcrumb diff`)
- Conventional commit message generation (`breadcrumb commit`)
- Error explanation tool (`breadcrumb explain-error`)
- Daily commit digest (`breadcrumb digest`)
- Session management with named conversations
- `.breadcrumbignore` support for skipping files
- Repository-level configuration via `.breadcrumb.yaml`
- Token usage tracking and reporting
- Shareable HTML chat exports (`breadcrumb share`)
- Command-line configuration management
- Docker support
- Full test suite with GitHub Actions
- Automatic PyPI publishing and binary distribution

### Features
- Supports pipe/stdin mode for CI/CD integration
- Smart context compression for large files
- Session history persistence
- Custom system prompts per repository
- Multiple output formats (text, markdown, JSON)

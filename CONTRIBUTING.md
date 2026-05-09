# Contributing to Bread Crumb

Thanks for your interest in contributing to Bread Crumb! We love pull requests from everyone.

## Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/breadcrumb
   cd breadcrumb
   ```

2. **Set up development environment**
   ```bash
   pip install -e .
   pip install pytest ruff mypy
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Making Changes

- Write tests for new features
- Run the test suite: `pytest tests/`
- Run linting: `ruff check .`
- Ensure type hints are present: `mypy breadcrumb/`

## Commit Messages

Use conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `refactor:` for code refactoring
- `test:` for test changes
- `chore:` for dependency updates

Example:
```
feat(commands): add breadcrumb explain-error command
```

## Submitting Changes

1. Push your branch to GitHub
2. Create a Pull Request with a clear description
3. Link any related issues
4. Ensure all tests pass

## Code Style

- Use type hints
- Follow PEP 8
- Keep functions focused and well-documented
- Use docstrings for public functions

## Reporting Issues

Please include:
- Python version
- Operating system
- Reproducible steps
- Expected behavior
- Actual behavior
- Error messages/logs

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT).

Thank you for contributing!🍞

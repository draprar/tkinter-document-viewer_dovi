# Contributing to tkinter-document-viewer_dovi

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment (recommended)

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/draprar/tkinter-document-viewer_dovi.git
   cd tkinter-document-viewer_dovi
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install dev dependencies
   ```

4. **Install pre-commit hooks (optional but recommended):**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Style

We follow PEP 8 and use automated tools for formatting:

- **Black**: Code formatter (max line length: 120)
- **Flake8**: Linter
- **mypy**: Type checker

Run before committing:
```bash
black main.py test_main.py logger.py
flake8 main.py test_main.py logger.py --max-line-length=120
mypy main.py --ignore-missing-imports
```

Or use pre-commit:
```bash
pre-commit run --all-files
```

### Testing

Run tests with pytest:
```bash
# All tests
python -m pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test
pytest test_main.py::test_zoom_limits -v
```

### Documentation

- Add docstrings to all functions/methods (Google style)
- Update README.md for user-facing changes
- Add type hints to function signatures

## Making Changes

### Branching

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git commit -m "feat: description of changes"
   ```

### Commit Message Convention

We follow Conventional Commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring without feature changes
- `test:` Adding or updating tests
- `chore:` Build process, dependencies, etc.

Example:
```
feat: add MOBI support for document loading
fix: validate empty input in goto_page
docs: update installation instructions
```

## Testing Your Changes

1. **Run all tests:**
   ```bash
   pytest
   ```

2. **Test the application:**
   ```bash
   python main.py
   ```

3. **Check code quality:**
   ```bash
   flake8 . --max-line-length=120
   black --check .
   mypy main.py --ignore-missing-imports
   ```

## Security

- Never commit secrets or sensitive data
- Run `pip-audit` to check for vulnerable dependencies:
  ```bash
  pip-audit
  ```
- Report security issues privately to maintainers

## Pull Requests

1. Push your branch and create a PR
2. Fill in the PR template completely
3. Ensure all CI checks pass
4. Request review from maintainers
5. Address feedback and re-request review

### PR Title Format
```
[Type] Brief description (e.g., [feat] Add MOBI support)
```

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include:
  - Detailed description
  - Steps to reproduce (for bugs)
  - Expected vs actual behavior
  - Environment (Python version, OS, etc.)
  - Screenshots/logs if applicable

## Questions?

- Open a discussion in GitHub Discussions
- Check existing issues and documentation first
- Be respectful and constructive

---

**Thank you for contributing!** 🎉


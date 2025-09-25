# Contributing to tldns

Thank you for your interest in contributing to tldns! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/tldns.git
   cd tldns
   ```

2. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up development environment**:
   ```bash
   uv sync
   uv pip install -e ".[test]"
   ```

4. **Generate test certificates**:
   ```bash
   ./generate_cert.sh
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run python -m pytest

# Run with coverage
uv run python -m pytest --cov=tldns

# Run specific test categories
uv run python -m pytest -m unit
uv run python -m pytest -m integration
uv run python -m pytest -m "not slow"

# Run tests in verbose mode
uv run python -m pytest -v

# Add test dependencies if needed
uv add --dev pytest pytest-cov pytest-asyncio
```

### Code Quality

```bash
# Format code (if using ruff)
uv add --dev ruff
uv run ruff format .

# Lint code (if using ruff)
uv run ruff check .

# Type checking (if using mypy)
uv add --dev mypy
uv run mypy tldns/
```

### Building the Package

```bash
# Build source and wheel distributions
uv build

# Check the built package
uv add --dev twine
uv run python -m twine check dist/*
```

### Testing the CLI

```bash
# Test CLI functionality
uv run tldns --help
uv run tldns start --help

# Test with custom parameters
uv run tldns --port 8853 --log_level DEBUG start
```

## Contributing Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write descriptive docstrings for classes and functions
- Keep functions focused and single-purpose
- Use meaningful variable and function names

### Testing

- Write tests for all new functionality
- Maintain or improve test coverage (currently 96%)
- Include both unit tests and integration tests
- Test error conditions and edge cases
- Use descriptive test names that explain what is being tested

### Documentation

- Update README.md for user-facing changes
- Update CHANGELOG.md following Keep a Changelog format
- Add docstrings to new classes and functions
- Update type hints when modifying function signatures

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add support for custom DNS record types
fix: handle SSL handshake failures gracefully
docs: update installation instructions
test: add performance tests for concurrent clients
```

### Pull Request Process

1. **Fork the repository** and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the guidelines above

3. **Run tests** to ensure everything works:
   ```bash
   uv run python -m pytest
   ```

4. **Update documentation** as needed

5. **Commit your changes** with descriptive messages

6. **Push to your fork** and create a pull request

7. **Ensure CI passes** - all GitHub Actions workflows must pass

### Pull Request Checklist

- [ ] Tests pass locally and in CI
- [ ] Code follows project style guidelines
- [ ] Documentation is updated (if applicable)
- [ ] CHANGELOG.md is updated (for significant changes)
- [ ] Type hints are included for new code
- [ ] Test coverage is maintained or improved

## Reporting Issues

When reporting issues, please include:

- Python version and operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant log output (with `--log_level DEBUG`)
- Configuration details (host, port, certificates, etc.)

## Feature Requests

For feature requests, please:

- Check existing issues to avoid duplicates
- Describe the use case and motivation
- Provide examples of how the feature would be used
- Consider implementation complexity and maintenance burden

## Release Process

Releases are automated through GitHub Actions:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Commit changes and push to main
4. Create and push a version tag:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
5. GitHub Actions will automatically:
   - Run tests
   - Build packages
   - Create GitHub release
   - Publish to PyPI

## Getting Help

- Check the README.md for usage instructions
- Look at existing tests for examples
- Review the GitHub Actions workflows for CI/CD details
- Open an issue for questions or problems

Thank you for contributing to tldns!
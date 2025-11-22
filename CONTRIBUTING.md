# Contributing to NEXUS Platform

First off, thank you for considering contributing to NEXUS Platform! It's people like you that make NEXUS such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed and what you expected**
- **Include screenshots if relevant**
- **Include your environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and explain the expected behavior**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/your-username/nexus-platform.git
cd nexus-platform
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

4. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run tests**

```bash
pytest
```

## Development Workflow

### Branch Naming

- Feature: `feature/description`
- Bug fix: `bugfix/description`
- Hotfix: `hotfix/description`
- Documentation: `docs/description`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(word): add text formatting toolbar

Add a new toolbar with bold, italic, and underline buttons
for the word processor module.

Closes #123
```

```
fix(database): resolve connection pool exhaustion

Fixed issue where database connections were not being
properly released back to the pool.

Fixes #456
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 100 characters (not 79)
- Use Black for formatting
- Use isort for import sorting
- Use type hints for all functions
- Write comprehensive docstrings

### Code Formatting

```bash
# Format code with Black
black app/ modules/ database/ tests/

# Sort imports with isort
isort app/ modules/ database/ tests/

# Check with flake8
flake8 app/ modules/ database/ tests/

# Type checking with mypy
mypy app/ database/
```

### Documentation Style

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed, explaining the function's
    behavior in more detail.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative

    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

## Testing Guidelines

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

```python
def test_user_creation():
    """Test that a new user can be created successfully"""
    # Arrange
    user_data = {"username": "test", "email": "test@example.com"}

    # Act
    user = create_user(user_data)

    # Assert
    assert user.username == "test"
    assert user.email == "test@example.com"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=database --cov=modules

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::test_user_creation

# Run tests matching pattern
pytest -k "test_user"

# Run with verbose output
pytest -v
```

## Module Development

When adding a new module:

1. Create module directory in `modules/`
2. Follow the standard module structure:

```
module_name/
├── __init__.py
├── ui.py           # Streamlit UI components
├── logic.py        # Business logic
├── models.py       # Database models
├── utils.py        # Module utilities
└── tests/
    ├── test_ui.py
    └── test_logic.py
```

3. Update `modules/__init__.py`
4. Update `modules/README.md`
5. Add comprehensive tests
6. Update documentation

## Documentation

- Keep README.md up to date
- Update API.md for API changes
- Update ARCHITECTURE.md for design changes
- Add inline comments for complex logic
- Write clear commit messages

## Review Process

All submissions require review. We use GitHub pull requests for this purpose:

1. Submit your pull request
2. Maintainers will review your code
3. Address any feedback
4. Once approved, your PR will be merged

### What We Look For

- **Code Quality**: Clean, readable, well-documented code
- **Tests**: Comprehensive test coverage
- **Documentation**: Clear documentation of changes
- **Performance**: No significant performance regressions
- **Security**: No security vulnerabilities
- **Compatibility**: Works across supported platforms

## Community

- Join our Discord server
- Follow us on Twitter
- Read our blog
- Attend community meetings

## Questions?

Feel free to:
- Open an issue
- Ask in Discord
- Email us at dev@nexus-platform.com

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to contributor events

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to NEXUS Platform! 🚀

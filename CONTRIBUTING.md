# Contributing to ADAML-Pluto

Thank you for your interest in contributing to ADAML-Pluto! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ADAML-Pluto.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests to ensure everything works
6. Submit a pull request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/ro0TuX777/ADAML-Pluto.git
cd ADAML-Pluto

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Install the package in editable mode
pip install -e .
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adaml_pluto --cov-report=html

# Run specific test file
pytest tests/test_lead.py

# Run tests matching a pattern
pytest -k "test_create"
```

## Code Style

We follow PEP 8 style guidelines. Please ensure your code is formatted properly:

```bash
# Format code with black
black src/

# Check code style with flake8
flake8 src/

# Type checking with mypy
mypy src/
```

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the tests to cover your changes
3. Ensure all tests pass
4. Update documentation as needed
5. The PR will be reviewed by maintainers

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Questions?

Feel free to open an issue for any questions or concerns.

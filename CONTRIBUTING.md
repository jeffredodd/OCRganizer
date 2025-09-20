# Contributing to OCRganizer

Thank you for your interest in contributing to OCRganizer! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- System dependencies: `poppler-utils`, `tesseract-ocr`

### Getting Started

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/OCRganizer.git
   cd OCRganizer
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -e .[dev]
   ```

4. **Run Tests**
   ```bash
   # Test CI setup locally
   ./scripts/test-ci.sh
   
   # Or run individual commands
   pytest
   flake8 src tests
   black --check src tests
   mypy src
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run the full test suite
pytest

# Run specific tests
pytest tests/test_your_module.py

# Check code quality
./scripts/test-ci.sh
```

### 4. Commit and Push

```bash
git add .
git commit -m "Add your feature description"
git push origin feature/your-feature-name
```

### 5. Create Pull Request

- Use a descriptive title
- Include details about your changes
- Reference any related issues

## Code Style Guidelines

### Python Code

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions
- Keep functions small and focused

### Testing

- Write tests for all new functionality
- Aim for high test coverage
- Use descriptive test names
- Mock external dependencies

### Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update API documentation if needed

## Project Structure

```
OCRganizer/
├── src/                    # Core application modules
│   ├── ai_analyzer.py      # AI-powered document analysis
│   ├── pdf_processor.py    # PDF text extraction
│   ├── file_organizer.py   # File organization logic
│   └── config.py          # Configuration management
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── .github/workflows/      # CI/CD workflows
└── pyproject.toml          # Project configuration
```

## Testing Guidelines

### Test Categories

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

### Mocking External Services

- Mock AI API calls (OpenAI, Anthropic)
- Mock file system operations
- Mock network requests

### Test Data

- Use realistic but anonymized test data
- Include edge cases and error conditions
- Test with various PDF types

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

### Automated Checks

- **Linting**: flake8, black, isort, mypy
- **Testing**: pytest with coverage
- **Building**: Package build verification
- **Versioning**: Automatic version bumping

### Workflow Triggers

- **Push to main**: Full CI pipeline + version bump
- **Pull Request**: CI checks only
- **Manual**: Workflow dispatch

## Release Process

### Version Management

- Uses semantic versioning (MAJOR.MINOR.PATCH)
- Automatic version bumping on main branch
- GitHub releases created automatically

### Version Bumping

```bash
# Manual version bump
python scripts/version.py patch  # or minor, major
```

## Documentation

### Documentation Structure

- **README.md**: Main project documentation
- **docs/**: Detailed documentation
- **API docs**: Auto-generated from code
- **GitHub Pages**: Published documentation

### Documentation Updates

- Update relevant docs with code changes
- Add examples for new features
- Keep installation instructions current

## Issue Guidelines

### Bug Reports

- Use the bug report template
- Include steps to reproduce
- Provide system information
- Include error messages/logs

### Feature Requests

- Use the feature request template
- Describe the use case
- Consider implementation complexity
- Discuss with maintainers first

## Code Review Process

### For Contributors

- Address all review comments
- Keep commits focused and atomic
- Write clear commit messages
- Test your changes thoroughly

### For Reviewers

- Be constructive and helpful
- Check for security issues
- Verify test coverage
- Ensure documentation is updated

## Security

### Reporting Security Issues

- **DO NOT** create public issues for security problems
- Email security issues to: security@example.com
- Include detailed reproduction steps
- Allow time for response before disclosure

### Security Best Practices

- Never commit API keys or secrets
- Use environment variables for configuration
- Validate all user inputs
- Keep dependencies updated

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the golden rule

### Getting Help

- Check existing issues first
- Use discussions for questions
- Be specific about your problem
- Provide relevant context

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to OCRganizer! 🎉

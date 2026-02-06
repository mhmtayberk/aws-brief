# Contributing to AWS-Brief

First off, thank you for considering contributing to AWS-Brief! 🎉

## 🤝 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Docker version)
- **Logs** if applicable

### Suggesting Features

Feature suggestions are welcome! Please:

- **Check existing feature requests** first
- **Explain the use case** clearly
- **Describe the expected behavior**
- Consider if it fits the project scope (AWS intelligence tool)

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes** following our code style
4. **Test your changes** thoroughly
5. **Commit** with clear messages:
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **Push** to your fork:
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.11 or higher
- Docker (optional, for testing)
- Git

### Local Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/aws-brief.git
cd aws-brief

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Initialize database
python main.py init-db
```

### Running Tests

```bash
# Syntax validation
python -m py_compile src/**/*.py

# Import tests
python -c "from src.core.scraper import FeedScraper"
python -c "from src.core.database import NewsItem"

# Docker build test
docker build -t aws-brief:test .
docker run aws-brief:test --help
```

## 📝 Code Style

We use **Ruff** for linting and formatting. Pre-commit hooks will automatically format your code.

### Guidelines

- **Type hints**: Use type hints for function signatures
- **Docstrings**: Add docstrings to public functions/classes
- **Line length**: Soft limit of 100 characters (not enforced)
- **Imports**: Group by standard library, third-party, local
- **Naming**: 
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

### Example

```python
from typing import List, Dict, Any

class FeedScraper:
    """Scraper for AWS RSS feeds."""
    
    MAX_RETRIES = 3
    
    def fetch(self, url: str) -> str:
        """
        Fetch feed content from URL.
        
        Args:
            url: Feed URL to fetch
            
        Returns:
            Raw feed content as string
        """
        # Implementation
        pass
```

## 🧪 Testing Requirements

- All new features must include tests
- Existing tests must pass
- Code must pass pre-commit hooks
- Docker build must succeed

## 🔀 Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat: add Telegram notification support
fix: resolve SSRF vulnerability in URL validation
docs: update README with installation steps
```

## 📋 Pull Request Checklist

Before submitting your PR, ensure:

- [ ] Code follows the style guidelines
- [ ] Pre-commit hooks pass
- [ ] All tests pass
- [ ] Documentation is updated (if needed)
- [ ] Commit messages follow the convention
- [ ] PR description clearly explains the changes

## 🎯 Good First Issues

Look for issues labeled `good first issue` - these are great starting points for new contributors!

## 💬 Questions?

Feel free to open an issue with the `question` label or reach out to the maintainers.

## 📜 Code of Conduct

Be respectful, inclusive, and professional. We're all here to build something great together! 🚀

---

Thank you for contributing to AWS-Brief! 🙏

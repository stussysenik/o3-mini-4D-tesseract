P.S. difference between setup.py and pyproject.toml, difference between requirements.txt/base.txt and requirements/dev.txt, what's pre-commit, what's development workflow?, what's development package? what's run.bat vs run.sh?, what's a build artifact?

# 4D Tesseract Ball Animation

This project demonstrates a ball bouncing inside a 4D tesseract (a four-dimensional hypercube), projected into 2D space.

![Tesseract Animation](docs/tesseract.gif)

## Quick Start
```bash
# Setup Python environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements/dev.txt
python -m src.main
```

## Development Setup
See [Development Guide](docs/dev-documentation.md)

## Modern Python Project Structure Explained

### 1. setup.py vs pyproject.toml
- `setup.py` is the old way of packaging Python projects
- `pyproject.toml` is the new standard (PEP 517/518)
  - Handles both build and development configuration
  - Supports modern tools like Black, Pytest
  - More maintainable and cleaner syntax

### 2. Requirements Organization
- `requirements/base.txt`: Core dependencies needed to run the project
  - Example: pygame
- `requirements/dev.txt`: Additional tools for development
  - Includes testing, formatting, and quality tools
  - References base.txt using `-r base.txt`

### 3. Pre-commit Hooks
Pre-commit automatically runs checks before each commit:
- Formats code (Black)
- Checks style (Flake8)
- Validates syntax
- Prevents committing invalid code

### 4. Development Workflow
1. Create feature branch
2. Make changes
3. Auto-format and test (handled by pre-commit)
4. Commit and push
5. Create pull request

## License
MIT License - see [LICENSE](LICENSE)
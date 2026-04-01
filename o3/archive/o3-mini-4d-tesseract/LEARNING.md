# Learning Modern Python Project Structure

This document explains the concepts and reasoning behind modern Python project organization, using our 4D Tesseract project as an example.

## Project Structure Explained

```
tesseract-4d/
├── src/                    # Source code directory
│   └── tesseract_4d/      # Main package
├── tests/                  # Test files
├── docs/                   # Documentation
├── requirements/           # Dependencies
├── .gitignore             # Git exclusions
├── .pre-commit-config.yaml # Code quality automation
├── .python-version        # Python version lock
├── pyproject.toml         # Project configuration
└── README.md              # Project overview
```

## 🎓 Illustrative Primers

### 1. Source Code Organization (`src/`)
Think of `src/` as a factory floor:
```
src/
└── tesseract_4d/
    ├── __init__.py    # Factory entrance
    ├── core/          # Core machinery
    └── main.py        # Control panel
```
**Why?** The `src/` layout prevents accidental imports and ensures your package works the same way installed or in development.

### 2. Dependencies Management
Think of requirements like a recipe book:
```
requirements/
├── base.txt    # Basic recipe (pygame)
└── dev.txt     # Chef's tools (testing, formatting)
```
**Why?** Separating dependencies helps users install only what they need:
- Users only need `base.txt` to run the program
- Developers need `dev.txt` for building and testing

### 3. Configuration Files
Think of these as instruction manuals:

#### pyproject.toml
Like a master blueprint:
```toml
[project]
name = "tesseract-4d"      # What we're building
version = "0.1.0"          # Current model
dependencies = [...]       # Required parts

[tool.black]               # Quality control specs
line-length = 88
```

#### .pre-commit-config.yaml
Like a quality control checklist:
```yaml
repos:
-   repo: https://github.com/psf/black
    hooks:
    -   id: black         # Format code
-   repo: https://github.com/PyCQA/flake8
    hooks:
    -   id: flake8       # Check style
```

### 4. Development Workflow
Think of it as an assembly line:

1. **Feature Branch** (Create workstation)
   ```bash
   git checkout -b feature/new-widget
   ```

2. **Development** (Build and test)
   ```bash
   # Make changes
   pytest                 # Test
   black .               # Format
   ```

3. **Quality Control** (Pre-commit checks)
   ```bash
   git add .
   git commit            # Triggers pre-commit hooks
   ```

4. **Integration** (Ship to main)
   ```bash
   git push
   # Create Pull Request
   ```

## 🔍 Key Concepts Explained

### Virtual Environments
Think of it as a clean workshop:
```bash
python -m venv venv      # Create clean room
source venv/activate     # Enter clean room
```
**Why?** Prevents tool and version conflicts between projects.

### Pre-commit Hooks
Think of them as quality control gates:
- Code can't leave the workstation without passing checks
- Ensures consistent quality
- Automates formatting and testing

### Python Version Management
`.python-version` is like a tool compatibility chart:
```
3.12.1
```
**Why?** Ensures everyone uses the same Python version, preventing compatibility issues.

## �� Common Questions

### Q: Why use pyproject.toml instead of setup.py?
**A:** `pyproject.toml` is:
- More structured (like a form vs. a blank page)
- Standardized (PEP 517/518)
- Supports modern tools automatically

### Q: What are build artifacts?
**A:** Think of them as sawdust and scraps:
- `__pycache__/` (Compiled Python files)
- `*.egg-info/` (Package metadata)
- `build/` (Temporary build files)
We clean these up using `.gitignore`.

### Q: What's the difference between run.sh and run.bat?
**A:** They're startup scripts for different operating systems:
- `run.sh`: Unix/Linux/Mac
- `run.bat`: Windows
Modern projects often avoid these in favor of `python -m package.module`.

## �� Best Practices

1. **Keep it Clean**
   - Use `.gitignore` to exclude temporary files
   - Organize code logically in `src/`
   - Separate tests from source code

2. **Automate Quality**
   - Use pre-commit hooks
   - Run tests automatically
   - Format code consistently

3. **Document Everything**
   - README.md for quick start
   - docs/ for detailed documentation
   - Type hints and docstrings in code

## 🎯 Learning Path

1. Start with basic project structure
2. Add automated testing
3. Implement pre-commit hooks
4. Learn dependency management
5. Master version control workflow

Remember: Modern Python project structure is about making development more predictable, maintainable, and collaborative. 
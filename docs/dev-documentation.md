# Developer Documentation

This document provides technical details about the 4D Tesseract Ball Animation project's implementation and architecture.

## Project Architecture

### Core Components

1. **Tesseract Generation**
   - `generate_tesseract_vertices()`: Creates 16 vertices (±1 in each dimension)
   - `generate_tesseract_edges()`: Connects vertices differing in one coordinate

2. **Projection System**
   - `project_point()`: Projects 4D points to 2D using:
     - x-w plane rotation
     - Perspective projection
     - Screen space transformation

3. **Physics System**
   - Simple boundary collision detection
   - Velocity reflection at boundaries
   - Time-based movement updates

## Implementation Details

### 4D to 2D Projection Pipeline

1. **4D Space**
   ```python
   [x, y, z, w] # Original coordinates
   ```

2. **Rotation in x-w plane**
   ```python
   x_rot = x * cos(angle) - w * sin(angle)
   w_rot = x * sin(angle) + w * cos(angle)
   ```

3. **3D Perspective Projection**
   ```python
   factor = distance / (distance + z + z_offset)
   proj_x = x_rot * factor * scale
   proj_y = y * factor * scale
   ```

### Ball Physics

The ball moves in 4D space with these properties:
- Position: `ball_pos = [x, y, z, w]`
- Velocity: `ball_vel = [vx, vy, vz, vw]`
- Boundaries: `-1 to +1` in each dimension

Collision response:
```python
if position > max_bound or position < min_bound:
    velocity *= -1  # Perfect reflection
```

## Performance Considerations

1. **Vertex Generation**
   - One-time computation at startup
   - O(2⁴) vertices = 16 vertices
   - O(32) edges maximum

2. **Per-Frame Operations**
   - Ball position update: O(1)
   - Tesseract edge projections: O(32)
   - Single rotation plane (x-w)

## Code Style Guide

1. **Naming Conventions**
   - Functions: snake_case
   - Constants: UPPER_CASE
   - Variables: snake_case

2. **Documentation**
   - Docstrings for functions
   - Inline comments for complex math
   - Clear variable names

## Testing

### Manual Testing Checklist

1. Ball Movement
   - [ ] Smooth motion
   - [ ] Correct boundary collisions
   - [ ] No clipping through edges

2. Visualization
   - [ ] Consistent frame rate
   - [ ] Clear edge rendering
   - [ ] Proper perspective

## Future Improvements

1. **Features**
   - Multiple rotation planes
   - User-controlled rotation
   - Color gradients based on 4D position
   - Interactive ball control

2. **Technical**
   - Optimization for larger structures
   - More sophisticated physics
   - Additional projection methods

## Contributing Guidelines

1. **Code Contributions**
   - Follow existing code style
   - Add comments for complex math
   - Update documentation
   - Test thoroughly

2. **Pull Request Process**
   - Create feature branch
   - Update documentation
   - Add tests if applicable
   - Request review

## Development Environment Setup

1. **Required Tools**
   - Python 3.7+
   - Visual Studio Code (recommended)
   - Git

2. **Recommended Extensions**
   - Python
   - Pylint
   - Black formatter

3. **Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

## Debugging Tips

1. **Common Debug Points**
   - Ball position logging
   - Projection matrix values
   - Frame timing
   - Collision detection

2. **Visualization Aids**
   - Add coordinate display
   - Show velocity vectors
   - Print 4D coordinates

## Version Control

1. **Branch Structure**
   - main: stable releases
   - develop: integration branch
   - feature/*: new features
   - bugfix/*: bug fixes

2. **Commit Messages**
   - Start with verb (Add, Fix, Update)
   - Include component affected
   - Brief description

## Release Process

1. **Pre-release Checklist**
   - [ ] All tests pass
   - [ ] Documentation updated
   - [ ] Version numbers updated
   - [ ] Change log updated

2. **Release Steps**
   - Merge to main
   - Tag version
   - Update documentation
   - Create release notes

## Python Version Management

### Using pyenv

pyenv is recommended for managing multiple Python versions. It allows you to:
- Install multiple Python versions
- Set global and project-specific Python versions
- Switch between versions seamlessly

#### Installation

1. **macOS (with Homebrew)**
   ```bash
   brew install pyenv
   ```

2. **Add to shell configuration**
   Add to `~/.zshrc` or `~/.bash_profile`:
   ```bash
   echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
   echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
   echo 'eval "$(pyenv init -)"' >> ~/.zshrc
   ```

3. **Restart your terminal or run**
   ```bash
   source ~/.zshrc
   ```

#### Project Setup

1. **Install specific Python version**
   ```bash
   pyenv install 3.12
   ```

2. **Set project-specific version**
   ```bash
   # Navigate to project directory
   cd your-project-directory
   
   # Set local Python version
   pyenv local 3.12
   ```

3. **Verify installation**
   ```bash
   python --version  # Should show 3.12
   ```

### Virtual Environment Workflow

After setting Python version with pyenv:

1. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

2. **Activate environment**
   ```bash
   # macOS/Linux
   source venv/bin/activate
   
   # Windows
   .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Best Practices

1. **Version Control**
   - Include `.python-version` file (created by pyenv)
   - Add `venv/` to `.gitignore`
   - Keep `requirements.txt` updated

2. **Project Setup**
   - Use pyenv for Python version management
   - Use venv for dependency isolation
   - Document Python version in README.md

3. **Team Workflow**
   - All developers should use same Python version
   - Use pyenv to ensure version consistency
   - Document any version-specific dependencies

### Troubleshooting pyenv

1. **Common Issues**
   - Shell not recognizing pyenv commands
   - Python build failures
   - Version conflicts

2. **Solutions**
   - Verify shell configuration
   - Install build dependencies
   - Check for path conflicts

### IDE Integration

1. **VS Code**
   - Select Python interpreter from venv
   - Enable pylint/flake8 for linting
   - Configure debugger for venv

2. **PyCharm**
   - Configure project interpreter
   - Set Python version
   - Enable virtual environment


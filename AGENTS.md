# AGENTS.md

Guidelines for agentic coding assistants working on the POSIX Compatibility Layer project.

## Project Overview

A cross-platform POSIX compatibility layer with CLI and GUI interfaces, implemented in Python. Provides POSIX-style commands (ls, cd, pwd, etc.) that work across Windows, macOS, and Linux. Supports internationalization (i18n) and integrates with Ollama for AI-assisted command generation.

## Build Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Build package
pip install build
python -m build

# Run CLI (interactive mode or with command)
python -m posix_compat.cli
python start_gui.py

# Or after installation:
posix-cli          # Interactive REPL
posix-cli ls -a    # Single command
posix-gui          # Launch GUI
```

## PyPI Upload

```bash
# Linux/macOS - automatically bumps version, builds, and uploads
./upload_pypi.sh

# Windows
upload_pypi.bat

# Manual build and upload (if needed)
python -m build
python -m twine upload dist/*
```

## Test Commands

```bash
# Run all verification tests
python verify_changes.py
python verify_new_cmds.py
python test_i18n.py

# Run a single test file
python test_i18n.py

# Run from project root (tests use sys.path manipulation)
cd /path/to/POSIX-Compatibility-Layer
python verify_changes.py
```

Note: This project uses simple Python scripts for testing, not pytest or unittest framework. Tests verify basic functionality and import correctness.

## Code Style Guidelines

### Imports

```python
# Standard library imports first (alphabetically)
import datetime
import getpass
import glob
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile

# Third-party imports second
import psutil  # optional dependency

# Local imports last (use relative imports)
from .i18n import _
from .core import CompatLayer, CommandRegistry
```

### Naming Conventions

- **Functions**: `snake_case` (e.g., `cmd_ls`, `get_cwd`, `run_command`)
- **Classes**: `PascalCase` (e.g., `CompatLayer`, `CommandRegistry`, `OllamaClient`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `TRANSLATIONS`, `CURRENT_LANG`)
- **Private methods**: `_leading_underscore` (e.g., `_fetch_models_thread`)
- **Command functions**: `cmd_<name>` pattern (e.g., `cmd_ls`, `cmd_cd`)

### Formatting

- Use 4 spaces for indentation (no tabs)
- Maximum line length: ~100 characters
- Blank lines between function/class definitions
- No trailing whitespace
- Use double quotes for strings, single quotes for dict keys when practical

### Type Annotations

Not currently used in this codebase. Keep existing code consistent; new code may optionally add types.

### Error Handling

```python
# Use specific exception types with descriptive messages
try:
    result = operation()
except FileNotFoundError:
    return f"cmd: {_('err_no_file')}: {path}"
except PermissionError:
    return f"cmd: {_('err_perm')}: {path}"
except Exception as e:
    return f"cmd: error: {str(e)}"
```

- Catch specific exceptions before generic `Exception`
- Use i18n keys for user-facing error messages via `_()` function
- Include context (file path, command name) in error messages

### Command Implementation Pattern

```python
@CommandRegistry.register("command_name", "help_command_name")
def cmd_command_name(ctx, args):
    """
    Brief description.
    
    Args:
        ctx: CompatLayer instance with cwd context
        args: List of string arguments
    
    Returns:
        String result or error message
    """
    if not args:
        return f"command_name: {_('err_missing_arg')}"
    
    try:
        # Parse args, handle flags
        clean_args = [a for a in args if not a.startswith("-")]
        
        # Resolve paths relative to ctx.cwd
        target_path = pathlib.Path(ctx.cwd) / clean_args[0]
        
        # Perform operation
        return _("msg_success", result)
    except Exception as e:
        return f"command_name: error: {str(e)}"
```

### Internationalization (i18n)

- All user-facing strings must use the `_()` function
- Add new keys to all language dictionaries in `i18n.py`
- Message format with placeholders: `_("msg_key", arg1, arg2)` with `"msg_key": "Text {} and {}"` in translations

### Path Handling

- Use `pathlib.Path` for cross-platform compatibility
- Resolve relative paths against `ctx.cwd`, not `os.getcwd()`
- Handle `~` expansion with `os.path.expanduser()`
- Check `os.path.isabs()` before joining with cwd

### Threading (GUI)

```python
# GUI uses threading for blocking operations
thread = threading.Thread(target=self._worker_thread, args=(params,), daemon=True)
thread.start()

# Results communicated via queue
self.result_queue.put(("result_type", data))

# Main thread polls queue
def check_queue(self):
    try:
        msg_type, data = self.result_queue.get_nowait()
        # Handle message
    except queue.Empty:
        pass
    self.root.after(100, self.check_queue)
```

## Project Structure

```
POSIX-Compatibility-Layer/
├── src/posix_compat/
│   ├── __init__.py      # Package exports
│   ├── core.py          # Command implementations and CompatLayer
│   ├── cli.py           # Command-line interface (REPL)
│   ├── gui.py           # Tkinter GUI with AI integration
│   ├── i18n.py          # Internationalization translations
│   └── ollama_client.py # Ollama API client
├── pyproject.toml       # Build configuration
├── requirements.txt     # Dependencies
├── start_gui.py         # GUI launcher script
├── test_i18n.py         # i18n verification tests
├── verify_changes.py    # Import verification
└── verify_new_cmds.py   # Command verification
```

## Key Patterns

### Command Registry

Commands are registered via decorator pattern:

```python
@CommandRegistry.register("ls", "help_ls")
def cmd_ls(ctx, args):
    # implementation
```

### Adding New Commands

1. Implement function following the pattern above
2. Register with `@CommandRegistry.register("name", "help_key")`
3. Add help text to all language dicts in `i18n.py`
4. Add any new error/success message keys to i18n
5. Test with `python verify_new_cmds.py`

### Adding New Languages

1. Add language code and translations to `TRANSLATIONS` dict in `i18n.py`
2. Include `lang_name` key for menu display
3. Test with `python test_i18n.py`

## Dependencies

- **Required**: Python 3.7+
- **Optional**: `psutil` (enhanced system info), `requests` (HTTP operations)
- **External**: Ollama service (for AI features)

Use only standard library when possible. The project prioritizes minimal dependencies.
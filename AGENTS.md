# AGENTS.md

Guidelines for agentic coding assistants working on the POSIX Compatibility Layer project.

## Project Overview

A cross-platform POSIX compatibility layer with CLI and GUI interfaces, implemented in Python. Provides POSIX-style commands (ls, cd, pwd, etc.) that work across Windows, macOS, and Linux. Features natural language command parsing, AI-assisted command generation via Ollama, comprehensive permission management, and internationalization (i18n).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│              (CLI / GUI / Programmatic API)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     IntentParser                             │
│  - Natural language parsing                                  │
│  - AI-assisted command interpretation                        │
│  - Pattern matching for common operations                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   PermissionManager                          │
│  - Risk level assessment                                     │
│  - Confirmation flow management                              │
│  - Session/permanent approval tracking                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     CompatLayer                              │
│  - Command execution context                                 │
│  - Cross-platform path handling                              │
│  - Command registry dispatch                                 │
└─────────────────────────────────────────────────────────────┘
```

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
posix-cli "list all python files"  # Natural language
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
from .intent_parser import IntentParser, ParsedIntent
from .permission_manager import PermissionManager, PermissionScope
```

### Naming Conventions

- **Functions**: `snake_case` (e.g., `cmd_ls`, `get_cwd`, `parse_intent`)
- **Classes**: `PascalCase` (e.g., `CompatLayer`, `IntentParser`, `OllamaClient`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `TRANSLATIONS`, `DANGEROUS_COMMANDS`)
- **Private methods**: `_leading_underscore` (e.g., `_detect_os`, `_parse_ai_response`)
- **Command functions**: `cmd_<name>` pattern (e.g., `cmd_ls`, `cmd_cd`)
- **Enums**: `PascalCase` for type, `UPPER_SNAKE_CASE` for values

### Formatting

- Use 4 spaces for indentation (no tabs)
- Maximum line length: ~100 characters
- Blank lines between function/class definitions
- No trailing whitespace
- Use double quotes for strings, single quotes for dict keys when practical

### Type Annotations

Use type annotations for new code:

```python
from typing import Optional, List, Dict, Any

def parse(self, user_input: str, ai_client: Optional[OllamaClient] = None) -> ParsedIntent:
    ...

def get_command_risk_level(self, command: str, args: List[str]) -> tuple:
    ...
```

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
        clean_args = [a for a in args if not a.startswith("-")]
        target_path = pathlib.Path(ctx.cwd) / clean_args[0]
        return _("msg_success", result)
    except Exception as e:
        return f"command_name: error: {str(e)}"
```

### Internationalization (i18n)

- All user-facing strings must use the `_()` function
- Add new keys to all language dictionaries in `i18n.py`
- Message format with placeholders: `_("msg_key", arg1, arg2)`

### Path Handling

- Use `pathlib.Path` for cross-platform compatibility
- Resolve relative paths against `ctx.cwd`, not `os.getcwd()`
- Handle `~` expansion with `os.path.expanduser()`
- Check `os.path.isabs()` before joining with cwd

## Project Structure

```
POSIX-Compatibility-Layer/
├── src/posix_compat/
│   ├── __init__.py          # Package exports and version
│   ├── core.py              # Command implementations and CompatLayer
│   ├── cli.py               # Command-line interface with shell
│   ├── gui.py               # Tkinter GUI with AI integration
│   ├── i18n.py              # Internationalization translations
│   ├── ollama_client.py     # Ollama API client
│   ├── system_detector.py   # OS/shell detection (NEW)
│   ├── command_docs.py      # Command documentation system (NEW)
│   ├── permission_manager.py # Permission and risk management (NEW)
│   └── intent_parser.py     # Natural language intent parsing (NEW)
├── pyproject.toml           # Build configuration
├── requirements.txt         # Dependencies
├── upload_pypi.sh           # PyPI upload script (Linux/macOS)
├── upload_pypi.bat          # PyPI upload script (Windows)
├── start_gui.py             # GUI launcher script
├── test_i18n.py             # i18n verification tests
├── verify_changes.py        # Import verification
└── verify_new_cmds.py       # Command verification
```

## Key Patterns

### Command Registry

Commands are registered via decorator pattern:

```python
@CommandRegistry.register("ls", "help_ls")
def cmd_ls(ctx, args):
    # implementation
```

### Intent Parsing Flow

1. User input → `IntentParser.parse()`
2. Check for direct command match
3. Check for natural language pattern match
4. Optionally delegate to AI (Ollama)
5. Return `ParsedIntent` with commands and metadata

### Permission Flow

1. `PermissionManager.needs_confirmation()` checks if command requires approval
2. If yes, present confirmation dialog with options:
   - **Once**: Execute this time only
   - **Session**: Allow for current session
   - **Always**: Permanently allow
   - **Never**: Permanently deny
3. Track approvals in `~/.posix_compat/permissions.json`

### Risk Levels

| Level | Description | Examples |
|-------|-------------|----------|
| `safe` | Read-only, no side effects | ls, pwd, cat, grep |
| `low` | Minor modifications | mkdir, touch, cp |
| `medium` | Moderate modifications | mv, chmod |
| `high` | Significant changes | rm -r, kill, chown |
| `critical` | Irreversible data loss | rm -rf /, mkfs, dd |

### Adding New Commands

1. Implement function in `core.py` following the pattern
2. Register with `@CommandRegistry.register("name", "help_key")`
3. Add documentation in `command_docs.py` `CommandDoc`
4. Add help text to all language dicts in `i18n.py`
5. Add permission handling in `permission_manager.py` if dangerous
6. Test with `python verify_new_cmds.py`

### Adding Natural Language Patterns

In `intent_parser.py`:

```python
PATTERNS = {
    "my_new_action": [
        r"(?:action|do something)\s+(.+)",
        r"another pattern\s+(.+)",
    ],
}

def _convert_to_command(self, intent_name: str, captures: tuple, raw_input: str):
    if intent_name == "my_new_action":
        # Convert to command
        ...
```

### Adding New Languages

1. Add language code and translations to `TRANSLATIONS` dict in `i18n.py`
2. Include `lang_name` key for menu display
3. Test with `python test_i18n.py`

## Dependencies

- **Required**: Python 3.7+
- **Optional**: `psutil` (enhanced system info), `requests` (HTTP operations)
- **External**: Ollama service (for AI features)

Use only standard library when possible. The project prioritizes minimal dependencies.

## Confirmation Dialog Options

When executing dangerous commands, users see:

```
==================================================
  Confirmation Required
==================================================
  Command: rm -rf important_folder
  Risk Level: HIGH
  Warning: This command can cause irreversible data loss.
==================================================

  [y] Yes, execute once
  [a] Always allow this command
  [s] Allow for this session
  [n] No, cancel
  [e] Explain this command

  Choice [y/a/s/n/e]: 
```

## AI Integration

The system can use Ollama for:
- Natural language command interpretation
- Command explanation
- Error fix suggestions

To use AI features:
1. Install and run Ollama: `ollama serve`
2. Pull a model: `ollama pull llama2`
3. AI features are automatically enabled when Ollama is available
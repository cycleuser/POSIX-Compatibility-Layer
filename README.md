# POSIX Compatibility Layer

A powerful cross-platform compatibility layer that brings POSIX-style commands to Windows, macOS, and Linux with a consistent experience.

## Features

*   **Cross-Platform**: Works on Windows, macOS, and Linux.
*   **Unified Core**: Implements `ls`, `cd`, `pwd`, `cp`, `mv`, `rm`, `mkdir`, `touch`, `cat`, `grep`, `find`, `tar`, `zip` and more.
*   **Dual Interface**:
    *   **CLI**: A powerful command-line interface with REPL support.
    *   **GUI**: A user-friendly graphical interface with multi-language support and progress bars.
*   **Internationalization**: Supports 10+ languages (English, Chinese, Japanese, French, etc.).

## Installation

```bash
pip install posix-compat
```

## Usage

### CLI Mode

Run the command-line interface:

```bash
posix-cli
```

Or execute a single command:

```bash
posix-cli ls -a
posix-cli grep "import" core.py
```

### GUI Mode

Launch the graphical interface:

```bash
posix-gui
```

## License

MIT License

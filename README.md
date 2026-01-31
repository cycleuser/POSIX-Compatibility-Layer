# POSIX Compatibility Layer

An **experimental exploration tool** designed to attempt establishing a preliminary interactive connection between the operating system and local Large Language Models (LLMs) via a POSIX compatibility layer.

## Project Background

With the rapid development of local Large Language Model (LLM) technology, we have begun to consider how to enable AI to understand and operate computer systems more naturally. However, the command instruction differences between various operating systems (Windows, Linux, macOS) create barriers for AI to have a unified understanding.

This project is not intended to replace existing mature Shells or provide a production-grade cross-platform solution, but rather serves as a **Proof of Concept (PoC)**. We are attempting to build a lightweight Python intermediate layer that uses standard POSIX commands as a "common language" for interaction between AI and the operating system. Through this intermediate layer, we hope to explore the possibility of enabling local models (such as Ollama) to assist users with simple file operations and system queries using a standardized instruction set.

## Experimental Scenarios

As an exploratory prototype, the applicable scenarios for this project are primarily focused on research and personal experimentation:

*   **AI-Assisted Interaction Exploration**: Testing whether local LLMs can more accurately understand user intent through the POSIX instruction set and translate it into actual system operations (e.g., converting "clean up my desktop" into a series of `mv` commands).
*   **Instruction Set Standardization Research**: Verifying whether using a unified POSIX interface on heterogeneous systems helps reduce the complexity for AI to learn system operations.
*   **Simple Cross-Environment Script Testing**: Providing a simple environment for individual developers to verify the behavioral differences of basic file operation scripts across different systems, though it is not recommended for complex production environments.
*   **Teaching & Demonstration**: Serving as a teaching case to demonstrate how to encapsulate system calls using Python and how to design a basic "Human-AI-System" interaction interface.

## Compatibility Notes (Experimental)

This project is built on the Python Standard Library and theoretically possesses some cross-platform capabilities, but it is still in the **early development stage**:

*   **Hardware Support**: Basic runtime tests have been conducted on standard x86/x64 PCs and some ARM devices (such as Mac M-series). Due to its low resource footprint, it can also launch on some devices with limited performance for simple functional verification.
*   **Operating Systems**: Currently primarily debugged in Windows 10/11 environments, with attempts to run on macOS and Linux. We have masked some system differences through Python libraries, but unknown compatibility issues may still be encountered.
*   **Local Model Support**: Integrated preliminary support for calling the Ollama local interface, allowing users to select local models within the GUI for simple conversation and command generation tests.

## Dependencies

To keep the tool lightweight, we have minimized external dependencies:

*   **Base Environment**: Python 3.7+.
*   **Core Functions**: Primarily relies on Python native libraries (`os`, `sys`, etc.).
*   **GUI**: Uses Python's built-in **Tkinter**, with a relatively plain interface mainly for functional demonstration.
*   **System Info (Optional)**: It is recommended to install `psutil` to obtain more accurate system status information. If not installed, the program will attempt to fall back to simple system commands, and data precision may be limited.
*   **AI Features**: Requires a locally running **Ollama** service to support model interaction features.

## Installation & Trial

This project is for learning and research purposes only. It is recommended to try it out in the following ways:

**Method 1: PyPI Installation**
If you want a quick experience, you can try downloading from PyPI:
```bash
pip install posix-compat

# Run CLI mode
posix-cli

# Run GUI mode
posix-gui
```

**Method 2: Source Code Execution (Recommended)**
For convenience in debugging and modifying code, it is recommended to download the source code directly:
```bash
git clone https://github.com/cycleuser/POSIX-Compatibility-Layer
cd POSIX-Compatibility-Layer
# Run the startup script directly
python start_gui.py
```
This method does not require installation into system libraries, making it convenient for you to adjust the code for experiments at any time.

## Screenshots

The following screenshots show the current rudimentary form of the tool, with basic interface and functionality.

### Help Command
Lists the few basic commands currently supported.
![Help Command](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/0-help.png)

### Directory List (ls)
Attempts to simulate the output format of the ls command.
![List Directory](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/1-ls.png)

### Path Display (pwd)
Displays the current working directory.
![PWD](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/2-pwd.png)

### Directory Switch (cd)
Basic directory navigation functionality.
![Change Directory](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/3-cd.png)

### System Overview (lscpu)
Retrieves basic CPU information.
![LSCPU](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/4-lscpu.png)

### Hardware List (lspci)
Attempts to simulate lspci output via commands on Windows.
![LSPCI](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/5-lspci.png)

## License

This project is open-sourced under the **GPLv3** license.

As an experimental project, we hope to foster exchange through open source. If you are interested in the direction of "OS and AI Interaction", you are welcome to study the code, offer suggestions, or make modifications. Please note that this software is provided without any form of warranty; please pay attention to data security when using it. For detailed license terms, please refer to the `LICENSE` file.

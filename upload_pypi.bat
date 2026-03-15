@echo off
REM POSIX Compatibility Layer - Build and upload to PyPI
setlocal enabledelayedexpansion

cd /d "%~dp0"

set PYTHON=python
set VERSION_FILE=src\posix_compat\__init__.py

echo === POSIX Compatibility Layer PyPI Upload ===

echo [1/5] Bumping patch version...
%PYTHON% -c "import re; t = open('%VERSION_FILE%', encoding='utf-8').read(); m = re.search(r'(__version__\s*=\s*\"(\d+\.\d+\.)(\d+)\")', t); old = m.group(2) + m.group(3); new = m.group(2) + str(int(m.group(3)) + 1); open('%VERSION_FILE%', 'w', encoding='utf-8').write(t.replace(m.group(1), '__version__ = \"' + new + '\"')); print(f'  {old} -> {new}')"
if errorlevel 1 (
    echo ERROR: Failed to bump version
    exit /b 1
)

echo [2/5] Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist src\posix_compat.egg-info rmdir /s /q src\posix_compat.egg-info
for %%d in (*.egg-info) do rmdir /s /q "%%d" 2>nul

echo [3/5] Installing build tools...
%PYTHON% -m pip install --upgrade build twine -q

echo [4/5] Building package...
%PYTHON% -m build
if errorlevel 1 (
    echo ERROR: Build failed
    exit /b 1
)

%PYTHON% -m twine check dist\*
if errorlevel 1 (
    echo ERROR: Twine check failed
    exit /b 1
)

echo [5/5] Uploading to PyPI...
%PYTHON% -m twine upload dist\*

echo === Done! ===
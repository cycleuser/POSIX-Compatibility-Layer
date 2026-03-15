import os
import platform
import subprocess
import sys
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict


class OSType(Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    BSD = "bsd"
    UNKNOWN = "unknown"


class ShellType(Enum):
    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"
    POWERSHELL = "powershell"
    CMD = "cmd"
    SH = "sh"
    UNKNOWN = "unknown"


@dataclass
class SystemInfo:
    os_type: OSType
    os_name: str
    os_version: str
    shell_type: ShellType
    shell_path: str
    home_dir: str
    path_separator: str
    line_ending: str
    case_sensitive: bool


class SystemDetector:
    _instance: Optional['SystemDetector'] = None
    _info: Optional[SystemInfo] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_info(cls) -> SystemInfo:
        if cls._info is None:
            cls._info = cls._detect()
        return cls._info

    @classmethod
    def _detect(cls) -> SystemInfo:
        os_type = cls._detect_os()
        shell_type, shell_path = cls._detect_shell()
        
        return SystemInfo(
            os_type=os_type,
            os_name=cls._get_os_name(),
            os_version=cls._get_os_version(),
            shell_type=shell_type,
            shell_path=shell_path,
            home_dir=os.path.expanduser("~"),
            path_separator=os.sep,
            line_ending="\r\n" if os_type == OSType.WINDOWS else "\n",
            case_sensitive=os_type != OSType.WINDOWS
        )

    @classmethod
    def _detect_os(cls) -> OSType:
        system = platform.system().lower()
        if system == "windows":
            return OSType.WINDOWS
        elif system == "darwin":
            return OSType.MACOS
        elif system == "linux":
            return OSType.LINUX
        elif system in ("freebsd", "openbsd", "netbsd"):
            return OSType.BSD
        return OSType.UNKNOWN

    @classmethod
    def _get_os_name(cls) -> str:
        system = platform.system()
        if system == "Windows":
            return "Windows " + platform.release()
        elif system == "Darwin":
            return "macOS " + platform.mac_ver()[0]
        elif system == "Linux":
            try:
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=", 1)[1].strip('"')
            except:
                pass
            return "Linux"
        return system

    @classmethod
    def _get_os_version(cls) -> str:
        return platform.version()

    @classmethod
    def _detect_shell(cls) -> tuple:
        shell_env = os.environ.get("SHELL", "")
        shell_lower = shell_env.lower()
        
        if sys.platform == "win32":
            ps_module = os.environ.get("PSModulePath", "")
            if ps_module:
                return ShellType.POWERSHELL, "powershell.exe"
            return ShellType.CMD, "cmd.exe"
        
        if "zsh" in shell_lower:
            return ShellType.ZSH, shell_env
        elif "fish" in shell_lower:
            return ShellType.FISH, shell_env
        elif "bash" in shell_lower:
            return ShellType.BASH, shell_env
        elif "sh" in shell_lower:
            return ShellType.SH, shell_env
        
        if shell_env:
            return ShellType.UNKNOWN, shell_env
        
        return ShellType.SH, "/bin/sh"

    @classmethod
    def get_shell_config_path(cls) -> Optional[str]:
        info = cls.get_info()
        home = info.home_dir
        
        if info.shell_type == ShellType.BASH:
            for path in [f"{home}/.bashrc", f"{home}/.bash_profile"]:
                if os.path.exists(path):
                    return path
        elif info.shell_type == ShellType.ZSH:
            return f"{home}/.zshrc"
        elif info.shell_type == ShellType.FISH:
            return f"{home}/.config/fish/config.fish"
        
        return None

    @classmethod
    def get_available_shells(cls) -> List[str]:
        shells = []
        if cls.get_info().os_type == OSType.WINDOWS:
            for cmd in ["powershell.exe", "cmd.exe"]:
                if cls._command_exists(cmd):
                    shells.append(cmd)
        else:
            for cmd in ["/bin/bash", "/bin/zsh", "/bin/fish", "/bin/sh"]:
                if os.path.exists(cmd):
                    shells.append(cmd)
        return shells

    @classmethod
    def _command_exists(cls, cmd: str) -> bool:
        try:
            subprocess.run(
                ["which", cmd] if sys.platform != "win32" else ["where", cmd],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False

    @classmethod
    def is_windows(cls) -> bool:
        return cls.get_info().os_type == OSType.WINDOWS

    @classmethod
    def is_macos(cls) -> bool:
        return cls.get_info().os_type == OSType.MACOS

    @classmethod
    def is_linux(cls) -> bool:
        return cls.get_info().os_type == OSType.LINUX
__version__ = "0.2.0"

from .core import CompatLayer, CommandRegistry
from .cli import main as cli_main
from .gui import main as gui_main
from .i18n import _
from .system_detector import SystemDetector, SystemInfo, OSType, ShellType
from .command_docs import CommandDocumentation, CommandDoc, CommandCategory, RiskLevel
from .permission_manager import PermissionManager, PermissionType, PermissionScope
from .intent_parser import IntentParser, IntentType, ParsedIntent, ParsedCommand
from .ollama_client import OllamaClient

__all__ = [
    '__version__',
    'CompatLayer',
    'CommandRegistry',
    'cli_main',
    'gui_main',
    '_',
    'SystemDetector',
    'SystemInfo',
    'OSType',
    'ShellType',
    'CommandDocumentation',
    'CommandDoc',
    'CommandCategory',
    'RiskLevel',
    'PermissionManager',
    'PermissionType',
    'PermissionScope',
    'IntentParser',
    'IntentType',
    'ParsedIntent',
    'ParsedCommand',
    'OllamaClient',
]
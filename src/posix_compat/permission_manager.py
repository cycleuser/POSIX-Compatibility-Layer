import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime, timedelta
from pathlib import Path


class PermissionScope(Enum):
    SESSION = "session"
    ALWAYS = "always"
    NEVER = "never"
    ASK = "ask"


class PermissionType(Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    DIRECTORY_CREATE = "directory_create"
    DIRECTORY_DELETE = "directory_delete"
    COMMAND_EXECUTE = "command_execute"
    SYSTEM_MODIFY = "system_modify"
    PROCESS_KILL = "process_kill"
    NETWORK_ACCESS = "network_access"
    SHELL_ESCAPE = "shell_escape"
    AI_GENERATED = "ai_generated"


@dataclass
class PermissionRule:
    permission_type: PermissionType
    scope: PermissionScope
    target: Optional[str] = None
    expires: Optional[datetime] = None
    granted_at: datetime = field(default_factory=datetime.now)
    granted_by: str = "user"


@dataclass
class CommandApproval:
    command: str
    args: list
    approved: PermissionScope
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None


class PermissionManager:
    _instance: Optional['PermissionManager'] = None
    
    DANGEROUS_COMMANDS = {
        "rm", "rmdir", "mv", "kill", "killall", "chmod", "chown",
        "dd", "mkfs", "fdisk", "format", "del", "erase", "wipe",
        "shutdown", "reboot", "halt", "poweroff", "init",
    }
    
    SYSTEM_MODIFY_COMMANDS = {
        "apt", "apt-get", "yum", "dnf", "pacman", "pip", "npm",
        "brew", "choco", "winget", "snap", "flatpak",
        "systemctl", "service", "launchctl",
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._rules: Dict[PermissionType, PermissionRule] = {}
        self._command_approvals: Dict[str, CommandApproval] = {}
        self._session_approvals: Set[str] = set()
        self._current_session: str = self._generate_session_id()
        self._confirmation_callback: Optional[Callable] = None
        self._audit_log: list = []
        
        self._load_persisted_rules()

    def _generate_session_id(self) -> str:
        import uuid
        return str(uuid.uuid4())[:8]

    def _get_config_path(self) -> Path:
        config_dir = Path.home() / ".posix_compat"
        config_dir.mkdir(exist_ok=True)
        return config_dir / "permissions.json"

    def _load_persisted_rules(self):
        try:
            config_path = self._get_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for perm_str, rule_data in data.get("rules", {}).items():
                        perm_type = PermissionType(perm_str)
                        scope = PermissionScope(rule_data["scope"])
                        expires = None
                        if rule_data.get("expires"):
                            expires = datetime.fromisoformat(rule_data["expires"])
                        self._rules[perm_type] = PermissionRule(
                            permission_type=perm_type,
                            scope=scope,
                            target=rule_data.get("target"),
                            expires=expires,
                        )
        except Exception:
            pass

    def _persist_rules(self):
        try:
            config_path = self._get_config_path()
            data = {
                "rules": {
                    rule.permission_type.value: {
                        "scope": rule.scope.value,
                        "target": rule.target,
                        "expires": rule.expires.isoformat() if rule.expires else None,
                    }
                    for rule in self._rules.values()
                }
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def set_confirmation_callback(self, callback: Callable):
        self._confirmation_callback = callback

    def set_permission(self, perm_type: PermissionType, scope: PermissionScope, 
                       target: Optional[str] = None, duration_minutes: Optional[int] = None):
        expires = None
        if duration_minutes:
            expires = datetime.now() + timedelta(minutes=duration_minutes)
        
        self._rules[perm_type] = PermissionRule(
            permission_type=perm_type,
            scope=scope,
            target=target,
            expires=expires,
        )
        self._persist_rules()
        self._log_audit(f"Permission set: {perm_type.value} -> {scope.value}")

    def get_permission(self, perm_type: PermissionType) -> PermissionScope:
        rule = self._rules.get(perm_type)
        if rule:
            if rule.expires and datetime.now() > rule.expires:
                del self._rules[perm_type]
                self._persist_rules()
                return PermissionScope.ASK
            return rule.scope
        return PermissionScope.ASK

    def is_dangerous_command(self, command: str) -> bool:
        return command.lower() in self.DANGEROUS_COMMANDS

    def is_system_modify_command(self, command: str) -> bool:
        return command.lower() in self.SYSTEM_MODIFY_COMMANDS

    def get_command_risk_level(self, command: str, args: list) -> tuple:
        cmd_lower = command.lower()
        
        if cmd_lower in {"rm", "kill", "killall", "dd", "mkfs", "fdisk", "format"}:
            return "critical", "This command can cause irreversible data loss."
        
        if cmd_lower in {"mv", "rmdir", "chmod", "chown"}:
            return "high", "This command modifies or removes files."
        
        if cmd_lower in self.SYSTEM_MODIFY_COMMANDS:
            return "high", "This command modifies system packages or services."
        
        if cmd_lower in {"mkdir", "touch", "cp", "ln", "tar", "zip", "unzip"}:
            return "medium", "This command modifies the filesystem."
        
        return "low", None

    def needs_confirmation(self, command: str, args: list) -> bool:
        perm_type = self._get_command_permission_type(command)
        scope = self.get_permission(perm_type)
        
        if scope == PermissionScope.ALWAYS:
            return False
        if scope == PermissionScope.NEVER:
            return True
        
        if command in self._session_approvals:
            return False
        
        if self.is_dangerous_command(command):
            return True
        
        if self.is_system_modify_command(command):
            return True
        
        return False

    def _get_command_permission_type(self, command: str) -> PermissionType:
        if command.lower() in {"rm", "rmdir"}:
            return PermissionType.FILE_DELETE
        if command.lower() in {"mv", "cp", "touch", "mkdir"}:
            return PermissionType.FILE_WRITE
        if command.lower() in {"kill", "killall"}:
            return PermissionType.PROCESS_KILL
        if command.lower() in {"chmod", "chown"}:
            return PermissionType.SYSTEM_MODIFY
        if command.lower() in {"apt", "pip", "npm", "brew"}:
            return PermissionType.SYSTEM_MODIFY
        return PermissionType.COMMAND_EXECUTE

    async def request_confirmation(self, command: str, args: list, 
                                    risk_level: str, risk_message: str) -> tuple:
        if self._confirmation_callback:
            return await self._confirmation_callback(command, args, risk_level, risk_message)
        return False, PermissionScope.ASK

    def grant_session_approval(self, command: str, args: list):
        cmd_key = self._make_command_key(command, args)
        self._session_approvals.add(cmd_key)
        self._command_approvals[cmd_key] = CommandApproval(
            command=command,
            args=args,
            approved=PermissionScope.SESSION,
            session_id=self._current_session,
        )
        self._log_audit(f"Session approval granted: {command} {' '.join(args)}")

    def grant_permanent_approval(self, command: str, args: list):
        perm_type = self._get_command_permission_type(command)
        self.set_permission(perm_type, PermissionScope.ALWAYS)
        self._log_audit(f"Permanent approval granted for: {command}")

    def deny_permanent(self, command: str, args: list):
        perm_type = self._get_command_permission_type(command)
        self.set_permission(perm_type, PermissionScope.NEVER)
        self._log_audit(f"Permanently denied: {command}")

    def _make_command_key(self, command: str, args: list) -> str:
        return f"{command}:{' '.join(args)}"

    def new_session(self):
        self._current_session = self._generate_session_id()
        self._session_approvals.clear()
        self._log_audit("New session started")

    def _log_audit(self, message: str):
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "session": self._current_session,
            "message": message,
        })

    def get_audit_log(self, limit: int = 100) -> list:
        return self._audit_log[-limit:]

    def get_permission_summary(self) -> Dict[str, Any]:
        return {
            "session_id": self._current_session,
            "session_approvals": len(self._session_approvals),
            "permanent_rules": {
                perm.value: rule.scope.value 
                for perm, rule in self._rules.items()
            },
            "dangerous_commands": list(self.DANGEROUS_COMMANDS),
            "system_modify_commands": list(self.SYSTEM_MODIFY_COMMANDS),
        }

    def reset_all_permissions(self):
        self._rules.clear()
        self._session_approvals.clear()
        self._command_approvals.clear()
        self._persist_rules()
        self._log_audit("All permissions reset")
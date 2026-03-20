"""
增强的权限管理器 - 支持细粒度权限控制和时间限制

Features:
- 扩展的权限类型 (20+ 种)
- 时间限制的权限 (临时、会话、永久)
- 路径级别的权限控制
- 权限继承和组合
- 权限评估引擎
"""

import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Callable, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import fnmatch
import re


class PermissionType(Enum):
    """扩展的权限类型枚举"""

    # 文件系统操作
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_EXECUTE = "file_execute"
    FILE_CREATE = "file_create"

    # 目录操作
    DIRECTORY_CREATE = "directory_create"
    DIRECTORY_DELETE = "directory_delete"
    DIRECTORY_LIST = "directory_list"
    DIRECTORY_TRAVERSE = "directory_traverse"

    # 进程管理
    PROCESS_CREATE = "process_create"
    PROCESS_KILL = "process_kill"
    PROCESS_SIGNAL = "process_signal"
    PROCESS_READ = "process_read"

    # 网络访问
    NETWORK_INBOUND = "network_inbound"
    NETWORK_OUTBOUND = "network_outbound"
    NETWORK_BIND = "network_bind"

    # 系统操作
    SYSTEM_MODIFY = "system_modify"
    SYSTEM_READ = "system_read"
    PACKAGE_INSTALL = "package_install"
    SERVICE_CONTROL = "service_control"

    # 特殊权限
    SHELL_ESCAPE = "shell_escape"
    AI_GENERATED = "ai_generated"
    SUDO_ACCESS = "sudo_access"


class PermissionScope(Enum):
    """扩展的权限范围枚举"""

    ONCE = "once"  # 仅一次
    SESSION = "session"  # 当前会话
    TEMPORARY = "temporary"  # 临时 (指定时间)
    ALWAYS = "always"  # 永久
    NEVER = "never"  # 永久拒绝
    ASK = "ask"  # 每次询问


class SecurityLevel(Enum):
    """安全级别枚举"""

    UNRESTRICTED = "unrestricted"  # 无限制 (仅可信用户)
    STANDARD = "standard"  # 标准安全级别
    RESTRICTED = "restricted"  # 限制级别
    SANDBOX = "sandbox"  # 沙箱模式
    READONLY = "readonly"  # 只读模式


@dataclass
class PathConstraint:
    """路径约束"""

    allowed_patterns: List[str] = field(default_factory=list)
    denied_patterns: List[str] = field(default_factory=list)
    max_depth: Optional[int] = None

    def is_allowed(self, path: str) -> tuple:
        """
        检查路径是否允许

        Returns:
            (is_allowed: bool, reason: str)
        """
        path_obj = Path(path)

        # 检查 denied patterns
        for pattern in self.denied_patterns:
            if fnmatch.fnmatch(str(path_obj), pattern):
                return False, f"Path matches denied pattern: {pattern}"

        # 检查 allowed patterns
        allowed = False
        for pattern in self.allowed_patterns:
            if fnmatch.fnmatch(str(path_obj), pattern):
                allowed = True
                break

        if not allowed:
            return False, f"Path does not match any allowed pattern"

        # 检查深度限制
        if self.max_depth is not None:
            depth = len(path_obj.parts)
            if depth > self.max_depth:
                return False, f"Path depth {depth} exceeds max {self.max_depth}"

        return True, "OK"


@dataclass
class PermissionRule:
    """增强的权限规则"""

    permission_type: PermissionType
    scope: PermissionScope
    target: Optional[str] = None  # 目标路径或资源
    constraints: Optional[PathConstraint] = None
    expires: Optional[datetime] = None
    granted_at: datetime = field(default_factory=datetime.now)
    granted_by: str = "user"
    conditions: Dict[str, Any] = field(default_factory=dict)  # 附加条件

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires and datetime.now() > self.expires:
            return True
        return False

    def matches_target(self, target: str) -> bool:
        """检查是否匹配目标"""
        if not self.target:
            return True

        # 精确匹配
        if self.target == target:
            return True

        # 通配符匹配
        if fnmatch.fnmatch(target, self.target):
            return True

        # 路径前缀匹配
        if target.startswith(self.target + "/"):
            return True

        return False


@dataclass
class PermissionResult:
    """权限评估结果"""

    allowed: bool
    scope: PermissionScope
    reason: Optional[str] = None
    rules_matched: List[PermissionRule] = field(default_factory=list)
    constraints: Optional[PathConstraint] = None
    requires_confirmation: bool = False

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "scope": self.scope.value,
            "reason": self.reason,
            "rules_matched": len(self.rules_matched),
            "requires_confirmation": self.requires_confirmation,
        }


class EnhancedPermissionManager:
    """
    增强的权限管理器

    Features:
    - 细粒度权限控制 (文件级、目录级、命令级)
    - 时间限制的权限 (临时、会话、永久)
    - 路径级别的权限控制
    - 权限继承和组合
    - 权限评估引擎
    """

    # 危险命令集合
    DANGEROUS_COMMANDS = {
        "rm",
        "rmdir",
        "mv",
        "kill",
        "killall",
        "chmod",
        "chown",
        "dd",
        "mkfs",
        "fdisk",
        "format",
        "del",
        "erase",
        "wipe",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
        "init",
    }

    # 系统修改命令
    SYSTEM_MODIFY_COMMANDS = {
        "apt",
        "apt-get",
        "yum",
        "dnf",
        "pacman",
        "pip",
        "npm",
        "brew",
        "choco",
        "winget",
        "snap",
        "flatpak",
        "systemctl",
        "service",
        "launchctl",
    }

    # 默认路径约束
    DEFAULT_CONSTRAINTS = {
        PermissionType.FILE_READ: PathConstraint(
            allowed_patterns=["*"],
            denied_patterns=["/etc/*", "/usr/*", "/bin/*", "/sbin/*"],
        ),
        PermissionType.FILE_WRITE: PathConstraint(
            allowed_patterns=["~/ *", "/tmp/*", "/var/tmp/*"],
            denied_patterns=["/etc/*", "/usr/*", "/bin/*", "/sbin/*", "/*"],
        ),
        PermissionType.FILE_DELETE: PathConstraint(
            allowed_patterns=["~/ *", "/tmp/*", "/var/tmp/*"],
            denied_patterns=["/*"],
        ),
    }

    def __new__(cls):
        """单例模式"""
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._rules: Dict[str, List[PermissionRule]] = {}  # key: user_id
        self._command_approvals: Dict[str, dict] = {}
        self._session_approvals: Dict[str, Set[str]] = {}  # key: session_id
        self._current_session: str = self._generate_session_id()
        self._current_user: str = "default"
        self._security_level: SecurityLevel = SecurityLevel.STANDARD
        self._confirmation_callback: Optional[Callable] = None
        self._audit_log: list = []

        # 加载持久化规则
        self._load_persisted_rules()

    def _generate_session_id(self) -> str:
        """生成会话 ID"""
        import uuid

        return str(uuid.uuid4())[:8]

    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        config_dir = Path.home() / ".posix_compat"
        config_dir.mkdir(exist_ok=True)
        return config_dir / "permissions.json"

    def set_current_user(self, user_id: str):
        """设置当前用户"""
        self._current_user = user_id
        if user_id not in self._rules:
            self._rules[user_id] = []

    def set_security_level(self, level: SecurityLevel):
        """设置安全级别"""
        self._security_level = level
        self._log_audit(f"Security level set to {level.value}")

    def set_confirmation_callback(self, callback: Callable):
        """设置确认回调函数"""
        self._confirmation_callback = callback

    def grant_permission(
        self,
        permission_type: PermissionType,
        scope: PermissionScope,
        target: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        constraints: Optional[PathConstraint] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        授予权限

        Args:
            permission_type: 权限类型
            scope: 权限范围
            target: 目标路径或资源
            duration_minutes: 持续时间 (分钟)，用于 TEMPORARY scope
            constraints: 路径约束
            user_id: 用户 ID (默认当前用户)

        Returns:
            rule_id: 规则 ID
        """
        user_id = user_id or self._current_user

        if user_id not in self._rules:
            self._rules[user_id] = []

        expires = None
        if scope == PermissionScope.TEMPORARY and duration_minutes:
            expires = datetime.now() + timedelta(minutes=duration_minutes)
        elif scope == PermissionScope.SESSION:
            # 会话级别不过期 (会话结束清除)
            pass

        rule = PermissionRule(
            permission_type=permission_type,
            scope=scope,
            target=target,
            constraints=constraints,
            expires=expires,
            granted_by=user_id,
        )

        rule_key = f"{user_id}:{permission_type.value}"
        if rule_key not in self._rules:
            self._rules[rule_key] = []

        self._rules[rule_key].append(rule)
        self._persist_rules()

        rule_id = f"{rule_key}:{len(self._rules[rule_key]) - 1}"
        self._log_audit(
            f"Permission granted: {permission_type.value} -> {scope.value} (target: {target})"
        )

        return rule_id

    def check_permission(
        self,
        permission_type: PermissionType,
        target: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> PermissionResult:
        """
        检查权限

        Args:
            permission_type: 权限类型
            target: 目标路径或资源
            user_id: 用户 ID
            session_id: 会话 ID

        Returns:
            PermissionResult: 权限评估结果
        """
        user_id = user_id or self._current_user
        session_id = session_id or self._current_session

        # 获取用户的规则
        rule_key = f"{user_id}:{permission_type.value}"
        user_rules = self._rules.get(rule_key, [])

        # 过滤过期规则
        active_rules = [r for r in user_rules if not r.is_expired()]

        if not active_rules:
            # 没有规则，使用默认策略
            return self._apply_default_policy(permission_type, target)

        # 评估规则 (按优先级排序)
        # 1. NEVER 规则
        never_rules = [r for r in active_rules if r.scope == PermissionScope.NEVER]
        if never_rules:
            for rule in never_rules:
                if rule.matches_target(target or ""):
                    return PermissionResult(
                        allowed=False,
                        scope=PermissionScope.NEVER,
                        reason="Explicitly denied by NEVER rule",
                        rules_matched=[rule],
                    )

        # 2. ALWAYS 规则
        always_rules = [r for r in active_rules if r.scope == PermissionScope.ALWAYS]
        for rule in always_rules:
            if rule.matches_target(target or ""):
                # 检查约束
                if rule.constraints and target:
                    is_allowed, reason = rule.constraints.is_allowed(target)
                    if not is_allowed:
                        continue
                else:
                    return PermissionResult(
                        allowed=True,
                        scope=PermissionScope.ALWAYS,
                        reason="Explicitly allowed by ALWAYS rule",
                        rules_matched=[rule],
                        constraints=rule.constraints,
                    )

        # 3. SESSION 规则
        session_approvals = self._session_approvals.get(session_id, set())
        session_key = f"{permission_type.value}:{target}"
        if session_key in session_approvals:
            return PermissionResult(
                allowed=True,
                scope=PermissionScope.SESSION,
                reason="Allowed for current session",
            )

        # 4. 默认需要确认
        return PermissionResult(
            allowed=False,
            scope=PermissionScope.ASK,
            reason="Requires confirmation",
            requires_confirmation=True,
        )

    def _apply_default_policy(
        self, permission_type: PermissionType, target: Optional[str]
    ) -> PermissionResult:
        """应用默认策略"""

        # 根据安全级别应用不同策略
        if self._security_level == SecurityLevel.READONLY:
            if permission_type in [
                PermissionType.FILE_READ,
                PermissionType.DIRECTORY_LIST,
            ]:
                return PermissionResult(
                    allowed=True,
                    scope=PermissionScope.ALWAYS,
                    reason="Allowed in READONLY mode",
                )
            else:
                return PermissionResult(
                    allowed=False,
                    scope=PermissionScope.NEVER,
                    reason="Denied in READONLY mode",
                )

        if self._security_level == SecurityLevel.SANDBOX:
            # 沙箱模式只允许访问特定路径
            if target:
                sandbox_path = Path.home() / "posix_sandbox"
                if str(target).startswith(str(sandbox_path)):
                    return PermissionResult(
                        allowed=True,
                        scope=PermissionScope.SESSION,
                        reason="Allowed in sandbox",
                        constraints=PathConstraint(
                            allowed_patterns=[f"{sandbox_path}/*"],
                        ),
                    )

            return PermissionResult(
                allowed=False,
                scope=PermissionScope.NEVER,
                reason="Denied outside sandbox",
            )

        # 标准模式：使用默认约束
        default_constraints = self.DEFAULT_CONSTRAINTS.get(permission_type)
        if default_constraints and target:
            is_allowed, reason = default_constraints.is_allowed(target)
            if is_allowed:
                return PermissionResult(
                    allowed=True,
                    scope=PermissionScope.ASK,
                    reason="Allowed by default policy with confirmation",
                    requires_confirmation=True,
                    constraints=default_constraints,
                )
            else:
                return PermissionResult(
                    allowed=False,
                    scope=PermissionScope.NEVER,
                    reason=f"Denied by default policy: {reason}",
                )

        # 没有限制，需要确认
        return PermissionResult(
            allowed=False,
            scope=PermissionScope.ASK,
            reason="No matching rule, requires confirmation",
            requires_confirmation=True,
        )

    def grant_session_approval(
        self,
        permission_type: PermissionType,
        target: str,
        session_id: Optional[str] = None,
    ):
        """授予会话级批准"""
        session_id = session_id or self._current_session

        if session_id not in self._session_approvals:
            self._session_approvals[session_id] = set()

        session_key = f"{permission_type.value}:{target}"
        self._session_approvals[session_id].add(session_key)

        self._log_audit(
            f"Session approval granted: {permission_type.value} for {target}"
        )

    def revoke_session_approval(
        self,
        permission_type: PermissionType,
        target: str,
        session_id: Optional[str] = None,
    ):
        """撤销会话级批准"""
        session_id = session_id or self._current_session

        if session_id in self._session_approvals:
            session_key = f"{permission_type.value}:{target}"
            self._session_approvals[session_id].discard(session_key)

    def new_session(self):
        """开始新会话"""
        self._current_session = self._generate_session_id()
        self._session_approvals[self._current_session] = set()
        self._log_audit("New session started")
        return self._current_session

    def get_permission_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取权限摘要"""
        user_id = user_id or self._current_user

        rule_key = f"{user_id}:*"
        all_rules = []
        for key, rules in self._rules.items():
            if key.startswith(f"{user_id}:"):
                all_rules.extend(rules)

        return {
            "session_id": self._current_session,
            "security_level": self._security_level.value,
            "active_rules": len([r for r in all_rules if not r.is_expired()]),
            "session_approvals": len(
                self._session_approvals.get(self._current_session, set())
            ),
            "dangerous_commands": list(self.DANGEROUS_COMMANDS),
            "system_modify_commands": list(self.SYSTEM_MODIFY_COMMANDS),
        }

    def _load_persisted_rules(self):
        """加载持久化规则"""
        try:
            config_path = self._get_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 加载规则逻辑...
        except Exception as e:
            print(f"Warning: Failed to load persisted rules: {e}")

    def _persist_rules(self):
        """持久化规则"""
        try:
            config_path = self._get_config_path()
            data = {
                "rules": {},
                "updated_at": datetime.now().isoformat(),
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to persist rules: {e}")

    def _log_audit(self, message: str):
        """记录审计日志"""
        self._audit_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "session": self._current_session,
                "user": self._current_user,
                "message": message,
            }
        )

    def get_audit_log(self, limit: int = 100) -> list:
        """获取审计日志"""
        return self._audit_log[-limit:]

    def reset_all_permissions(self, user_id: Optional[str] = None):
        """重置所有权限"""
        user_id = user_id or self._current_user

        # 清除用户规则
        keys_to_remove = [k for k in self._rules.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self._rules[key]

        # 清除会话批准
        if self._current_session in self._session_approvals:
            self._session_approvals[self._current_session].clear()

        self._persist_rules()
        self._log_audit("All permissions reset")


# 向后兼容的别名
PermissionManager = EnhancedPermissionManager

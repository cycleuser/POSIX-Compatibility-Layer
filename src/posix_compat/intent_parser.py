import re
import json
import shlex
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from .command_docs import CommandDocumentation, CommandCategory
from .permission_manager import PermissionManager
from .system_detector import SystemDetector


class IntentType(Enum):
    COMMAND = "command"
    QUESTION = "question"
    MULTI_COMMAND = "multi_command"
    CLARIFICATION = "clarification"
    CANCEL = "cancel"
    HELP = "help"
    UNKNOWN = "unknown"


class ConfirmationType(Enum):
    ONCE = "once"
    ALWAYS = "always"
    NEVER = "never"
    SESSION = "session"


@dataclass
class ParsedCommand:
    command: str
    args: List[str]
    raw_input: str
    confidence: float = 1.0
    needs_confirmation: bool = False
    risk_level: str = "low"
    risk_message: Optional[str] = None
    is_ai_generated: bool = False


@dataclass
class ParsedIntent:
    intent_type: IntentType
    commands: List[ParsedCommand] = field(default_factory=list)
    response: Optional[str] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class IntentParser:
    PATTERNS = {
        "list_files": [
            r"(?:list|show|display|ls)\s+(?:files?\s+)?(?:in\s+)?(.+)",
            r"(?:what'?s?\s+)?(?:is\s+)?(?:in\s+)?(.+)",
            r"ls\s*(.*)",
        ],
        "change_dir": [
            r"(?:go\s+to|cd|change\s+(?:to\s+)?(?:directory\s+)?)\s+(.+)",
            r"(?:open|enter)\s+(?:directory\s+)?(.+)",
        ],
        "create_directory": [
            r"(?:create|make|mkdir)\s+(?:a\s+)?(?:new\s+)?(?:directory|folder)\s+(?:called\s+)?(.+)",
            r"mkdir\s+(.+)",
        ],
        "create_file": [
            r"(?:create|make|touch)\s+(?:a\s+)?(?:new\s+)?file\s+(?:called\s+)?(.+)",
            r"touch\s+(.+)",
        ],
        "delete": [
            r"(?:delete|remove|rm)\s+(.+)",
            r"get\s+rid\s+of\s+(.+)",
        ],
        "copy": [
            r"(?:copy|cp)\s+(.+?)\s+(?:to\s+)?(.+)",
        ],
        "move": [
            r"(?:move|mv)\s+(.+?)\s+(?:to\s+)?(.+)",
            r"rename\s+(.+?)\s+(?:to\s+)?(.+)",
        ],
        "find": [
            r"(?:find|search\s+(?:for\s+)?)\s+(.+)",
            r"(?:where\s+(?:is|are)\s+)?(.+)",
        ],
        "grep": [
            r"(?:search|grep|find)\s+(?:for\s+)?['\"]?(.+?)['\"]?\s+(?:in\s+)?(.+)",
        ],
        "show_content": [
            r"(?:show|display|cat|read)\s+(?:the\s+)?(?:content(?:s)?\s+(?:of\s+)?)?(.+)",
            r"(?:what'?s?\s+(?:in\s+)?)['\"]?(.+?)['\"]?",
        ],
        "system_info": [
            r"(?:show|display|what\s+is)\s+(?:the\s+)?(?:system\s+)?info(?:rmation)?",
            r"(?:uname|system\s+info)",
        ],
        "disk_usage": [
            r"(?:show|display|what\s+is)\s+(?:the\s+)?(?:disk\s+)?(?:usage|space)",
            r"(?:df|du)\s*(.*)",
        ],
        "process_list": [
            r"(?:show|list|display)\s+(?:running\s+)?(?:process(?:es)?|programs)",
            r"ps\s*(.*)",
        ],
        "kill_process": [
            r"(?:kill|stop|terminate)\s+(?:process\s+)?(.+)",
        ],
        "help": [
            r"(?:help|what\s+can\s+you\s+do|\?)",
        ],
        "cancel": [
            r"(?:cancel|stop|never\s*mind|forget\s+it)",
        ],
    }

    CONFIRMATION_PATTERNS = {
        "once": [
            r"^(?:y|yes|ok|sure|go\s*ahead|do\s*it|confirm)$",
            r"^y(es)?$",
        ],
        "always": [
            r"^(?:always|always\s+yes|yes\s+always|y\s*-a|--always|-a\s*y)$",
        ],
        "session": [
            r"^(?:session|this\s+session|for\s+now)$",
        ],
        "never": [
            r"^(?:n|no|never|don'?t)$",
        ],
    }

    def __init__(self):
        self.command_docs = CommandDocumentation()
        self.permission_mgr = PermissionManager()
        self.system_info = SystemDetector.get_info()
        self._context: Dict[str, Any] = {
            "last_command": None,
            "last_directory": None,
            "conversation_history": [],
        }

    def parse(self, user_input: str, ai_client=None) -> ParsedIntent:
        user_input = user_input.strip()
        
        if not user_input:
            return ParsedIntent(intent_type=IntentType.UNKNOWN)
        
        self._context["conversation_history"].append({
            "role": "user",
            "content": user_input,
        })
        
        help_intent = self._try_parse_help(user_input)
        if help_intent:
            return help_intent
        
        cancel_intent = self._try_parse_cancel(user_input)
        if cancel_intent:
            return cancel_intent
        
        confirmation_intent = self._try_parse_confirmation(user_input)
        if confirmation_intent:
            return confirmation_intent
        
        direct_cmd = self._try_parse_direct_command(user_input)
        if direct_cmd:
            return direct_cmd
        
        natural_intent = self._try_parse_natural_language(user_input)
        if natural_intent:
            return natural_intent
        
        if ai_client:
            ai_intent = self._parse_with_ai(user_input, ai_client)
            if ai_intent:
                return ai_intent
        
        return ParsedIntent(
            intent_type=IntentType.UNKNOWN,
            response=self._get_unknown_response(),
            needs_clarification=True,
            clarification_question="I'm not sure what you mean. Could you rephrase that?"
        )

    def _try_parse_help(self, user_input: str) -> Optional[ParsedIntent]:
        for pattern in self.PATTERNS["help"]:
            if re.match(pattern, user_input, re.IGNORECASE):
                return ParsedIntent(
                    intent_type=IntentType.HELP,
                    response=self._generate_help_response(),
                )
        return None

    def _try_parse_cancel(self, user_input: str) -> Optional[ParsedIntent]:
        for pattern in self.PATTERNS["cancel"]:
            if re.match(pattern, user_input, re.IGNORECASE):
                return ParsedIntent(
                    intent_type=IntentType.CANCEL,
                    response="Cancelled.",
                )
        return None

    def _try_parse_confirmation(self, user_input: str) -> Optional[ParsedIntent]:
        lower_input = user_input.lower().strip()
        
        for conf_type, patterns in self.CONFIRMATION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, lower_input, re.IGNORECASE):
                    return ParsedIntent(
                        intent_type=IntentType.CLARIFICATION,
                        context={"confirmation_type": conf_type},
                    )
        return None

    def _try_parse_direct_command(self, user_input: str) -> Optional[ParsedIntent]:
        try:
            parts = shlex.split(user_input)
        except ValueError:
            parts = user_input.split()
        
        if not parts:
            return None
        
        cmd = parts[0]
        args = parts[1:]
        
        if self.command_docs.get_command(cmd):
            parsed_cmd = self._create_parsed_command(cmd, args, user_input)
            return ParsedIntent(
                intent_type=IntentType.COMMAND,
                commands=[parsed_cmd],
            )
        
        return None

    def _try_parse_natural_language(self, user_input: str) -> Optional[ParsedIntent]:
        lower_input = user_input.lower()
        
        for intent_name, patterns in self.PATTERNS.items():
            if intent_name in ("help", "cancel"):
                continue
            
            for pattern in patterns:
                match = re.match(pattern, lower_input, re.IGNORECASE)
                if match:
                    result = self._convert_to_command(intent_name, match.groups(), user_input)
                    if result:
                        return result
        
        return None

    def _convert_to_command(self, intent_name: str, captures: tuple, raw_input: str) -> Optional[ParsedIntent]:
        commands = []
        
        if intent_name == "list_files":
            path = captures[0].strip() if captures and captures[0] else "."
            path = self._clean_path(path)
            cmd = ParsedCommand(command="ls", args=[path], raw_input=raw_input, confidence=0.9)
            commands.append(cmd)
            
        elif intent_name == "change_dir":
            path = captures[0].strip() if captures else "~"
            path = self._clean_path(path)
            cmd = ParsedCommand(command="cd", args=[path], raw_input=raw_input, confidence=0.9)
            commands.append(cmd)
            
        elif intent_name == "create_directory":
            name = captures[0].strip() if captures else ""
            if name:
                cmd = ParsedCommand(command="mkdir", args=[name], raw_input=raw_input, confidence=0.9)
                commands.append(cmd)
                
        elif intent_name == "create_file":
            name = captures[0].strip() if captures else ""
            if name:
                cmd = ParsedCommand(command="touch", args=[name], raw_input=raw_input, confidence=0.9)
                commands.append(cmd)
                
        elif intent_name == "delete":
            target = captures[0].strip() if captures else ""
            if target:
                cmd = ParsedCommand(command="rm", args=["-r", target], raw_input=raw_input, confidence=0.85)
                commands.append(cmd)
                
        elif intent_name == "copy":
            if len(captures) >= 2:
                src = self._clean_path(captures[0].strip())
                dst = self._clean_path(captures[1].strip())
                cmd = ParsedCommand(command="cp", args=["-r", src, dst], raw_input=raw_input, confidence=0.9)
                commands.append(cmd)
                
        elif intent_name == "move":
            if len(captures) >= 2:
                src = self._clean_path(captures[0].strip())
                dst = self._clean_path(captures[1].strip())
                cmd = ParsedCommand(command="mv", args=[src, dst], raw_input=raw_input, confidence=0.9)
                commands.append(cmd)
                
        elif intent_name == "find":
            pattern = captures[0].strip() if captures else "*"
            cmd = ParsedCommand(command="find", args=[".", "-name", pattern], raw_input=raw_input, confidence=0.8)
            commands.append(cmd)
            
        elif intent_name == "grep":
            if len(captures) >= 2:
                pattern = captures[0].strip()
                file_path = self._clean_path(captures[1].strip())
                cmd = ParsedCommand(command="grep", args=[pattern, file_path], raw_input=raw_input, confidence=0.85)
                commands.append(cmd)
                
        elif intent_name == "show_content":
            file_path = captures[0].strip() if captures else ""
            if file_path:
                file_path = self._clean_path(file_path)
                cmd = ParsedCommand(command="cat", args=[file_path], raw_input=raw_input, confidence=0.9)
                commands.append(cmd)
                
        elif intent_name == "system_info":
            cmd = ParsedCommand(command="uname", args=["-a"], raw_input=raw_input, confidence=0.95)
            commands.append(cmd)
            
        elif intent_name == "disk_usage":
            args = []
            if captures and captures[0]:
                args = [self._clean_path(captures[0].strip())]
            cmd = ParsedCommand(command="df", args=["-h"] + args, raw_input=raw_input, confidence=0.9)
            commands.append(cmd)
            
        elif intent_name == "process_list":
            cmd = ParsedCommand(command="ps", args=["aux"], raw_input=raw_input, confidence=0.9)
            commands.append(cmd)
            
        elif intent_name == "kill_process":
            target = captures[0].strip() if captures else ""
            if target:
                if target.isdigit():
                    cmd = ParsedCommand(command="kill", args=[target], raw_input=raw_input, confidence=0.9)
                else:
                    cmd = ParsedCommand(command="killall", args=[target], raw_input=raw_input, confidence=0.85)
                commands.append(cmd)
        
        if commands:
            for cmd in commands:
                self._enrich_command(cmd)
            return ParsedIntent(
                intent_type=IntentType.COMMAND if len(commands) == 1 else IntentType.MULTI_COMMAND,
                commands=commands,
            )
        
        return None

    def _clean_path(self, path: str) -> str:
        path = path.strip()
        path = re.sub(r'^(?:the\s+)?(?:directory|folder|file)\s+', '', path, flags=re.IGNORECASE)
        path = re.sub(r'\s+(?:directory|folder|file)$', '', path, flags=re.IGNORECASE)
        
        path = path.strip('\'"')
        
        if path in ("here", "this directory", "current directory"):
            return "."
        if path in ("home", "~"):
            return "~"
        if path in ("up", "parent", "parent directory"):
            return ".."
        if path in ("root"):
            return "/"
        
        return path

    def _create_parsed_command(self, cmd: str, args: List[str], raw_input: str, 
                                 is_ai: bool = False) -> ParsedCommand:
        parsed = ParsedCommand(
            command=cmd,
            args=args,
            raw_input=raw_input,
            is_ai_generated=is_ai,
        )
        self._enrich_command(parsed)
        return parsed

    def _enrich_command(self, cmd: ParsedCommand):
        risk_level, risk_msg = self.permission_mgr.get_command_risk_level(cmd.command, cmd.args)
        cmd.risk_level = risk_level
        cmd.risk_message = risk_msg
        cmd.needs_confirmation = self.permission_mgr.needs_confirmation(cmd.command, cmd.args)

    def _parse_with_ai(self, user_input: str, ai_client) -> Optional[ParsedIntent]:
        system_prompt = self._build_ai_system_prompt()
        
        try:
            response = ai_client.generate(
                model=ai_client.default_model if hasattr(ai_client, 'default_model') else None,
                prompt=user_input,
                system=system_prompt,
            )
            
            if response:
                parsed = self._parse_ai_response(response, user_input)
                if parsed:
                    return parsed
        except Exception:
            pass
        
        return None

    def _build_ai_system_prompt(self) -> str:
        lines = [
            "You are a POSIX command interpreter. Convert natural language to shell commands.",
            "",
            "System information:",
            f"  OS: {self.system_info.os_name}",
            f"  Shell: {self.system_info.shell_type.value}",
            "",
            self.command_docs.get_system_prompt_context(),
            "",
            "Rules:",
            "1. Return ONLY valid shell commands, one per line.",
            "2. Use safe defaults for ambiguous requests.",
            "3. If unclear, respond with: CLARIFY: <question>",
            "4. For multiple operations, return multiple commands.",
            "",
            "Example inputs and outputs:",
            "  'list all python files' -> find . -name '*.py'",
            "  'delete old logs' -> CLARIFY: What is old? Specify days or date.",
            "  'backup my documents' -> tar -czf ~/backup.tar.gz ~/Documents",
        ]
        return "\n".join(lines)

    def _parse_ai_response(self, response: str, raw_input: str) -> Optional[ParsedIntent]:
        response = response.strip()
        
        if response.startswith("CLARIFY:"):
            question = response[8:].strip()
            return ParsedIntent(
                intent_type=IntentType.CLARIFICATION,
                needs_clarification=True,
                clarification_question=question,
            )
        
        commands = []
        for line in response.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            try:
                parts = shlex.split(line)
            except ValueError:
                parts = line.split()
            
            if parts:
                cmd = self._create_parsed_command(parts[0], parts[1:], raw_input, is_ai=True)
                commands.append(cmd)
        
        if commands:
            return ParsedIntent(
                intent_type=IntentType.COMMAND if len(commands) == 1 else IntentType.MULTI_COMMAND,
                commands=commands,
            )
        
        return None

    def _generate_help_response(self) -> str:
        lines = [
            "POSIX Compatibility Layer - Available Commands:",
            "",
        ]
        
        categories = {
            "File Operations": ["ls", "cd", "pwd", "mkdir", "touch", "rm", "cp", "mv", "cat", "head", "tail"],
            "Search": ["find", "grep"],
            "Text Processing": ["sort", "uniq", "wc", "echo"],
            "System Info": ["uname", "hostname", "whoami", "date", "uptime", "df", "du", "free"],
            "Process Management": ["ps", "kill", "killall"],
            "Archive": ["tar", "zip", "unzip"],
            "Permissions": ["chmod", "chown"],
            "Other": ["clear", "history", "env"],
        }
        
        for category, cmds in categories.items():
            lines.append(f"  {category}:")
            for cmd in cmds:
                doc = self.command_docs.get_command(cmd)
                if doc:
                    lines.append(f"    {cmd:12} - {doc.description}")
            lines.append("")
        
        lines.extend([
            "Natural Language Examples:",
            "  'list files in /home'         -> ls /home",
            "  'go to documents'              -> cd ~/Documents",
            "  'create a new folder called test' -> mkdir test",
            "  'find all python files'        -> find . -name '*.py'",
            "  'show disk usage'              -> df -h",
            "",
            "For more help on a specific command, type: man <command>",
        ])
        
        return "\n".join(lines)

    def _get_unknown_response(self) -> str:
        return "I couldn't understand that command. Type 'help' for available commands."

    def update_context(self, key: str, value: Any):
        self._context[key] = value

    def get_context(self, key: str, default=None) -> Any:
        return self._context.get(key, default)
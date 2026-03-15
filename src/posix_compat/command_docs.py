import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
from enum import Enum
from .system_detector import SystemDetector, OSType


class CommandCategory(Enum):
    FILE_OPS = "file_ops"
    DIRECTORY_OPS = "directory_ops"
    TEXT_PROCESSING = "text_processing"
    SYSTEM_INFO = "system_info"
    PROCESS_MGMT = "process_mgmt"
    NETWORK = "network"
    ARCHIVE = "archive"
    PERMISSION = "permission"
    SEARCH = "search"
    ENVIRONMENT = "environment"
    USER_MGMT = "user_mgmt"
    DISK_MGMT = "disk_mgmt"
    OTHER = "other"


class RiskLevel(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CommandArg:
    name: str
    description: str
    required: bool = False
    default: Optional[str] = None
    examples: List[str] = field(default_factory=list)


@dataclass
class CommandFlag:
    short: str
    long: Optional[str]
    description: str
    requires_value: bool = False


@dataclass
class CommandDoc:
    name: str
    description: str
    category: CommandCategory
    risk_level: RiskLevel
    args: List[CommandArg] = field(default_factory=list)
    flags: List[CommandFlag] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)
    os_specific: Dict[str, str] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)
    destructive: bool = False
    modifies_system: bool = False


class CommandDocumentation:
    _instance: Optional['CommandDocumentation'] = None
    _commands: Dict[str, CommandDoc] = {}
    _loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._loaded:
            self._load_builtin_commands()
            self._loaded = True

    def _load_builtin_commands(self):
        builtin_commands = [
            CommandDoc(
                name="ls",
                description="List directory contents",
                category=CommandCategory.DIRECTORY_OPS,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("path", "Directory path to list", default=".")
                ],
                flags=[
                    CommandFlag("-a", "--all", "Show hidden files"),
                    CommandFlag("-l", None, "Long format"),
                    CommandFlag("-h", "--human-readable", "Human readable sizes"),
                    CommandFlag("-R", "--recursive", "Recursive listing"),
                ],
                examples=["ls -la", "ls -la /home/user", "ls -R"],
                see_also=["dir", "find"],
            ),
            CommandDoc(
                name="cd",
                description="Change current directory",
                category=CommandCategory.DIRECTORY_OPS,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("path", "Target directory path", default="~")
                ],
                examples=["cd /home", "cd ..", "cd ~"],
                see_also=["pwd", "pushd", "popd"],
            ),
            CommandDoc(
                name="pwd",
                description="Print working directory",
                category=CommandCategory.DIRECTORY_OPS,
                risk_level=RiskLevel.SAFE,
                examples=["pwd", "pwd -P"],
            ),
            CommandDoc(
                name="mkdir",
                description="Create directories",
                category=CommandCategory.DIRECTORY_OPS,
                risk_level=RiskLevel.LOW,
                args=[
                    CommandArg("path", "Directory name(s) to create", required=True)
                ],
                flags=[
                    CommandFlag("-p", "--parents", "Create parent directories"),
                    CommandFlag("-v", "--verbose", "Verbose output"),
                ],
                examples=["mkdir newdir", "mkdir -p path/to/dir"],
                modifies_system=True,
            ),
            CommandDoc(
                name="rmdir",
                description="Remove empty directories",
                category=CommandCategory.DIRECTORY_OPS,
                risk_level=RiskLevel.MEDIUM,
                args=[
                    CommandArg("path", "Directory to remove", required=True)
                ],
                flags=[
                    CommandFlag("-p", "--parents", "Remove parent directories"),
                ],
                examples=["rmdir emptydir", "rmdir -p path/to/dir"],
                destructive=True,
                modifies_system=True,
            ),
            CommandDoc(
                name="rm",
                description="Remove files or directories",
                category=CommandCategory.FILE_OPS,
                risk_level=RiskLevel.HIGH,
                args=[
                    CommandArg("path", "File or directory to remove", required=True)
                ],
                flags=[
                    CommandFlag("-r", "--recursive", "Remove directories recursively"),
                    CommandFlag("-f", "--force", "Force removal"),
                    CommandFlag("-i", None, "Interactive mode"),
                    CommandFlag("-v", "--verbose", "Verbose output"),
                ],
                examples=["rm file.txt", "rm -rf directory", "rm -i *.txt"],
                destructive=True,
                modifies_system=True,
            ),
            CommandDoc(
                name="cp",
                description="Copy files or directories",
                category=CommandCategory.FILE_OPS,
                risk_level=RiskLevel.LOW,
                args=[
                    CommandArg("source", "Source file/directory", required=True),
                    CommandArg("dest", "Destination path", required=True),
                ],
                flags=[
                    CommandFlag("-r", "--recursive", "Copy directories recursively"),
                    CommandFlag("-f", "--force", "Force overwrite"),
                    CommandFlag("-i", None, "Interactive mode"),
                    CommandFlag("-v", "--verbose", "Verbose output"),
                    CommandFlag("-p", "--preserve", "Preserve attributes"),
                ],
                examples=["cp file1.txt file2.txt", "cp -r dir1 dir2"],
                modifies_system=True,
            ),
            CommandDoc(
                name="mv",
                description="Move or rename files",
                category=CommandCategory.FILE_OPS,
                risk_level=RiskLevel.MEDIUM,
                args=[
                    CommandArg("source", "Source file/directory", required=True),
                    CommandArg("dest", "Destination path", required=True),
                ],
                flags=[
                    CommandFlag("-f", "--force", "Force overwrite"),
                    CommandFlag("-i", None, "Interactive mode"),
                    CommandFlag("-v", "--verbose", "Verbose output"),
                ],
                examples=["mv old.txt new.txt", "mv file.txt /tmp/"],
                destructive=True,
                modifies_system=True,
            ),
            CommandDoc(
                name="cat",
                description="Concatenate and display file contents",
                category=CommandCategory.TEXT_PROCESSING,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("files", "File(s) to display", required=True)
                ],
                flags=[
                    CommandFlag("-n", "--number", "Number all lines"),
                    CommandFlag("-b", "--number-nonblank", "Number non-blank lines"),
                    CommandFlag("-s", "--squeeze-blank", "Squeeze blank lines"),
                ],
                examples=["cat file.txt", "cat -n file.txt", "cat file1 file2"],
            ),
            CommandDoc(
                name="head",
                description="Display first lines of files",
                category=CommandCategory.TEXT_PROCESSING,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("file", "File to display", required=True)
                ],
                flags=[
                    CommandFlag("-n", "--lines", "Number of lines", requires_value=True),
                    CommandFlag("-c", "--bytes", "Number of bytes", requires_value=True),
                ],
                examples=["head file.txt", "head -n 20 file.txt"],
            ),
            CommandDoc(
                name="tail",
                description="Display last lines of files",
                category=CommandCategory.TEXT_PROCESSING,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("file", "File to display", required=True)
                ],
                flags=[
                    CommandFlag("-n", "--lines", "Number of lines", requires_value=True),
                    CommandFlag("-f", "--follow", "Follow file updates"),
                    CommandFlag("-c", "--bytes", "Number of bytes", requires_value=True),
                ],
                examples=["tail file.txt", "tail -f /var/log/syslog"],
            ),
            CommandDoc(
                name="grep",
                description="Search text patterns",
                category=CommandCategory.SEARCH,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("pattern", "Pattern to search", required=True),
                    CommandArg("file", "File to search", required=True),
                ],
                flags=[
                    CommandFlag("-i", "--ignore-case", "Case insensitive"),
                    CommandFlag("-v", "--invert-match", "Invert match"),
                    CommandFlag("-r", "--recursive", "Recursive search"),
                    CommandFlag("-n", "--line-number", "Show line numbers"),
                    CommandFlag("-l", "--files-with-matches", "Only show filenames"),
                    CommandFlag("-c", "--count", "Count matches"),
                ],
                examples=["grep pattern file.txt", "grep -r 'TODO' src/"],
            ),
            CommandDoc(
                name="find",
                description="Search for files",
                category=CommandCategory.SEARCH,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("path", "Starting directory", default="."),
                ],
                flags=[
                    CommandFlag("-name", None, "Filename pattern", requires_value=True),
                    CommandFlag("-type", None, "File type (f,d,l)", requires_value=True),
                    CommandFlag("-size", None, "File size", requires_value=True),
                    CommandFlag("-mtime", None, "Modified time", requires_value=True),
                    CommandFlag("-exec", None, "Execute command", requires_value=True),
                ],
                examples=["find . -name '*.py'", "find /tmp -type f -mtime +7"],
            ),
            CommandDoc(
                name="chmod",
                description="Change file permissions",
                category=CommandCategory.PERMISSION,
                risk_level=RiskLevel.MEDIUM,
                args=[
                    CommandArg("mode", "Permission mode (e.g., 755)", required=True),
                    CommandArg("file", "File to modify", required=True),
                ],
                flags=[
                    CommandFlag("-R", "--recursive", "Apply recursively"),
                    CommandFlag("-v", "--verbose", "Verbose output"),
                ],
                examples=["chmod 755 script.sh", "chmod -R 644 *.txt"],
                modifies_system=True,
            ),
            CommandDoc(
                name="chown",
                description="Change file owner",
                category=CommandCategory.PERMISSION,
                risk_level=RiskLevel.HIGH,
                args=[
                    CommandArg("owner", "New owner", required=True),
                    CommandArg("file", "File to modify", required=True),
                ],
                flags=[
                    CommandFlag("-R", "--recursive", "Apply recursively"),
                ],
                examples=["chown user file.txt", "chown -R user:group dir/"],
                modifies_system=True,
            ),
            CommandDoc(
                name="ps",
                description="List processes",
                category=CommandCategory.PROCESS_MGMT,
                risk_level=RiskLevel.SAFE,
                flags=[
                    CommandFlag("-a", None, "All processes"),
                    CommandFlag("-u", None, "User-oriented format"),
                    CommandFlag("-x", None, "Include daemons"),
                    CommandFlag("-e", None, "All processes"),
                ],
                examples=["ps aux", "ps -ef"],
            ),
            CommandDoc(
                name="kill",
                description="Terminate processes",
                category=CommandCategory.PROCESS_MGMT,
                risk_level=RiskLevel.HIGH,
                args=[
                    CommandArg("pid", "Process ID", required=True),
                ],
                flags=[
                    CommandFlag("-9", None, "Force kill (SIGKILL)"),
                    CommandFlag("-l", None, "List signals"),
                ],
                examples=["kill 1234", "kill -9 1234"],
                destructive=True,
                modifies_system=True,
            ),
            CommandDoc(
                name="killall",
                description="Kill processes by name",
                category=CommandCategory.PROCESS_MGMT,
                risk_level=RiskLevel.HIGH,
                args=[
                    CommandArg("name", "Process name", required=True),
                ],
                examples=["killall firefox", "killall -9 python"],
                destructive=True,
                modifies_system=True,
            ),
            CommandDoc(
                name="top",
                description="Display system processes",
                category=CommandCategory.PROCESS_MGMT,
                risk_level=RiskLevel.SAFE,
                examples=["top", "top -u username"],
            ),
            CommandDoc(
                name="df",
                description="Disk space usage",
                category=CommandCategory.DISK_MGMT,
                risk_level=RiskLevel.SAFE,
                flags=[
                    CommandFlag("-h", "--human-readable", "Human readable sizes"),
                    CommandFlag("-T", "--print-type", "Show filesystem type"),
                    CommandFlag("-i", "--inodes", "Show inode info"),
                ],
                examples=["df -h", "df -T"],
            ),
            CommandDoc(
                name="du",
                description="Directory space usage",
                category=CommandCategory.DISK_MGMT,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("path", "Directory path", default="."),
                ],
                flags=[
                    CommandFlag("-h", "--human-readable", "Human readable sizes"),
                    CommandFlag("-s", "--summarize", "Summary only"),
                    CommandFlag("-d", "--max-depth", "Depth", requires_value=True),
                ],
                examples=["du -sh *", "du -h --max-depth=1"],
            ),
            CommandDoc(
                name="free",
                description="Memory usage",
                category=CommandCategory.SYSTEM_INFO,
                risk_level=RiskLevel.SAFE,
                flags=[
                    CommandFlag("-h", "--human", "Human readable"),
                    CommandFlag("-b/k/m/g", None, "Bytes/KB/MB/GB"),
                ],
                examples=["free -h"],
            ),
            CommandDoc(
                name="uname",
                description="System information",
                category=CommandCategory.SYSTEM_INFO,
                risk_level=RiskLevel.SAFE,
                flags=[
                    CommandFlag("-a", "--all", "All info"),
                    CommandFlag("-r", "--kernel-release", "Kernel release"),
                    CommandFlag("-m", "--machine", "Machine hardware"),
                ],
                examples=["uname -a", "uname -r"],
            ),
            CommandDoc(
                name="hostname",
                description="System hostname",
                category=CommandCategory.SYSTEM_INFO,
                risk_level=RiskLevel.SAFE,
                flags=[
                    CommandFlag("-I", None, "IP addresses"),
                    CommandFlag("-f", "--fqdn", "Full domain name"),
                ],
                examples=["hostname", "hostname -I"],
            ),
            CommandDoc(
                name="whoami",
                description="Current username",
                category=CommandCategory.USER_MGMT,
                risk_level=RiskLevel.SAFE,
                examples=["whoami"],
            ),
            CommandDoc(
                name="id",
                description="User/group IDs",
                category=CommandCategory.USER_MGMT,
                risk_level=RiskLevel.SAFE,
                flags=[
                    CommandFlag("-u", "--user", "User ID"),
                    CommandFlag("-g", "--group", "Group ID"),
                    CommandFlag("-G", "--groups", "All groups"),
                ],
                examples=["id", "id -u"],
            ),
            CommandDoc(
                name="env",
                description="Environment variables",
                category=CommandCategory.ENVIRONMENT,
                risk_level=RiskLevel.SAFE,
                examples=["env", "env | grep PATH"],
            ),
            CommandDoc(
                name="export",
                description="Set environment variable",
                category=CommandCategory.ENVIRONMENT,
                risk_level=RiskLevel.LOW,
                args=[
                    CommandArg("name", "Variable name", required=True),
                    CommandArg("value", "Variable value", required=True),
                ],
                examples=["export PATH=$PATH:/new/path"],
                modifies_system=True,
            ),
            CommandDoc(
                name="tar",
                description="Archive files",
                category=CommandCategory.ARCHIVE,
                risk_level=RiskLevel.LOW,
                flags=[
                    CommandFlag("-c", "--create", "Create archive"),
                    CommandFlag("-x", "--extract", "Extract archive"),
                    CommandFlag("-v", "--verbose", "Verbose"),
                    CommandFlag("-f", "--file", "Archive file", requires_value=True),
                    CommandFlag("-z", "--gzip", "Gzip compression"),
                    CommandFlag("-j", "--bzip2", "Bzip2 compression"),
                ],
                examples=["tar -czf archive.tar.gz dir/", "tar -xzf archive.tar.gz"],
                modifies_system=True,
            ),
            CommandDoc(
                name="zip",
                description="Create ZIP archives",
                category=CommandCategory.ARCHIVE,
                risk_level=RiskLevel.LOW,
                args=[
                    CommandArg("archive", "Archive name", required=True),
                    CommandArg("files", "Files to add", required=True),
                ],
                flags=[
                    CommandFlag("-r", None, "Recursive"),
                    CommandFlag("-q", None, "Quiet mode"),
                ],
                examples=["zip -r archive.zip dir/"],
                modifies_system=True,
            ),
            CommandDoc(
                name="unzip",
                description="Extract ZIP archives",
                category=CommandCategory.ARCHIVE,
                risk_level=RiskLevel.LOW,
                args=[
                    CommandArg("archive", "Archive to extract", required=True),
                ],
                flags=[
                    CommandFlag("-d", None, "Destination directory", requires_value=True),
                    CommandFlag("-l", None, "List contents"),
                ],
                examples=["unzip archive.zip", "unzip archive.zip -d /tmp/"],
                modifies_system=True,
            ),
            CommandDoc(
                name="touch",
                description="Create empty file or update timestamp",
                category=CommandCategory.FILE_OPS,
                risk_level=RiskLevel.LOW,
                args=[
                    CommandArg("file", "File to touch", required=True),
                ],
                examples=["touch newfile.txt", "touch -d '2024-01-01' file.txt"],
                modifies_system=True,
            ),
            CommandDoc(
                name="ln",
                description="Create links",
                category=CommandCategory.FILE_OPS,
                risk_level=RiskLevel.MEDIUM,
                args=[
                    CommandArg("target", "Target file", required=True),
                    CommandArg("link", "Link name", required=True),
                ],
                flags=[
                    CommandFlag("-s", "--symbolic", "Symbolic link"),
                    CommandFlag("-f", "--force", "Force overwrite"),
                ],
                examples=["ln -s /path/to/target linkname"],
                modifies_system=True,
            ),
            CommandDoc(
                name="echo",
                description="Display text",
                category=CommandCategory.TEXT_PROCESSING,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("text", "Text to display", default=""),
                ],
                flags=[
                    CommandFlag("-n", None, "No trailing newline"),
                    CommandFlag("-e", None, "Enable escapes"),
                ],
                examples=["echo 'Hello World'", "echo $PATH"],
            ),
            CommandDoc(
                name="wc",
                description="Count lines, words, bytes",
                category=CommandCategory.TEXT_PROCESSING,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("file", "File to count", required=True),
                ],
                flags=[
                    CommandFlag("-l", "--lines", "Lines"),
                    CommandFlag("-w", "--words", "Words"),
                    CommandFlag("-c", "--bytes", "Bytes"),
                    CommandFlag("-m", "--chars", "Characters"),
                ],
                examples=["wc -l file.txt", "wc -w *.txt"],
            ),
            CommandDoc(
                name="sort",
                description="Sort lines",
                category=CommandCategory.TEXT_PROCESSING,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("file", "File to sort", required=True),
                ],
                flags=[
                    CommandFlag("-r", "--reverse", "Reverse order"),
                    CommandFlag("-n", "--numeric-sort", "Numeric sort"),
                    CommandFlag("-u", "--unique", "Unique lines"),
                    CommandFlag("-k", "--key", "Sort by key", requires_value=True),
                ],
                examples=["sort file.txt", "sort -n -k2 data.txt"],
            ),
            CommandDoc(
                name="uniq",
                description="Filter duplicate lines",
                category=CommandCategory.TEXT_PROCESSING,
                risk_level=RiskLevel.SAFE,
                args=[
                    CommandArg("file", "File to process", required=True),
                ],
                flags=[
                    CommandFlag("-c", "--count", "Show counts"),
                    CommandFlag("-d", "--repeated", "Only duplicates"),
                    CommandFlag("-u", "--unique", "Only unique"),
                ],
                examples=["sort file.txt | uniq", "uniq -c file.txt"],
            ),
            CommandDoc(
                name="date",
                description="Display date/time",
                category=CommandCategory.SYSTEM_INFO,
                risk_level=RiskLevel.SAFE,
                flags=[
                    CommandFlag("+FORMAT", None, "Output format"),
                ],
                examples=["date", "date '+%Y-%m-%d %H:%M:%S'"],
            ),
            CommandDoc(
                name="uptime",
                description="System uptime",
                category=CommandCategory.SYSTEM_INFO,
                risk_level=RiskLevel.SAFE,
                flags=[
                    CommandFlag("-p", "--pretty", "Pretty format"),
                ],
                examples=["uptime", "uptime -p"],
            ),
            CommandDoc(
                name="lscpu",
                description="CPU information",
                category=CommandCategory.SYSTEM_INFO,
                risk_level=RiskLevel.SAFE,
                examples=["lscpu"],
            ),
            CommandDoc(
                name="clear",
                description="Clear terminal",
                category=CommandCategory.OTHER,
                risk_level=RiskLevel.SAFE,
                examples=["clear"],
            ),
            CommandDoc(
                name="history",
                description="Command history",
                category=CommandCategory.OTHER,
                risk_level=RiskLevel.SAFE,
                examples=["history", "history 20"],
            ),
        ]
        
        for cmd in builtin_commands:
            self._commands[cmd.name] = cmd
            for alias in cmd.aliases:
                self._commands[alias] = cmd

    def get_command(self, name: str) -> Optional[CommandDoc]:
        return self._commands.get(name)

    def get_all_commands(self) -> Dict[str, CommandDoc]:
        return self._commands.copy()

    def get_commands_by_category(self, category: CommandCategory) -> List[CommandDoc]:
        return [cmd for cmd in self._commands.values() if cmd.category == category]

    def get_commands_by_risk(self, risk: RiskLevel) -> List[CommandDoc]:
        return [cmd for cmd in self._commands.values() if cmd.risk_level == risk]

    def get_destructive_commands(self) -> List[str]:
        return [name for name, cmd in self._commands.items() if cmd.destructive]

    def search_commands(self, query: str) -> List[CommandDoc]:
        query_lower = query.lower()
        results = []
        seen = set()
        
        for name, cmd in self._commands.items():
            if name in seen:
                continue
            if query_lower in name.lower() or query_lower in cmd.description.lower():
                results.append(cmd)
                seen.add(name)
        
        return results

    def add_command(self, cmd: CommandDoc) -> None:
        self._commands[cmd.name] = cmd

    def to_json(self) -> str:
        data = {}
        for name, cmd in self._commands.items():
            if name not in data:
                data[name] = {
                    "name": cmd.name,
                    "description": cmd.description,
                    "category": cmd.category.value,
                    "risk_level": cmd.risk_level.value,
                    "destructive": cmd.destructive,
                    "modifies_system": cmd.modifies_system,
                    "args": [{"name": a.name, "description": a.description, "required": a.required} for a in cmd.args],
                    "flags": [{"short": f.short, "long": f.long, "description": f.description} for f in cmd.flags],
                    "examples": cmd.examples,
                }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_system_prompt_context(self) -> str:
        lines = ["Available POSIX commands:"]
        for name, cmd in sorted(self._commands.items()):
            if cmd.name == name:
                risk = f"[{cmd.risk_level.value.upper()}]"
                desc = cmd.description
                lines.append(f"  {name}: {risk} {desc}")
        
        lines.append("\nRisk levels: SAFE, LOW, MEDIUM, HIGH, CRITICAL")
        lines.append("Destructive commands require explicit confirmation.")
        
        return "\n".join(lines)
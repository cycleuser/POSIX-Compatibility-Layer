import argparse
import sys
import shlex
from typing import Optional, Tuple
from .core import CompatLayer, CommandRegistry
from .intent_parser import IntentParser, IntentType, ParsedCommand
from .permission_manager import PermissionManager, PermissionScope
from .ollama_client import OllamaClient
from .i18n import _
from .system_detector import SystemDetector


class ConfirmationDialog:
    @staticmethod
    def ask(command: str, args: list, risk_level: str, risk_message: str) -> Tuple[bool, PermissionScope]:
        print(f"\n{'='*50}")
        print(f"  Confirmation Required")
        print(f"{'='*50}")
        print(f"  Command: {command} {' '.join(args)}")
        print(f"  Risk Level: {risk_level.upper()}")
        if risk_message:
            print(f"  Warning: {risk_message}")
        print(f"{'='*50}")
        print()
        print("  [y] Yes, execute once")
        print("  [a] Always allow this command")
        print("  [s] Allow for this session")
        print("  [n] No, cancel")
        print("  [e] Explain this command")
        print()
        
        while True:
            try:
                choice = input("  Choice [y/a/s/n/e]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n  Cancelled.")
                return False, PermissionScope.NEVER
            
            if choice in ("y", "yes"):
                return True, PermissionScope.SESSION
            elif choice in ("a", "always"):
                return True, PermissionScope.ALWAYS
            elif choice in ("s", "session"):
                return True, PermissionScope.SESSION
            elif choice in ("n", "no", "cancel"):
                return False, PermissionScope.NEVER
            elif choice in ("e", "explain"):
                print(f"\n  Command explanation for '{command}':")
                doc = CommandRegistry.get_command(command) if hasattr(CommandRegistry, 'get_command_doc') else None
                if doc:
                    print(f"    {doc}")
                else:
                    print(f"    This command may modify or delete files.")
                print()


class POSIXShell:
    def __init__(self, use_ai: bool = True):
        self.compat = CompatLayer()
        self.intent_parser = IntentParser()
        self.permission_mgr = PermissionManager()
        self.ollama = OllamaClient() if use_ai else None
        self.system_info = SystemDetector.get_info()
        self._pending_commands: list = []
        self._waiting_for_confirmation: bool = False
        
        self._init_ai()

    def _init_ai(self):
        if self.ollama:
            models = self.ollama.get_models()
            if models:
                self.ollama.set_default_model(models[0])
                print(f"AI enabled with model: {models[0]}")
            else:
                print("AI features disabled (Ollama not running)")

    def run_interactive(self):
        print(_("repl_start"))
        print(f"System: {self.system_info.os_name}")
        print(f"Shell: {self.system_info.shell_type.value}")
        print("Type 'help' for commands, 'exit' to quit.")
        print()
        
        while True:
            try:
                cwd = self.compat.get_cwd()
                prompt = f"{cwd} $ "
                user_input = input(prompt)
                
                if not user_input.strip():
                    continue
                
                result = self.process_input(user_input)
                if result:
                    print(result)
                    
            except KeyboardInterrupt:
                print(f"\n{_('repl_start')}")
            except EOFError:
                break

    def process_input(self, user_input: str) -> Optional[str]:
        user_input = user_input.strip()
        
        if user_input.lower() in ("exit", "quit"):
            return None
        
        if user_input.lower() == "clear":
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            return ""
        
        if user_input.lower() == "help":
            return self._show_help()
        
        intent = self.intent_parser.parse(user_input, self.ollama)
        
        if intent.intent_type == IntentType.HELP:
            return intent.response
        
        if intent.intent_type == IntentType.CANCEL:
            self._pending_commands.clear()
            self._waiting_for_confirmation = False
            return "Cancelled."
        
        if intent.needs_clarification:
            return intent.clarification_question
        
        if intent.response and not intent.commands:
            return intent.response
        
        results = []
        for cmd in intent.commands:
            result = self._execute_command(cmd)
            results.append(result)
        
        return "\n".join(filter(None, results))

    def _execute_command(self, parsed_cmd: ParsedCommand) -> str:
        if parsed_cmd.needs_confirmation:
            approved, scope = ConfirmationDialog.ask(
                parsed_cmd.command,
                parsed_cmd.args,
                parsed_cmd.risk_level,
                parsed_cmd.risk_message or ""
            )
            
            if not approved:
                return "Command cancelled."
            
            if scope == PermissionScope.ALWAYS:
                self.permission_mgr.grant_permanent_approval(parsed_cmd.command, parsed_cmd.args)
            elif scope == PermissionScope.SESSION:
                self.permission_mgr.grant_session_approval(parsed_cmd.command, parsed_cmd.args)
        
        result = self.compat.execute(parsed_cmd.command, parsed_cmd.args)
        
        self.intent_parser.update_context("last_command", parsed_cmd.command)
        if parsed_cmd.command == "cd":
            self.intent_parser.update_context("last_directory", self.compat.cwd)
        
        return result

    def _show_help(self) -> str:
        registry = CommandRegistry.get_all_commands()
        lines = ["Available commands:", ""]
        
        for cmd_name in sorted(registry.keys()):
            help_key = registry[cmd_name].get("help_key", f"help_{cmd_name}")
            help_text = _(help_key)
            lines.append(f"  {cmd_name:12} - {help_text}")
        
        lines.extend([
            "",
            "Natural language examples:",
            "  'list files'              -> ls",
            "  'go to home'              -> cd ~",
            "  'create folder test'      -> mkdir test",
            "  'find all python files'   -> find . -name '*.py'",
            "",
            "Type 'man <command>' for detailed help.",
        ])
        
        return "\n".join(lines)


def main():
    if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    parser = argparse.ArgumentParser(
        description="POSIX Compatibility Layer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  posix-cli                   Start interactive shell
  posix-cli ls -la            List files
  posix-cli "find all py files"  Natural language command
        """
    )
    
    parser.add_argument("--no-ai", action="store_true", help="Disable AI features")
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Command arguments")
    
    args = parser.parse_args()
    
    shell = POSIXShell(use_ai=not args.no_ai)
    
    if args.command:
        result = shell.process_input(f"{args.command} {' '.join(args.args)}".strip())
        if result:
            print(result)
    else:
        shell.run_interactive()


if __name__ == "__main__":
    main()
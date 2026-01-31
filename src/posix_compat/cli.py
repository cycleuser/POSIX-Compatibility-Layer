import argparse
import sys
import shlex
from .core import CompatLayer, CommandRegistry
from .i18n import _

def main():
    # Ensure stdout handles unicode correctly on Windows legacy consoles
    if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    compat = CompatLayer()
    registry = CommandRegistry.get_all_commands()

    # Dynamic Parser Construction
    parser = argparse.ArgumentParser(description="POSIX Compatibility Layer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Automatically add subcommands based on registry
    # Note: argparse requires defining arguments upfront. 
    # To be truly dynamic with argparse, we'd need to inspect function signatures or define metadata.
    # For now, we will use a generic "args" collector for CLI mode, 
    # or rely on the REPL for flexible argument passing.
    
    # We will register known commands with a generic catch-all for arguments
    # to let the command handler parse them manually (like we did in core.py functions).
    
    for cmd_name, cmd_info in registry.items():
        sub = subparsers.add_parser(cmd_name, help=_(cmd_info["help_key"]))
        # Collect all remaining args as a list
        sub.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for command")

    # Check if arguments are provided
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if args.command:
            # Execute command
            result = compat.execute(args.command, args.args)
            print(result)
        else:
            parser.print_help()
    else:
        # Interactive mode
        print(_("repl_start"))
        while True:
            try:
                cwd = compat.get_cwd()
                user_input = input(f"{cwd} $ ")
                if not user_input.strip():
                    continue
                
                if user_input.strip() in ["exit", "quit"]:
                    break
                
                # Split input using shlex to handle quotes
                try:
                    split_args = shlex.split(user_input)
                except ValueError as e:
                    print(f"Error parsing input: {e}")
                    continue

                if not split_args:
                    continue

                cmd = split_args[0]
                params = split_args[1:]

                if cmd == "help":
                    print("Available commands: " + ", ".join(sorted(registry.keys())))
                elif cmd == "clear":
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                elif cmd == "exit":
                    break
                else:
                    # Execute via CompatLayer which uses Registry
                    result = compat.execute(cmd, params)
                    print(result)

            except KeyboardInterrupt:
                print(f"\n{_('repl_start')}")
            except EOFError:
                break

if __name__ == "__main__":
    main()

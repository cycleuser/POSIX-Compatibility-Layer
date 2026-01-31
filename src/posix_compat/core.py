import os
import shutil
import platform
import pathlib
import time
import glob
import re
import getpass
import datetime
import tarfile
import zipfile
import collections
import subprocess
from .i18n import _

class CommandRegistry:
    """
    Registry for all POSIX-compatible commands.
    """
    _commands = {}

    @classmethod
    def register(cls, name, help_key=None):
        def decorator(func):
            cls._commands[name] = {
                "func": func,
                "help_key": help_key or f"help_{name}",
                "name": name
            }
            return func
        return decorator

    @classmethod
    def get_command(cls, name):
        return cls._commands.get(name)

    @classmethod
    def get_all_commands(cls):
        return cls._commands

class CompatLayer:
    """
    A cross-platform compatibility layer implementing POSIX-style commands.
    Now uses CommandRegistry for dynamic dispatch.
    """

    def __init__(self):
        self.cwd = os.getcwd()
        self.env = os.environ.copy()

    def get_cwd(self):
        return self.cwd

    def execute(self, cmd_name, args):
        cmd_info = CommandRegistry.get_command(cmd_name)
        if not cmd_info:
            return f"{_('err_cmd_not_found')}: {cmd_name}"
        
        try:
            # Pass self (context) as first argument, then args
            return cmd_info["func"](self, args)
        except Exception as e:
            return f"{cmd_name}: error: {str(e)}"

# --- Existing Commands Migration ---

@CommandRegistry.register("ls", "help_ls")
def cmd_ls(ctx, args):
    path = "."
    show_hidden = False
    
    # Simple manual parsing to avoid argparse overhead for internal calls if needed,
    # but for consistency we'll just handle list of args
    if "-a" in args or "--all" in args:
        show_hidden = True
    
    # Filter flags
    clean_args = [a for a in args if not a.startswith("-")]
    if clean_args:
        path = clean_args[0]

    try:
        # Handle relative paths based on ctx.cwd
        if not os.path.isabs(path):
            target_path = pathlib.Path(ctx.cwd) / path
        else:
            target_path = pathlib.Path(path)
            
        target_path = target_path.resolve()
        
        if not target_path.exists():
            return f"ls: cannot access '{path}': {_('err_no_file')}"
        
        items = []
        if target_path.is_dir():
            for item in target_path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                suffix = "/" if item.is_dir() else ""
                items.append(f"{item.name}{suffix}")
            return "\n".join(sorted(items))
        else:
            return str(target_path.name)
    except Exception as e:
        return f"ls: error: {str(e)}"

@CommandRegistry.register("cd", "help_cd")
def cmd_cd(ctx, args):
    if not args:
        return f"cd: {_('err_missing_arg')}"
    
    path = args[0]
    try:
        if not os.path.isabs(path):
            target_path = os.path.abspath(os.path.join(ctx.cwd, os.path.expanduser(path)))
        else:
            target_path = os.path.abspath(os.path.expanduser(path))
            
        os.chdir(target_path)
        ctx.cwd = os.getcwd()
        return _("msg_changed_dir", ctx.cwd)
    except FileNotFoundError:
        return f"cd: {_('err_no_file')}: {path}"
    except NotADirectoryError:
        return f"cd: {_('err_not_dir')}: {path}"
    except PermissionError:
        return f"cd: {_('err_perm')}: {path}"

@CommandRegistry.register("pwd", "help_pwd")
def cmd_pwd(ctx, args):
    return ctx.cwd

@CommandRegistry.register("mkdir", "help_mkdir")
def cmd_mkdir(ctx, args):
    if not args:
        return f"mkdir: {_('err_missing_operand')}"
    
    path = args[0]
    try:
        if not os.path.isabs(path):
            target_path = os.path.join(ctx.cwd, path)
        else:
            target_path = path
            
        os.makedirs(target_path, exist_ok=True)
        return _("msg_created_dir", path)
    except Exception as e:
        return f"mkdir: {str(e)}"

@CommandRegistry.register("touch", "help_touch")
def cmd_touch(ctx, args):
    if not args:
        return f"touch: {_('err_missing_operand')}"
    
    path = args[0]
    try:
        if not os.path.isabs(path):
            target_path = os.path.join(ctx.cwd, path)
        else:
            target_path = path
            
        pathlib.Path(target_path).touch()
        return _("msg_touched", path)
    except Exception as e:
        return f"touch: {str(e)}"

@CommandRegistry.register("rm", "help_rm")
def cmd_rm(ctx, args):
    recursive = "-r" in args or "--recursive" in args
    clean_args = [a for a in args if not a.startswith("-")]
    
    if not clean_args:
        return f"rm: {_('err_missing_operand')}"
    
    path = clean_args[0]
    try:
        if not os.path.isabs(path):
            target_path = pathlib.Path(ctx.cwd) / path
        else:
            target_path = pathlib.Path(path)
            
        if not target_path.exists():
            return f"rm: cannot remove '{path}': {_('err_no_file')}"
        
        if target_path.is_dir():
            if recursive:
                shutil.rmtree(target_path)
                return _("msg_removed_dir", path)
            else:
                try:
                    target_path.rmdir()
                    return _("msg_removed_dir", path)
                except OSError:
                    return f"rm: cannot remove '{path}': {_('err_is_dir')} (use recursive)"
        else:
            target_path.unlink()
            return _("msg_removed_file", path)
    except Exception as e:
        return f"rm: error: {str(e)}"

@CommandRegistry.register("cp", "help_cp")
def cmd_cp(ctx, args):
    recursive = "-r" in args or "--recursive" in args
    clean_args = [a for a in args if not a.startswith("-")]
    
    if len(clean_args) < 2:
        return f"cp: {_('err_missing_operand')}"
    
    src = clean_args[0]
    dst = clean_args[1]
    
    try:
        # Resolve paths
        src_path = pathlib.Path(src) if os.path.isabs(src) else pathlib.Path(ctx.cwd) / src
        dst_path = pathlib.Path(dst) if os.path.isabs(dst) else pathlib.Path(ctx.cwd) / dst
        
        if not src_path.exists():
            return f"cp: cannot stat '{src}': {_('err_no_file')}"

        if src_path.is_dir():
            if recursive:
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                return _("msg_copied_dir", src, dst)
            else:
                return f"cp: -r not specified; omitting directory '{src}'"
        else:
            shutil.copy2(src_path, dst_path)
            return _("msg_copied_file", src, dst)
    except Exception as e:
        return f"cp: error: {str(e)}"

@CommandRegistry.register("mv", "help_mv")
def cmd_mv(ctx, args):
    if len(args) < 2:
        return f"mv: {_('err_missing_operand')}"
    
    src = args[0]
    dst = args[1]
    
    try:
        src_path = os.path.join(ctx.cwd, src) if not os.path.isabs(src) else src
        dst_path = os.path.join(ctx.cwd, dst) if not os.path.isabs(dst) else dst
        
        shutil.move(src_path, dst_path)
        return _("msg_moved", src, dst)
    except Exception as e:
        return f"mv: error: {str(e)}"

@CommandRegistry.register("cat", "help_cat")
def cmd_cat(ctx, args):
    if not args:
        return f"cat: {_('err_missing_arg')}"
    
    path = args[0]
    try:
        target_path = pathlib.Path(path) if os.path.isabs(path) else pathlib.Path(ctx.cwd) / path
        
        if not target_path.exists():
            return f"cat: {path}: {_('err_no_file')}"
        if target_path.is_dir():
            return f"cat: {path}: {_('err_is_dir')}"
        
        try:
            return target_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return f"cat: {path}: {_('err_binary')}"
    except Exception as e:
        return f"cat: error: {str(e)}"

@CommandRegistry.register("uname", "help_uname")
def cmd_uname(ctx, args):
    return (f"System: {platform.system()}\n"
            f"Node: {platform.node()}\n"
            f"Release: {platform.release()}\n"
            f"Version: {platform.version()}\n"
            f"Machine: {platform.machine()}\n"
            f"Processor: {platform.processor()}")

@CommandRegistry.register("find", "help_find")
def cmd_find(ctx, args):
    path = "."
    pattern = "*"
    
    clean_args = []
    i = 0
    while i < len(args):
        if args[i] == "-name":
            if i + 1 < len(args):
                pattern = args[i+1]
                i += 2
            else:
                i += 1
        else:
            clean_args.append(args[i])
            i += 1
            
    if clean_args:
        path = clean_args[0]
        
    try:
        matches = []
        base_path = pathlib.Path(path) if os.path.isabs(path) else pathlib.Path(ctx.cwd) / path
        
        if not base_path.exists():
            return f"find: '{path}': {_('err_no_file')}"
        
        for p in base_path.rglob(pattern):
            matches.append(str(p))
        
        if not matches:
            return ""
        return "\n".join(matches)
    except Exception as e:
        return f"find: error: {str(e)}"

# --- New Commands (Text Processing) ---

@CommandRegistry.register("grep", "help_grep")
def cmd_grep(ctx, args):
    if len(args) < 2:
        return "grep: missing pattern or file"
    
    pattern = args[0]
    file_path = args[1]
    
    try:
        target_path = pathlib.Path(file_path) if os.path.isabs(file_path) else pathlib.Path(ctx.cwd) / file_path
        if not target_path.exists():
            return f"grep: {file_path}: {_('err_no_file')}"
        
        content = target_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        
        matches = []
        regex = re.compile(pattern)
        
        for i, line in enumerate(lines):
            if regex.search(line):
                matches.append(f"{i+1}:{line}")
                
        return "\n".join(matches)
    except Exception as e:
        return f"grep: error: {str(e)}"

@CommandRegistry.register("head", "help_head")
def cmd_head(ctx, args):
    n = 10
    file_path = None
    
    i = 0
    while i < len(args):
        if args[i] == "-n" and i + 1 < len(args):
            try:
                n = int(args[i+1])
                i += 2
            except:
                return "head: invalid number of lines"
        else:
            file_path = args[i]
            i += 1
            
    if not file_path:
        return "head: missing file"
        
    try:
        target_path = pathlib.Path(file_path) if os.path.isabs(file_path) else pathlib.Path(ctx.cwd) / file_path
        if not target_path.exists():
            return f"head: {file_path}: {_('err_no_file')}"
            
        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [next(f) for _ in range(n)]
        return "".join(lines).rstrip()
    except StopIteration:
        return "" # File has fewer lines than n
    except Exception as e:
        return f"head: error: {str(e)}"

@CommandRegistry.register("tail", "help_tail")
def cmd_tail(ctx, args):
    n = 10
    file_path = None
    
    i = 0
    while i < len(args):
        if args[i] == "-n" and i + 1 < len(args):
            try:
                n = int(args[i+1])
                i += 2
            except:
                return "tail: invalid number of lines"
        else:
            file_path = args[i]
            i += 1
            
    if not file_path:
        return "tail: missing file"
        
    try:
        target_path = pathlib.Path(file_path) if os.path.isabs(file_path) else pathlib.Path(ctx.cwd) / file_path
        if not target_path.exists():
            return f"tail: {file_path}: {_('err_no_file')}"
            
        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return "".join(lines[-n:]).rstrip()
    except Exception as e:
        return f"tail: error: {str(e)}"

@CommandRegistry.register("wc", "help_wc")
def cmd_wc(ctx, args):
    if not args:
        return "wc: missing file"
    
    file_path = args[0]
    try:
        target_path = pathlib.Path(file_path) if os.path.isabs(file_path) else pathlib.Path(ctx.cwd) / file_path
        if not target_path.exists():
            return f"wc: {file_path}: {_('err_no_file')}"
            
        content = target_path.read_bytes()
        lines = content.split(b'\n')
        words = content.split()
        
        return f" {len(lines)}  {len(words)}  {len(content)} {file_path}"
    except Exception as e:
        return f"wc: error: {str(e)}"

@CommandRegistry.register("echo", "help_echo")
def cmd_echo(ctx, args):
    return " ".join(args)

@CommandRegistry.register("sort", "help_sort")
def cmd_sort(ctx, args):
    if not args:
        return "sort: missing file"
    
    reverse = "-r" in args
    clean_args = [a for a in args if not a.startswith("-")]
    
    if not clean_args:
        return "sort: missing file"
        
    file_path = clean_args[0]
    try:
        target_path = pathlib.Path(file_path) if os.path.isabs(file_path) else pathlib.Path(ctx.cwd) / file_path
        if not target_path.exists():
            return f"sort: {file_path}: {_('err_no_file')}"
            
        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            lines.sort(reverse=reverse)
            return "".join(lines).rstrip()
    except Exception as e:
        return f"sort: error: {str(e)}"

@CommandRegistry.register("uniq", "help_uniq")
def cmd_uniq(ctx, args):
    if not args:
        return "uniq: missing file"
        
    file_path = args[0]
    try:
        target_path = pathlib.Path(file_path) if os.path.isabs(file_path) else pathlib.Path(ctx.cwd) / file_path
        if not target_path.exists():
            return f"uniq: {file_path}: {_('err_no_file')}"
            
        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        if not lines:
            return ""
            
        result = [lines[0]]
        for i in range(1, len(lines)):
            if lines[i] != lines[i-1]:
                result.append(lines[i])
                
        return "".join(result).rstrip()
    except Exception as e:
        return f"uniq: error: {str(e)}"

# --- New Commands (System) ---

@CommandRegistry.register("whoami", "help_whoami")
def cmd_whoami(ctx, args):
    return getpass.getuser()

@CommandRegistry.register("date", "help_date")
def cmd_date(ctx, args):
    return str(datetime.datetime.now())

@CommandRegistry.register("env", "help_env")
def cmd_env(ctx, args):
    return "\n".join([f"{k}={v}" for k, v in os.environ.items()])

@CommandRegistry.register("du", "help_du")
def cmd_du(ctx, args):
    path = "."
    if args:
        path = args[0]
        
    try:
        target_path = pathlib.Path(path) if os.path.isabs(path) else pathlib.Path(ctx.cwd) / path
        total_size = 0
        if target_path.is_file():
            total_size = target_path.stat().st_size
        else:
            for dirpath, _, filenames in os.walk(target_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
        return f"{total_size}\t{path}"
    except Exception as e:
        return f"du: error: {str(e)}"

@CommandRegistry.register("uptime", "help_uptime")
def cmd_uptime(ctx, args):
    # Cross-platform way to get uptime is tricky without external libs.
    # We can use psutil if allowed, but we are sticking to stdlib.
    # On Linux/macOS we can read /proc/uptime or sysctl.
    # On Windows we can use ctypes GetTickCount64.
    
    try:
        if platform.system() == 'Windows':
            import ctypes
            uptime_ms = ctypes.windll.kernel32.GetTickCount64()
            uptime_sec = uptime_ms / 1000
        else:
            with open('/proc/uptime', 'r') as f:
                uptime_sec = float(f.readline().split()[0])
    except:
        # Fallback
        return "uptime: not available"
        
    return str(datetime.timedelta(seconds=uptime_sec))

@CommandRegistry.register("hostname", "help_hostname")
def cmd_hostname(ctx, args):
    return platform.node()

@CommandRegistry.register("lscpu", "help_lscpu")
def cmd_lscpu(ctx, args):
    info = []
    info.append(f"Architecture:        {platform.machine()}")
    info.append(f"CPU op-mode(s):      32-bit, 64-bit")
    # sys is needed here
    import sys
    info.append(f"Byte Order:          {sys.byteorder.title()}Endian")
    info.append(f"CPU(s):              {os.cpu_count()}")
    info.append(f"Vendor ID:           {platform.processor()}")
    
    # Try to get more detailed info on Windows
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("wmic cpu get Name,MaxClockSpeed /format:list", shell=True).decode()
            for line in output.splitlines():
                if line.strip():
                    info.append(f"  {line.strip()}")
        except:
            pass
            
    return "\n".join(info)

@CommandRegistry.register("lspci", "help_lspci")
def cmd_lspci(ctx, args):
    if platform.system() == "Windows":
        try:
            # Try PowerShell if wmic fails
            cmd = "powershell -Command \"Get-PnpDevice | Where-Object { $_.InstanceId -like '*PCI*' } | Select-Object -Property FriendlyName, InstanceId | Format-Table -HideTableHeaders\""
            output = subprocess.check_output(cmd, shell=True).decode(errors='ignore')
            if not output.strip():
                 return "No PCI devices found."
            return output.strip()
        except Exception as e:
            return f"lspci: error getting info: {e} (Note: wmic/powershell required)"
    else:
        # Linux/Mac fallback - usually lspci is installed, but if we are simulating...
        # We can try to read /sys/bus/pci/devices if on Linux
        return "lspci: Not fully implemented for non-Windows (try real 'lspci')"

@CommandRegistry.register("lsusb", "help_lsusb")
def cmd_lsusb(ctx, args):
    if platform.system() == "Windows":
        try:
            cmd = "powershell -Command \"Get-PnpDevice | Where-Object { $_.InstanceId -like '*USB*' } | Select-Object -Property FriendlyName, InstanceId | Format-Table -HideTableHeaders\""
            output = subprocess.check_output(cmd, shell=True).decode(errors='ignore')
            if not output.strip():
                 return "No USB devices found."
            return output.strip()
        except Exception as e:
            return f"lsusb: error: {e} (Note: wmic/powershell required)"
    return "lsusb: Not available"

@CommandRegistry.register("free", "help_free")
def cmd_free(ctx, args):
    # Try to provide memory info
    try:
        import psutil
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        header = f"{'':>10} {'total':>10} {'used':>10} {'free':>10} {'shared':>10} {'buff/cache':>10} {'available':>10}"
        mem_row = f"{'Mem:':>10} {vm.total//1024:>10} {vm.used//1024:>10} {vm.free//1024:>10} {0:>10} {0:>10} {vm.available//1024:>10}"
        swap_row = f"{'Swap:':>10} {swap.total//1024:>10} {swap.used//1024:>10} {swap.free//1024:>10}"
        return f"{header}\n{mem_row}\n{swap_row}"
    except ImportError:
        # Fallback without psutil
        if platform.system() == "Windows":
             try:
                 output = subprocess.check_output("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value", shell=True).decode()
                 info = {}
                 for line in output.splitlines():
                     if "=" in line:
                         k, v = line.split("=", 1)
                         info[k.strip()] = v.strip()
                 
                 total = int(info.get('TotalVisibleMemorySize', 0))
                 free = int(info.get('FreePhysicalMemory', 0))
                 used = total - free
                 
                 header = f"{'':>10} {'total':>10} {'used':>10} {'free':>10}"
                 mem_row = f"{'Mem:':>10} {total:>10} {used:>10} {free:>10}"
                 return f"{header}\n{mem_row}\n(Install 'psutil' for detailed info)"
             except:
                 return "free: unavailable (install psutil)"
        else:
            return "free: unavailable (install psutil)"

@CommandRegistry.register("df", "help_df")
def cmd_df(ctx, args):
    path = "."
    if args:
        path = args[0]
    
    try:
        target_path = path if os.path.isabs(path) else os.path.join(ctx.cwd, path)
        # Check if path exists or use cwd
        if not os.path.exists(target_path):
            target_path = ctx.cwd
            
        total, used, free = shutil.disk_usage(target_path)
        
        header = f"{'Filesystem':<15} {'1K-blocks':>12} {'Used':>12} {'Available':>12} {'Use%':>5} {'Mounted on'}"
        
        # 1K blocks
        total_k = total // 1024
        used_k = used // 1024
        free_k = free // 1024
        percent = int((used / total) * 100) if total > 0 else 0
        
        drive = os.path.splitdrive(os.path.abspath(target_path))[0] or "/"
        
        return f"{header}\n{drive:<15} {total_k:>12} {used_k:>12} {free_k:>12} {percent:>4}% {target_path}"
    except Exception as e:
        return f"df: error: {str(e)}"

# --- New Commands (Archive/File) ---

@CommandRegistry.register("chmod", "help_chmod")
def cmd_chmod(ctx, args):
    if len(args) < 2:
        return "chmod: missing mode or file"
        
    mode_str = args[0] # Octal assumed e.g. 755
    file_path = args[1]
    
    try:
        target_path = pathlib.Path(file_path) if os.path.isabs(file_path) else pathlib.Path(ctx.cwd) / file_path
        mode = int(mode_str, 8)
        os.chmod(target_path, mode)
        return f"Changed mode of {file_path} to {mode_str}"
    except Exception as e:
        return f"chmod: error: {str(e)}"

@CommandRegistry.register("tar", "help_tar")
def cmd_tar(ctx, args):
    # Minimal implementation: tar -cvf out.tar input_dir or tar -xvf in.tar
    if len(args) < 2:
        return "tar: missing arguments"
        
    mode = "r"
    filename = ""
    source = ""
    
    if args[0] == "-cvf":
        mode = "w"
        filename = args[1]
        if len(args) > 2:
            source = args[2]
    elif args[0] == "-xvf":
        mode = "r"
        filename = args[1]
    else:
        return "tar: only -cvf and -xvf supported"
        
    try:
        target_file = pathlib.Path(filename) if os.path.isabs(filename) else pathlib.Path(ctx.cwd) / filename
        
        if mode == "w":
            source_path = pathlib.Path(source) if os.path.isabs(source) else pathlib.Path(ctx.cwd) / source
            with tarfile.open(target_file, "w") as tar:
                tar.add(source_path, arcname=source_path.name)
            return f"Created archive {filename}"
        else:
            with tarfile.open(target_file, "r") as tar:
                tar.extractall(path=ctx.cwd)
            return f"Extracted archive {filename}"
            
    except Exception as e:
        return f"tar: error: {str(e)}"

@CommandRegistry.register("zip", "help_zip")
def cmd_zip(ctx, args):
    # zip out.zip input_dir
    if len(args) < 2:
        return "zip: missing arguments"
        
    zip_name = args[0]
    source = args[1]
    
    try:
        target_file = pathlib.Path(zip_name) if os.path.isabs(zip_name) else pathlib.Path(ctx.cwd) / zip_name
        source_path = pathlib.Path(source) if os.path.isabs(source) else pathlib.Path(ctx.cwd) / source
        
        with zipfile.ZipFile(target_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if source_path.is_dir():
                for root, _, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_path.parent)
                        zipf.write(file_path, arcname)
            else:
                zipf.write(source_path, arcname=source_path.name)
        return f"Created zip {zip_name}"
    except Exception as e:
        return f"zip: error: {str(e)}"

# --- New Commands (Process) ---

@CommandRegistry.register("ps", "help_ps")
def cmd_ps(ctx, args):
    # Try to use psutil if available
    try:
        import psutil
        header = f"{'PID':<8} {'USER':<12} {'STATUS':<10} {'NAME'}"
        rows = [header]
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
            try:
                info = proc.info
                rows.append(f"{info['pid']:<8} {str(info['username'])[:12]:<12} {info['status']:<10} {info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return "\n".join(rows)
    except ImportError:
        # Fallback to system commands
        if platform.system() == "Windows":
             try:
                 # tasklist is standard on Windows
                 return subprocess.check_output("tasklist", shell=True).decode()
             except Exception as e:
                 return f"ps: tasklist failed: {e}"
        else:
             try:
                 return subprocess.check_output(["ps", "aux"]).decode()
             except:
                 return "ps: not available (install psutil)"

@CommandRegistry.register("kill", "help_kill")
def cmd_kill(ctx, args):
    if not args:
        return "kill: missing PID"
    
    try:
        pid = int(args[0])
        # Try os.kill (works on Unix and Windows for SIGTERM/SIGKILL equivalent)
        import signal
        
        # Windows only supports signal.SIGTERM (15) and signal.CTRL_C_EVENT etc.
        # But os.kill(pid, signal.SIGTERM) works on Windows to terminate.
        
        os.kill(pid, signal.SIGTERM)
        return f"Sent SIGTERM to process {pid}"
    except ValueError:
        return "kill: PID must be an integer"
    except ProcessLookupError:
        return f"kill: PID {pid} not found"
    except PermissionError:
        return f"kill: Permission denied for PID {pid}"
    except Exception as e:
        return f"kill: error: {str(e)}"

@CommandRegistry.register("who", "help_who")
def cmd_who(ctx, args):
    # who is similar to whoami but shows login info.
    # We'll just show current user and time for now as a simple approximation
    user = getpass.getuser()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # In a real shell 'who' shows tty, we don't have that easily without psutil/w
    return f"{user:<10} tty1         {ts}"

import tkinter as tk
from tkinter import scrolledtext, font, Menu, messagebox
from tkinter import ttk
import shlex
import threading
import queue
from typing import Optional, Tuple
from .core import CompatLayer, CommandRegistry
from .ollama_client import OllamaClient
from .intent_parser import IntentParser, IntentType, ParsedCommand
from .permission_manager import PermissionManager, PermissionScope
from . import i18n
from .i18n import _
from .system_detector import SystemDetector


class ConfirmationDialog(tk.Toplevel):
    def __init__(self, parent, command: str, args: list, risk_level: str, risk_message: str):
        super().__init__(parent)
        self.title(_("gui_confirm_title") or "Confirmation Required")
        self.result: Optional[Tuple[bool, PermissionScope]] = None
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets(command, args, risk_level, risk_message)
        self._center_window()
        
    def _create_widgets(self, command: str, args: list, risk_level: str, risk_message: str):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(frame, text=_("gui_confirm_title") or "Confirmation Required", 
                                font=("", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        info_frame = ttk.LabelFrame(frame, padding=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text=f"Command: {command} {' '.join(args)}", 
                  font=("", 10)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Risk Level: {risk_level.upper()}", 
                  font=("", 10, "bold")).pack(anchor=tk.W)
        if risk_message:
            ttk.Label(info_frame, text=f"Warning: {risk_message}", 
                      wraplength=400, font=("", 9)).pack(anchor=tk.W, pady=(5, 0))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text=_("gui_btn_once") or "Once", width=12,
                   command=lambda: self._respond(True, PermissionScope.SESSION)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=_("gui_btn_always") or "Always", width=12,
                   command=lambda: self._respond(True, PermissionScope.ALWAYS)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=_("gui_btn_session") or "Session", width=12,
                   command=lambda: self._respond(True, PermissionScope.SESSION)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=_("gui_btn_cancel") or "Cancel", width=12,
                   command=lambda: self._respond(False, PermissionScope.NEVER)).pack(side=tk.LEFT, padx=5)
        
        self.protocol("WM_DELETE_WINDOW", lambda: self._respond(False, PermissionScope.NEVER))
    
    def _respond(self, approved: bool, scope: PermissionScope):
        self.result = (approved, scope)
        self.destroy()
    
    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")


class CompatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(_("gui_title"))
        self.root.geometry("1000x700")
        
        self.compat = CompatLayer()
        self.registry = CommandRegistry.get_all_commands()
        self.ollama_client = OllamaClient()
        self.intent_parser = IntentParser()
        self.permission_mgr = PermissionManager()
        self.system_info = SystemDetector.get_info()
        
        self.result_queue = queue.Queue()
        self.is_running = False
        self._pending_command: Optional[ParsedCommand] = None
        
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.entry_bg = "#2d2d2d"
        self.button_bg = "#3c3c3c"
        
        self.root.configure(bg=self.bg_color)
        
        self.create_menu()
        self.create_widgets()
        
        self.update_ui_text()
        self.update_status()
        
        self.check_queue()

    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        self.lang_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("menu_lang"), menu=self.lang_menu)
        
        available_langs = i18n.get_available_languages()
        for code, name in available_langs:
            self.lang_menu.add_command(label=name, command=lambda c=code: self.change_language(c))
        
        self.settings_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("menu_settings") or "Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label=_("menu_reset_perms") or "Reset Permissions", 
                                        command=self._reset_permissions)

    def change_language(self, lang_code):
        i18n.set_language(lang_code)
        self.update_ui_text()
        
    def _reset_permissions(self):
        self.permission_mgr.reset_all_permissions()
        messagebox.showinfo("Permissions", _("msg_perms_reset") or "All permissions have been reset.")

    def update_ui_text(self):
        self.root.title(_("gui_title"))
        
        try:
            self.create_menu()
        except:
            pass

        self.status_bar.config(text=_("gui_curr_dir", self.compat.get_cwd()))
        
        try:
            self.lbl_model.config(text=_("gui_lbl_model"))
            self.btn_refresh.config(text=_("gui_btn_refresh"))
            self.btn_ask.config(text=_("gui_btn_ask_ai"))
            self.btn_suggest.config(text=_("gui_btn_ai_suggest"))
        except:
            pass

        for widget in self.btn_container.winfo_children():
            widget.destroy()
            
        priority_cmds = ["ls", "pwd", "cd", "mkdir", "clear", "help"]
        for cmd in priority_cmds:
            text = cmd
            if cmd == "clear": text = _("gui_btn_clear")
            elif cmd == "help": text = _("gui_btn_help")
            elif cmd == "ls": text = _("gui_btn_ls")
            elif cmd == "pwd": text = _("gui_btn_pwd")
            elif cmd == "uname": text = _("gui_btn_uname")
                
            btn = tk.Button(
                self.btn_container, 
                text=text, 
                command=lambda c=cmd: self.run_command(c),
                bg=self.button_bg,
                fg=self.fg_color,
                relief=tk.FLAT,
                padx=10
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))

    def create_widgets(self):
        self.output_area = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            bg=self.bg_color, 
            fg=self.fg_color,
            font=("Consolas", 10),
            insertbackground="white",
            state='disabled'
        )
        self.output_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        input_frame = tk.Frame(self.root, bg=self.bg_color)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.prompt_label = tk.Label(
            input_frame, 
            text="$", 
            bg=self.bg_color, 
            fg="#00ff00",
            font=("Consolas", 12, "bold")
        )
        self.prompt_label.pack(side=tk.LEFT)
        
        self.command_entry = tk.Entry(
            input_frame, 
            bg=self.entry_bg, 
            fg=self.fg_color,
            insertbackground="white",
            font=("Consolas", 12),
            relief=tk.FLAT
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.command_entry.bind("<Return>", self.process_command)
        self.command_entry.focus_set()

        self.btn_container = tk.Frame(self.root, bg=self.bg_color)
        self.btn_container.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.create_ai_panel()
        
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        
        self.status_bar = tk.Label(
            self.root, 
            text="Ready", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            bg=self.button_bg,
            fg=self.fg_color
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_ai_panel(self):
        self.ai_container = tk.Frame(self.root, bg=self.bg_color)
        self.ai_container.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.lbl_model = tk.Label(self.ai_container, text=_("gui_lbl_model"), bg=self.bg_color, fg=self.fg_color)
        self.lbl_model.pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_var = tk.StringVar()
        self.combo_model = ttk.Combobox(self.ai_container, textvariable=self.model_var, state="readonly", width=20)
        self.combo_model.pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_refresh = tk.Button(self.ai_container, text=_("gui_btn_refresh"), command=self.refresh_models,
                                     bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT)
        self.btn_refresh.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_ask = tk.Button(self.ai_container, text=_("gui_btn_ask_ai"), command=self.ask_ai,
                                 bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT)
        self.btn_ask.pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_suggest = tk.Button(self.ai_container, text=_("gui_btn_ai_suggest"), command=self.ai_suggest,
                                     bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT)
        self.btn_suggest.pack(side=tk.LEFT)

        self.root.after(500, self.refresh_models)

    def refresh_models(self):
        self.log_output("Fetching local models...\n")
        threading.Thread(target=self._fetch_models_thread, daemon=True).start()

    def _fetch_models_thread(self):
        models = self.ollama_client.get_models()
        self.result_queue.put(("models", models))

    def ask_ai(self):
        prompt = self.command_entry.get()
        if not prompt.strip():
            return
        
        model = self.model_var.get()
        if not model:
            self.log_output("Error: No model selected.\n")
            return

        self.command_entry.delete(0, tk.END)
        self.log_output(f"AI ({model}) > {prompt}\n")
        self.log_output(_("msg_ai_thinking") + "\n")
        
        self.start_ai_execution("chat", model, prompt)

    def ai_suggest(self):
        prompt = self.command_entry.get()
        if not prompt.strip():
            return

        model = self.model_var.get()
        if not model:
            self.log_output("Error: No model selected.\n")
            return
            
        self.log_output(f"AI Suggest ({model}) > {prompt}\n")
        self.log_output(_("msg_ai_thinking") + "\n")
        
        system_prompt = "You are a command line assistant. Return ONLY the POSIX command to execute based on the user request. Do not include markdown code blocks or explanations. Just the command."
        self.start_ai_execution("suggest", model, prompt, system_prompt)

    def start_ai_execution(self, mode, model, prompt, system=None):
        self.is_running = True
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.progress.start(10)
        self.command_entry.config(state='disabled')
        
        threading.Thread(target=self._ai_thread, args=(mode, model, prompt, system), daemon=True).start()

    def _ai_thread(self, mode, model, prompt, system):
        try:
            response = self.ollama_client.generate(model, prompt, system)
            self.result_queue.put(("ai_result", (mode, response)))
        except Exception as e:
            self.result_queue.put(("error", str(e)))
        finally:
            self.result_queue.put(("done", None))

    def process_command(self, event=None):
        if self.is_running:
            return
            
        cmd_text = self.command_entry.get()
        if not cmd_text.strip():
            return
        
        self.command_entry.delete(0, tk.END)
        self.run_command(cmd_text)

    def run_command(self, cmd_text):
        if self.is_running:
            return

        if cmd_text == "clear":
            self.output_area.config(state='normal')
            self.output_area.delete(1.0, tk.END)
            self.output_area.config(state='disabled')
            return
        
        if cmd_text == "exit":
            self.root.quit()
            return
            
        if cmd_text == "help":
             self.log_output("$ help\n")
             self.log_output("Available commands: " + ", ".join(sorted(self.registry.keys())) + "\n")
             self.log_output("\nNatural language examples:\n")
             self.log_output("  'list files' -> ls\n")
             self.log_output("  'go to home' -> cd ~\n")
             return

        self.log_output(f"$ {cmd_text}\n")
        
        try:
            intent = self.intent_parser.parse(cmd_text, self.ollama_client if self.ollama_client.is_available() else None)
            
            if intent.intent_type == IntentType.HELP:
                self.log_output(intent.response + "\n")
                return
            
            if intent.needs_clarification:
                self.log_output(intent.clarification_question + "\n")
                return
            
            if intent.response and not intent.commands:
                self.log_output(intent.response + "\n")
                return
            
            for parsed_cmd in intent.commands:
                self._execute_with_confirmation(parsed_cmd)
                
        except Exception as e:
            self.log_output(f"Error: {str(e)}\n")

    def _execute_with_confirmation(self, parsed_cmd: ParsedCommand):
        if parsed_cmd.needs_confirmation:
            dialog = ConfirmationDialog(
                self.root,
                parsed_cmd.command,
                parsed_cmd.args,
                parsed_cmd.risk_level,
                parsed_cmd.risk_message or ""
            )
            
            self.root.wait_window(dialog)
            
            if dialog.result:
                approved, scope = dialog.result
                if not approved:
                    self.log_output("Command cancelled.\n")
                    return
                
                if scope == PermissionScope.ALWAYS:
                    self.permission_mgr.grant_permanent_approval(parsed_cmd.command, parsed_cmd.args)
                elif scope == PermissionScope.SESSION:
                    self.permission_mgr.grant_session_approval(parsed_cmd.command, parsed_cmd.args)
        
        self.start_async_execution(parsed_cmd.command, parsed_cmd.args)

    def start_async_execution(self, cmd, params):
        self.is_running = True
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.progress.start(10)
        self.command_entry.config(state='disabled')
        
        thread = threading.Thread(target=self._execute_thread, args=(cmd, params))
        thread.daemon = True
        thread.start()

    def _execute_thread(self, cmd, params):
        try:
            result = self.compat.execute(cmd, params)
            self.result_queue.put(("result", result))
            if cmd == "cd":
                self.result_queue.put(("update_status", None))
        except Exception as e:
            self.result_queue.put(("error", str(e)))
        finally:
            self.result_queue.put(("done", None))

    def check_queue(self):
        try:
            while True:
                msg_type, data = self.result_queue.get_nowait()
                
                if msg_type == "result":
                    if data:
                        self.log_output(str(data) + "\n")
                elif msg_type == "error":
                    self.log_output(f"Error: {data}\n")
                elif msg_type == "update_status":
                    self.update_status()
                elif msg_type == "models":
                    if data:
                        self.combo_model['values'] = data
                        self.combo_model.current(0)
                        self.log_output(f"Found {len(data)} models.\n")
                    else:
                        self.log_output(_("err_ollama_not_found") + "\n")
                elif msg_type == "ai_result":
                    mode, response = data
                    if mode == "chat":
                        self.log_output(f"{response}\n\n")
                    elif mode == "suggest":
                        self.command_entry.delete(0, tk.END)
                        self.command_entry.insert(0, response.strip())
                        self.log_output("Suggestion inserted into input.\n")
                elif msg_type == "done":
                    self.is_running = False
                    self.progress.stop()
                    self.progress.pack_forget()
                    self.command_entry.config(state='normal')
                    self.command_entry.focus_set()
                    
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_queue)

    def log_output(self, text):
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, text)
        self.output_area.see(tk.END)
        self.output_area.config(state='disabled')

    def update_status(self):
        self.status_bar.config(text=_("gui_curr_dir", self.compat.get_cwd()))

def main():
    root = tk.Tk()
    app = CompatGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
import tkinter as tk
from tkinter import scrolledtext, font, Menu
from tkinter import ttk
import shlex
import threading
import queue
from .core import CompatLayer, CommandRegistry
from .ollama_client import OllamaClient
from . import i18n
from .i18n import _

class CompatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(_("gui_title"))
        self.root.geometry("900x600")
        
        self.compat = CompatLayer()
        self.registry = CommandRegistry.get_all_commands()
        self.ollama_client = OllamaClient()
        
        # Thread communication
        self.result_queue = queue.Queue()
        self.is_running = False
        
        # Configure style
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.entry_bg = "#2d2d2d"
        self.button_bg = "#3c3c3c"
        
        self.root.configure(bg=self.bg_color)
        
        # Setup Menu
        self.create_menu()
        
        # Main Layout
        self.create_widgets()
        
        # Initial Text Update
        self.update_ui_text()
        self.update_status()
        
        # Start queue checker
        self.check_queue()

    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # Language Menu
        self.lang_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("menu_lang"), menu=self.lang_menu)
        
        # Add languages dynamically
        available_langs = i18n.get_available_languages()
        for code, name in available_langs:
            self.lang_menu.add_command(label=name, command=lambda c=code: self.change_language(c))

    def change_language(self, lang_code):
        i18n.set_language(lang_code)
        self.update_ui_text()
        
    def update_ui_text(self):
        """Update all static text elements based on current language."""
        self.root.title(_("gui_title"))
        
        # Update Menu Label (Trickier in Tkinter, usually needs recreation or index access)
        # Simplified: Just update the menu item if possible, or recreate menu.
        # For this example, we'll recreate the menu bar title if possible, 
        # but standard Tk menu bar labels are hard to change dynamically without recreation.
        # Let's try to update the cascade label by index.
        try:
            # Assuming Language is index 1 (or 0 if it's the first one)
            # Actually we can't easily get the menu object reference from here to config label.
            # Recreating menu is safer.
            self.create_menu() 
        except:
            pass

        self.status_bar.config(text=_("gui_curr_dir", self.compat.get_cwd()))
        
        # Update AI Panel
        try:
            self.lbl_model.config(text=_("gui_lbl_model"))
            self.btn_refresh.config(text=_("gui_btn_refresh"))
            self.btn_ask.config(text=_("gui_btn_ask_ai"))
            self.btn_suggest.config(text=_("gui_btn_ai_suggest"))
        except:
            pass

        # Update Buttons
        # We need references to buttons to update them.
        # Let's recreate the button bar to be safe and simple.
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
        # 1. Output Area
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
        
        # 2. Input Area
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

        # 3. Button Bar Container
        self.btn_container = tk.Frame(self.root, bg=self.bg_color)
        self.btn_container.pack(fill=tk.X, padx=10, pady=(0, 5))

        # 3.5 AI Panel
        self.create_ai_panel()
        
        # 4. Progress Bar (Indeterminate)
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        # Initially hidden (pack/unpack on demand or just use pack_forget)
        
        # 5. Status Bar
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
        
        # Model Label
        self.lbl_model = tk.Label(self.ai_container, text=_("gui_lbl_model"), bg=self.bg_color, fg=self.fg_color)
        self.lbl_model.pack(side=tk.LEFT, padx=(0, 5))
        
        # Combobox
        self.model_var = tk.StringVar()
        self.combo_model = ttk.Combobox(self.ai_container, textvariable=self.model_var, state="readonly", width=20)
        self.combo_model.pack(side=tk.LEFT, padx=(0, 5))
        
        # Refresh Button
        self.btn_refresh = tk.Button(self.ai_container, text=_("gui_btn_refresh"), command=self.refresh_models,
                                     bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT)
        self.btn_refresh.pack(side=tk.LEFT, padx=(0, 10))
        
        # Ask AI Button
        self.btn_ask = tk.Button(self.ai_container, text=_("gui_btn_ask_ai"), command=self.ask_ai,
                                 bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT)
        self.btn_ask.pack(side=tk.LEFT, padx=(0, 5))
        
        # Suggest Cmd Button
        self.btn_suggest = tk.Button(self.ai_container, text=_("gui_btn_ai_suggest"), command=self.ai_suggest,
                                     bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT)
        self.btn_suggest.pack(side=tk.LEFT)

        # Initial load
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
            return # Ignore input while running
            
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
             return

        self.log_output(f"$ {cmd_text}\n")
        
        # Parse args
        try:
            split_args = shlex.split(cmd_text)
            if not split_args:
                return
            cmd = split_args[0]
            params = split_args[1:]
        except Exception as e:
            self.log_output(f"Error: {str(e)}\n")
            return

        # Start Async Execution
        self.start_async_execution(cmd, params)

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

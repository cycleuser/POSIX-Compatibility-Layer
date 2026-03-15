import json
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.default_model: Optional[str] = None
        self._available_models: List[str] = []
        self._timeout: int = 120

    def set_timeout(self, seconds: int):
        self._timeout = seconds

    def is_available(self) -> bool:
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except:
            return False

    def get_models(self) -> List[str]:
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [model["name"] for model in data.get("models", [])]
                self._available_models = models
                if models and not self.default_model:
                    self.default_model = models[0]
                return models
        except urllib.error.URLError:
            return []
        except Exception:
            return []

    def set_default_model(self, model: str):
        self.default_model = model

    def generate(self, model: Optional[str] = None, prompt: str = "", 
                 system: Optional[str] = None, stream: bool = False,
                 context: Optional[List[int]] = None) -> str:
        model = model or self.default_model
        if not model:
            return "Error: No model specified and no default model set."

        url = f"{self.base_url}/api/generate"
        
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
        
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except urllib.error.URLError as e:
            return f"Error: Cannot connect to Ollama at {self.base_url}. Is Ollama running?"
        except json.JSONDecodeError:
            return "Error: Invalid response from Ollama."
        except Exception as e:
            return f"Error: {str(e)}"

    def chat(self, model: Optional[str] = None, messages: List[Dict[str, str]] = None,
             system: Optional[str] = None) -> str:
        model = model or self.default_model
        if not model:
            return "Error: No model specified."

        url = f"{self.base_url}/api/chat"
        
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages or [],
            "stream": False,
        }
        
        if system:
            payload["system"] = system
        
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("message", {}).get("content", "")
        except urllib.error.URLError:
            return f"Error: Cannot connect to Ollama."
        except Exception as e:
            return f"Error: {str(e)}"

    def embed(self, model: Optional[str] = None, prompt: str = "") -> Optional[List[float]]:
        model = model or self.default_model
        if not model:
            return None

        url = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": model,
            "prompt": prompt,
        }
        
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("embedding")
        except:
            return None

    def pull_model(self, model_name: str) -> bool:
        url = f"{self.base_url}/api/pull"
        
        payload = {"name": model_name, "stream": False}
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("status") == "success"
        except:
            return False

    def get_model_info(self, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        model = model or self.default_model
        if not model:
            return None

        url = f"{self.base_url}/api/show"
        
        payload = {"name": model}
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except:
            return None

    def interpret_command(self, natural_input: str, context: str = "") -> str:
        system_prompt = """You are a POSIX shell command interpreter.
Convert natural language input to shell commands.

Rules:
1. Return ONLY the shell command, no explanations.
2. Use safe defaults.
3. For dangerous operations, prefix with CONFIRM:
4. If unclear, respond with: CLARIFY: <question>

Examples:
- "list files" -> ls
- "delete all temp files" -> CONFIRM: rm -f /tmp/*
- "find large files" -> find . -size +100M
"""

        if context:
            system_prompt += f"\n\nContext:\n{context}"

        return self.generate(prompt=natural_input, system=system_prompt)

    def explain_command(self, command: str) -> str:
        system_prompt = """You are a shell command explainer.
Explain what the given command does in simple terms.
Include: purpose, options, potential risks, and alternatives if relevant.
Keep explanations concise (2-4 sentences)."""

        return self.generate(prompt=f"Explain: {command}", system=system_prompt)

    def suggest_fix(self, command: str, error: str) -> str:
        system_prompt = """You are a shell debugging assistant.
Given a failed command and its error, suggest a fix.
Return only the corrected command or a brief explanation."""

        return self.generate(
            prompt=f"Command: {command}\nError: {error}\nSuggest fix:",
            system=system_prompt
        )
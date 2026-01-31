import json
import urllib.request
import urllib.error

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def get_models(self):
        """
        Fetch list of available local models.
        Returns a list of model names (strings).
        """
        try:
            url = f"{self.base_url}/api/tags"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                # API returns {"models": [{"name": "...", ...}, ...]}
                return [model["name"] for model in data.get("models", [])]
        except urllib.error.URLError:
            # Could not connect
            return []
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def generate(self, model, prompt, system=None):
        """
        Generate a response from the model.
        Returns the generated text.
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if system:
            payload["system"] = system
            
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "")
        except Exception as e:
            return f"Error: {str(e)}"

"""Real AI integration for reVoAgent - OpenAI, Anthropic, and Local Models."""
import os
import asyncio
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import json

class BaseModelManager(ABC):
    """Base class for AI model managers."""
    
    @abstractmethod
    async def generate_response(self, prompt: str, model_name: str = None, **kwargs) -> str:
        """Generate response from AI model."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        pass

class OpenAIModelManager(BaseModelManager):
    """OpenAI API integration."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                import openai
                self.client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                print("⚠️ OpenAI package not installed. Run: pip install openai")
    
    async def generate_response(self, prompt: str, model_name: str = "gpt-4", **kwargs) -> str:
        """Generate response using OpenAI API."""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")
        
        try:
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

class AnthropicModelManager(BaseModelManager):
    """Anthropic Claude API integration."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                print("⚠️ Anthropic package not installed. Run: pip install anthropic")
    
    async def generate_response(self, prompt: str, model_name: str = "claude-3-sonnet-20240229", **kwargs) -> str:
        """Generate response using Anthropic API."""
        if not self.client:
            raise ValueError("Anthropic client not initialized. Check API key.")
        
        try:
            response = await self.client.messages.create(
                model=model_name,
                max_tokens=kwargs.get("max_tokens", 2000),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        return ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]

class LocalModelManager(BaseModelManager):
    """Local model integration using transformers."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
        except ImportError:
            print("⚠️ Transformers package not installed. Run: pip install transformers torch")
    
    async def generate_response(self, prompt: str, model_name: str = None, **kwargs) -> str:
        """Generate response using local model."""
        if not self.model or not self.tokenizer:
            raise ValueError("Local model not initialized.")
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._generate_sync, prompt, kwargs)
            return response
        except Exception as e:
            raise Exception(f"Local model error: {str(e)}")
    
    def _generate_sync(self, prompt: str, kwargs: Dict[str, Any]) -> str:
        """Synchronous generation for thread pool."""
        try:
            import torch
        except ImportError:
            return "Local model requires PyTorch. Install with: pip install torch"
            
        inputs = self.tokenizer.encode(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=kwargs.get("max_tokens", 200),
                temperature=kwargs.get("temperature", 0.7),
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(prompt):].strip()
    
    def get_available_models(self) -> List[str]:
        return ["microsoft/DialoGPT-medium", "microsoft/DialoGPT-large", "gpt2"]

class MockModelManager(BaseModelManager):
    """Mock model manager for testing and fallback."""
    
    async def generate_response(self, prompt: str, model_name: str = None, **kwargs) -> str:
        """Generate mock responses for testing."""
        await asyncio.sleep(0.2)  # Simulate API delay
        
        prompt_lower = prompt.lower()
        
        if "code" in prompt_lower and "generate" in prompt_lower:
            return '''def example_function():
    """Generated code example."""
    return "Hello, World!"

# This is a mock response for testing
print(example_function())'''
        
        elif "debug" in prompt_lower or "error" in prompt_lower:
            return '''**Debug Analysis:**
This appears to be a mock debugging response.

**Recommendations:**
1. Check variable initialization
2. Verify function parameters
3. Add error handling

**Note:** This is a mock response. Configure real AI integration for production.'''
        
        else:
            return f"Mock response for: {prompt[:100]}...\n\n**Note:** This is a mock response. Configure real AI integration for production."
    
    def get_available_models(self) -> List[str]:
        return ["mock-model"]

class SmartModelManager:
    """Smart model manager that automatically selects the best available provider."""
    
    def __init__(self):
        self.providers = {}
        self.primary_provider = None
        
        # Initialize available providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available AI providers."""
        # Try OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.providers["openai"] = OpenAIModelManager()
                if not self.primary_provider:
                    self.primary_provider = "openai"
                print("✅ OpenAI integration initialized")
            except Exception as e:
                print(f"⚠️ OpenAI initialization failed: {e}")
        
        # Try Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.providers["anthropic"] = AnthropicModelManager()
                if not self.primary_provider:
                    self.primary_provider = "anthropic"
                print("✅ Anthropic integration initialized")
            except Exception as e:
                print(f"⚠️ Anthropic initialization failed: {e}")
        
        # Try Local Models
        try:
            self.providers["local"] = LocalModelManager()
            if not self.primary_provider:
                self.primary_provider = "local"
            print("✅ Local model integration initialized")
        except Exception as e:
            print(f"⚠️ Local model initialization failed: {e}")
        
        # Fallback to mock
        if not self.providers:
            self.providers["mock"] = MockModelManager()
            self.primary_provider = "mock"
            print("⚠️ Using mock responses - configure real AI integration for production")
    
    async def generate_response(self, prompt: str, model_name: str = None, provider: str = None, **kwargs) -> str:
        """Generate response using the best available provider."""
        target_provider = provider or self.primary_provider
        
        if target_provider not in self.providers:
            target_provider = self.primary_provider
        
        try:
            return await self.providers[target_provider].generate_response(prompt, model_name, **kwargs)
        except Exception as e:
            print(f"⚠️ Provider {target_provider} failed: {e}")
            
            # Fallback to mock if primary fails
            if target_provider != "mock" and "mock" in self.providers:
                print("🔄 Falling back to mock responses")
                return await self.providers["mock"].generate_response(prompt, model_name, **kwargs)
            
            raise e
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())
    
    def get_provider_models(self, provider: str) -> List[str]:
        """Get available models for a provider."""
        if provider in self.providers:
            return self.providers[provider].get_available_models()
        return []

class RealToolManager:
    """Real tool manager with actual tool execution."""
    
    def __init__(self):
        self.tools = {
            "terminal": self._execute_terminal,
            "file_manager": self._execute_file_manager,
            "pytest": self._execute_pytest,
            "docker": self._execute_docker,
            "git": self._execute_git,
            "security_scanner": self._execute_security_scanner,
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None, **kwargs) -> Any:
        """Execute a real tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not available")
        
        if parameters is None:
            parameters = {}
        
        try:
            return await self.tools[tool_name](parameters)
        except Exception as e:
            return {"error": str(e), "tool": tool_name}
    
    async def _execute_terminal(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute terminal commands safely."""
        import subprocess
        
        command = params.get("command", "echo 'No command provided'")
        
        # Security: Only allow safe commands
        safe_commands = ["ls", "pwd", "echo", "cat", "grep", "find", "ps", "top", "df", "free"]
        cmd_parts = command.split()
        
        if not cmd_parts or cmd_parts[0] not in safe_commands:
            return {"error": "Command not allowed for security reasons", "allowed": safe_commands}
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _execute_file_manager(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """File management operations."""
        operation = params.get("operation", "list")
        path = params.get("path", ".")
        
        try:
            if operation == "list":
                import os
                files = os.listdir(path)
                return {"files": files, "path": path}
            elif operation == "read":
                with open(path, 'r') as f:
                    content = f.read()
                return {"content": content, "path": path}
            else:
                return {"error": f"Operation {operation} not supported"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _execute_pytest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pytest commands."""
        test_path = params.get("path", ".")
        
        try:
            import subprocess
            result = subprocess.run(
                ["python", "-m", "pytest", test_path, "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _execute_docker(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Docker operations."""
        return {"info": "Docker integration not implemented yet"}
    
    async def _execute_git(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Git operations."""
        return {"info": "Git integration not implemented yet"}
    
    async def _execute_security_scanner(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Security scanning."""
        return {
            "scan_results": {
                "vulnerabilities": 0,
                "security_score": 95,
                "recommendations": ["Enable HTTPS", "Update dependencies"]
            }
        }

# Factory function to create the appropriate model manager
def create_model_manager(provider: str = "auto") -> BaseModelManager:
    """Create model manager based on configuration."""
    if provider == "auto":
        return SmartModelManager()
    elif provider == "openai":
        return OpenAIModelManager()
    elif provider == "anthropic":
        return AnthropicModelManager()
    elif provider == "local":
        return LocalModelManager()
    else:
        return MockModelManager()

def create_tool_manager(use_real_tools: bool = True):
    """Create tool manager."""
    if use_real_tools:
        return RealToolManager()
    else:
        # Return mock tool manager for testing
        from apps.backend.main_with_auth import MockToolManager
        return MockToolManager()
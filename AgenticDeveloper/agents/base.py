from abc import ABC, abstractmethod
import logging
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from langchain_core.language_models.llms import BaseLLM
from langchain_ollama import OllamaLLM
from langchain_openai import OpenAI
from pydantic import BaseModel, Field
from openai import OpenAI as OpenAIClient
import concurrent.futures
import asyncio
from dotenv import load_dotenv
load_dotenv()

class OpenRouterLLMWrapper:
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.7, max_tokens: int = 4000, timeout: int = 60):
        self.client = OpenAIClient(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def invoke(self, prompt: str) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://your-site-url.com",
                        "X-Title": "Your Site Name",
                    },
                    extra_body={},
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                if not response:
                    raise ValueError("API returned None response")
                if not hasattr(response, 'choices') or not response.choices:
                    raise ValueError("API response missing choices")
                if not hasattr(response.choices[0], 'message') or not response.choices[0].message:
                    raise ValueError("API response missing message")
                if not hasattr(response.choices[0].message, 'content'):
                    raise ValueError("API response missing content")
                
                return response.choices[0].message.content
                
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise RuntimeError(f"Failed to get valid response after {max_retries} attempts: {str(e)}")
                import time
                time.sleep(1 * (attempt + 1))  # Exponential backoff

    async def ainvoke(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        def sync_call():
            max_retries = 3
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        extra_headers={
                            "HTTP-Referer": "https://your-site-url.com",
                            "X-Title": "Your Site Name",
                        },
                        extra_body={},
                        model=self.model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    if not response:
                        raise ValueError("API returned None response")
                    if not hasattr(response, 'choices') or not response.choices:
                        raise ValueError("API response missing choices")
                    if not hasattr(response.choices[0], 'message') or not response.choices[0].message:
                        raise ValueError("API response missing message")
                    if not hasattr(response.choices[0].message, 'content'):
                        raise ValueError("API response missing content")
                    
                    return response.choices[0].message.content
                    
                except Exception as e:
                    last_error = e
                    if attempt == max_retries - 1:  # Last attempt
                        raise RuntimeError(f"Failed to get valid response after {max_retries} attempts: {str(e)}")
                    import time
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    
            raise last_error  # Should not reach here, but just in case
            
        return await loop.run_in_executor(None, sync_call)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AgentConfig(BaseModel):
    """Configuration model for agents"""
    name: str = Field(..., description="Name of the agent")
    tools: List[str] = Field(default_factory=list, description="List of tools available to the agent")
    max_iterations: int = Field(default=5, description="Maximum number of iterations for the agent")
    
class BaseAgent(ABC):
    """Base agent class that all other agents will inherit from"""
    
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config if config is not None else self._load_config(config_path)
        self._initialize_llms()
        self.tools = self._initialize_tools()
        self.max_iterations = self.config.get("max_iterations", 5)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from yaml file"""
        if config_path is None:
            # Get the path to config relative to this file
            config_path = str(Path(__file__).parent.parent / "config" / "system_config.yaml")
            
        try:
            abs_path = str(Path(config_path).resolve())
            with open(abs_path, 'r') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {str(e)}")
            raise
            
    def _initialize_llms(self):
        """Initialize LLMs based on configured providers"""
        llm_config = self.config.get("llm", {})

        # Get the list of providers we need
        providers_to_init = [
            llm_config.get("thinking_provider", "openrouter_quasar"),
            llm_config.get("strategy_writer_provider", "openrouter_quasar")
        ]
        
        # Add research provider if the agent has _analyze_resource method
        if hasattr(self, '_analyze_resource'):
            providers_to_init.append(llm_config.get("research_provider", "openrouter_llama4-scout"))

        # Track initialized providers to avoid duplicate initialization
        initialized_providers = {}
        
        # Initialize each provider once and store the instance
        for provider in providers_to_init:
            if provider not in initialized_providers:
                provider_config = llm_config.get(provider, {})
                
                # Initialize based on provider type
                if provider.startswith("ollama_"):
                    initialized_providers[provider] = self._initialize_ollama(provider_config)
                elif provider.startswith("openrouter_"):
                    initialized_providers[provider] = self._initialize_openrouter(provider_config)
                elif provider.startswith("openai_"):
                    initialized_providers[provider] = self._initialize_openai(provider_config)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")

        # Assign providers to their respective roles
        self.thinking_llm = initialized_providers[llm_config.get("thinking_provider")]
        self.strategy_writer_llm = initialized_providers[llm_config.get("strategy_writer_provider")]
        if hasattr(self, '_analyze_resource'):
            self.research_llm = initialized_providers[llm_config.get("research_provider")]
            
    def _initialize_ollama(self, config: Dict) -> BaseLLM:
        """Initialize Ollama LLM with validation and availability check."""
        try:
            model = str(config.get("model"))
            base_url = str(config.get("base_url")).rstrip('/')
            timeout = int(config.get("timeout", 60))

            if not model:
                raise ValueError("Model name is required for Ollama")
            if timeout <= 0:
                raise ValueError("Timeout must be a positive integer")

            # Initialize Ollama LLM with validated configuration
            self.logger.info(f"Initializing Ollama LLM with model: {model}")
            llm = OllamaLLM(
                model=model,
                base_url=base_url,
                timeout=timeout
            )
            
            # Test if LLM is responsive
            llm.invoke("test")  # This will raise an exception if Ollama is not available
            return llm
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Ollama LLM: {str(e)}")
        
    def _initialize_openai(self, config: Dict) -> BaseLLM:
        """Initialize OpenAI LLM"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        return OpenAI(
            api_base=config.get("base_url", "https://api.openai.com/v1"),
            model_name=config.get("model", "gpt-4"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60)
        )

    def _initialize_openrouter(self, config: Dict) -> BaseLLM:
        """Initialize OpenRouter LLM"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        model = config.get("model")
        base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 4000)
        timeout = config.get("timeout", 60)

        if not model:
            raise ValueError("Model name is required for OpenRouter")

        return OpenRouterLLMWrapper(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize tools based on configuration"""
        tool_config = self.config.get("tools", {})
        tools = {}
        
        for tool_name in self.config.get("agents", {}).get(self.__class__.__name__.lower(), {}).get("tools", []):
            if tool_name in tool_config:
                tools[tool_name] = self._load_tool(tool_name, tool_config[tool_name])
                
        return tools
        
    def _load_tool(self, tool_name: str, tool_config: Dict) -> Any:
        """Load a specific tool based on configuration"""
        # This will be implemented by specific agents based on their needs
        pass
        
    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        """Main execution method to be implemented by specific agents"""
        pass
        
    async def call_llm(self, prompt: str, llm_destination: str = "thinking") -> str:
        """Call the appropriate LLM based on destination."""
        if llm_destination == "strategy_writer":
            # provider = self.config.get("llm", {}).get("strategy_writer_provider", "unknown")
            # self.logger.info(f"[LLM CALL] Provider: {provider} (strategy_writer)\nPrompt:\n{prompt[:200]}")
            return await self.strategy_writer_llm.ainvoke(prompt)
        elif llm_destination == "research":
            # provider = self.config.get("llm", {}).get("research_provider", "unknown")
            # self.logger.info(f"[LLM CALL] Provider: {provider} (research)\nPrompt:\n{prompt[:200]}")
            return await self.research_llm.ainvoke(prompt)
        else:
            # provider = self.config.get("llm", {}).get("thinking_provider", "unknown")
            # self.logger.info(f"[LLM CALL] Provider: {provider} (thinking)\nPrompt:\n{prompt[:200]}")
            return await self.thinking_llm.ainvoke(prompt)

    def log_progress(self, message: str, level: str = "info") -> None:
        """Log progress messages"""
        log_method = getattr(self.logger, level.lower())
        log_method(message)
        
    async def wait_for_human_input(self, duration: int = 15) -> Optional[str]:
        """Wait for human input with a timeout"""
        self.logger.info(f"Waiting {duration} seconds for human input...")
        # Implementation for human input with timeout would go here
        return None

    def cleanup(self) -> None:
        """Cleanup method to be called when agent is done"""
        pass
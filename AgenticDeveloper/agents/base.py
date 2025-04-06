from abc import ABC, abstractmethod
import logging
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from langchain_core.language_models.llms import BaseLLM
from langchain_ollama import OllamaLLM
from langchain_community.llms import OpenAI
from pydantic import BaseModel, Field

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
        self.llm = self._initialize_llm()
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
            
    def _initialize_llm(self) -> BaseLLM:
        """Initialize LLM based on configuration"""
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider", "ollama")
        
        if provider == "ollama":
            return self._initialize_ollama(llm_config.get("ollama", {}))
        elif provider == "openai":
            return self._initialize_openai(llm_config.get("openai", {}))
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
            
    def _initialize_ollama(self, config: Dict) -> BaseLLM:
        """Initialize Ollama LLM with validation and availability check.

        Args:
            config (Dict): Configuration dictionary for Ollama settings

        Returns:
            BaseLLM: Initialized Ollama language model

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If Ollama service is not available
        """
        try:
            # Validate configuration
            model = str(config.get("model", "llama2"))
            base_url = str(config.get("base_url", "http://localhost:11434")).rstrip('/')
            timeout = int(config.get("timeout", 60))

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
            model_name=config.get("model", "gpt-4"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60)
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
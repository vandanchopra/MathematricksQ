from abc import ABC, abstractmethod
import logging
import yaml
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_core.language_models.llms import BaseLLM
from langchain_ollama import OllamaLLM
from langchain_openai import OpenAI
from pydantic import BaseModel, Field
from openai import OpenAI as OpenAIClient
import concurrent.futures
import asyncio
import json
import glob
from dotenv import load_dotenv
load_dotenv()

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

    def get_backtest_output_template(self, strategy_filename: str = "", backtest_id: str = "") -> Dict:
        """
        Creates a standardized template for backtest output.
        
        Args:
            strategy_filename: Name of the strategy file being backtested
            backtest_id: Unique identifier for the backtest
            
        Returns:
            Dict: Template with all required fields initialized
        """
        return {
            "strategy_filename": strategy_filename,
            "backtest_id": backtest_id,
            "backtest_success": False,
            "backtest_folder_path": "",
            "performance": {},
            "analysis": {},
            "errors": [],
            "backtest_raw_data": {},
            "backtest_console_output": "",
            "failed_data_requests": [],
            "succeeded_data_requests": []
        }

    def update_backtest_output(self, folder_path: str, updates: Dict[str, Any]) -> None:
        """
        Update the backtest output file with new data.
        
        Args:
            folder_path: Path to the backtest folder
            updates: Dictionary containing fields to update in the output file
        """
        output_path = os.path.join(folder_path, 'backtest_output.json')
        try:
            # Load existing data or create new from template
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    output_data = json.load(f)
            else:
                output_data = self.get_backtest_output_template()
            
            # Update with new data
            for key, value in updates.items():
                output_data[key] = value
            
            # Save updated data
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Failed to update backtest output: {str(e)}")
            raise
    
    def load_backtest_output(self, folder_path: str) -> Dict[str, Any]:
        """
        Load the backtest output file.
        
        Args:
            folder_path: Path to the backtest folder
            
        Returns:
            Dict containing the backtest output data
        """
        output_path = os.path.join(folder_path, 'backtest_output.json')
        try:
            if not os.path.exists(output_path):
                return self.get_backtest_output_template()
                
            with open(output_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load backtest output: {str(e)}")
            raise
        
    def _load_backtest_results(self, backtest_dir: str) -> Dict[str, Any]:
        """Load all relevant backtest data for analysis"""
        return self.load_backtest_output(backtest_dir)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from yaml file"""
        if config_path is None:
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
        providers_to_init = [
            llm_config.get("thinking_provider", "openrouter_quasar"),
            llm_config.get("strategy_writer_provider", "openrouter_quasar")
        ]
        
        if hasattr(self, '_analyze_resource'):
            providers_to_init.append(llm_config.get("research_provider", "openrouter_llama4-scout"))

        initialized_providers = {}
        
        for provider in providers_to_init:
            if provider not in initialized_providers:
                provider_config = llm_config.get(provider, {})
                
                if provider.startswith("ollama_"):
                    initialized_providers[provider] = self._initialize_ollama(provider_config)
                elif provider.startswith("openrouter_"):
                    initialized_providers[provider] = self._initialize_openrouter(provider_config)
                elif provider.startswith("openai_"):
                    initialized_providers[provider] = self._initialize_openai(provider_config)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")

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

            llm = OllamaLLM(
                model=model,
                base_url=base_url,
                timeout=timeout
            )
            
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
        llm = OpenRouterLLMWrapper(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
        return llm
        
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
        pass
        
    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        """Main execution method to be implemented by specific agents"""
        pass
        
    async def call_llm(self, prompt: str, llm_destination: str = "thinking") -> str:
        """Call the appropriate LLM based on destination."""
        if llm_destination == "strategy_writer":
            return await self.strategy_writer_llm.ainvoke(prompt)
        elif llm_destination == "research":
            return await self.research_llm.ainvoke(prompt)
        else:
            return await self.thinking_llm.ainvoke(prompt)

    def log_progress(self, message: str, level: str = "info") -> None:
        """Log progress messages"""
        log_method = getattr(self.logger, level.lower())
        log_method(message)
        
    def cleanup(self) -> None:
        """Cleanup method to be called when agent is done"""
        pass
    
    def paginate_output(self, content: str, page_size: int = 1000) -> None:
        """Display content in pages with user control"""
        total_len = len(content)
        num_pages = (total_len + page_size - 1) // page_size
                
        current_page = 1
        start_idx = 0
        
        while start_idx < total_len:
            end_idx = min(start_idx + page_size, total_len)
            chunk = content[start_idx:end_idx]
            
            self.logger.info(f"\n--- Page {current_page}/{num_pages} ---\n")
            self.logger.info(chunk)
            
            if end_idx < total_len:
                user_input = input("\nPress Enter for next page, 'q' to quit: ")
                if user_input.lower() == 'q':
                    break
                    
            start_idx += page_size
            current_page += 1

class OpenRouterLLMWrapper:
    """OpenRouter LLM wrapper class supporting sync and async operations"""
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
        """Synchronous invoke method"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://mathematricksQ.com",
                        "X-Title": "MathematricksQ",
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
                    
                if not hasattr(response, 'choices'):
                    if hasattr(response, 'status_code') and response.status_code == 429:
                        raise ValueError("Rate limit exceeded. Please wait before retrying.")
                    elif hasattr(response, 'error'):
                        raise ValueError(f"API error: {response.error}")
                    else:
                        raise ValueError(f"API response missing choices. Full response: {response}")
                        
                if not response.choices or len(response.choices) == 0:
                    raise ValueError("API response has empty choices array")
                    
                if not hasattr(response.choices[0], 'message') or not response.choices[0].message:
                    raise ValueError("API response missing message")
                    
                if not hasattr(response.choices[0].message, 'content'):
                    raise ValueError("API response missing content")
                
                return response.choices[0].message.content
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed after {max_retries} attempts: {str(e)}")
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                print(f"Retrying in 10 seconds... (attempt {attempt + 1} of {max_retries})")
                import time
                time.sleep(10)

    async def ainvoke(self, prompt: str) -> str:
        """Asynchronous invoke method"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.invoke, prompt)

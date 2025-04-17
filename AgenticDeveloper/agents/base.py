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
import json
import glob
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
                
                # Debug logging for API response
                print(f"Debug - Raw API response: {response}")
                
                # Check for specific error conditions
                if not response:
                    raise ValueError("API returned None response")
                    
                if not hasattr(response, 'choices'):
                    # Check for rate limiting or model unavailability
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
                if attempt == max_retries - 1:  # Last attempt
                    raise RuntimeError(f"Failed to get valid response after {max_retries} attempts: {str(e)}")
                # print the error message for debugging
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                print(f"Retrying in 10 seconds... (attempt {attempt + 1} of {max_retries})")
                import time
                time.sleep(10)  # 10 second delay between retries

    async def ainvoke(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        def sync_call():
            max_retries = 3
            last_error = None
            
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
                    
                    # Debug logging for API response
                    print(f"Debug - Raw API response: {response}")
                    
                    if not response:
                        raise ValueError("API returned None response")
                        
                    if not hasattr(response, 'choices'):
                        # Check for rate limiting or model unavailability
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
                    last_error = e
                    if attempt == max_retries - 1:  # Last attempt
                        raise RuntimeError(f"Failed to get valid response after {max_retries} attempts: {str(e)}")
                    print(f"Retrying in 10 seconds... (attempt {attempt + 1} of {max_retries})")
                    import time
                    time.sleep(10)  # 10 second delay between retries
                    
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
            self.logger.info(f"Ollama LLM initialized successfully with model: {model}")
            
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
        self.logger.info(f"Initializing OpenRouter LLM with model: {model}")
        llm = OpenRouterLLMWrapper(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        self.logger.info(f"OpenRouter LLM initialized successfully with model: {model}")
        
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
        # This will be implemented by specific agents based on their needs
        pass
    
    def _load_backtest_results(self, backtest_dir: str) -> Dict[str, Any]:
        """Load all relevant backtest data for analysis"""
        results = {}
        backtest_files = os.listdir(backtest_dir)
        # Find backtest ID from files
        json_files = glob.glob(os.path.join(backtest_dir, "[0-9]*-*.json"))
        if not json_files:
            raise ValueError(f"No backtest result files found in {backtest_dir}")
            
        backtest_id = os.path.basename(json_files[0]).split('-')[0]
        
        # Load errors file
        errors_path = os.path.join(backtest_dir, "errors.json")
        try:
            with open(errors_path, 'r') as f:
                results["errors"] = json.load(f)
                self.logger.debug("Loaded errors data")
        except FileNotFoundError:
            self.logger.debug(f"Warning: Errors file not found: {errors_path}")
            results["errors"] = []
            
        # Load failed data requests - find file containing "failed-data-requests-"
        results["failed_requests"] = []  # Initialize empty list
        for filename in backtest_files:
            if 'data-monitor-report-' in filename:
                data_monitor_report_path = os.path.join(backtest_dir, filename)
                try:
                    with open(data_monitor_report_path, 'r') as f:
                        data_monitor_report = json.load(f)
                    results["failed_requests"] = data_monitor_report['failed-data-requests-count']
                    self.logger.debug(f"failed_requests: {results['failed_requests']}")
                except Exception as e:
                    self.logger.error(f"Warning: Failed to load failed requests file: {str(e)}")
                break
        
        # Load summary data
        summary_path = os.path.join(backtest_dir, f"{backtest_id}-summary.json")
        try:
            with open(summary_path, 'r') as f:
                summary_data = json.load(f)
                # Remove charts data if context window is small
                del summary_data["charts"]
                results["summary"] = summary_data
                self.logger.debug(f"Loaded summary data with keys: {summary_data.keys()}")
        except FileNotFoundError:
            raise ValueError(f"Required summary file not found: {summary_path}")
            
        # Load order events
        # Only load order events if context window is large enough
        orders_path = os.path.join(backtest_dir, f"{backtest_id}-order-events.json")
        for filename in backtest_files:
            if '-order-events' in filename:
                orders_path = os.path.join(backtest_dir, filename)
                try:
                    with open(orders_path, 'r') as f:
                        results["orders"] = json.load(f)
                        self.logger.debug("Loaded order events data with keys: " + str(len(results["orders"])))
                except FileNotFoundError:
                    self.logger.error(f"Warning: Order events file not found: {orders_path}" )
                    results["orders"] = []
                break
            
            self.logger.debug("Skipping order events due to small context window")
            results["orders"] = []
            
        # Load strategy code if available
        if "strategy_code_filepath" in results["errors"]:
            code_path = results["errors"]["strategy_code_filepath"]
        try:
            with open(code_path, 'r') as f:
                results["strategy_code"] = f.read()
                self.logger.debug(f"Loaded strategy code: {results['strategy_code'][:100]}")
        except FileNotFoundError:
            self.logger.debug(f"Warning: Strategy code not found: {code_path}")
            
        # Load the 'analysis' file if it exists
        for filename in backtest_files:
            if 'BacktestAnalyzerAgent_analysis' in filename:
                analysis_report_path = os.path.join(backtest_dir, filename)
                try:
                    with open(code_path, 'r') as f:
                        results["analysis"] = f.read()
                        self.logger.debug(f"Loaded strategy code: {results['strategy_code'][:100]}")
                except FileNotFoundError:
                    self.logger.debug(f"Warning: Strategy code not found: {code_path}")
            
        return results
        
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
    
    def paginate_output(self, content: str, page_size: int = 1000) -> None:
        """
        Display content in pages with user control
        
        Args:
            content: The text content to display
            page_size: Characters per page
        """
        total_len = len(content)
        num_pages = (total_len + page_size - 1) // page_size  # Ceiling division
        
        self.logger.info(f"Content will be displayed in {num_pages} pages. Press Enter to continue, 'q' to quit...")
        
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
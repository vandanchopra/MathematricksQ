import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from .base import BaseAgent
from .memory_agent import MemoryAgent
from AgenticDeveloper.logger import get_logger

class BacktestAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing backtest results and providing improvement suggestions"""

    def __init__(self, config_path: str = "AgenticDeveloper/config/system_config.yaml", config: Optional[Dict] = None):
        super().__init__(config_path=config_path, config=config)
        self.logger = get_logger("BacktestAnalyzerAgent")
        # Get context window size in tokens from config
        provider = self.config["llm"]["thinking_provider"]
        self.context_window = self.config["llm"][provider]["context_window_in_k"] * 1000

        # Initialize memory agent
        self.memory_agent = MemoryAgent(config_path=config_path, config=config)

    async def run(self, backtest_dir: str) -> Dict[str, Any]:
        """
        Analyze results for a specific backtest

        Args:
            backtest_dir: Path to the specific backtest directory
                         (e.g., "Strategies/SMAStrategy/backtests/2025-03-26_11-34-48")

        Returns:
            Dictionary containing analysis results and suggestions
        """
        self.logger.debug(f"Starting analysis for backtest: {backtest_dir}")

        # Verify backtest directory exists
        if not os.path.exists(backtest_dir):
            raise ValueError(f"Backtest directory not found: {backtest_dir}")

        # Load backtest results
        backtest_info = self._load_backtest_results(backtest_dir)

        # Check memory for similar backtests
        try:
            # Extract strategy information
            strategy_filename = backtest_info.get("strategy_filename", "")
            if strategy_filename:
                # Read the strategy file
                strategy_path = os.path.join(backtest_dir, "code", strategy_filename)
                if os.path.exists(strategy_path):
                    with open(strategy_path, 'r') as f:
                        strategy_code = f.read()

                    # Extract a description from the strategy code
                    description = self._extract_description_from_code(strategy_code)

                    # Query memory for similar ideas
                    similar_ideas_result = await self.memory_agent.run(
                        "query_similar_ideas",
                        query_text=description,
                        top_k=3
                    )

                    if similar_ideas_result.get("results"):
                        self.logger.info("Found similar strategies in memory:")
                        for i, idea in enumerate(similar_ideas_result["results"]):
                            self.logger.info(f"  {i+1}. {idea.get('description', '')[:100]}...")

                            # Check if this idea has backtests with good metrics
                            try:
                                backtest_results = await self.memory_agent.run(
                                    "query_top_ideas",
                                    metric="Sharpe",
                                    limit=1
                                )

                                if backtest_results.get("results"):
                                    top_idea = backtest_results["results"][0]
                                    metrics = top_idea.get("metrics", {})
                                    self.logger.info(f"    Top backtest metrics: Sharpe={metrics.get('Sharpe', 'N/A')}, CAGR={metrics.get('CAGR', 'N/A')}")
                            except Exception as e:
                                self.logger.warning(f"Error querying top backtests: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Error querying memory for similar strategies: {str(e)}")

        # Analyze results using LLM
        analysis = await self._analyze_results(backtest_info)

        # Store analysis
        analysis_output = {
            "timestamp": datetime.now().isoformat(),
            "backtest_path": backtest_dir,
            "analysis": analysis
        }
        # Save standalone analysis file
        standalone_output = os.path.join(backtest_dir, "BacktestAnalyzerAgent_analysis.json")
        with open(standalone_output, 'w') as f:
            json.dump(analysis_output, f, indent=2)
        self.logger.debug(f"Analysis complete and stored in: {standalone_output}")

        # Update backtest_output.json with analysis
        backtest_output_path = os.path.join(backtest_dir, "backtest_output.json")
        if os.path.exists(backtest_output_path):
            with open(backtest_output_path, 'r') as f:
                backtest_output = json.load(f)

            # Add/update analysis field
            backtest_output["analysis"] = analysis

            # Save updated backtest_output.json
            with open(backtest_output_path, 'w') as f:
                json.dump(backtest_output, f, indent=2)
            self.logger.debug(f"Updated analysis in {backtest_output_path}")

        # Update version history
        self._update_version_history(backtest_dir, analysis)

        # Store analysis in memory
        try:
            # Process backtest results in memory
            memory_result = await self.memory_agent.run(
                "process_backtest_results",
                backtest_dir=backtest_dir
            )
            self.logger.info(f"Stored backtest analysis in memory: {memory_result.get('status', 'unknown')}")
        except Exception as e:
            self.logger.warning(f"Error storing backtest analysis in memory: {str(e)}")

        return analysis_output

    def _update_version_history(self, backtest_dir: str, analysis: Dict) -> None:
        """Update version history with backtest analysis"""
        try:
            # Navigate up to find strategy directory
            strategy_dir = os.path.dirname(backtest_dir)  # backtests/
            strategy_dir = os.path.dirname(strategy_dir)  # StrategyName/
            version_history_path = os.path.join(strategy_dir, "version_history.json")

            if not os.path.exists(version_history_path):
                self.logger.warning(f"Version history file not found: {version_history_path}")
                return

            # Load version history
            with open(version_history_path, 'r') as f:
                version_history = json.load(f)

            # Find matching version and backtest
            backtest_path = os.path.abspath(backtest_dir)
            updated = False

            for version in version_history:
                if 'backtests' in version:
                    for backtest in version['backtests']:
                        if os.path.abspath(backtest.get('backtest_folder', '')) == backtest_path:
                            # Add or update analysis
                            backtest['BacktestAnalyzerAgent-analysis'] = analysis
                            updated = True
                            break
                if updated:
                    break

            if not updated:
                self.logger.warning(f"Could not find matching backtest in version history for: {backtest_path}")
                return

            # Save updated version history
            with open(version_history_path, 'w') as f:
                json.dump(version_history, f, indent=2)
                self.logger.debug(f"Updated version history in {version_history_path}")

        except Exception as e:
            self.logger.error(f"Failed to update version history: {str(e)}")



    async def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze backtest results and generate insights"""
        # Prepare the prompt for analysis

        prompt = self._create_analysis_prompt(results)

        '''# Log prompt size and content for visibility
        prompt_size = len(prompt.encode('utf-8'))
        self.logger.debug(f"Analysis prompt size: {prompt_size} bytes")
        self.logger.debug("Analysis prompt content (paginated):")
        self.paginate_output(prompt)'''

        try:
            # Get LLM analysis using thinking_llm from base class
            response = await self.call_llm(prompt)  # Uses thinking_llm by default
            self.logger.debug("Received LLM response, parsing JSON...")

            # Parse JSON from response
            analysis = self._parse_llm_response(response)
            return analysis

        except Exception as e:
            self.logger.debug(f"Error during LLM analysis: {str(e)}")
            raise

    def _load_backtest_results(self, backtest_dir: str) -> Dict[str, Any]:
        """Load backtest results from backtest_output.json"""
        output_json_path = os.path.join(backtest_dir, "backtest_output.json")
        if not os.path.exists(output_json_path):
            raise ValueError(f"backtest_output.json not found in {backtest_dir}")

        with open(output_json_path, 'r') as f:
            results = json.load(f)
            self.logger.debug(f"Loaded backtest results from {output_json_path}")
            return results

    def _create_analysis_prompt(self, results: Dict[str, Any]) -> str:
        """Create a detailed prompt for the LLM to analyze backtest results"""
        performance_metrics = results.get("performance", {})
        orders = results.get("orders", [])
        errors = results.get("errors", [])
        failed_requests = results.get("failed_data_requests", [])

        prompt = f"""As a quantitative trading expert, analyze these backtest results and return your analysis in JSON format.

IMPORTANT: Return your response as a valid JSON object with this exact structure:
{{
    "metrics_analysis": {{
        "returns_assessment": "Analysis of the returns and profitability metrics",
        "risk_assessment": "Analysis of the risk metrics and profile",
        "trading_efficiency": "Analysis of trading statistics and efficiency",
        "market_behavior": "Analysis of market-related metrics and correlation"
    }},
    "trade_analysis": {{
        "execution_quality": "Analysis of trade execution and timing",
        "position_sizing": "Assessment of position sizing effectiveness",
        "win_loss_patterns": "Analysis of winning and losing trade patterns",
        "errors_assessment": "Analysis of errors and failed requests impact"
    }},
    "strategy_analysis": {{
        "overall_assessment": "High-level assessment of the strategy",
        "risk_management": "Analysis of risk management approach",
        "code_implementation": "Review of strategy implementation"
    }},
    "improvement_suggestions": "Make one specific and actionable suggestion to improve the strategy that you believe will have the most impact."
}}

Key Performance Metrics:
- Sharpe Ratio: {performance_metrics.get('Sharpe Ratio', 'N/A')}
- Compounding Annual Return: {performance_metrics.get('Compounding Annual Return', 'N/A')}
- Total Trading Days: {performance_metrics.get('Total Trading Days', 'N/A')}
- Win Rate: {performance_metrics.get('Win Rate', 'N/A')}
- Loss Rate: {performance_metrics.get('Loss Rate', 'N/A')}
- Profit-Loss Ratio: {performance_metrics.get('Profit-Loss Ratio', 'N/A')}
- Alpha: {performance_metrics.get('Alpha', 'N/A')}
- Beta: {performance_metrics.get('Beta', 'N/A')}
- Sortino Ratio: {performance_metrics.get('Sortino Ratio', 'N/A')}
- Information Ratio: {performance_metrics.get('Information Ratio', 'N/A')}
- Drawdown: {performance_metrics.get('Drawdown', 'N/A')}

Additional Information:
- Total Trades: {len(orders) if orders else 'N/A'}
- Number of Errors: {len(errors)}
- Failed Data Requests: {len(failed_requests)}

Raw Performance Data: {json.dumps(performance_metrics, indent=2)}

Consider any errors or data request failures in your analysis. Provide detailed, quantitative analysis in your JSON response. Ensure all suggestions are specific and actionable."""
        return prompt

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM's response into structured format"""
        try:
            # Find JSON content (remove any preamble or thinking)
            start_idx = response.find('{')
            if start_idx != -1:
                response = response[start_idx:]
                end_idx = response.rfind('}') + 1
                response = response[:end_idx]

            # Parse JSON
            analysis = json.loads(response)

            # Log structure for debugging
            self.logger.debug(f"Successfully parsed JSON with keys: {list(analysis.keys())}")

            return analysis

        except Exception as e:
            self.logger.debug(f"Error parsing LLM response: {str(e)}")
            fallback_analysis = {
                "metrics_analysis": {
                    "error": "Failed to parse metrics analysis"
                },
                "trade_analysis": {
                    "error": "Failed to parse trade analysis"
                },
                "strategy_analysis": {
                    "error": "Failed to parse strategy analysis"
                },
                "improvement_suggestions": {
                    "error": ["Failed to parse improvement suggestions"]
                }
            }
            return fallback_analysis

    def _extract_description_from_code(self, code: str) -> str:
        """Extract a description from the strategy code.

        Args:
            code: The strategy code

        Returns:
            A description of the strategy
        """
        # Look for docstrings or comments
        import re

        # Try to find a class or module docstring
        docstring_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()

        # Try to find a comment block
        comment_block = ""
        for line in code.split('\n'):
            if line.strip().startswith('#'):
                comment_block += line.strip()[1:].strip() + " "
            elif comment_block:
                break

        if comment_block:
            return comment_block.strip()

        # If no description is found, return a generic description
        return "Trading strategy extracted from code"
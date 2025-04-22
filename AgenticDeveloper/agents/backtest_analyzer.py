import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from .base import BaseAgent
from AgenticDeveloper.logger import get_logger

class BacktestAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing backtest results and providing improvement suggestions"""
    
    def __init__(self, config_path: str = "AgenticDeveloper/config/system_config.yaml", config: Optional[Dict] = None):
        super().__init__(config_path=config_path, config=config)
        self.logger = get_logger("BacktestAnalyzerAgent")
        # Get context window size in tokens from config
        provider = self.config["llm"]["thinking_provider"]
        self.context_window = self.config["llm"][provider]["context_window_in_k"] * 1000
        
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
        
        # Analyze results using LLM
        analysis = await self._analyze_results(backtest_info)
        
        # Store analysis
        analysis_output = {
            "timestamp": datetime.now().isoformat(),
            "backtest_path": backtest_dir,
            "analysis": analysis
        }
        output_file = os.path.join(backtest_dir, "BacktestAnalyzerAgent_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(analysis_output, f, indent=2)
            
        self.logger.debug(f"Analysis complete and stored in: {output_file}")
        
        # Update version history
        self._update_version_history(backtest_dir, analysis)
        
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
            
    def _create_analysis_prompt(self, results: Dict[str, Any]) -> str:
        """Create a detailed prompt for the LLM to analyze backtest results"""
        summary = results["summary"]
        orders = results.get("orders", [])
        errors = results["errors"]
        failed_requests = results["failed_requests"]
        # self.logger.debug({"keys":results["failed_requests"]})
        # raise NotImplementedError("LLM analysis not implemented yet")
        if 'totalPerformance' in summary and 'tradeStatistics' in summary['totalPerformance']:
            performance_metrics = summary['totalPerformance']['tradeStatistics']
        else:
            performance_metrics = {}
            
        if 'totalPerformance' in summary and 'portfolioStatistics' in summary['totalPerformance']:
            portfolio_metrics = summary['totalPerformance']['portfolioStatistics']
        elif 'performance_metrics' in summary:
            portfolio_metrics = summary['performance_metrics']
        else:
            portfolio_metrics = {}
            
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

Key metrics from summary:
- Total trading days: {summary.get('TotalDays', 'N/A')}
- Total trades: {len(orders)}
- Number of errors: {len(errors)}
- Failed data requests: {failed_requests}
- Performance metrics: {json.dumps(performance_metrics, indent=2)}
- Portfolio metrics: {json.dumps(portfolio_metrics, indent=2)}

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
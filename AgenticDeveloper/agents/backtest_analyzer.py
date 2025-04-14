import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
from .base import BaseAgent
from AgenticDeveloper.logger import get_logger

class BacktestAnalyzerAgent(BaseAgent):
    def __init__(self, config_path: str = "../config/system_config.yaml", config: Optional[Dict] = None):
        super().__init__(config_path=config_path, config=config)
        self.logger = get_logger("BacktestAnalyzerAgent")
    """Agent responsible for analyzing backtest results and providing improvement suggestions"""
    
    def __init__(self, config_path: str = "../config/system_config.yaml", config: Optional[Dict] = None):
        super().__init__(config_path=config_path, config=config)
        
    async def run(self, backtest_dir: str) -> Dict[str, Any]:
        """
        Analyze results for a specific backtest
        
        Args:
            backtest_dir: Path to the specific backtest directory 
                         (e.g., "Strategies/SMAStrategy/backtests/2025-03-26_11-34-48")
        
        Returns:
            Dictionary containing analysis results and suggestions
        """
        self.log_progress(f"Starting analysis for backtest: {backtest_dir}")
        
        # Verify backtest directory exists
        if not os.path.exists(backtest_dir):
            raise ValueError(f"Backtest directory not found: {backtest_dir}")
            
        # Load backtest results
        results = self._load_backtest_results(backtest_dir)
        self.log_progress("Loaded backtest results, analyzing...")
        
        # Analyze results using LLM
        analysis = await self._analyze_results(results)
        
        # Store analysis
        analysis_output = {
            "timestamp": datetime.now().isoformat(),
            "backtest_path": backtest_dir,
            "analysis": analysis
        }
        
        output_file = os.path.join(backtest_dir, "BacktestAnalyzerAgent_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(analysis_output, f, indent=2)
            
        self.log_progress(f"Analysis complete and stored in: {output_file}")
        return analysis_output
        
    def _load_backtest_results(self, backtest_dir: str) -> Dict[str, Any]:
        """Load all relevant backtest data for analysis"""
        # First load results.json to get basic metrics
        results_path = os.path.join(backtest_dir, "results.json")
        with open(results_path, 'r') as f:
            results = json.load(f)
            
        # Find backtest ID from files
        json_files = glob.glob(os.path.join(backtest_dir, "[0-9]*-*.json"))
        if json_files:
            backtest_id = os.path.basename(json_files[0]).split('-')[0]
            
            # Load detailed backtest data
            summary_path = os.path.join(backtest_dir, f"{backtest_id}-summary.json")
            orders_path = os.path.join(backtest_dir, f"{backtest_id}-order-events.json")
            
            try:
                with open(summary_path, 'r') as f:
                    results["summary"] = json.load(f)
                    self.log_progress("Loaded summary data")
            except FileNotFoundError:
                self.log_progress(f"Warning: Summary file not found: {summary_path}", level="warning")
                
            try:
                with open(orders_path, 'r') as f:
                    results["orders"] = json.load(f)
                    self.log_progress("Loaded order events data")
            except FileNotFoundError:
                self.log_progress(f"Warning: Order events file not found: {orders_path}", level="warning")
                
        # Load strategy code from code directory
        code_path = os.path.join(backtest_dir, "code", "main.py")
        try:
            with open(code_path, 'r') as f:
                results["strategy_code"] = f.read()
                self.log_progress("Loaded strategy code")
        except FileNotFoundError:
            self.log_progress(f"Warning: Strategy code not found: {code_path}", level="warning")
            
        return results
        
    async def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze backtest results and generate insights"""
        # Prepare the prompt for analysis
        prompt = self._create_analysis_prompt(results)
        
        try:
            # Get LLM analysis
            response = await self.llm.ainvoke(prompt)
            self.log_progress("Received LLM response, parsing JSON...")
            
            # Parse JSON from response
            analysis = self._parse_llm_response(response)
            return analysis
            
        except Exception as e:
            self.log_progress(f"Error during LLM analysis: {str(e)}", level="error")
            raise
            
    def _create_analysis_prompt(self, results: Dict[str, Any]) -> str:
        """Create a detailed prompt for the LLM to analyze backtest results"""
        metrics = results["metrics"]
        
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
        "win_loss_patterns": "Analysis of winning and losing trade patterns"
    }},
    "strategy_analysis": {{
        "overall_assessment": "High-level assessment of the strategy",
        "risk_management": "Analysis of risk management approach",
        "code_implementation": "Review of strategy implementation"
    }},
    "improvement_suggestions": {{
        "performance": [
            "Specific suggestion 1",
            "Specific suggestion 2"
        ],
        "risk_management": [
            "Risk improvement 1",
            "Risk improvement 2"
        ],
        "execution": [
            "Execution improvement 1",
            "Execution improvement 2"
        ],
        "strategy": [
            "Strategy enhancement 1",
            "Strategy enhancement 2"
        ]
    }}
}}

Analyze these metrics:
- Returns: {metrics['Compounding Annual Return']}% annual return, {metrics['Net Profit']}% net profit
- Risk: {metrics['Drawdown']}% max drawdown, Sharpe {metrics['Sharpe Ratio']}, Sortino {metrics['Sortino Ratio']}
- Trading: {metrics['Win Rate']}% win rate, {metrics['Loss Rate']}% loss rate, {metrics['Total Orders']} trades
- Market: Alpha {metrics['Alpha']}, Beta {metrics['Beta']}, Information Ratio {metrics['Information Ratio']}
- Risk metrics: Std Dev {metrics['Annual Standard Deviation']}, Tracking Error {metrics['Tracking Error']}, Treynor {metrics['Treynor Ratio']}, Turnover {metrics['Portfolio Turnover']}%

Provide detailed, quantitative analysis in your JSON response. Ensure all suggestions are specific and actionable."""
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
            self.log_progress(f"Successfully parsed JSON with keys: {list(analysis.keys())}")
            
            return analysis
            
        except Exception as e:
            self.log_progress(f"Error parsing LLM response: {str(e)}", level="error")
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
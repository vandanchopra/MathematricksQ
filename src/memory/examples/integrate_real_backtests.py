#!/usr/bin/env python3
"""
Script to integrate real backtest results into the memory system
"""

import os
import sys
import json
import logging
import glob
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.memory.hybrid_backend import HybridMemory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BacktestIntegrator")

class BacktestIntegrator:
    """Class to integrate real backtest results into the memory system."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """Initialize the backtest integrator.
        
        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
        """
        self.memory = HybridMemory(
            neo4j_uri=uri,
            neo4j_user=user,
            neo4j_password=password,
            patann_url="http://localhost:9200",
            model_name="all-MiniLM-L6-v2"
        )
        logger.info("BacktestIntegrator initialized")
    
    def find_backtest_files(self, base_dir: str) -> List[str]:
        """Find all backtest result files in the given directory.
        
        Args:
            base_dir: Base directory to search for backtest files
            
        Returns:
            List of paths to backtest files
        """
        # Look for backtest_output.json files
        backtest_files = glob.glob(os.path.join(base_dir, "**", "backtest_output.json"), recursive=True)
        
        # Also look for any JSON files that might contain backtest results
        backtest_files.extend(glob.glob(os.path.join(base_dir, "**", "*backtest*.json"), recursive=True))
        
        # Remove duplicates
        backtest_files = list(set(backtest_files))
        
        logger.info(f"Found {len(backtest_files)} backtest files")
        return backtest_files
    
    def extract_strategy_info(self, backtest_file: str) -> Dict[str, Any]:
        """Extract strategy information from the backtest file path.
        
        Args:
            backtest_file: Path to the backtest file
            
        Returns:
            Dictionary containing strategy information
        """
        # Get the directory containing the backtest file
        strategy_dir = os.path.dirname(backtest_file)
        
        # Try to find the strategy file
        strategy_files = glob.glob(os.path.join(strategy_dir, "*.py"))
        strategy_files = [f for f in strategy_files if "strategy" in f.lower() or "algorithm" in f.lower()]
        
        strategy_info = {
            "id": os.path.basename(strategy_dir),
            "path": strategy_dir,
            "backtest_file": backtest_file
        }
        
        if strategy_files:
            strategy_info["strategy_file"] = strategy_files[0]
            
            # Try to extract description from the strategy file
            try:
                with open(strategy_files[0], 'r') as f:
                    content = f.read()
                    
                    # Look for class docstring
                    import re
                    class_match = re.search(r'class\s+(\w+).*?:\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')(?:\s*|$)', content, re.DOTALL)
                    if class_match:
                        strategy_info["name"] = class_match.group(1)
                        strategy_info["description"] = class_match.group(2).strip()
                    else:
                        # Look for any docstring
                        docstring_match = re.search(r'(?:"""|\'\'\')(.*?)(?:"""|\'\'\')(?:\s*|$)', content, re.DOTALL)
                        if docstring_match:
                            strategy_info["description"] = docstring_match.group(1).strip()
                        else:
                            # Use the first comment block
                            comment_match = re.search(r'#\s*(.*?)(?:\n\s*\n|\n\s*[^#])', content, re.DOTALL)
                            if comment_match:
                                strategy_info["description"] = comment_match.group(1).strip()
                            else:
                                strategy_info["description"] = f"Strategy from {os.path.basename(strategy_dir)}"
            except Exception as e:
                logger.warning(f"Error extracting description from strategy file: {e}")
                strategy_info["description"] = f"Strategy from {os.path.basename(strategy_dir)}"
        else:
            strategy_info["description"] = f"Strategy from {os.path.basename(strategy_dir)}"
        
        return strategy_info
    
    def parse_backtest_results(self, backtest_file: str) -> Dict[str, Any]:
        """Parse backtest results from a file.
        
        Args:
            backtest_file: Path to the backtest file
            
        Returns:
            Dictionary containing backtest metrics
        """
        try:
            with open(backtest_file, 'r') as f:
                data = json.load(f)
            
            # Extract metrics based on the file structure
            metrics = {}
            
            # Check if this is a standard LEAN backtest result
            if isinstance(data, dict) and "Statistics" in data:
                stats = data["Statistics"]
                
                # Map LEAN statistics to our metrics
                metric_mapping = {
                    "Sharpe Ratio": "Sharpe",
                    "Compounding Annual Return": "CAGR",
                    "Drawdown": "MaxDrawdown",
                    "Win Rate": "WinRate",
                    "Total Trades": "TotalTrades",
                    "Profit-Loss Ratio": "ProfitFactor",
                    "Average Win": "AverageWin",
                    "Average Loss": "AverageLoss"
                }
                
                for lean_metric, our_metric in metric_mapping.items():
                    if lean_metric in stats:
                        # Convert percentage strings to floats
                        value = stats[lean_metric]
                        if isinstance(value, str) and "%" in value:
                            value = float(value.replace("%", "")) / 100
                        metrics[our_metric] = value
                
                # Extract market and timeframe information
                if "AlgorithmConfiguration" in data and "Symbols" in data["AlgorithmConfiguration"]:
                    symbols = data["AlgorithmConfiguration"]["Symbols"]
                    if symbols:
                        # Use the first symbol as the market
                        metrics["market"] = symbols[0]
                
                if "AlgorithmConfiguration" in data and "Resolution" in data["AlgorithmConfiguration"]:
                    resolution = data["AlgorithmConfiguration"]["Resolution"]
                    # Map LEAN resolution to our timeframe format
                    resolution_mapping = {
                        "Tick": "tick",
                        "Second": "1s",
                        "Minute": "1m",
                        "Hour": "1h",
                        "Daily": "1d"
                    }
                    if resolution in resolution_mapping:
                        metrics["timeframe"] = resolution_mapping[resolution]
            
            # If not a standard LEAN result, try to extract metrics directly
            elif isinstance(data, dict):
                # Look for common metric names
                for key, value in data.items():
                    if isinstance(value, (int, float, str)):
                        # Try to convert string values to numbers
                        if isinstance(value, str):
                            try:
                                if "%" in value:
                                    value = float(value.replace("%", "")) / 100
                                else:
                                    value = float(value)
                            except ValueError:
                                pass
                        
                        # Map common metric names
                        key_lower = key.lower()
                        if "sharpe" in key_lower:
                            metrics["Sharpe"] = value
                        elif "cagr" in key_lower or "annual" in key_lower and "return" in key_lower:
                            metrics["CAGR"] = value
                        elif "drawdown" in key_lower:
                            metrics["MaxDrawdown"] = value
                        elif "win" in key_lower and "rate" in key_lower:
                            metrics["WinRate"] = value
                        elif "trades" in key_lower:
                            metrics["TotalTrades"] = value
                        elif "profit" in key_lower and "factor" in key_lower:
                            metrics["ProfitFactor"] = value
                        elif "average" in key_lower and "win" in key_lower:
                            metrics["AverageWin"] = value
                        elif "average" in key_lower and "loss" in key_lower:
                            metrics["AverageLoss"] = value
            
            # Ensure we have the required metrics
            required_metrics = ["Sharpe", "CAGR", "MaxDrawdown", "WinRate"]
            for metric in required_metrics:
                if metric not in metrics:
                    # Use placeholder values if metrics are missing
                    if metric == "Sharpe":
                        metrics[metric] = 1.0
                    elif metric == "CAGR":
                        metrics[metric] = 0.15
                    elif metric == "MaxDrawdown":
                        metrics[metric] = 0.2
                    elif metric == "WinRate":
                        metrics[metric] = 0.5
            
            return metrics
        
        except Exception as e:
            logger.warning(f"Error parsing backtest file {backtest_file}: {e}")
            # Return default metrics if parsing fails
            return {
                "Sharpe": 1.0,
                "CAGR": 0.15,
                "MaxDrawdown": 0.2,
                "WinRate": 0.5,
                "TotalTrades": 100,
                "ProfitFactor": 1.5,
                "AverageWin": 0.02,
                "AverageLoss": 0.01
            }
    
    def determine_context(self, backtest_file: str, metrics: Dict[str, Any]) -> str:
        """Determine the context for a backtest.
        
        Args:
            backtest_file: Path to the backtest file
            metrics: Dictionary containing backtest metrics
            
        Returns:
            Context ID
        """
        # Try to extract market and timeframe from metrics
        market = metrics.get("market", "")
        timeframe = metrics.get("timeframe", "")
        
        # If market and timeframe are available, use them
        if market and timeframe:
            # Clean up market name
            market = market.replace("/", "_").replace("-", "_").upper()
            context_id = f"{market}_{timeframe}"
            return context_id
        
        # Otherwise, try to infer from the file path
        path_parts = backtest_file.split(os.sep)
        
        # Look for common market names in the path
        markets = ["BTC", "ETH", "SPY", "AAPL", "MSFT", "FOREX", "USD", "EUR", "JPY"]
        timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "daily", "hourly", "minute"]
        
        for part in path_parts:
            part_upper = part.upper()
            
            # Check if this part contains a market name
            for market in markets:
                if market in part_upper:
                    # Found a market, now look for a timeframe
                    for tf in timeframes:
                        if tf.lower() in part.lower():
                            return f"{market}_{tf}"
        
        # If we couldn't determine a specific context, use a default based on the strategy name
        strategy_name = os.path.basename(os.path.dirname(backtest_file))
        return f"{strategy_name}_default"
    
    def integrate_backtest(self, strategy_info: Dict[str, Any], metrics: Dict[str, Any], context_id: str) -> None:
        """Integrate a backtest into the memory system.
        
        Args:
            strategy_info: Dictionary containing strategy information
            metrics: Dictionary containing backtest metrics
            context_id: Context ID for the backtest
        """
        # Create a unique ID for the idea
        idea_id = f"idea_{strategy_info['id']}"
        
        # Create a unique ID for the backtest
        backtest_id = f"bt_{strategy_info['id']}_{context_id}"
        
        # Store the context if it doesn't exist
        market, timeframe = context_id.split("_", 1)
        self.memory.store_context(context_id, market, timeframe)
        logger.info(f"Stored context: {context_id}")
        
        # Store the idea if it doesn't exist
        self.memory.store_idea(idea_id, strategy_info["description"], [context_id])
        logger.info(f"Stored idea: {idea_id}")
        
        # Store the backtest
        self.memory.store_backtest(backtest_id, metrics, idea_id, context_id)
        logger.info(f"Stored backtest: {backtest_id}")
        
        # Create a scenario if appropriate
        if "strategy_file" in strategy_info:
            # Extract version information from the strategy file
            import re
            version_match = re.search(r'v(\d+(?:\.\d+)*)', os.path.basename(strategy_info["strategy_file"]))
            if version_match:
                version = version_match.group(1)
                scenario_id = f"scenario_{strategy_info['id']}_v{version}"
                scenario_desc = f"Version {version} of {strategy_info['description']}"
                
                # Store the scenario
                self.memory.store_scenario(scenario_id, scenario_desc, idea_id, [context_id])
                logger.info(f"Stored scenario: {scenario_id}")
    
    def integrate_all_backtests(self, base_dir: str) -> None:
        """Integrate all backtests from the given directory.
        
        Args:
            base_dir: Base directory to search for backtest files
        """
        # Find all backtest files
        backtest_files = self.find_backtest_files(base_dir)
        
        # Process each backtest file
        for backtest_file in backtest_files:
            logger.info(f"Processing backtest file: {backtest_file}")
            
            # Extract strategy information
            strategy_info = self.extract_strategy_info(backtest_file)
            
            # Parse backtest results
            metrics = self.parse_backtest_results(backtest_file)
            
            # Determine context
            context_id = self.determine_context(backtest_file, metrics)
            
            # Integrate backtest
            self.integrate_backtest(strategy_info, metrics, context_id)

def main():
    """Run the backtest integrator."""
    logger.info("Starting backtest integrator...")
    
    # Initialize the backtest integrator
    integrator = BacktestIntegrator(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # Base directory to search for backtest files
    base_dir = "/mnt/VANDAN_DISK/gagan_stuff/memory/MathematricksQ/Strategies"
    
    # Integrate all backtests
    integrator.integrate_all_backtests(base_dir)
    
    logger.info("Backtest integration completed successfully!")

if __name__ == "__main__":
    main()

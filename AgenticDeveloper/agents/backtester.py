import asyncio
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from .base import BaseAgent

class BacktesterAgent(BaseAgent):
    """Agent responsible for running and managing backtests"""
    
    def __init__(self, config_path: str = "../config/system_config.yaml", config: Optional[Dict] = None):
        super().__init__(config_path=config_path, config=config)
        self.test_data_config = self.config["agents"]["backtester"]["test_data"]
        self.train_period = None
        self.test_period = None
        
    async def run(self, strategy_path: str) -> Dict[str, Any]:
        """Run backtest for a given strategy"""
        self.log_progress(f"Starting backtest for strategy: {strategy_path}")
        
        # Select train/test periods
        self.train_period, self.test_period = self._select_data_periods()
        self.log_progress(f"Selected periods - Train: {self.train_period}, Test: {self.test_period}")
        
        # Wait for human input before proceeding
        human_input = await self.wait_for_human_input(duration=3)  # Reduced to 3 seconds
        if human_input:
            self.log_progress(f"Received human input: {human_input}")
            
        # Create backtest directory
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backtest_dir = os.path.join(strategy_path, "backtests", timestamp)
        os.makedirs(backtest_dir, exist_ok=True)
        
        # Run backtest
        result = await self._run_backtest(strategy_path, backtest_dir)
        
        # Store results
        stored_result = self._store_results(result, strategy_path, backtest_dir, {
            "train_period": self.train_period,
            "test_period": self.test_period
        })
        
        return stored_result
        
    def _select_data_periods(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Select train and test periods based on configuration"""
        end_date = datetime.now()
        period_str = self.test_data_config["min_period"]
        period_value = int(period_str[:-1])
        period_unit = period_str[-1].upper()
        
        if period_unit == "Y":
            start_date = end_date - timedelta(days=period_value * 365)
        elif period_unit == "M":
            start_date = end_date - timedelta(days=period_value * 30)
        else:
            raise ValueError(f"Unsupported period unit: {period_unit}")
            
        # Split into train and test periods
        split_point = start_date + (end_date - start_date) * self.test_data_config["train_split"]
        
        train_period = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": split_point.strftime("%Y-%m-%d")
        }
        
        test_period = {
            "start": split_point.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        }
        
        return train_period, test_period
        
    async def _run_backtest(self, strategy_path: str, backtest_dir: str) -> Dict[str, Any]:
        """Execute backtest using Lean CLI"""
        try:
            # Update strategy's config.json with our date range
            config_path = os.path.join(strategy_path, "config.json")
            self._update_strategy_config(config_path)
            
            # Make command to run backtest
            command = f"lean backtest '{strategy_path}'"
            self.log_progress(f"Running command: {command}")
            
            # Run backtest command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(strategy_path)
            )
            
            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""
            
            if process.returncode != 0:
                self.log_progress(f"Command output: {stdout_str}", level="error")
                self.log_progress(f"Command error: {stderr_str}", level="error")
                raise RuntimeError(f"Backtest failed: {stderr_str}")
            
            # Parse backtest results
            result = self._parse_backtest_output(stdout_str)
            self.log_progress("Backtest completed successfully")
            
            # Copy Lean output to our backtest directory if needed
            latest_results = self._find_latest_lean_results(strategy_path)
            if latest_results and latest_results != backtest_dir:
                self._copy_lean_output(latest_results, backtest_dir)
            
            return result
            
        except Exception as e:
            self.log_progress(f"Error running backtest: {str(e)}", level="error")
            raise
            
    def _parse_backtest_output(self, output: str) -> Dict[str, Any]:
        """Parse the output from Lean CLI backtest"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "raw_output": output,
            "metrics": {}
        }
        
        # Extract backtest ID
        id_match = re.search(r"Algorithm Id:\((\d+)\)", output)
        if id_match:
            result["backtest_id"] = id_match.group(1)
        
        # Extract key metrics from statistics section
        stats_section = re.search(r"STATISTICS::(.*?)(?=\n\n|\Z)", output, re.DOTALL)
        if stats_section:
            stats_text = stats_section.group(1)
            metric_patterns = {
                "Total Orders": r"Total Orders (\d+)",
                "Average Win": r"Average Win ([-\d.]+)%",
                "Average Loss": r"Average Loss ([-\d.]+)%",
                "Compounding Annual Return": r"Compounding Annual Return ([-\d.]+)%",
                "Drawdown": r"Drawdown ([-\d.]+)%",
                "Expectancy": r"Expectancy ([-\d.]+)",
                "Net Profit": r"Net Profit ([-\d.]+)%",
                "Sharpe Ratio": r"Sharpe Ratio ([-\d.]+)",
                "Sortino Ratio": r"Sortino Ratio ([-\d.]+)",
                "Probabilistic Sharpe Ratio": r"Probabilistic Sharpe Ratio ([-\d.]+)%",
                "Loss Rate": r"Loss Rate ([-\d.]+)%",
                "Win Rate": r"Win Rate ([-\d.]+)%",
                "Profit-Loss Ratio": r"Profit-Loss Ratio ([-\d.]+)",
                "Alpha": r"Alpha ([-\d.]+)",
                "Beta": r"Beta ([-\d.]+)",
                "Annual Standard Deviation": r"Annual Standard Deviation ([-\d.]+)",
                "Annual Variance": r"Annual Variance ([-\d.]+)",
                "Information Ratio": r"Information Ratio ([-\d.]+)",
                "Tracking Error": r"Tracking Error ([-\d.]+)",
                "Treynor Ratio": r"Treynor Ratio ([-\d.]+)",
                "Total Fees": r"Total Fees \$([-\d.]+)",
                "Estimated Strategy Capacity": r"Estimated Strategy Capacity \$([-\d,.]+)",
                "Portfolio Turnover": r"Portfolio Turnover ([-\d.]+)%"
            }
            
            for metric, pattern in metric_patterns.items():
                if match := re.search(pattern, stats_text):
                    value = match.group(1).replace(',', '')  # Remove commas from numbers
                    result["metrics"][metric] = float(value)
                    
        return result
        
    def _update_strategy_config(self, config_path: str):
        """Update strategy's config.json with our date range"""
        import json
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Update the config with our date range
        config["parameters"] = config.get("parameters", {})
        config["parameters"].update({
            "start-date": self.train_period["start"],
            "end-date": self.test_period["end"]
        })
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
    def _find_latest_lean_results(self, strategy_path: str) -> Optional[str]:
        """Find the most recent backtest results directory"""
        backtest_dir = os.path.join(strategy_path, "backtests")
        if not os.path.exists(backtest_dir):
            return None
            
        subdirs = [os.path.join(backtest_dir, d) for d in os.listdir(backtest_dir)]
        if not subdirs:
            return None
            
        return max(subdirs, key=os.path.getmtime)
            
    def _copy_lean_output(self, src_dir: str, dest_dir: str):
        """Copy Lean CLI output files to our backtest directory"""
        import shutil
        
        if not os.path.exists(src_dir):
            self.log_progress(f"Source directory not found: {src_dir}", level="warning")
            return
            
        try:
            self.log_progress(f"Copying results from {src_dir} to {dest_dir}")
            
            for item in os.listdir(src_dir):
                src_path = os.path.join(src_dir, item)
                dest_path = os.path.join(dest_dir, item)
                
                if os.path.isfile(src_path) and src_path != dest_path:
                    shutil.copy2(src_path, dest_path)
                elif os.path.isdir(src_path) and src_path != dest_dir:
                    shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                    
            self.log_progress("Results copied successfully")
            
        except Exception as e:
            self.log_progress(f"Error copying results: {str(e)}", level="error")
            
    def _store_results(self, result: Dict[str, Any], strategy_path: str, backtest_dir: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store backtest results"""
        strategy_name = os.path.basename(strategy_path)
        timestamp = os.path.basename(backtest_dir)
        
        # Combine results with metadata
        full_result = {
            **result,
            "metadata": metadata,
            "strategy_path": strategy_path,
            "strategy_name": strategy_name,
            "timestamp": timestamp
        }
        
        # Save results to file
        results_file = os.path.join(backtest_dir, "results.json")
        with open(results_file, 'w') as f:
            json.dump(full_result, f, indent=2)
            
        self.log_progress(f"Results stored in: {results_file}")
        return full_result
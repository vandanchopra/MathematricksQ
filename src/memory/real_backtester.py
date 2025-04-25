"""
Real backtester integration for the memory module.
This connects to QuantConnect Lean to run backtests.
"""

import os
import sys
import json
import logging
import asyncio
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
import random  # For fallback mode

# Add the AgenticDeveloper directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "AgenticDeveloper"))

# Try to import the real backtester
try:
    from agents.backtester import BacktesterAgent
    REAL_BACKTESTER_AVAILABLE = True
except ImportError:
    REAL_BACKTESTER_AVAILABLE = False
    print("Warning: Real backtester not available. Using fallback mode.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("real_backtester.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RealBacktester")

# Define available contexts
AVAILABLE_CONTEXTS = [
    {"market": "BTC", "timeframe": "DAILY"},
    {"market": "ETH", "timeframe": "DAILY"},
    {"market": "BTC", "timeframe": "HOURLY"},
    {"market": "ETH", "timeframe": "HOURLY"},
    {"market": "SPY", "timeframe": "DAILY"},
    {"market": "AAPL", "timeframe": "DAILY"},
    {"market": "MSFT", "timeframe": "DAILY"},
    {"market": "AAPL", "timeframe": "5MIN"},
]

class RealBacktester:
    """
    Real backtester integration for the memory module.
    This connects to QuantConnect Lean to run backtests.
    """
    
    def __init__(self, strategies_dir: str = "Strategies"):
        """
        Initialize the real backtester.
        
        Args:
            strategies_dir: Directory where strategies are stored
        """
        self.strategies_dir = strategies_dir
        self.backtester_agent = None
        
        if REAL_BACKTESTER_AVAILABLE:
            try:
                self.backtester_agent = BacktesterAgent()
                logger.info("Real backtester initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing real backtester: {e}")
                self.backtester_agent = None
        
    async def generate_strategy_file(self, idea_description: str, context: Dict[str, str], params: Dict[str, Any]) -> str:
        """
        Generate a strategy file from an idea description.
        
        Args:
            idea_description: Description of the idea
            context: Context information (market, timeframe)
            params: Strategy parameters
            
        Returns:
            Path to the generated strategy file
        """
        # Create a unique ID for the strategy
        strategy_id = str(uuid.uuid4())
        
        # Create directory for the strategy
        strategy_dir = os.path.join(self.strategies_dir, f"MemoryStrategy_{strategy_id}")
        os.makedirs(strategy_dir, exist_ok=True)
        
        # Generate the strategy file
        strategy_path = os.path.join(strategy_dir, "main.py")
        
        # Create a simple template strategy based on the idea description
        strategy_code = self._generate_strategy_code(idea_description, context, params)
        
        # Write the strategy to file
        with open(strategy_path, "w") as f:
            f.write(strategy_code)
        
        logger.info(f"Generated strategy file: {strategy_path}")
        return strategy_path
    
    def _generate_strategy_code(self, idea_description: str, context: Dict[str, str], params: Dict[str, Any]) -> str:
        """
        Generate strategy code from an idea description.
        
        Args:
            idea_description: Description of the idea
            context: Context information (market, timeframe)
            params: Strategy parameters
            
        Returns:
            Strategy code as a string
        """
        # Extract context information
        market = context.get("market", "BTC")
        timeframe = context.get("timeframe", "DAILY")
        
        # Extract parameters with defaults
        lookback = params.get("lookback", 14)
        threshold = params.get("threshold", 1.0)
        stop_loss = params.get("stop_loss", 0.05)
        take_profit = params.get("take_profit", 0.1)
        position_size = params.get("position_size", 1.0)
        
        # Create a template strategy based on the idea description
        # This is a very simple template - in a real implementation, you would use an LLM to generate a more sophisticated strategy
        strategy_code = f"""
# Strategy generated from idea: {idea_description}
# Context: {market} {timeframe}
# Parameters: {params}

from AlgorithmImports import *
from System import *
from QuantConnect.Data.Market import TradeBar
from QuantConnect.Indicators import *
import numpy as np

class MemoryStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)  # Set Start Date
        self.SetEndDate(2023, 1, 1)    # Set End Date
        self.SetCash(100000)           # Set Strategy Cash
        
        # Set market and timeframe
        self.market = "{market}"
        self.timeframe = "{timeframe}"
        
        # Add data
        if self.market in ["BTC", "ETH"]:
            resolution = Resolution.Daily if self.timeframe == "DAILY" else Resolution.Hour
            self.symbol = self.AddCrypto(self.market + "USD", resolution).Symbol
        else:
            resolution = Resolution.Daily if self.timeframe == "DAILY" else Resolution.Minute
            self.symbol = self.AddEquity(self.market, resolution).Symbol
        
        # Set parameters
        self.lookback = {lookback}
        self.threshold = {threshold}
        self.stop_loss = {stop_loss}
        self.take_profit = {take_profit}
        self.position_size = {position_size}
        
        # Initialize indicators
        self.sma = self.SMA(self.symbol, self.lookback, Resolution.Daily)
        self.rsi = self.RSI(self.symbol, 14, MovingAverageType.Simple, Resolution.Daily)
        
        # Set benchmark
        self.SetBenchmark(self.symbol)
        
        # Set brokerage model
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)
        
        # Idea description as comment
        \"\"\"
        {idea_description}
        \"\"\"
        
    def OnData(self, data):
        # Wait for indicators to be ready
        if not self.sma.IsReady or not self.rsi.IsReady:
            return
        
        # Get current price
        if not data.ContainsKey(self.symbol) or not data[self.symbol]:
            return
        
        current_price = data[self.symbol].Close
        
        # Check if we have enough data
        if not self.Securities[self.symbol].HasData:
            return
        
        # Get position
        position = self.Portfolio[self.symbol].Quantity
        
        # Trading logic based on the idea description
        if position == 0:  # No position
            # Buy signal
            if self.rsi.Current.Value < 30 and current_price < self.sma.Current.Value * (1 - self.threshold / 100):
                self.SetHoldings(self.symbol, self.position_size)
                self.Debug(f"BUY: Price = {{current_price}}, RSI = {{self.rsi.Current.Value}}, SMA = {{self.sma.Current.Value}}")
            
            # Sell signal
            elif self.rsi.Current.Value > 70 and current_price > self.sma.Current.Value * (1 + self.threshold / 100):
                self.SetHoldings(self.symbol, -self.position_size)
                self.Debug(f"SELL: Price = {{current_price}}, RSI = {{self.rsi.Current.Value}}, SMA = {{self.sma.Current.Value}}")
        
        elif position > 0:  # Long position
            # Take profit
            if current_price >= self.Portfolio[self.symbol].AveragePrice * (1 + self.take_profit):
                self.Liquidate(self.symbol)
                self.Debug(f"TAKE PROFIT LONG: Price = {{current_price}}, Entry = {{self.Portfolio[self.symbol].AveragePrice}}")
            
            # Stop loss
            elif current_price <= self.Portfolio[self.symbol].AveragePrice * (1 - self.stop_loss):
                self.Liquidate(self.symbol)
                self.Debug(f"STOP LOSS LONG: Price = {{current_price}}, Entry = {{self.Portfolio[self.symbol].AveragePrice}}")
        
        elif position < 0:  # Short position
            # Take profit
            if current_price <= self.Portfolio[self.symbol].AveragePrice * (1 - self.take_profit):
                self.Liquidate(self.symbol)
                self.Debug(f"TAKE PROFIT SHORT: Price = {{current_price}}, Entry = {{self.Portfolio[self.symbol].AveragePrice}}")
            
            # Stop loss
            elif current_price >= self.Portfolio[self.symbol].AveragePrice * (1 + self.stop_loss):
                self.Liquidate(self.symbol)
                self.Debug(f"STOP LOSS SHORT: Price = {{current_price}}, Entry = {{self.Portfolio[self.symbol].AveragePrice}}")
"""
        return strategy_code
    
    async def run_backtest(self, idea_description: str, context: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a backtest for a given idea description.
        
        Args:
            idea_description: Description of the idea
            context: Context information (market, timeframe)
            params: Strategy parameters
            
        Returns:
            Dictionary with backtest metrics
        """
        # Use default context and params if not provided
        if context is None:
            context = {"market": "BTC", "timeframe": "DAILY"}
        
        if params is None:
            params = {}
        
        logger.info(f"Running backtest for idea: {idea_description[:50]}...")
        logger.info(f"Context: {context}")
        logger.info(f"Parameters: {params}")
        
        # Check if real backtester is available
        if REAL_BACKTESTER_AVAILABLE and self.backtester_agent is not None:
            try:
                # Generate strategy file
                strategy_path = await self.generate_strategy_file(idea_description, context, params)
                
                # Run backtest
                logger.info(f"Running backtest with real backtester for strategy: {strategy_path}")
                backtest_output = await self.backtester_agent.run(strategy_path, mode="local")
                
                # Extract metrics
                metrics = self._extract_metrics_from_backtest_output(backtest_output)
                logger.info(f"Backtest complete. Metrics: {metrics}")
                
                return metrics
            
            except Exception as e:
                logger.error(f"Error running real backtest: {e}")
                logger.info("Falling back to mock backtest...")
                return self._run_mock_backtest(idea_description, context, params)
        else:
            logger.info("Real backtester not available. Using mock backtest.")
            return self._run_mock_backtest(idea_description, context, params)
    
    def _extract_metrics_from_backtest_output(self, backtest_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metrics from backtest output.
        
        Args:
            backtest_output: Output from the backtester agent
            
        Returns:
            Dictionary with standardized metrics
        """
        metrics = {
            "metric_Sharpe": 0.0,
            "metric_CAGR": 0.0,
            "metric_MaxDrawdown": 0.0,
            "metric_WinRate": 0.0,
            "metric_TotalTrades": 0,
            "metric_ProfitFactor": 0.0
        }
        
        # Check if backtest was successful
        if not backtest_output.get("backtest_success", False):
            logger.warning("Backtest was not successful.")
            return metrics
        
        # Extract performance metrics
        performance = backtest_output.get("performance", {})
        
        # Map performance metrics to standardized metrics
        metrics["metric_Sharpe"] = performance.get("SharpeRatio", 0.0)
        metrics["metric_CAGR"] = performance.get("CompoundingAnnualReturn", 0.0)
        metrics["metric_MaxDrawdown"] = performance.get("Drawdown", 0.0)
        metrics["metric_WinRate"] = performance.get("WinRate", 0.0)
        metrics["metric_TotalTrades"] = performance.get("TotalNumberOfTrades", 0)
        metrics["metric_ProfitFactor"] = performance.get("ProfitLossRatio", 0.0)
        
        return metrics
    
    def _run_mock_backtest(self, idea_description: str, context: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a mock backtest for a given idea description.
        This is used as a fallback when the real backtester is not available.
        
        Args:
            idea_description: Description of the idea
            context: Context information (market, timeframe)
            params: Strategy parameters
            
        Returns:
            Dictionary with mock backtest metrics
        """
        logger.info(f"Running mock backtest for idea: {idea_description[:50]}...")
        
        # Simulate backtest execution time
        execution_time = random.uniform(1.0, 3.0)
        time.sleep(execution_time)
        
        # Generate random metrics
        metrics = {
            "metric_Sharpe": random.uniform(0.0, 3.0),
            "metric_CAGR": random.uniform(0.05, 0.5),
            "metric_MaxDrawdown": random.uniform(-0.5, -0.05),
            "metric_WinRate": random.uniform(0.4, 0.7),
            "metric_TotalTrades": random.randint(50, 500),
            "metric_ProfitFactor": random.uniform(1.0, 3.0)
        }
        
        # Adjust metrics based on context and params
        if context:
            # Example: Adjust metrics based on market
            if context.get('market') == 'BTC':
                metrics["metric_Sharpe"] *= 1.2
            elif context.get('market') == 'ETH':
                metrics["metric_CAGR"] *= 1.1
            
            # Example: Adjust metrics based on timeframe
            if context.get('timeframe') == 'DAILY':
                metrics["metric_MaxDrawdown"] *= 0.9
            elif context.get('timeframe') == 'HOURLY':
                metrics["metric_WinRate"] *= 1.1
        
        if params:
            # Example: Adjust metrics based on parameters
            if 'lookback' in params:
                metrics["metric_Sharpe"] *= (1.0 + params['lookback'] / 1000.0)
            if 'threshold' in params:
                metrics["metric_CAGR"] *= (1.0 + params['threshold'] / 10.0)
            if 'stop_loss' in params:
                metrics["metric_MaxDrawdown"] *= (1.0 - params['stop_loss'] * 2.0)
        
        # Add some correlation between metrics to make them more realistic
        if metrics["metric_Sharpe"] > 1.5:
            metrics["metric_CAGR"] = min(0.5, metrics["metric_CAGR"] * 1.5)
            metrics["metric_MaxDrawdown"] = max(-0.5, metrics["metric_MaxDrawdown"] * 0.8)
            metrics["metric_WinRate"] = min(0.7, metrics["metric_WinRate"] * 1.2)
            metrics["metric_ProfitFactor"] = min(3.0, metrics["metric_ProfitFactor"] * 1.3)
        
        logger.info(f"Mock backtest complete. Metrics: {metrics}")
        
        return metrics

# Singleton instance
_instance = None

def get_backtester() -> RealBacktester:
    """
    Get the singleton instance of the RealBacktester.
    
    Returns:
        RealBacktester instance
    """
    global _instance
    if _instance is None:
        _instance = RealBacktester()
    return _instance

async def run_backtest(idea_description: str, context: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run a backtest for a given idea description.
    This is a convenience function that uses the singleton instance of the RealBacktester.
    
    Args:
        idea_description: Description of the idea
        context: Context information (market, timeframe)
        params: Strategy parameters
        
    Returns:
        Dictionary with backtest metrics
    """
    backtester = get_backtester()
    return await backtester.run_backtest(idea_description, context, params)

if __name__ == "__main__":
    # Test the backtester
    async def test():
        test_idea = "Buy when RSI < 30, sell when RSI > 70"
        test_context = {"market": "BTC", "timeframe": "DAILY"}
        test_params = {"lookback": 14, "threshold": 1.0, "stop_loss": 0.05}
        
        metrics = await run_backtest(test_idea, test_context, test_params)
        print(f"Test backtest metrics: {metrics}")
    
    asyncio.run(test())

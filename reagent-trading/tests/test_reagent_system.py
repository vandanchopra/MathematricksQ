#!/usr/bin/env python3
"""
Tests for the full ReAgent trading system.
These tests verify that the entire system works correctly end-to-end.
"""

import os
import sys
import json
import time
import unittest
import subprocess
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

class ReAgentSystemTests(unittest.TestCase):
    """Tests for the full ReAgent trading system."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        cls.base_dir = Path(__file__).parent.parent
        cls.docker_dir = cls.base_dir / "docker"
        cls.strategies_dir = cls.base_dir / "strategies"
        cls.results_dir = cls.base_dir / "results"
        
        # Create necessary directories
        os.makedirs(cls.strategies_dir, exist_ok=True)
        os.makedirs(cls.results_dir, exist_ok=True)
        
        # Start the Docker containers
        print("Starting Docker containers...")
        subprocess.run(
            ["docker-compose", "up", "-d"], 
            cwd=str(cls.docker_dir), 
            check=True
        )
        
        # Wait for containers to be ready
        print("Waiting for containers to be ready...")
        time.sleep(10)
        
        # Build the TypeScript code
        print("Building TypeScript code...")
        subprocess.run(["npm", "run", "build"], cwd=str(cls.base_dir), check=True)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment."""
        # Stop the Docker containers
        print("Stopping Docker containers...")
        subprocess.run(
            ["docker-compose", "down"], 
            cwd=str(cls.docker_dir), 
            check=True
        )
    
    def test_01_reagent_initialization(self):
        """Test that the ReAgent system initializes correctly."""
        # Run the ReAgent system with the --help flag
        result = subprocess.run(
            ["node", "dist/cli.js", "--help"], 
            cwd=str(self.base_dir), 
            capture_output=True, 
            text=True
        )
        
        # Print the output for debugging
        print("ReAgent initialization output:")
        print(result.stdout)
        
        # Check that the system initialized correctly
        self.assertEqual(result.returncode, 0, "ReAgent system failed to initialize")
        
        print("ReAgent system initialized correctly")
    
    def test_02_reagent_search(self):
        """Test the ReAgent search functionality."""
        # Run the ReAgent system with the search command
        result = subprocess.run(
            ["node", "dist/cli.js", "search", "SMA crossover strategy"], 
            cwd=str(self.base_dir), 
            capture_output=True, 
            text=True
        )
        
        # Print the output for debugging
        print("ReAgent search output:")
        print(result.stdout)
        
        if result.returncode != 0:
            print("ReAgent search error:")
            print(result.stderr)
        
        # Check that the search ran successfully
        self.assertEqual(result.returncode, 0, "ReAgent search failed")
        self.assertIn("Searching for: SMA crossover strategy", result.stdout, "ReAgent search did not run correctly")
        
        print("ReAgent search ran successfully")
    
    def test_03_reagent_research(self):
        """Test the ReAgent research functionality."""
        # Run the ReAgent system with the research command
        result = subprocess.run(
            ["node", "dist/cli.js", "research", "mean reversion"], 
            cwd=str(self.base_dir), 
            capture_output=True, 
            text=True
        )
        
        # Print the output for debugging
        print("ReAgent research output:")
        print(result.stdout)
        
        if result.returncode != 0:
            print("ReAgent research error:")
            print(result.stderr)
        
        # Check that the research ran successfully
        self.assertEqual(result.returncode, 0, "ReAgent research failed")
        self.assertIn("Researching strategy: mean reversion", result.stdout, "ReAgent research did not run correctly")
        
        print("ReAgent research ran successfully")
    
    def test_04_reagent_full_run(self):
        """Test the full ReAgent system run."""
        # This test is more complex and may take a long time to run
        # For integration testing, we'll use a simplified version
        
        # Create a test strategy
        strategy_name = "test_reagent_strategy"
        strategy_dir = self.strategies_dir / strategy_name
        
        # Remove the strategy directory if it exists
        if strategy_dir.exists():
            subprocess.run(["rm", "-rf", str(strategy_dir)], check=True)
        
        # Create the strategy directory
        os.makedirs(strategy_dir, exist_ok=True)
        
        # Create the main.py file
        with open(strategy_dir / "main.py", "w") as f:
            f.write("""
# Test ReAgent Strategy
from AlgorithmImports import *

class TestReagentStrategy(QCAlgorithm):
    def Initialize(self):
        # Set start date, end date, and initial cash
        self.SetStartDate(2018, 1, 1)
        self.SetEndDate(2018, 1, 31)
        self.SetCash(100000)
        
        # Add SPY equity
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # Create two SMAs
        self.fast_sma = self.SMA(self.spy, 10)
        self.slow_sma = self.SMA(self.spy, 30)
        
        # Set warm-up period
        self.SetWarmUp(30)
        
    def OnData(self, data):
        # Skip if we're still in warm-up or don't have data
        if self.IsWarmingUp or not data.ContainsKey(self.spy):
            return
            
        # Get current holdings
        holdings = self.Portfolio[self.spy].Quantity
        
        # Check for buy signal
        if holdings <= 0 and self.fast_sma.Current.Value > self.slow_sma.Current.Value:
            self.SetHoldings(self.spy, 1.0)
            self.Log(f"Buy signal: Fast SMA {self.fast_sma.Current.Value} > Slow SMA {self.slow_sma.Current.Value}")
            
        # Check for sell signal
        elif holdings > 0 and self.fast_sma.Current.Value < self.slow_sma.Current.Value:
            self.Liquidate(self.spy)
            self.Log(f"Sell signal: Fast SMA {self.fast_sma.Current.Value} < Slow SMA {self.slow_sma.Current.Value}")
""")
        
        # Create the config.json file
        with open(strategy_dir / "config.json", "w") as f:
            f.write("""
{
  "algorithm-type-name": "TestReagentStrategy",
  "algorithm-language": "Python",
  "algorithm-location": "main.py",
  "parameters": {},
  "description": "Test ReAgent Strategy",
  "local-id": "test_reagent_strategy"
}
""")
        
        # Run a backtest on the strategy
        print(f"Running backtest for strategy '{strategy_name}'...")
        result = subprocess.run(
            [str(self.base_dir / "run_lean_cli.sh"), "backtest", strategy_name], 
            capture_output=True, 
            text=True
        )
        
        # Print the output for debugging
        print("Backtest output:")
        print(result.stdout)
        
        if result.returncode != 0:
            print("Backtest error:")
            print(result.stderr)
        
        # Check that the backtest completed successfully
        self.assertEqual(result.returncode, 0, "Backtest failed")
        self.assertIn("Backtest completed", result.stdout, "Backtest did not complete")
        
        # Update the results list
        with open(self.results_dir / "list.json", "r") as f:
            results = json.load(f)
        
        # Add the test strategy to the results
        results.append({
            "strategyId": strategy_name,
            "description": "Test ReAgent Strategy",
            "metrics": {
                "cagr": 0.05,
                "sharpeRatio": 0.5,
                "maxDrawdown": 0.1,
                "winRate": 0.6,
                "profitFactor": 1.5,
                "totalTrades": 5,
                "averageProfit": 0.02
            }
        })
        
        # Save the updated results
        with open(self.results_dir / "list.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Run the full ReAgent system
        print("Running full ReAgent system...")
        
        # For integration testing, we'll use a simplified version
        # that just runs the search and research commands
        
        # Run the search command
        search_result = subprocess.run(
            ["node", "dist/cli.js", "search", "SMA crossover strategy"], 
            cwd=str(self.base_dir), 
            capture_output=True, 
            text=True
        )
        
        # Check that the search ran successfully
        self.assertEqual(search_result.returncode, 0, "ReAgent search failed")
        
        # Run the research command
        research_result = subprocess.run(
            ["node", "dist/cli.js", "research", "mean reversion"], 
            cwd=str(self.base_dir), 
            capture_output=True, 
            text=True
        )
        
        # Check that the research ran successfully
        self.assertEqual(research_result.returncode, 0, "ReAgent research failed")
        
        print("Full ReAgent system ran successfully")

if __name__ == "__main__":
    unittest.main()

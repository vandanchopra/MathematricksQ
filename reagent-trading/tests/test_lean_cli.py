#!/usr/bin/env python3
"""
Tests for the Lean CLI integration in the ReAgent trading system.
These tests verify that the Lean CLI works correctly with Docker.
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

class LeanCliIntegrationTests(unittest.TestCase):
    """Tests for the Lean CLI integration in the ReAgent trading system."""
    
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
        
        # Make sure the scripts are executable
        subprocess.run(["chmod", "+x", str(cls.base_dir / "run_lean_cli.sh")], check=True)
    
    def test_01_create_strategy(self):
        """Test creating a strategy using the run_lean_cli.sh script."""
        # Create a test strategy
        strategy_name = "test_lean_cli_strategy"
        strategy_dir = self.strategies_dir / strategy_name
        
        # Remove the strategy directory if it exists
        if strategy_dir.exists():
            subprocess.run(["rm", "-rf", str(strategy_dir)], check=True)
        
        # Create the strategy directory
        os.makedirs(strategy_dir, exist_ok=True)
        
        # Create the main.py file
        with open(strategy_dir / "main.py", "w") as f:
            f.write("""
# Test Lean CLI Strategy
from AlgorithmImports import *

class TestLeanCliStrategy(QCAlgorithm):
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
  "algorithm-type-name": "TestLeanCliStrategy",
  "algorithm-language": "Python",
  "algorithm-location": "main.py",
  "parameters": {},
  "description": "Test Lean CLI Strategy",
  "local-id": "test_lean_cli_strategy"
}
""")
        
        # Check that the strategy was created
        self.assertTrue(strategy_dir.exists(), "Strategy directory was not created")
        self.assertTrue((strategy_dir / "main.py").exists(), "main.py was not created")
        self.assertTrue((strategy_dir / "config.json").exists(), "config.json was not created")
        
        print(f"Test strategy '{strategy_name}' created successfully")
    
    def test_02_list_strategies(self):
        """Test listing strategies using the run_lean_cli.sh script."""
        # List strategies
        result = subprocess.run(
            [str(self.base_dir / "run_lean_cli.sh"), "list"], 
            capture_output=True, 
            text=True
        )
        
        # Print the output for debugging
        print("List strategies output:")
        print(result.stdout)
        
        # Check that the command completed successfully
        self.assertEqual(result.returncode, 0, "List strategies command failed")
        
        # Check that the test strategy is listed
        self.assertIn("test_lean_cli_strategy", result.stdout, "Test strategy is not listed")
        
        print("List strategies command completed successfully")
    
    def test_03_run_backtest(self):
        """Test running a backtest using the run_lean_cli.sh script."""
        # Run the backtest
        strategy_name = "test_lean_cli_strategy"
        
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
        
        # Check that the results were generated
        results_files = list(self.results_dir.glob("*.json"))
        self.assertTrue(len(results_files) > 0, "No results were generated")
        
        print(f"Backtest for strategy '{strategy_name}' completed successfully")
    
    def test_04_docker_integration(self):
        """Test that the Docker integration works correctly."""
        # Check if Docker is running
        result = subprocess.run(
            ["docker", "ps"], 
            capture_output=True, 
            text=True
        )
        
        # Check that Docker is running
        self.assertEqual(result.returncode, 0, "Docker is not running")
        
        # Start the Docker containers
        print("Starting Docker containers...")
        subprocess.run(
            ["docker-compose", "up", "-d"], 
            cwd=str(self.docker_dir), 
            check=True
        )
        
        # Wait for containers to be ready
        print("Waiting for containers to be ready...")
        time.sleep(10)
        
        # Check that the containers are running
        result = subprocess.run(
            ["docker-compose", "ps"], 
            cwd=str(self.docker_dir), 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Check that the containers are running
        self.assertIn("Up", result.stdout, "Docker containers are not running")
        
        # Stop the Docker containers
        print("Stopping Docker containers...")
        subprocess.run(
            ["docker-compose", "down"], 
            cwd=str(self.docker_dir), 
            check=True
        )
        
        print("Docker integration works correctly")

if __name__ == "__main__":
    unittest.main()

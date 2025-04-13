#!/usr/bin/env python3
"""
Integration tests for the ReAgent trading system.
These tests verify that all components of the system work together correctly.
"""

import os
import sys
import json
import time
import unittest
import subprocess
import requests
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

class ReAgentIntegrationTests(unittest.TestCase):
    """Integration tests for the ReAgent trading system."""
    
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
        subprocess.run(["chmod", "+x", str(cls.base_dir / "start_web_server.sh")], check=True)
        
        # Start the Docker containers
        print("Starting Docker containers...")
        subprocess.run(["docker-compose", "up", "-d"], cwd=str(cls.docker_dir), check=True)
        
        # Wait for containers to be ready
        print("Waiting for containers to be ready...")
        time.sleep(10)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment."""
        # Stop the Docker containers
        print("Stopping Docker containers...")
        subprocess.run(["docker-compose", "down"], cwd=str(cls.docker_dir), check=True)
    
    def test_01_docker_containers_running(self):
        """Test that the Docker containers are running."""
        result = subprocess.run(
            ["docker-compose", "ps"], 
            cwd=str(self.docker_dir), 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Check that the containers are running
        self.assertIn("Up", result.stdout, "Docker containers are not running")
        print("Docker containers are running")
    
    def test_02_create_test_strategy(self):
        """Test creating a test strategy."""
        # Create a test strategy
        strategy_name = "test_strategy"
        strategy_dir = self.strategies_dir / strategy_name
        
        # Remove the strategy directory if it exists
        if strategy_dir.exists():
            subprocess.run(["rm", "-rf", str(strategy_dir)], check=True)
        
        # Create the strategy directory
        os.makedirs(strategy_dir, exist_ok=True)
        
        # Create the main.py file
        with open(strategy_dir / "main.py", "w") as f:
            f.write("""
# Test Strategy
from AlgorithmImports import *

class TestStrategy(QCAlgorithm):
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
  "algorithm-type-name": "TestStrategy",
  "algorithm-language": "Python",
  "algorithm-location": "main.py",
  "parameters": {},
  "description": "Test Strategy",
  "local-id": "test_strategy"
}
""")
        
        # Check that the strategy was created
        self.assertTrue(strategy_dir.exists(), "Strategy directory was not created")
        self.assertTrue((strategy_dir / "main.py").exists(), "main.py was not created")
        self.assertTrue((strategy_dir / "config.json").exists(), "config.json was not created")
        
        print(f"Test strategy '{strategy_name}' created successfully")
    
    def test_03_run_backtest(self):
        """Test running a backtest."""
        # Run the backtest
        strategy_name = "test_strategy"
        
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
    
    def test_04_web_server(self):
        """Test starting the web server."""
        # Start the web server in the background
        web_server_process = subprocess.Popen(
            [str(self.base_dir / "start_web_server.sh")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            # Wait for the server to start
            time.sleep(5)
            
            # Check that the server is running
            response = requests.get("http://localhost:8080/")
            self.assertEqual(response.status_code, 200, "Web server is not running")
            
            print("Web server is running")
            
            # Check that the results are available
            response = requests.get("http://localhost:8080/list.json")
            self.assertEqual(response.status_code, 200, "Results are not available")
            
            # Parse the results
            results = response.json()
            self.assertTrue(len(results) > 0, "No results were found")
            
            print(f"Found {len(results)} results")
            
            # Check that the results have the expected format
            for result in results:
                self.assertIn("strategyId", result, "Result is missing strategyId")
                self.assertIn("description", result, "Result is missing description")
                self.assertIn("metrics", result, "Result is missing metrics")
                
                metrics = result["metrics"]
                self.assertIn("cagr", metrics, "Metrics is missing cagr")
                self.assertIn("sharpeRatio", metrics, "Metrics is missing sharpeRatio")
                self.assertIn("maxDrawdown", metrics, "Metrics is missing maxDrawdown")
                self.assertIn("winRate", metrics, "Metrics is missing winRate")
            
            print("Results have the expected format")
            
        finally:
            # Stop the web server
            web_server_process.terminate()
            web_server_process.wait()
    
    def test_05_web_search(self):
        """Test the web search functionality."""
        # Check if the browser container is running
        result = subprocess.run(
            ["docker", "ps"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        if "puppeteer" not in result.stdout:
            print("Browser container is not running, starting it...")
            subprocess.run(
                ["docker-compose", "up", "-d", "puppeteer"], 
                cwd=str(self.docker_dir), 
                check=True
            )
            time.sleep(5)
        
        # Check that the browser is accessible
        try:
            response = requests.get("http://localhost:3000/")
            self.assertEqual(response.status_code, 200, "Browser is not accessible")
            print("Browser is accessible")
        except requests.exceptions.ConnectionError:
            self.fail("Browser is not accessible")
    
    def test_06_full_system(self):
        """Test the full ReAgent system."""
        # Build the TypeScript code
        print("Building TypeScript code...")
        subprocess.run(["npm", "run", "build"], cwd=str(self.base_dir), check=True)
        
        # Run the ReAgent system with a small test
        print("Running ReAgent system...")
        result = subprocess.run(
            ["node", "dist/cli.js", "search", "SMA crossover strategy"], 
            cwd=str(self.base_dir), 
            capture_output=True, 
            text=True
        )
        
        # Print the output for debugging
        print("ReAgent output:")
        print(result.stdout)
        
        if result.returncode != 0:
            print("ReAgent error:")
            print(result.stderr)
        
        # Check that the system ran successfully
        self.assertEqual(result.returncode, 0, "ReAgent system failed")
        self.assertIn("Searching for: SMA crossover strategy", result.stdout, "ReAgent system did not run correctly")
        
        print("ReAgent system ran successfully")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Script to load real backtest metrics from Lean/QuantConnect."""

import json
import os
from pathlib import Path
import pandas as pd
from typing import Dict, Any, Optional
import sys

class LeanMetricsLoader:
    def __init__(self, results_dir: str = None):
        """Initialize the metrics loader."""
        self.results_dir = Path(results_dir) if results_dir else Path(__file__).parent.parent / "backtest_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_lean_results(self, algorithm_name: str, results_path: str) -> Optional[Dict[str, float]]:
        """Load metrics from Lean backtest results."""
        try:
            # Load Lean backtest results from JSON file
            with open(results_path, 'r') as f:
                results = json.load(f)
            
            # Extract key metrics from Lean results
            metrics = {
                'sharpe': float(results['Statistics']['Sharpe Ratio']),
                'cagr': float(results['Statistics']['Compounding Annual Return']),
                'max_drawdown': float(results['Statistics']['Drawdown']),
                'win_rate': float(results['Statistics']['Win Rate'])
            }
            
            # Save metrics to backtest_results directory
            output_path = self.results_dir / f"{algorithm_name}_metrics.json"
            with open(output_path, 'w') as f:
                json.dump(metrics, f, indent=2)
                
            print(f"Saved metrics for {algorithm_name}")
            return metrics
            
        except Exception as e:
            print(f"Error loading metrics for {algorithm_name}: {str(e)}")
            return None
            
    def load_lean_directory(self, lean_results_dir: str):
        """Load all Lean backtest results from a directory."""
        lean_dir = Path(lean_results_dir)
        
        if not lean_dir.exists():
            print(f"Lean results directory not found: {lean_dir}")
            return
            
        # Look for backtest result files
        for result_file in lean_dir.glob("*.json"):
            try:
                # Extract algorithm name from filename
                algorithm_name = result_file.stem.replace("_backtest_results", "")
                self.load_lean_results(algorithm_name, str(result_file))
            except Exception as e:
                print(f"Error processing {result_file}: {str(e)}")
                
    def list_loaded_metrics(self):
        """List all strategies with loaded metrics."""
        print("\nLoaded strategy metrics:")
        for metric_file in self.results_dir.glob("*_metrics.json"):
            strategy_name = metric_file.stem.replace("_metrics", "")
            try:
                with open(metric_file, 'r') as f:
                    metrics = json.load(f)
                print(f"\n{strategy_name}:")
                print(f"  Sharpe: {metrics['sharpe']:.2f}")
                print(f"  CAGR: {metrics['cagr']:.2%}")
                print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
                print(f"  Win Rate: {metrics['win_rate']:.2%}")
            except Exception as e:
                print(f"Error reading metrics for {strategy_name}: {str(e)}")

def main():
    """Main function to load metrics."""
    if len(sys.argv) < 2:
        print("Usage: python load_lean_metrics.py <lean_results_directory>")
        return
        
    lean_results_dir = sys.argv[1]
    loader = LeanMetricsLoader()
    
    print(f"Loading metrics from: {lean_results_dir}")
    loader.load_lean_directory(lean_results_dir)
    loader.list_loaded_metrics()

if __name__ == "__main__":
    main()
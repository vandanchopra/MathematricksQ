#!/usr/bin/env python3
"""Module to load and manage backtest metrics."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

class BacktestMetricsLoader:
    def __init__(self, metrics_dir: str = None):
        """Initialize the metrics loader."""
        self.metrics_dir = Path(metrics_dir) if metrics_dir else Path(__file__).parent.parent / "backtest_results"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
    def get_metrics_path(self, strategy_name: str) -> Path:
        """Get the path for strategy metrics file."""
        return self.metrics_dir / f"{strategy_name}_metrics.json"
        
    def load_metrics(self, strategy_name: str) -> Optional[Dict[str, float]]:
        """Load backtest metrics for a strategy."""
        metrics_path = self.get_metrics_path(strategy_name)
        
        if not metrics_path.exists():
            return None
            
        try:
            with open(metrics_path, 'r') as f:
                data = json.load(f)
                # Validate required metrics
                required_metrics = {'sharpe', 'cagr', 'max_drawdown', 'win_rate'}
                if not all(metric in data for metric in required_metrics):
                    print(f"Warning: Missing required metrics for {strategy_name}")
                    return None
                return data
        except Exception as e:
            print(f"Error loading metrics for {strategy_name}: {str(e)}")
            return None
            
    def save_metrics(self, strategy_name: str, metrics: Dict[str, float]) -> bool:
        """Save backtest metrics for a strategy."""
        try:
            metrics_path = self.get_metrics_path(strategy_name)
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving metrics for {strategy_name}: {str(e)}")
            return False
            
    def list_strategies_with_metrics(self) -> list:
        """List all strategies that have metrics."""
        metrics_files = self.metrics_dir.glob("*_metrics.json")
        return [f.stem.replace("_metrics", "") for f in metrics_files]
            
    def delete_metrics(self, strategy_name: str) -> bool:
        """Delete metrics for a strategy."""
        try:
            metrics_path = self.get_metrics_path(strategy_name)
            if metrics_path.exists():
                metrics_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting metrics for {strategy_name}: {str(e)}")
            return False

def create_sample_metrics() -> None:
    """Create sample metrics for demonstration."""
    loader = BacktestMetricsLoader()
    
    # Sample strategies with realistic metrics
    sample_metrics = {
        "MultiAssetLongShort": {
            "sharpe": 1.8,
            "cagr": 0.22,
            "max_drawdown": -0.15,
            "win_rate": 0.58
        },
        "MultiAssetLongShortImproved": {
            "sharpe": 2.1,
            "cagr": 0.25,
            "max_drawdown": -0.12,
            "win_rate": 0.62
        },
        "SMAStrategy": {
            "sharpe": 1.5,
            "cagr": 0.18,
            "max_drawdown": -0.20,
            "win_rate": 0.55
        }
    }
    
    for strategy_name, metrics in sample_metrics.items():
        loader.save_metrics(strategy_name, metrics)
        print(f"Created sample metrics for {strategy_name}")

if __name__ == "__main__":
    # Create sample metrics if run directly
    create_sample_metrics()
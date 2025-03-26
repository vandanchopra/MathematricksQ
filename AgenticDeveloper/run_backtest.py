import asyncio
import os
import sys
from rich import print as rprint
from rich.console import Console
from rich.theme import Theme
from agents.backtester import BacktesterAgent

# Create custom theme for output
custom_theme = Theme({
    "id": "bold cyan",
    "metric": "blue",
    "value": "bright_white"
})
console = Console(theme=custom_theme)

async def main():
    # Get absolute path to config
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config", "system_config.yaml")
    
    # Redirect stdout to devnull to suppress QuantConnect output
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        
        try:
            # Initialize and run backtest
            agent = BacktesterAgent(config_path=config_path)
            strategy_path = os.path.join(os.path.dirname(current_dir), "Strategies", "SMAStrategy")
            result = await agent.run(strategy_path)
            
            # Restore stdout for our output
            sys.stdout = old_stdout
            
            # Extract test ID and metrics
            test_id = result.get("backtest_id", "Unknown")
            metrics = result.get("metrics", {})
            
            # Print results in a clean, compact format
            console.print(f"\n[id]#{test_id}[/id] ", end="")
            console.print("[metric]Metrics[/metric]:")
            
            # Create groups of metrics for better organization
            key_metrics = {
                "Returns": ["Compounding Annual Return", "Net Profit", "Drawdown"],
                "Statistics": ["Sharpe Ratio", "Sortino Ratio", "Information Ratio"],
                "Trading": ["Total Orders", "Win Rate", "Loss Rate", "Average Win", "Average Loss"],
                "Risk": ["Alpha", "Beta", "Annual Standard Deviation"]
            }
            
            # Print metrics by group
            for group, metric_names in key_metrics.items():
                values = {m: metrics[m] for m in metric_names if m in metrics}
                if values:
                    console.print(f"  [metric]{group}[/metric]:")
                    for metric, value in values.items():
                        if isinstance(value, float):
                            value = round(value, 3)  # Round floats to 3 decimal places
                        console.print(f"    [metric]{metric:25}[/metric] [value]{value}[/value]")
                        
        except Exception as e:
            # Restore stdout in case of error
            sys.stdout = old_stdout
            print(f"Error running backtest: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
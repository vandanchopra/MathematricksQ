import sys
import os
import asyncio
import json
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.backtest_analyzer import BacktestAnalyzerAgent

def display_json_section(title: str, content: dict, indent: int = 2):
    """Helper function to display JSON sections nicely"""
    print(f"\n{title}:")
    print("-" * 40)
    if isinstance(content, dict):
        for key, value in content.items():
            if isinstance(value, list):
                print(f"{' ' * indent}{key}:")
                for item in value:
                    print(f"{' ' * (indent * 2)}- {item}")
            else:
                print(f"{' ' * indent}{key}: {value}")
    else:
        print(json.dumps(content, indent=2))

async def main():
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize analyzer agent
    agent = BacktestAnalyzerAgent("AgenticDeveloper/config/system_config.yaml")
    
    # Specific backtest directory to analyze
    backtest_dir = "Strategies/SMAStrategy/backtests/2025-03-26_11-34-48"
    
    try:
        print(f"\nAnalyzing backtest results in: {backtest_dir}")
        print("=" * 80)
        
        # Run analysis
        result = await agent.run(backtest_dir)
        analysis = result["analysis"]
        
        # Display analysis sections
        display_json_section("Metrics Analysis", analysis["metrics_analysis"])
        display_json_section("Trade Analysis", analysis["trade_analysis"])
        display_json_section("Strategy Analysis", analysis["strategy_analysis"])
        display_json_section("Improvement Suggestions", analysis["improvement_suggestions"])
        
        print("\nBacktest analysis complete! ✅")
        print(f"Full analysis stored in: {backtest_dir}/BacktestAnalyzerAgent_analysis.json")
        
    except Exception as e:
        print(f"\nError analyzing backtest: {str(e)} ❌")
        raise

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""Example script demonstrating the backtester agent with memory integration."""

import os
import sys
import asyncio
from typing import List, Dict, Any
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from AgenticDeveloper.agents import BacktesterAgent, BacktestAnalyzerAgent, MemoryAgent

async def setup_memory_contexts():
    """Set up initial contexts in the memory system."""
    print("Setting up memory contexts...")
    
    # Initialize the memory agent
    memory_agent = MemoryAgent()
    
    # Define contexts for different markets and timeframes
    contexts = [
        {"id": "spy_daily", "market": "SPY", "timeframe": "1d"},
        {"id": "qqq_daily", "market": "QQQ", "timeframe": "1d"}
    ]
    
    # Store contexts in memory
    for context in contexts:
        result = await memory_agent.run(
            "store_context",
            context_id=context["id"],
            market=context["market"],
            timeframe=context["timeframe"]
        )
        print(f"Stored context: {context['id']}")
    
    return memory_agent

async def run_backtest(strategy_path: str, mode: str = "local"):
    """Run a backtest for a strategy and store the results in memory."""
    print(f"Running backtest for strategy: {strategy_path}")
    
    # Initialize the backtester agent
    backtester = BacktesterAgent()
    
    # Run the backtest
    backtest_result = await backtester.run(strategy_path, mode)
    
    print(f"Backtest completed. Success: {backtest_result.get('backtest_success', False)}")
    
    # Get the backtest folder path
    backtest_folder = backtest_result.get("backtest_folder_path", "")
    if not backtest_folder or not os.path.exists(backtest_folder):
        print(f"Backtest folder not found: {backtest_folder}")
        return None
    
    print(f"Backtest folder: {backtest_folder}")
    return backtest_folder

async def analyze_backtest(backtest_folder: str):
    """Analyze a backtest and store the results in memory."""
    print(f"Analyzing backtest: {backtest_folder}")
    
    # Initialize the backtest analyzer agent
    analyzer = BacktestAnalyzerAgent()
    
    # Analyze the backtest
    analysis_result = await analyzer.run(backtest_folder)
    
    print(f"Analysis completed.")
    
    # Display some analysis results
    metrics_analysis = analysis_result.get("analysis", {}).get("metrics_analysis", {})
    if metrics_analysis:
        print("\nMetrics Analysis:")
        for key, value in metrics_analysis.items():
            print(f"  {key}: {value[:100]}..." if isinstance(value, str) and len(value) > 100 else f"  {key}: {value}")
    
    improvement_suggestions = analysis_result.get("analysis", {}).get("improvement_suggestions", "")
    if improvement_suggestions:
        print("\nImprovement Suggestions:")
        print(f"  {improvement_suggestions[:200]}..." if len(improvement_suggestions) > 200 else f"  {improvement_suggestions}")
    
    return analysis_result

async def query_similar_strategies(strategy_description: str, context_id: str = None):
    """Query similar strategies from memory."""
    print(f"Querying similar strategies for: {strategy_description}")
    
    # Initialize the memory agent
    memory_agent = MemoryAgent()
    
    # Query similar ideas
    result = await memory_agent.run(
        "query_similar_ideas",
        query_text=strategy_description,
        context_id=context_id,
        top_k=3
    )
    
    # Display results
    print(f"Found {len(result.get('results', []))} similar strategies:")
    for i, idea in enumerate(result.get('results', [])):
        print(f"  {i+1}. {idea.get('description', '')[:100]}...")
    
    return result

async def main():
    """Run the example."""
    # Set up memory contexts
    await setup_memory_contexts()
    
    # Define the strategy path
    strategy_path = "Strategies/SMAStrategy/main.py"
    
    # Check if the strategy file exists
    if not os.path.exists(strategy_path):
        print(f"Strategy file not found: {strategy_path}")
        print("Please provide a valid strategy path.")
        return
    
    # Run the backtest
    backtest_folder = await run_backtest(strategy_path)
    if not backtest_folder:
        print("Backtest failed.")
        return
    
    # Analyze the backtest
    await analyze_backtest(backtest_folder)
    
    # Query similar strategies
    strategy_description = "Moving average crossover strategy that buys when the short-term MA crosses above the long-term MA"
    await query_similar_strategies(strategy_description, "spy_daily")
    
    print("\nExample complete!")

if __name__ == "__main__":
    asyncio.run(main())

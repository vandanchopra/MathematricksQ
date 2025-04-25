#!/usr/bin/env python3
"""Example script demonstrating the hybrid memory system with agents."""

import os
import sys
import asyncio
from typing import List, Dict, Any
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from AgenticDeveloper.agents import MemoryAgent, IdeaResearcherAgent, BacktesterAgent, BacktestAnalyzerAgent

async def setup_memory_contexts():
    """Set up initial contexts in the memory system."""
    print("Setting up memory contexts...")
    
    # Initialize the memory agent
    memory_agent = MemoryAgent()
    
    # Define contexts for different markets and timeframes
    contexts = [
        {"id": "btc_daily", "market": "BTC/USD", "timeframe": "1d"},
        {"id": "eth_daily", "market": "ETH/USD", "timeframe": "1d"},
        {"id": "btc_hourly", "market": "BTC/USD", "timeframe": "1h"},
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

async def research_trading_ideas(query: str = "momentum trading strategies", max_results: int = 3):
    """Research trading ideas and store them in memory."""
    print(f"Researching trading ideas for: {query}")
    
    # Initialize the research agent
    research_agent = IdeaResearcherAgent()
    
    # Run the research agent
    result = await research_agent.run(query, max_results)
    
    print(f"Research complete. Found {len(result.get('new_ideas', {}))} new ideas.")
    return result

async def query_similar_ideas(query_text: str, context_id: str = None):
    """Query similar ideas from memory."""
    print(f"Querying similar ideas for: {query_text}")
    
    # Initialize the memory agent
    memory_agent = MemoryAgent()
    
    # Query similar ideas
    result = await memory_agent.run(
        "query_similar_ideas",
        query_text=query_text,
        context_id=context_id,
        top_k=5
    )
    
    # Display results
    print(f"Found {len(result.get('results', []))} similar ideas:")
    for i, idea in enumerate(result.get('results', [])):
        print(f"  {i+1}. {idea.get('description', '')[:100]}...")
    
    return result

async def recommend_ideas_for_strategy(strategy_text: str, context_id: str):
    """Get recommendations for a strategy in a specific context."""
    print(f"Getting recommendations for strategy in context: {context_id}")
    
    # Initialize the memory agent
    memory_agent = MemoryAgent()
    
    # Get recommendations
    result = await memory_agent.run(
        "recommend_ideas",
        strategy_text=strategy_text,
        context_id=context_id,
        top_k=3
    )
    
    # Display results
    print(f"Found {len(result.get('recommendations', []))} recommendations:")
    for i, idea in enumerate(result.get('recommendations', [])):
        metrics = idea.get('metrics', {})
        print(f"  {i+1}. {idea.get('description', '')[:100]}...")
        if metrics:
            print(f"     Metrics: Sharpe={metrics.get('Sharpe', 'N/A')}, CAGR={metrics.get('CAGR', 'N/A')}")
    
    return result

async def main():
    """Run the example."""
    # Set up memory contexts
    memory_agent = await setup_memory_contexts()
    
    # Research trading ideas
    research_result = await research_trading_ideas("momentum trading strategies", 2)
    
    # Wait a moment for processing
    await asyncio.sleep(2)
    
    # Query similar ideas
    query_result = await query_similar_ideas("RSI-based mean reversion strategy")
    
    # Get recommendations for a strategy
    strategy_text = """
    This strategy uses a combination of RSI and moving averages to identify oversold conditions.
    It buys when RSI is below 30 and the price is below the 20-day moving average.
    It sells when RSI is above 70 or the price crosses above the 50-day moving average.
    """
    recommend_result = await recommend_ideas_for_strategy(strategy_text, "btc_daily")
    
    print("\nExample complete!")

if __name__ == "__main__":
    asyncio.run(main())

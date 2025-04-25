#!/usr/bin/env python3
"""Example script demonstrating the memory agent."""

import os
import sys
from typing import List, Dict, Any
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.memory.memory_agent import MemoryAgent

def main():
    """Run the example."""
    print("Memory Agent Example")
    
    # Initialize the memory agent
    memory_agent = MemoryAgent(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        patann_url="http://localhost:9200",
        model_name="all-MiniLM-L6-v2"
    )
    
    # Store contexts
    contexts = [
        {"id": "btc_daily", "market": "BTC/USD", "timeframe": "1d"},
        {"id": "eth_daily", "market": "ETH/USD", "timeframe": "1d"},
        {"id": "btc_hourly", "market": "BTC/USD", "timeframe": "1h"}
    ]
    
    for context in contexts:
        result = memory_agent.run(
            "store_context",
            context_id=context["id"],
            market=context["market"],
            timeframe=context["timeframe"]
        )
        print(f"Stored context: {context['id']}")
    
    # Store ideas
    ideas = [
        {"name": "RSI Oversold", "description": "Buy when RSI is below 30", "contexts": ["btc_daily", "eth_daily"]},
        {"name": "RSI Overbought", "description": "Sell when RSI is above 70", "contexts": ["btc_daily", "eth_daily"]},
        {"name": "Golden Cross", "description": "Buy on golden cross (50 SMA crosses above 200 SMA)", "contexts": ["btc_daily"]},
        {"name": "Death Cross", "description": "Sell on death cross (50 SMA crosses below 200 SMA)", "contexts": ["btc_daily"]},
        {"name": "MA Pullback", "description": "Buy when price is 10% below 20-day moving average", "contexts": ["btc_hourly"]}
    ]
    
    idea_ids = {}
    for idea in ideas:
        result = memory_agent.run(
            "store_idea",
            idea_name=idea["name"],
            description=idea["description"],
            context_ids=idea["contexts"]
        )
        idea_ids[idea["name"]] = result["id"]
        print(f"Stored idea: {idea['name']} (ID: {result['id']})")
    
    # Store backtests
    backtests = [
        {"metrics": {"Sharpe": 1.5, "CAGR": 0.25, "MaxDrawdown": 0.15}, "idea_name": "RSI Oversold", "context_id": "btc_daily"},
        {"metrics": {"Sharpe": 1.2, "CAGR": 0.20, "MaxDrawdown": 0.18}, "idea_name": "RSI Overbought", "context_id": "btc_daily"},
        {"metrics": {"Sharpe": 0.8, "CAGR": 0.15, "MaxDrawdown": 0.25}, "idea_name": "Golden Cross", "context_id": "btc_daily"},
        {"metrics": {"Sharpe": 1.0, "CAGR": 0.18, "MaxDrawdown": 0.20}, "idea_name": "Death Cross", "context_id": "btc_daily"},
        {"metrics": {"Sharpe": 1.8, "CAGR": 0.30, "MaxDrawdown": 0.12}, "idea_name": "MA Pullback", "context_id": "btc_hourly"}
    ]
    
    for backtest in backtests:
        result = memory_agent.run(
            "store_backtest",
            backtest_id=f"bt_{backtest['idea_name']}",
            metrics=backtest["metrics"],
            idea_id=idea_ids[backtest["idea_name"]],
            context_id=backtest["context_id"]
        )
        print(f"Stored backtest for idea: {backtest['idea_name']}")
    
    # Query similar ideas
    query_text = "Buy when price is below average"
    result = memory_agent.run(
        "query_similar_ideas",
        query_text=query_text,
        context_id="btc_daily",
        top_k=3
    )
    
    print(f"\nSimilar ideas to '{query_text}':")
    for i, idea in enumerate(result["results"]):
        print(f"{i+1}. {idea['description']}")
    
    # Get recommendations
    strategy_text = "This strategy uses RSI to identify oversold conditions in the market."
    result = memory_agent.run(
        "recommend_ideas",
        strategy_text=strategy_text,
        context_id="btc_daily",
        top_k=3
    )
    
    print(f"\nRecommendations for strategy: '{strategy_text}'")
    for i, idea in enumerate(result["recommendations"]):
        metrics = idea.get("metrics", {})
        sharpe = metrics.get("Sharpe", "N/A")
        print(f"{i+1}. {idea['description']} (Sharpe: {sharpe})")
    
    # Query top ideas by metrics
    result = memory_agent.run(
        "query_top_ideas",
        context_id="btc_daily",
        metric="Sharpe",
        limit=3
    )
    
    print("\nTop ideas by Sharpe ratio:")
    for i, idea in enumerate(result["results"]):
        metrics = idea.get("metrics", {})
        sharpe = metrics.get("Sharpe", "N/A")
        print(f"{i+1}. {idea['description']} (Sharpe: {sharpe})")
    
    print("\nExample complete!")

if __name__ == "__main__":
    main()

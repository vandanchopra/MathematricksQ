#!/usr/bin/env python3
"""Test script for the hybrid memory system."""

import os
import sys
import asyncio
from typing import List, Dict, Any
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory import HybridMemory

def test_memory():
    """Test the hybrid memory system."""
    print("Testing the hybrid memory system...")
    
    # Initialize the memory system
    memory = HybridMemory(
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
        memory.store_context(context["id"], context["market"], context["timeframe"])
        print(f"Stored context: {context['id']}")
    
    # Store ideas
    ideas = [
        {"id": "idea1", "description": "Buy when RSI is below 30", "contexts": ["btc_daily", "eth_daily"]},
        {"id": "idea2", "description": "Sell when RSI is above 70", "contexts": ["btc_daily", "eth_daily"]},
        {"id": "idea3", "description": "Buy on golden cross (50 SMA crosses above 200 SMA)", "contexts": ["btc_daily"]},
        {"id": "idea4", "description": "Sell on death cross (50 SMA crosses below 200 SMA)", "contexts": ["btc_daily"]},
        {"id": "idea5", "description": "Buy when price is 10% below 20-day moving average", "contexts": ["btc_hourly"]}
    ]
    
    for idea in ideas:
        memory.store_idea(idea["id"], idea["description"], idea["contexts"])
        print(f"Stored idea: {idea['id']}")
    
    # Store backtests
    backtests = [
        {"id": "bt1", "metrics": {"Sharpe": 1.5, "CAGR": 0.25, "MaxDrawdown": 0.15}, "idea_id": "idea1", "context_id": "btc_daily"},
        {"id": "bt2", "metrics": {"Sharpe": 1.2, "CAGR": 0.20, "MaxDrawdown": 0.18}, "idea_id": "idea2", "context_id": "btc_daily"},
        {"id": "bt3", "metrics": {"Sharpe": 0.8, "CAGR": 0.15, "MaxDrawdown": 0.25}, "idea_id": "idea3", "context_id": "btc_daily"},
        {"id": "bt4", "metrics": {"Sharpe": 1.0, "CAGR": 0.18, "MaxDrawdown": 0.20}, "idea_id": "idea4", "context_id": "btc_daily"},
        {"id": "bt5", "metrics": {"Sharpe": 1.8, "CAGR": 0.30, "MaxDrawdown": 0.12}, "idea_id": "idea5", "context_id": "btc_hourly"}
    ]
    
    for backtest in backtests:
        memory.store_backtest(backtest["id"], backtest["metrics"], backtest["idea_id"], backtest["context_id"])
        print(f"Stored backtest: {backtest['id']}")
    
    # Query similar ideas
    query_text = "Buy when price is below average"
    embedding = memory.vector_backend._get_embedding(query_text)
    
    print(f"\nQuerying similar ideas to: '{query_text}'")
    similar_ideas = memory.query_similar_ideas(embedding, "btc_daily", 3)
    
    print("\nSimilar ideas:")
    for i, idea in enumerate(similar_ideas):
        print(f"{i+1}. {idea['description']}")
    
    # Get recommendations
    print("\nGetting recommendations:")
    recommendations = memory.recommend_ideas(embedding, "btc_daily", 3)
    
    print("\nRecommended ideas:")
    for i, idea in enumerate(recommendations):
        metrics = idea.get("metrics", {})
        sharpe = metrics.get("Sharpe", "N/A")
        print(f"{i+1}. {idea['description']} (Sharpe: {sharpe})")
    
    # Query ideas by metrics
    print("\nTop ideas by Sharpe ratio:")
    top_ideas = memory.query_top_ideas_by_metrics(context_id="btc_daily", metric="Sharpe", limit=3)
    
    for i, idea in enumerate(top_ideas):
        metrics = idea.get("metrics", {})
        sharpe = metrics.get("Sharpe", "N/A")
        print(f"{i+1}. {idea['description']} (Sharpe: {sharpe})")

if __name__ == "__main__":
    test_memory()

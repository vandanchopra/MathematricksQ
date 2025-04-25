#!/usr/bin/env python3
"""
Memory System Example

This script demonstrates how to use the memory system to store and retrieve
trading ideas, scenarios, contexts, and backtests.
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.memory.graph_memory_agent import GraphMemoryAgent

def main():
    """
    Main function to demonstrate the memory system.
    """
    # Create a memory agent
    agent = GraphMemoryAgent()
    
    # Step 1: Remember some ideas
    print("Step 1: Remembering ideas...")
    idea1_id = agent.remember_idea(
        description="Using Internal Bar Strength (IBS) for mean reversion trading",
        tags=["mean-reversion", "technical-indicator", "IBS"]
    )
    print(f"Remembered idea 1: {idea1_id}")
    
    idea2_id = agent.remember_idea(
        description="Momentum trading with RSI and moving average crossovers",
        tags=["momentum", "technical-indicator", "RSI", "moving-average"]
    )
    print(f"Remembered idea 2: {idea2_id}")
    
    idea3_id = agent.remember_idea(
        description="Volatility breakout strategy using Bollinger Bands",
        tags=["volatility", "breakout", "bollinger-bands"]
    )
    print(f"Remembered idea 3: {idea3_id}")
    
    # Step 2: Remember some scenarios
    print("\nStep 2: Remembering scenarios...")
    scenario1_id = agent.remember_scenario(
        description="IBS applied to country ETFs",
        parent_idea_id=idea1_id,
        tags=["ETF", "country", "global"]
    )
    print(f"Remembered scenario 1: {scenario1_id}")
    
    scenario2_id = agent.remember_scenario(
        description="RSI momentum on cryptocurrency markets",
        parent_idea_id=idea2_id,
        tags=["crypto", "bitcoin", "ethereum"]
    )
    print(f"Remembered scenario 2: {scenario2_id}")
    
    # Step 3: Remember some contexts
    print("\nStep 3: Remembering contexts...")
    context1_id = agent.remember_context(
        market="ETF-Basket",
        timeframe="1d",
        description="Daily timeframe for a basket of country ETFs"
    )
    print(f"Remembered context 1: {context1_id}")
    
    context2_id = agent.remember_context(
        market="BTC/USD",
        timeframe="4h",
        description="4-hour timeframe for Bitcoin/USD"
    )
    print(f"Remembered context 2: {context2_id}")
    
    context3_id = agent.remember_context(
        market="SPY",
        timeframe="1d",
        description="Daily timeframe for S&P 500 ETF"
    )
    print(f"Remembered context 3: {context3_id}")
    
    # Step 4: Remember some backtests
    print("\nStep 4: Remembering backtests...")
    backtest1_id = agent.remember_backtest(
        idea_id=idea1_id,
        context_id=context1_id,
        scenario_id=scenario1_id,
        metrics={
            "Sharpe": 1.85,
            "CAGR": 0.12,
            "MaxDrawdown": 0.15,
            "WinRate": 0.58,
            "ProfitFactor": 1.65,
            "TotalTrades": 250
        },
        notes="Initial test of IBS strategy on country ETFs"
    )
    print(f"Remembered backtest 1: {backtest1_id}")
    
    backtest2_id = agent.remember_backtest(
        idea_id=idea2_id,
        context_id=context2_id,
        scenario_id=scenario2_id,
        metrics={
            "Sharpe": 2.1,
            "CAGR": 0.25,
            "MaxDrawdown": 0.22,
            "WinRate": 0.62,
            "ProfitFactor": 1.8,
            "TotalTrades": 180
        },
        notes="RSI momentum strategy on BTC/USD"
    )
    print(f"Remembered backtest 2: {backtest2_id}")
    
    backtest3_id = agent.remember_backtest(
        idea_id=idea3_id,
        context_id=context3_id,
        metrics={
            "Sharpe": 1.5,
            "CAGR": 0.09,
            "MaxDrawdown": 0.18,
            "WinRate": 0.52,
            "ProfitFactor": 1.4,
            "TotalTrades": 120
        },
        notes="Bollinger Bands breakout strategy on SPY"
    )
    print(f"Remembered backtest 3: {backtest3_id}")
    
    # Step 5: Recall similar ideas
    print("\nStep 5: Recalling similar ideas...")
    similar_ideas = agent.recall_similar_ideas(
        description="mean reversion trading strategies",
        k=2
    )
    
    print("Similar ideas to 'mean reversion trading strategies':")
    for idea in similar_ideas:
        print(f"ID: {idea['id']}, Score: {idea['score']}")
        print(f"Text: {idea['metadata'].get('text', '')}")
        print()
    
    # Step 6: Get best ideas by metric
    print("\nStep 6: Getting best ideas by Sharpe ratio...")
    best_ideas = agent.recall_best_ideas(metric="Sharpe", k=3)
    
    print("Best ideas by Sharpe ratio:")
    for idea in best_ideas:
        print(f"ID: {idea['id']}, Description: {idea['description']}")
        print(f"Max Sharpe: {idea['max_Sharpe']}")
        print()
    
    # Step 7: Get idea performance
    print("\nStep 7: Getting idea performance...")
    performance = agent.get_idea_performance(idea1_id)
    
    print(f"Performance of idea {idea1_id}:")
    print(f"Number of backtests: {performance['num_backtests']}")
    for metric, stats in performance["metrics"].items():
        print(f"{metric}: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")
    print()
    
    # Step 8: Compare ideas
    print("\nStep 8: Comparing ideas...")
    comparison = agent.compare_ideas([idea1_id, idea2_id, idea3_id], metric="Sharpe")
    
    print("Idea comparison by Sharpe ratio:")
    for idea in comparison:
        print(f"ID: {idea['id']}, Description: {idea['description']}")
        print(f"Sharpe: min={idea['min']}, max={idea['max']}, mean={idea['mean']}")
        print()
    
    # Step 9: Get context performance
    print("\nStep 9: Getting context performance...")
    context_performance = agent.get_context_performance(context1_id)
    
    print(f"Performance in context {context1_id} ({context_performance['market']} {context_performance['timeframe']}):")
    print(f"Number of backtests: {context_performance['num_backtests']}")
    print(f"Number of ideas: {len(context_performance['ideas'])}")
    for idea in context_performance["ideas"]:
        print(f"Idea: {idea['description']}")
        for metric, stats in idea["metrics"].items():
            print(f"  {metric}: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")
        print()
    
    # Step 10: Compare contexts
    print("\nStep 10: Comparing contexts...")
    context_comparison = agent.compare_contexts([context1_id, context2_id, context3_id], metric="Sharpe")
    
    print("Context comparison by Sharpe ratio:")
    for context in context_comparison:
        print(f"ID: {context['id']}, Market: {context['market']}, Timeframe: {context['timeframe']}")
        print(f"Average Sharpe: {context['avg_value']}")
        print(f"Number of backtests: {context['num_backtests']}")
        print(f"Number of ideas: {context['num_ideas']}")
        print()
    
    # Step 11: Get visualization data
    print("\nStep 11: Getting visualization data...")
    graph = agent.get_visualization_data()
    
    print(f"Graph contains {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")
    
    # Step 12: Export to JSON
    print("\nStep 12: Exporting to JSON...")
    output_path = os.path.join(os.path.dirname(__file__), "memory_graph.json")
    agent.export_to_json(output_path)
    print(f"Memory graph exported to {output_path}")
    
    print("\nMemory system example completed successfully!")

if __name__ == "__main__":
    main()

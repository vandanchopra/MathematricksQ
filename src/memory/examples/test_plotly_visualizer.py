#!/usr/bin/env python3
"""
Test script for the PlotlyVisualizer
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.memory.hybrid_backend import HybridMemory
from src.memory.plotly_visualizer import PlotlyVisualizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PlotlyVisualizerTest")

def setup_test_data():
    """Set up test data for the visualizer."""
    logger.info("Setting up test data...")
    
    # Initialize the memory system
    memory = HybridMemory(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        patann_url="http://localhost:9200",
        model_name="all-MiniLM-L6-v2"
    )
    
    # Clear the database
    memory.graph_backend.clear_database()
    
    # Store contexts
    contexts = [
        {"id": "btc_daily", "market": "BTC/USD", "timeframe": "1d"},
        {"id": "eth_daily", "market": "ETH/USD", "timeframe": "1d"},
        {"id": "btc_hourly", "market": "BTC/USD", "timeframe": "1h"}
    ]
    
    for context in contexts:
        memory.store_context(context["id"], context["market"], context["timeframe"])
        logger.info(f"Stored context: {context['id']}")
    
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
        logger.info(f"Stored idea: {idea['id']}")
    
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
        logger.info(f"Stored backtest: {backtest['id']}")
    
    # Store scenarios
    scenarios = [
        {"id": "scenario1", "description": "RSI(14) < 30 on 4h timeframe", "parent_idea_id": "idea1", "contexts": ["btc_daily"]},
        {"id": "scenario2", "description": "RSI(7) < 25 with volume confirmation", "parent_idea_id": "idea1", "contexts": ["btc_daily"]}
    ]
    
    for scenario in scenarios:
        memory.store_scenario(scenario["id"], scenario["description"], scenario["parent_idea_id"], scenario["contexts"])
        logger.info(f"Stored scenario: {scenario['id']}")
    
    logger.info("Test data setup complete!")

def test_visualizer():
    """Test the PlotlyVisualizer."""
    logger.info("Testing PlotlyVisualizer...")
    
    # Initialize the visualizer
    visualizer = PlotlyVisualizer(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # Test 1: Fetch edges
    logger.info("Test 1: Fetching edges...")
    edges = visualizer.fetch_edges(limit=10)
    logger.info(f"Fetched {len(edges)} edges")
    
    # Test 2: Fetch scenario edges
    logger.info("Test 2: Fetching scenario edges...")
    scenario_edges = visualizer.fetch_scenario_edges(limit=10)
    logger.info(f"Fetched {len(scenario_edges)} scenario edges")
    
    # Test 3: Visualize knowledge graph
    logger.info("Test 3: Visualizing knowledge graph...")
    fig = visualizer.visualize(limit=10, output_file="knowledge_graph.html")
    if fig:
        logger.info("Knowledge graph visualization created successfully")
    else:
        logger.error("Failed to create knowledge graph visualization")
    
    # Test 4: Visualize metrics
    logger.info("Test 4: Visualizing metrics...")
    metrics_fig = visualizer.visualize_metrics(metric="Sharpe", limit=5, output_file="metrics_visualization.html")
    if metrics_fig:
        logger.info("Metrics visualization created successfully")
    else:
        logger.error("Failed to create metrics visualization")
    
    # Test 5: Visualize context performance
    logger.info("Test 5: Visualizing context performance...")
    context_fig = visualizer.visualize_context_performance(
        context_id="btc_daily", 
        metric="Sharpe", 
        limit=5, 
        output_file="context_performance.html"
    )
    if context_fig:
        logger.info("Context performance visualization created successfully")
    else:
        logger.error("Failed to create context performance visualization")
    
    # Close the visualizer
    visualizer.close()
    
    logger.info("PlotlyVisualizer tests completed!")

def main():
    """Run the PlotlyVisualizer test."""
    logger.info("Starting PlotlyVisualizer test...")
    
    # Set up test data
    setup_test_data()
    
    # Test the visualizer
    test_visualizer()
    
    logger.info("PlotlyVisualizer test completed successfully!")

if __name__ == "__main__":
    main()

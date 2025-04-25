#!/usr/bin/env python3
"""
Example script demonstrating how to use the PlotlyVisualizer
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.memory.hybrid_backend import HybridMemory
from src.memory.plotly_visualizer import PlotlyVisualizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VisualizerExample")

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
    with memory.graph_backend.driver.session() as session:
        session.run("""
        MATCH (n)
        DETACH DELETE n
        """)

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

def run_visualizer():
    """Run the PlotlyVisualizer."""
    logger.info("Running PlotlyVisualizer...")

    # Initialize the visualizer
    visualizer = PlotlyVisualizer(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )

    # Create visualizations
    logger.info("Creating knowledge graph visualization...")
    visualizer.visualize(limit=20, output_file="knowledge_graph.html")

    logger.info("Creating metrics visualization...")
    visualizer.visualize_metrics(metric="Sharpe", limit=5, output_file="metrics_visualization.html")

    logger.info("Creating context performance visualization...")
    visualizer.visualize_context_performance(
        context_id="btc_daily",
        metric="Sharpe",
        limit=5,
        output_file="context_performance.html"
    )

    # Close the visualizer
    visualizer.close()

    logger.info("Visualizations created successfully!")
    logger.info("Check the following files:")
    logger.info("- knowledge_graph.html")
    logger.info("- metrics_visualization.html")
    logger.info("- context_performance.html")

def main():
    """Run the visualizer example."""
    logger.info("Starting visualizer example...")

    # Set up test data
    setup_test_data()

    # Run the visualizer
    run_visualizer()

    logger.info("Visualizer example completed successfully!")

if __name__ == "__main__":
    main()

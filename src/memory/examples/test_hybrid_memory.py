#!/usr/bin/env python3
"""Comprehensive test script for the hybrid memory system."""

import os
import sys
import time
import numpy as np
import logging
from typing import List, Dict, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.memory import HybridMemory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HybridMemoryTest")

def test_hybrid_memory():
    """Test the hybrid memory system with PatANN and Neo4j."""
    try:
        # Initialize the memory system
        logger.info("Initializing hybrid memory system...")
        memory = HybridMemory(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            patann_url="http://localhost:9200",
            model_name="all-MiniLM-L6-v2"
        )

        # Test Neo4j connection
        logger.info("Testing Neo4j connection...")
        try:
            memory.graph_backend.driver.verify_connectivity()
            logger.info("Neo4j connection successful!")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {str(e)}")
            return False

        # Test PatANN connection
        logger.info("Testing PatANN connection...")
        try:
            # Create a simple embedding to test PatANN
            test_embedding = memory.vector_backend._get_embedding("Test embedding")
            logger.info(f"PatANN embedding generated successfully! Length: {len(test_embedding)}")
        except Exception as e:
            logger.error(f"PatANN connection failed: {str(e)}")
            return False

        # Store contexts
        logger.info("Storing contexts...")
        contexts = [
            {"id": "btc_daily", "market": "BTC/USD", "timeframe": "1d"},
            {"id": "eth_daily", "market": "ETH/USD", "timeframe": "1d"},
            {"id": "btc_hourly", "market": "BTC/USD", "timeframe": "1h"}
        ]

        for context in contexts:
            memory.store_context(context["id"], context["market"], context["timeframe"])
            logger.info(f"Stored context: {context['id']}")

        # Store ideas
        logger.info("Storing ideas...")
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
        logger.info("Storing backtests...")
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
        logger.info("Storing scenarios...")
        scenarios = [
            {"id": "scenario1", "description": "RSI(14) < 30 on 4h timeframe", "parent_idea_id": "idea1", "contexts": ["btc_daily"]},
            {"id": "scenario2", "description": "RSI(7) < 25 with volume confirmation", "parent_idea_id": "idea1", "contexts": ["btc_daily"]}
        ]

        for scenario in scenarios:
            memory.store_scenario(scenario["id"], scenario["description"], scenario["parent_idea_id"], scenario["contexts"])
            logger.info(f"Stored scenario: {scenario['id']}")

        # Query similar ideas
        logger.info("Testing vector similarity search...")
        query_text = "Buy when price is below average"
        embedding = memory.vector_backend._get_embedding(query_text)

        logger.info(f"Querying similar ideas to: '{query_text}'")
        similar_ideas = memory.query_similar_ideas(embedding, "btc_daily", 3)

        logger.info("\nSimilar ideas:")
        for i, idea in enumerate(similar_ideas):
            logger.info(f"{i+1}. {idea['description']}")

        # Get recommendations
        logger.info("\nTesting hybrid recommendations...")
        recommendations = memory.recommend_ideas(embedding, "btc_daily", 3)

        logger.info("\nRecommended ideas:")
        for i, idea in enumerate(recommendations):
            metrics = idea.get("metrics", {})
            sharpe = metrics.get("Sharpe", "N/A")
            logger.info(f"{i+1}. {idea['description']} (Sharpe: {sharpe})")

        # Query ideas by metrics
        logger.info("\nTesting graph query by metrics...")
        top_ideas = memory.query_top_ideas_by_metrics(context_id="btc_daily", metric="Sharpe", limit=3)

        logger.info("\nTop ideas by Sharpe ratio:")
        for i, idea in enumerate(top_ideas):
            metrics = idea.get("metrics", {})
            sharpe = metrics.get("Sharpe", "N/A")
            logger.info(f"{i+1}. {idea['description']} (Sharpe: {sharpe})")

        # Test relationship queries
        logger.info("\nTesting relationship queries...")

        # Get scenarios for an idea
        scenarios = memory.graph_backend.query_scenarios_for_idea("idea1")
        logger.info(f"\nScenarios for idea1:")
        for scenario in scenarios:
            logger.info(f"- {scenario['description']}")

        # Get backtests for an idea
        backtests = memory.graph_backend.query_backtests_for_idea("idea1")
        logger.info(f"\nBacktests for idea1:")
        for backtest in backtests:
            logger.info(f"- {backtest['id']} (Sharpe: {backtest['metrics'].get('Sharpe', 'N/A')})")

        # Get ideas for a context
        ideas = memory.graph_backend.query_ideas_for_context("btc_daily")
        logger.info(f"\nIdeas for btc_daily context:")
        for idea in ideas:
            logger.info(f"- {idea['description']}")

        logger.info("\nAll tests passed successfully!")
        return True
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = test_hybrid_memory()
    print(f"Hybrid memory test {'passed' if result else 'failed'}")

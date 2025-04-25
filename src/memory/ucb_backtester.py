"""
UCB-based backtester agent that selects ideas to test based on Upper Confidence Bound.
This agent integrates with the real backtester to run backtests across multiple contexts.
"""

import os
import time
import math
import logging
import asyncio
import random
from uuid import uuid4
from typing import Dict, Any, List, Optional, Tuple
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ucb_backtester.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("UCBBacktester")

# Load environment variables
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")

# Create a driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Import the real backtester
import sys
import os

# Add the current directory to the path so we can import the real_backtester module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from real_backtester import run_backtest, AVAILABLE_CONTEXTS

def compute_score(metrics):
    """
    Compute a composite score for a backtest based on its metrics.

    Args:
        metrics (dict): Dictionary containing backtest metrics

    Returns:
        float: Composite score
    """
    # Default values in case metrics are missing
    sharpe = metrics.get("metric_Sharpe", 0)
    cagr = metrics.get("metric_CAGR", 0)
    max_drawdown = metrics.get("metric_MaxDrawdown", 0)

    # Compute score using the formula: 0.5*Sharpe + 0.3*CAGR - 0.2*MaxDrawdown
    score = 0.5 * sharpe + 0.3 * cagr - 0.2 * max_drawdown

    return score

def select_idea_with_ucb(exploration_constant=1.0):
    """
    Select an idea to test using Upper Confidence Bound algorithm.

    Args:
        exploration_constant (float): Controls exploration vs. exploitation

    Returns:
        str: ID of the selected idea
    """
    with driver.session() as session:
        # First, try to find any untested ideas (testCount = 0)
        result = session.run("""
        MATCH (i:Idea)
        WHERE i.testCount = 0 OR i.testCount IS NULL
        RETURN i.id AS idea_id, i.description AS description
        LIMIT 1
        """)

        record = result.single()
        if record:
            idea_id = record["idea_id"]
            description = record["description"]
            logger.info(f"Selected untested idea: {idea_id} - {description[:50]}...")
            return idea_id, description

        # Get all ideas with their test counts and average scores
        result = session.run("""
        MATCH (i:Idea)
        WHERE i.testCount > 0
        RETURN i.id AS idea_id,
               i.description AS description,
               i.testCount AS testCount,
               i.totalScore / i.testCount AS avgScore
        """)

        # Get total test count
        total_result = session.run("""
        MATCH (i:Idea)
        RETURN sum(i.testCount) AS totalTests
        """)
        total_tests = total_result.single()["totalTests"]
        if total_tests is None or total_tests == 0:
            total_tests = 1

        # Calculate UCB scores manually and find the best idea
        best_idea_id = None
        best_description = None
        best_ucb = -1

        for record in result:
            idea_id = record["idea_id"]
            description = record["description"]
            test_count = record["testCount"]
            avg_score = record["avgScore"]

            # Calculate UCB score
            ucb = avg_score + exploration_constant * math.sqrt(math.log(total_tests) / test_count)

            if ucb > best_ucb:
                best_ucb = ucb
                best_idea_id = idea_id
                best_description = description

        if best_idea_id:
            logger.info(f"Selected idea with UCB: {best_idea_id} - UCB: {best_ucb:.4f} - {best_description[:50]}...")
            return best_idea_id, best_description

        # If no ideas found, return None
        logger.warning("No ideas found in the database")
        return None, None

def generate_random_params() -> Dict[str, Any]:
    """
    Generate random parameters for a backtest.

    Returns:
        Dictionary with random parameters
    """
    params = {
        "lookback": random.randint(5, 200),
        "threshold": random.uniform(0.1, 5.0),
        "stop_loss": random.uniform(0.01, 0.1),
        "take_profit": random.uniform(0.02, 0.2),
        "position_size": random.uniform(0.1, 1.0)
    }
    return params

async def test_one_idea(idea_id, description):
    """
    Run a backtest for a specific idea and update the memory graph.

    Args:
        idea_id (str): ID of the idea to test
        description (str): Description of the idea

    Returns:
        dict: Metrics from the backtest
    """
    logger.info(f"Testing idea: {idea_id}")

    try:
        # Select a random context
        context = random.choice(AVAILABLE_CONTEXTS)

        # Generate random parameters
        params = generate_random_params()

        logger.info(f"Selected context: {context}")
        logger.info(f"Generated parameters: {params}")

        # Run the backtest using the real backtester
        metrics = await run_backtest(description, context, params)

        # Compute the score
        score = compute_score(metrics)
        logger.info(f"Backtest complete. Score: {score:.4f}")

        # Generate a unique ID for the backtest
        bt_id = f"bt_{str(uuid4())}"

        # Store the backtest results in Neo4j
        with driver.session() as session:
            # Create Backtest node
            session.run("""
            MERGE (b:Backtest {id: $bt_id})
            SET b.metric_Sharpe = $Sharpe,
                b.metric_CAGR = $CAGR,
                b.metric_MaxDrawdown = $MaxDrawdown,
                b.metric_WinRate = $WinRate,
                b.metric_TotalTrades = $TotalTrades,
                b.metric_ProfitFactor = $ProfitFactor,
                b.date = datetime()
            """, {
                "bt_id": bt_id,
                "Sharpe": metrics.get("metric_Sharpe", 0),
                "CAGR": metrics.get("metric_CAGR", 0),
                "MaxDrawdown": metrics.get("metric_MaxDrawdown", 0),
                "WinRate": metrics.get("metric_WinRate", 0),
                "TotalTrades": metrics.get("metric_TotalTrades", 0),
                "ProfitFactor": metrics.get("metric_ProfitFactor", 0)
            })

            # Create TESTED_IN relationship
            session.run("""
            MATCH (i:Idea {id: $idea_id}), (b:Backtest {id: $bt_id})
            MERGE (i)-[r:TESTED_IN]->(b)
            """, {
                "idea_id": idea_id,
                "bt_id": bt_id
            })

            # Update idea counters
            session.run("""
            MATCH (i:Idea {id: $idea_id})
            SET i.testCount = COALESCE(i.testCount, 0) + 1,
                i.totalScore = COALESCE(i.totalScore, 0.0) + $score
            """, {
                "idea_id": idea_id,
                "score": score
            })

            # Connect to a Context
            context_id = f"context_{context['market']}_{context['timeframe']}"
            session.run("""
            MATCH (b:Backtest {id: $bt_id})
            MERGE (c:Context {id: $context_id, market: $market, timeframe: $timeframe})
            MERGE (b)-[:EXECUTED_IN]->(c)
            """, {
                "bt_id": bt_id,
                "context_id": context_id,
                "market": context["market"],
                "timeframe": context["timeframe"]
            })

            # Create a Scenario node for the parameters
            if params:
                scenario_id = f"scenario_{str(uuid4())}"
                scenario_desc = f"Parameters: {str(params)}"
                session.run("""
                MATCH (b:Backtest {id: $bt_id})
                MERGE (s:Scenario {id: $scenario_id, description: $description})
                MERGE (b)-[:APPLIES_TO]->(s)
                """, {
                    "bt_id": bt_id,
                    "scenario_id": scenario_id,
                    "description": scenario_desc
                })

            logger.info(f"Stored backtest results in Neo4j. Backtest ID: {bt_id}")

        return metrics

    except Exception as e:
        logger.error(f"Error testing idea {idea_id}: {e}")
        return None

async def main_loop(iterations=10, sleep_time=5, exploration_constant=1.0):
    """
    Main loop for the UCB-based backtester.

    Args:
        iterations (int): Number of iterations to run
        sleep_time (int): Time to sleep between iterations in seconds
        exploration_constant (float): Controls exploration vs. exploitation
    """
    logger.info(f"Starting UCB backtester main loop with {iterations} iterations")

    for i in range(iterations):
        logger.info(f"Iteration {i+1}/{iterations}")

        # Select an idea to test
        idea_id, description = select_idea_with_ucb(exploration_constant)

        if idea_id:
            # Test the idea
            metrics = await test_one_idea(idea_id, description)

            if metrics:
                logger.info(f"Successfully tested idea {idea_id}")
            else:
                logger.warning(f"Failed to test idea {idea_id}")
        else:
            logger.warning("No idea selected for testing")

        # Sleep to avoid overloading the system
        if i < iterations - 1:  # Don't sleep after the last iteration
            logger.info(f"Sleeping for {sleep_time} seconds")
            await asyncio.sleep(sleep_time)

    logger.info("UCB backtester main loop complete")

def initialize_idea_properties():
    """Initialize testCount and totalScore properties for existing Idea nodes."""
    with driver.session() as session:
        result = session.run("""
        MATCH (i:Idea)
        WHERE i.testCount IS NULL OR i.totalScore IS NULL
        SET i.testCount = COALESCE(i.testCount, 0),
            i.totalScore = COALESCE(i.totalScore, 0.0)
        RETURN count(i) AS updated_count
        """)
        updated_count = result.single()["updated_count"]
        logger.info(f"Initialized properties for {updated_count} Idea nodes")

if __name__ == "__main__":
    # Initialize idea properties
    initialize_idea_properties()

    # Run the main loop
    asyncio.run(main_loop(iterations=3, sleep_time=5))

    # Close the Neo4j driver
    driver.close()

"""
Initialize UCB properties (testCount and totalScore) for all Idea nodes in Neo4j.
This script should be run once to set up the UCB-based backtester.
"""

import os
import logging
import math
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("initialize_ucb.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InitializeUCB")

# Load environment variables
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")

# Create a driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def create_constraints():
    """Create constraints for the UCB-based backtester."""
    with driver.session() as session:
        # Create constraint on Idea.id
        try:
            session.run("CREATE CONSTRAINT idea_id_unique IF NOT EXISTS FOR (i:Idea) REQUIRE i.id IS UNIQUE")
            logger.info("Created constraint on Idea.id")
        except Exception as e:
            logger.info(f"Constraint on Idea.id already exists or error: {e}")

        # Create constraint on Backtest.id
        try:
            session.run("CREATE CONSTRAINT backtest_id_unique IF NOT EXISTS FOR (b:Backtest) REQUIRE b.id IS UNIQUE")
            logger.info("Created constraint on Backtest.id")
        except Exception as e:
            logger.info(f"Constraint on Backtest.id already exists or error: {e}")

def initialize_idea_properties():
    """Initialize testCount and totalScore properties for all Idea nodes."""
    with driver.session() as session:
        # Initialize testCount and totalScore for all Idea nodes
        result = session.run("""
        MATCH (i:Idea)
        WHERE i.testCount IS NULL OR i.totalScore IS NULL
        SET i.testCount = COALESCE(i.testCount, 0),
            i.totalScore = COALESCE(i.totalScore, 0.0)
        RETURN count(i) AS updated_count
        """)

        updated_count = result.single()["updated_count"]
        logger.info(f"Initialized properties for {updated_count} Idea nodes")

        # Calculate and update testCount and totalScore based on existing backtests
        result = session.run("""
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
        WITH i, count(b) AS testCount,
             sum(0.5 * b.metric_Sharpe + 0.3 * b.metric_CAGR - 0.2 * b.metric_MaxDrawdown) AS totalScore
        SET i.testCount = testCount,
            i.totalScore = totalScore
        RETURN count(i) AS updated_count
        """)

        updated_count = result.single()["updated_count"]
        logger.info(f"Updated properties for {updated_count} Idea nodes based on existing backtests")

def print_ucb_scores():
    """Print UCB scores for all Idea nodes."""
    with driver.session() as session:
        # Get all ideas with their test counts and average scores
        result = session.run("""
        MATCH (i:Idea)
        OPTIONAL MATCH (i)-[:TESTED_IN]->(b:Backtest)
        WITH i, count(b) as testCount,
             CASE WHEN count(b) > 0 THEN i.totalScore / count(b) ELSE 0 END as avgScore
        RETURN i.id as id,
               i.description as description,
               testCount,
               avgScore
        ORDER BY avgScore DESC
        LIMIT 10
        """)

        # Get total test count
        total_result = session.run("""
        MATCH (i:Idea)
        RETURN sum(i.testCount) as totalTests
        """)
        total_tests = total_result.single()["totalTests"]
        if total_tests is None or total_tests == 0:
            total_tests = 1

        logger.info(f"Total tests: {total_tests}")
        logger.info("Top 10 ideas by score:")

        # Calculate UCB scores manually
        for record in result:
            test_count = record["testCount"]
            avg_score = record["avgScore"]

            # Calculate UCB score
            if test_count > 0:
                ucb = avg_score + 1.0 * (math.sqrt(math.log(total_tests) / test_count))
            else:
                ucb = 999999  # High value for untested ideas

            logger.info(f"ID: {record['id']}, TestCount: {test_count}, AvgScore: {avg_score:.4f}, UCB: {ucb:.4f}")

if __name__ == "__main__":
    logger.info("Initializing UCB properties...")

    # Create constraints
    create_constraints()

    # Initialize idea properties
    initialize_idea_properties()

    # Print UCB scores
    print_ucb_scores()

    # Close the driver
    driver.close()

    logger.info("UCB properties initialized successfully")

"""
Automated backtester loop for the memory module.
This script automates the UCB backtester loop, running backtests and updating the memory graph.
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

# Import the UCB backtester
from ucb_backtester import main_loop as ucb_main_loop
from ucb_backtester import initialize_idea_properties

# Import the PatANN similarity search
from patann_similarity import index_all_ideas, create_all_subidea_relationships, find_and_create_new_ideas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automated_backtester.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutomatedBacktester")

# Load environment variables
load_dotenv()

async def automated_loop(iterations: int = 10, 
                        exploration_constant: float = 1.0,
                        sleep_time: int = 5,
                        create_variations: bool = True,
                        num_variations: int = 3,
                        create_relationships: bool = True) -> None:
    """
    Automated backtester loop.
    
    Args:
        iterations: Number of iterations to run
        exploration_constant: Exploration constant for UCB
        sleep_time: Time to sleep between iterations in seconds
        create_variations: Whether to create variations of the best ideas
        num_variations: Number of variations to create
        create_relationships: Whether to create SUBIDEA_OF relationships
    """
    logger.info("Starting automated backtester loop")
    
    # Initialize idea properties
    initialize_idea_properties()
    
    # Index all ideas in PatANN
    logger.info("Indexing all ideas in PatANN")
    index_all_ideas()
    
    # Create SUBIDEA_OF relationships if requested
    if create_relationships:
        logger.info("Creating SUBIDEA_OF relationships")
        create_all_subidea_relationships()
    
    # Run the UCB backtester loop
    logger.info(f"Running UCB backtester loop for {iterations} iterations")
    await ucb_main_loop(iterations=iterations, 
                       exploration_constant=exploration_constant,
                       sleep_time=sleep_time)
    
    # Create variations of the best ideas if requested
    if create_variations:
        logger.info(f"Creating variations of the best ideas")
        # Find the best ideas
        from neo4j import GraphDatabase
        
        # Neo4j connection parameters
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")
        
        # Create a driver
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Get the top 3 ideas by UCB score
            result = session.run("""
            MATCH (i:Idea)
            WHERE i.testCount > 0
            WITH i, i.totalScore / i.testCount as avgScore, i.testCount as testCount
            WITH i, avgScore, testCount, log(sum(testCount)) as logTotalTests
            WITH i, avgScore + $exploration_constant * sqrt(logTotalTests / testCount) as ucb
            ORDER BY ucb DESC
            LIMIT 3
            RETURN i.id as id, ucb
            """, exploration_constant=exploration_constant)
            
            # Create variations for each idea
            for record in result:
                idea_id = record["id"]
                ucb = record["ucb"]
                logger.info(f"Creating variations for idea {idea_id} with UCB score {ucb:.4f}")
                new_idea_ids = find_and_create_new_ideas(idea_id, num_variations)
                logger.info(f"Created {len(new_idea_ids)} variations for idea {idea_id}")
        
        # Close the driver
        driver.close()
    
    logger.info("Automated backtester loop completed")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Automated backtester loop")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations to run")
    parser.add_argument("--exploration", type=float, default=1.0, help="Exploration constant for UCB")
    parser.add_argument("--sleep", type=int, default=5, help="Time to sleep between iterations in seconds")
    parser.add_argument("--no-variations", action="store_true", help="Do not create variations of the best ideas")
    parser.add_argument("--num-variations", type=int, default=3, help="Number of variations to create")
    parser.add_argument("--no-relationships", action="store_true", help="Do not create SUBIDEA_OF relationships")
    args = parser.parse_args()
    
    # Run the automated loop
    asyncio.run(automated_loop(
        iterations=args.iterations,
        exploration_constant=args.exploration,
        sleep_time=args.sleep,
        create_variations=not args.no_variations,
        num_variations=args.num_variations,
        create_relationships=not args.no_relationships
    ))

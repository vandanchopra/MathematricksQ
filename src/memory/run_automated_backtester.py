"""
Script to run the automated UCB backtester continuously.
This script will:
1. Select the next idea to test based on UCB scores
2. Run a backtest for that idea
3. Store the results in Neo4j
4. Repeat
"""

import os
import sys
import asyncio
import argparse
import logging
import time
from ucb_backtester import main_loop

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

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run the automated UCB backtester continuously")
    parser.add_argument("--iterations", type=int, default=None, help="Number of iterations to run (None for infinite)")
    parser.add_argument("--interval", type=int, default=60, help="Interval between iterations in seconds")
    parser.add_argument("--exploration", type=float, default=1.0, help="Exploration constant for UCB")
    
    args = parser.parse_args()
    
    logger.info(f"Starting automated backtester with exploration {args.exploration}")
    if args.iterations:
        logger.info(f"Will run for {args.iterations} iterations")
    else:
        logger.info("Will run continuously until stopped")
    logger.info(f"Interval between iterations: {args.interval} seconds")
    
    # Run the UCB backtester
    await main_loop(iterations=args.iterations or 1000000, sleep_time=args.interval, exploration_constant=args.exploration)
    
    logger.info("Automated backtester completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Automated backtester stopped by user")
    except Exception as e:
        logger.error(f"Error in automated backtester: {e}")

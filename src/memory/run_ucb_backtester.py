"""
Script to run the UCB backtester continuously.
"""

import os
import sys
import asyncio
import argparse
import logging
from ucb_backtester import main_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("run_ucb_backtester.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RunUCBBacktester")

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run the UCB backtester continuously")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations to run")
    parser.add_argument("--sleep-time", type=int, default=5, help="Time to sleep between iterations in seconds")
    parser.add_argument("--exploration", type=float, default=1.0, help="Exploration constant for UCB")
    
    args = parser.parse_args()
    
    logger.info(f"Starting UCB backtester with {args.iterations} iterations, sleep time {args.sleep_time}s, exploration {args.exploration}")
    
    # Run the UCB backtester
    await main_loop(iterations=args.iterations, sleep_time=args.sleep_time, exploration_constant=args.exploration)
    
    logger.info("UCB backtester completed")

if __name__ == "__main__":
    asyncio.run(main())

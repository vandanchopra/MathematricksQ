"""
Command-line interface for running Monte Carlo Tree Search (MCTS).
"""

import argparse
import logging
import json
from mcts import run_mcts, get_best_child

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("run_mcts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RunMCTS")

def main():
    """Main function for the command-line interface."""
    parser = argparse.ArgumentParser(description="Run Monte Carlo Tree Search for trading strategy optimization")
    parser.add_argument("--idea-id", required=True, help="ID of the root idea")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations to run")
    parser.add_argument("--exploration", type=float, default=1.0, help="Exploration constant")
    parser.add_argument("--output", help="Output file for the best child")
    
    args = parser.parse_args()
    
    logger.info(f"Running MCTS with idea ID: {args.idea_id}, iterations: {args.iterations}, exploration: {args.exploration}")
    
    # Run MCTS
    root = run_mcts(args.idea_id, args.iterations, args.exploration)
    
    # Get the best child
    best_child = get_best_child(root)
    if best_child:
        logger.info(f"Best child: {best_child}")
        logger.info(f"Best child idea ID: {best_child.idea_id}")
        logger.info(f"Best child score: {best_child.Q:.4f}")
        
        # Save the best child to a file if specified
        if args.output:
            with open(args.output, "w") as f:
                json.dump({
                    "idea_id": best_child.idea_id,
                    "score": best_child.Q,
                    "context": best_child.context,
                    "params": best_child.params,
                    "description": best_child.description,
                    "backtest_id": best_child.backtest_id
                }, f, indent=2)
            logger.info(f"Best child saved to {args.output}")
    else:
        logger.info("No children found")

if __name__ == "__main__":
    main()

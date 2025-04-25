"""
Script to run the PatANN-based similarity search.
This script will:
1. Index all ideas in PatANN
2. Create SUBIDEA_OF relationships between similar ideas
3. Find and create new variations of ideas
"""

import os
import sys
import argparse
import logging
from patann_similarity import index_all_ideas, create_all_subidea_relationships, find_and_create_new_ideas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("run_patann_similarity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RunPatANNSimilarity")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run the PatANN-based similarity search")
    parser.add_argument("--index", action="store_true", help="Index all ideas in PatANN")
    parser.add_argument("--create-relationships", action="store_true", help="Create SUBIDEA_OF relationships between similar ideas")
    parser.add_argument("--create-variations", action="store_true", help="Find and create new variations of ideas")
    parser.add_argument("--idea-id", help="ID of the idea to find similar ideas for (required for --create-variations)")
    parser.add_argument("--num-variations", type=int, default=3, help="Number of variations to create (default: 3)")
    parser.add_argument("--k", type=int, default=3, help="Number of similar ideas to consider (default: 3)")
    parser.add_argument("--similarity-threshold", type=float, default=0.7, help="Minimum similarity score to create a relationship (default: 0.7)")
    
    args = parser.parse_args()
    
    # Check if at least one action is specified
    if not (args.index or args.create_relationships or args.create_variations):
        parser.error("At least one of --index, --create-relationships, or --create-variations must be specified")
    
    # Check if idea-id is specified for --create-variations
    if args.create_variations and not args.idea_id:
        parser.error("--idea-id is required for --create-variations")
    
    # Run the specified actions
    if args.index:
        logger.info("Indexing all ideas in PatANN")
        count = index_all_ideas()
        logger.info(f"Indexed {count} ideas")
    
    if args.create_relationships:
        logger.info(f"Creating SUBIDEA_OF relationships between similar ideas (k={args.k}, threshold={args.similarity_threshold})")
        count = create_all_subidea_relationships(args.k, args.similarity_threshold)
        logger.info(f"Created {count} SUBIDEA_OF relationships")
    
    if args.create_variations:
        logger.info(f"Finding and creating {args.num_variations} variations of idea {args.idea_id}")
        new_idea_ids = find_and_create_new_ideas(args.idea_id, args.num_variations)
        logger.info(f"Created {len(new_idea_ids)} new ideas: {new_idea_ids}")
    
    logger.info("PatANN similarity search completed")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test script for PatANN."""

import os
import sys
import numpy as np
import patann
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PatANN-Test")

# Configuration parameters
VECTOR_DIM = 128
NUM_VECTORS = 100
TOP_K = 10
SEARCH_RADIUS = 100
CONSTELLATION_SIZE = 16

def configure_index(ann):
    """Configure the PatANN index with standard settings"""
    ann.this_is_preproduction_software(True)
    # Use L2_SQUARE distance
    ann.setDistanceType(2)
    ann.setRadius(SEARCH_RADIUS)
    ann.setConstellationSize(CONSTELLATION_SIZE)

def generate_random_vectors(count, dim):
    """Generate random vectors for testing"""
    np.random.seed(42)  # Use fixed seed for reproducibility
    return np.float32(np.random.random((count, dim)) * 2 - 1)  # Values between -1 and 1

def test_patann():
    """Test PatANN functionality."""
    try:
        # Create an instance with specified dimensions
        logger.info("Creating PatANN instance...")
        ann = patann.createInstance(VECTOR_DIM)
        if ann is None:
            logger.error("Failed to create PatANN instance")
            return False

        # Configure the index
        logger.info("Configuring index...")
        configure_index(ann)

        # Create random vectors for testing
        logger.info("Generating random vectors...")
        vectors = generate_random_vectors(NUM_VECTORS, VECTOR_DIM)

        # Add vectors to the index
        logger.info("Adding vectors to the index...")
        vector_ids = []
        for i in range(vectors.shape[0]):
            # Make sure the vector is a proper float32 numpy array
            vector = np.ascontiguousarray(vectors[i], dtype=np.float32)
            vector_id = ann.addVector(vector)
            vector_ids.append(vector_id)

        # Create a query vector (use the first vector with slight modification)
        query_vector = vectors[0].copy()
        for i in range(10):
            pos = np.random.randint(0, VECTOR_DIM)
            query_vector[pos] += (np.random.random() - 0.5) * 0.1

        # Wait for the index to be ready (blocking call)
        logger.info("Waiting for index to be ready...")
        ann.waitForIndexReady()

        # Create query session and run query
        logger.info("Creating query session and performing search...")
        query = ann.createQuerySession(SEARCH_RADIUS, TOP_K)

        # Make sure query_vector is proper float32 numpy array
        query_vector_float32 = np.ascontiguousarray(query_vector, dtype=np.float32)
        query.query(query_vector_float32, TOP_K)

        # Get results
        result_ids = query.getResults(0)
        result_distances = query.getResultDists()

        logger.info(f"Found {len(result_ids)} results")
        for i in range(len(result_ids)):
            logger.info(f"Result {i}: ID={result_ids[i]}, Distance={result_distances[i]}")

        # Cleanup
        query.destroy()
        ann.destroy()

        return True
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = test_patann()
    print(f"PatANN test {'passed' if result else 'failed'}")

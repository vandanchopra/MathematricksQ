#!/usr/bin/env python3
"""
Script to check the current state of the Neo4j database
"""

import os
import sys
import logging
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Neo4jChecker")

def check_neo4j_state():
    """Check the current state of the Neo4j database."""
    # Connect to Neo4j
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Count nodes by label
        result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS count
        ORDER BY count DESC
        """)
        
        logger.info("Node counts by label:")
        for record in result:
            logger.info(f"  {record['label']}: {record['count']}")
        
        # Count relationships by type
        result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) AS rel, count(r) AS count
        ORDER BY count DESC
        """)
        
        logger.info("Relationship counts by type:")
        for record in result:
            logger.info(f"  {record['rel']}: {record['count']}")
        
        # Check for orphaned nodes (nodes without relationships)
        result = session.run("""
        MATCH (n)
        WHERE NOT (n)--()
        RETURN labels(n)[0] AS label, count(n) AS count
        ORDER BY count DESC
        """)
        
        logger.info("Orphaned node counts by label:")
        for record in result:
            logger.info(f"  {record['label']}: {record['count']}")
        
        # Check for Idea-Strategy-Context paths
        result = session.run("""
        MATCH p=(i:Idea)-[:TESTED_IN]->(s:Backtest)-[:EXECUTED_IN]->(c:Context)
        RETURN count(p) AS path_count
        """)
        
        logger.info(f"Idea-Backtest-Context path count: {result.single()['path_count']}")
    
    driver.close()

if __name__ == "__main__":
    check_neo4j_state()

#!/usr/bin/env python3
"""
Script to find orphaned nodes in the Neo4j database
"""

import os
import sys
import logging
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OrphanFinder")

def find_orphans():
    """Find orphaned nodes in the Neo4j database."""
    # Connect to Neo4j
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Find Contexts never linked by EXECUTED_IN
        logger.info("Contexts never linked by EXECUTED_IN:")
        result = session.run("""
        MATCH (c:Context)
        WHERE NOT ((:Backtest)-[:EXECUTED_IN]->(c))
        RETURN c.id AS id, c.market AS market, c.timeframe AS timeframe
        """)
        
        for record in result:
            logger.info(f"  {record['id']} ({record['market']} {record['timeframe']})")
        
        # Find Backtests never linked by TESTED_IN
        logger.info("Backtests never linked by TESTED_IN:")
        result = session.run("""
        MATCH (b:Backtest)
        WHERE NOT ((:Idea)-[:TESTED_IN]->(b))
        RETURN b.id AS id
        """)
        
        for record in result:
            logger.info(f"  {record['id']}")
        
        # Find Backtests never linked by EXECUTED_IN
        logger.info("Backtests never linked by EXECUTED_IN:")
        result = session.run("""
        MATCH (b:Backtest)
        WHERE NOT ((b)-[:EXECUTED_IN]->(:Context))
        RETURN b.id AS id
        """)
        
        for record in result:
            logger.info(f"  {record['id']}")
        
        # Find Ideas never linked by TESTED_IN
        logger.info("Ideas never linked by TESTED_IN:")
        result = session.run("""
        MATCH (i:Idea)
        WHERE NOT ((i)-[:TESTED_IN]->(:Backtest))
        RETURN i.id AS id, i.description AS description
        """)
        
        for record in result:
            logger.info(f"  {record['id']} ({record['description']})")
        
        # Find Ideas never linked by APPLIES_IN
        logger.info("Ideas never linked by APPLIES_IN:")
        result = session.run("""
        MATCH (i:Idea)
        WHERE NOT ((i)-[:APPLIES_IN]->(:Context))
        RETURN i.id AS id, i.description AS description
        """)
        
        for record in result:
            logger.info(f"  {record['id']} ({record['description']})")
        
        # Find Scenarios never linked by SUBIDEA_OF
        logger.info("Scenarios never linked by SUBIDEA_OF:")
        result = session.run("""
        MATCH (s:Scenario)
        WHERE NOT ((s)-[:SUBIDEA_OF]->(:Idea))
        RETURN s.id AS id, s.description AS description
        """)
        
        for record in result:
            logger.info(f"  {record['id']} ({record['description']})")
        
        # Find Scenarios never linked by APPLIES_IN
        logger.info("Scenarios never linked by APPLIES_IN:")
        result = session.run("""
        MATCH (s:Scenario)
        WHERE NOT ((s)-[:APPLIES_IN]->(:Context))
        RETURN s.id AS id, s.description AS description
        """)
        
        for record in result:
            logger.info(f"  {record['id']} ({record['description']})")
    
    driver.close()

if __name__ == "__main__":
    find_orphans()

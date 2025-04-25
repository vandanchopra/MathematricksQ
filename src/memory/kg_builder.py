#!/usr/bin/env python3
"""
Knowledge Graph Builder for Memory System

This module provides functions to build and maintain the Neo4j knowledge graph
for the memory system, including schema definition and data ingestion.
"""

import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Neo4j connection
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def setup_schema():
    """
    Set up the Neo4j schema with constraints and indexes.
    """
    with driver.session() as session:
        # Create constraints
        session.run("CREATE CONSTRAINT ON (i:Idea) ASSERT i.id IS UNIQUE")
        session.run("CREATE CONSTRAINT ON (b:Backtest) ASSERT b.id IS UNIQUE")
        session.run("CREATE CONSTRAINT ON (s:Scenario) ASSERT s.id IS UNIQUE")
        session.run("CREATE CONSTRAINT ON (c:Context) ASSERT c.id IS UNIQUE")
        
        print("Schema setup complete")

def store_idea(id=None, description=None, created_at=None, **kwargs):
    """
    Store an Idea node in the knowledge graph.
    
    Args:
        id (str): Unique identifier for the idea
        description (str): Description of the idea
        created_at (str): Timestamp when the idea was created
        **kwargs: Additional properties for the idea
    
    Returns:
        str: The ID of the created/updated idea
    """
    if id is None:
        id = str(uuid.uuid4())
    
    if created_at is None:
        created_at = datetime.now().isoformat()
    
    properties = {
        "id": id,
        "description": description,
        "created_at": created_at,
        **kwargs
    }
    
    with driver.session() as session:
        session.run("""
            MERGE (i:Idea {id: $id})
            SET i += $properties
        """, id=id, properties=properties)
    
    print(f"Stored Idea: {id}")
    return id

def store_scenario(id=None, description=None, created_at=None, parent_idea_id=None, **kwargs):
    """
    Store a Scenario node in the knowledge graph.
    
    Args:
        id (str): Unique identifier for the scenario
        description (str): Description of the scenario
        created_at (str): Timestamp when the scenario was created
        parent_idea_id (str): ID of the parent idea
        **kwargs: Additional properties for the scenario
    
    Returns:
        str: The ID of the created/updated scenario
    """
    if id is None:
        id = str(uuid.uuid4())
    
    if created_at is None:
        created_at = datetime.now().isoformat()
    
    properties = {
        "id": id,
        "description": description,
        "created_at": created_at,
        **kwargs
    }
    
    with driver.session() as session:
        session.run("""
            MERGE (s:Scenario {id: $id})
            SET s += $properties
        """, id=id, properties=properties)
        
        if parent_idea_id:
            session.run("""
                MATCH (s:Scenario {id: $scenario_id}), (i:Idea {id: $idea_id})
                MERGE (s)-[:SUBIDEA_OF]->(i)
            """, scenario_id=id, idea_id=parent_idea_id)
    
    print(f"Stored Scenario: {id}")
    return id

def store_context(id=None, market=None, timeframe=None, **kwargs):
    """
    Store a Context node in the knowledge graph.
    
    Args:
        id (str): Unique identifier for the context
        market (str): Market identifier (e.g., "BTC/USD")
        timeframe (str): Timeframe (e.g., "1d", "4h")
        **kwargs: Additional properties for the context
    
    Returns:
        str: The ID of the created/updated context
    """
    if id is None:
        id = str(uuid.uuid4())
    
    properties = {
        "id": id,
        "market": market,
        "timeframe": timeframe,
        **kwargs
    }
    
    with driver.session() as session:
        session.run("""
            MERGE (c:Context {id: $id})
            SET c += $properties
        """, id=id, properties=properties)
    
    print(f"Stored Context: {id}")
    return id

def store_backtest(id=None, idea_id=None, context_id=None, scenario_id=None, metrics=None, **kwargs):
    """
    Store a Backtest node in the knowledge graph.
    
    Args:
        id (str): Unique identifier for the backtest
        idea_id (str): ID of the idea being tested
        context_id (str): ID of the context in which the backtest was executed
        scenario_id (str): ID of the scenario to which the backtest applies (optional)
        metrics (dict): Dictionary of metrics (e.g., Sharpe, CAGR, MaxDrawdown)
        **kwargs: Additional properties for the backtest
    
    Returns:
        str: The ID of the created/updated backtest
    """
    if id is None:
        id = str(uuid.uuid4())
    
    if metrics is None:
        metrics = {}
    
    # Prefix metrics with "metric_" to make them easier to identify
    metric_properties = {f"metric_{k}": v for k, v in metrics.items()}
    
    properties = {
        "id": id,
        "date": datetime.now().isoformat(),
        **metric_properties,
        **kwargs
    }
    
    with driver.session() as session:
        # Create or update the backtest node
        session.run("""
            MERGE (b:Backtest {id: $id})
            SET b += $properties
        """, id=id, properties=properties)
        
        # Connect to idea
        if idea_id:
            session.run("""
                MATCH (i:Idea {id: $idea_id}), (b:Backtest {id: $backtest_id})
                MERGE (i)-[r:TESTED_IN]->(b)
                SET r += $metrics
            """, idea_id=idea_id, backtest_id=id, metrics=metrics)
        
        # Connect to context
        if context_id:
            session.run("""
                MATCH (b:Backtest {id: $backtest_id}), (c:Context {id: $context_id})
                MERGE (b)-[:EXECUTED_IN]->(c)
            """, backtest_id=id, context_id=context_id)
        
        # Connect to scenario (if provided)
        if scenario_id:
            session.run("""
                MATCH (b:Backtest {id: $backtest_id}), (s:Scenario {id: $scenario_id})
                MERGE (b)-[:APPLIES_TO]->(s)
            """, backtest_id=id, scenario_id=scenario_id)
    
    print(f"Stored Backtest: {id}")
    return id

def get_description(node_id):
    """
    Get the description of a node by its ID.
    
    Args:
        node_id (str): ID of the node
    
    Returns:
        str: Description of the node
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            WHERE n.id = $node_id
            RETURN n.description AS description
        """, node_id=node_id)
        
        record = result.single()
        if record:
            return record["description"]
        return None

def clear_database():
    """
    Clear all data from the database.
    WARNING: This will delete all nodes and relationships.
    """
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    
    print("Database cleared")

if __name__ == "__main__":
    # Example usage
    setup_schema()
    
    # Create some sample data
    idea_id = store_idea(
        description="Using Internal Bar Strength (IBS) for mean reversion trading",
        tags=["mean-reversion", "technical-indicator", "IBS"]
    )
    
    scenario_id = store_scenario(
        description="IBS applied to country ETFs",
        parent_idea_id=idea_id,
        tags=["ETF", "country", "global"]
    )
    
    context_id = store_context(
        market="ETF-Basket",
        timeframe="1d",
        description="Daily timeframe for a basket of country ETFs"
    )
    
    backtest_id = store_backtest(
        idea_id=idea_id,
        context_id=context_id,
        scenario_id=scenario_id,
        metrics={
            "Sharpe": 1.85,
            "CAGR": 0.12,
            "MaxDrawdown": 0.15,
            "WinRate": 0.58,
            "ProfitFactor": 1.65,
            "TotalTrades": 250
        }
    )
    
    print("Sample data created successfully")

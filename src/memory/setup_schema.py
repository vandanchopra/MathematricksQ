"""
Setup the Neo4j schema for the memory knowledge graph.
This script creates constraints and initializes properties for existing Idea nodes.
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")

print(f"Connecting to Neo4j at {neo4j_uri} with user {neo4j_user}")

# Create a driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def setup_schema():
    """Set up the Neo4j schema with constraints and indexes."""
    with driver.session() as session:
        # Create constraint on Idea.id
        try:
            session.run("CREATE CONSTRAINT ON (i:Idea) ASSERT i.id IS UNIQUE")
            print("Created constraint on Idea.id")
        except Exception as e:
            print(f"Constraint on Idea.id already exists or error: {e}")
        
        # Create constraint on Backtest.id
        try:
            session.run("CREATE CONSTRAINT ON (b:Backtest) ASSERT b.id IS UNIQUE")
            print("Created constraint on Backtest.id")
        except Exception as e:
            print(f"Constraint on Backtest.id already exists or error: {e}")
        
        # Create constraint on Context.id
        try:
            session.run("CREATE CONSTRAINT ON (c:Context) ASSERT c.id IS UNIQUE")
            print("Created constraint on Context.id")
        except Exception as e:
            print(f"Constraint on Context.id already exists or error: {e}")
        
        # Create constraint on Scenario.id
        try:
            session.run("CREATE CONSTRAINT ON (s:Scenario) ASSERT s.id IS UNIQUE")
            print("Created constraint on Scenario.id")
        except Exception as e:
            print(f"Constraint on Scenario.id already exists or error: {e}")

def initialize_idea_properties():
    """Initialize testCount and totalScore properties for existing Idea nodes."""
    with driver.session() as session:
        result = session.run("""
        MATCH (i:Idea)
        WHERE i.testCount IS NULL OR i.totalScore IS NULL
        SET i.testCount = COALESCE(i.testCount, 0),
            i.totalScore = COALESCE(i.totalScore, 0.0)
        RETURN count(i) AS updated_count
        """)
        updated_count = result.single()["updated_count"]
        print(f"Initialized properties for {updated_count} Idea nodes")

if __name__ == "__main__":
    setup_schema()
    initialize_idea_properties()
    driver.close()
    print("Schema setup complete")

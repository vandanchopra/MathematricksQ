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

# Create a test pattern
with driver.session() as session:
    # Get a sample idea
    result = session.run("""
    MATCH (i:Idea)
    RETURN i.id AS id, i.description AS description
    LIMIT 1
    """)
    idea = result.single()
    if idea:
        idea_id = idea['id']
        print(f"Using idea: {idea_id} - {idea['description']}")
        
        # Create a test backtest
        backtest_id = f"bt_test_{idea_id}"
        session.run("""
        MERGE (b:Backtest {id: $backtest_id})
        SET b.metric_Sharpe = 1.5,
            b.metric_CAGR = 0.12,
            b.metric_MaxDrawdown = -0.15,
            b.metric_WinRate = 0.65,
            b.metric_TotalTrades = 100,
            b.metric_ProfitFactor = 1.8
        RETURN b
        """, backtest_id=backtest_id)
        print(f"Created backtest: {backtest_id}")
        
        # Create a test context
        context_id = "test_context"
        session.run("""
        MERGE (c:Context {id: $context_id})
        SET c.market = 'TEST',
            c.timeframe = 'DAILY'
        RETURN c
        """, context_id=context_id)
        print(f"Created context: {context_id}")
        
        # Create the relationships
        session.run("""
        MATCH (i:Idea {id: $idea_id})
        MATCH (b:Backtest {id: $backtest_id})
        MERGE (i)-[:TESTED_IN]->(b)
        """, idea_id=idea_id, backtest_id=backtest_id)
        print(f"Created relationship: {idea_id} -[:TESTED_IN]-> {backtest_id}")
        
        session.run("""
        MATCH (b:Backtest {id: $backtest_id})
        MATCH (c:Context {id: $context_id})
        MERGE (b)-[:EXECUTED_IN]->(c)
        """, backtest_id=backtest_id, context_id=context_id)
        print(f"Created relationship: {backtest_id} -[:EXECUTED_IN]-> {context_id}")
        
        # Verify the pattern
        result = session.run("""
        MATCH (i:Idea {id: $idea_id})-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
        RETURN i.id AS idea_id, b.id AS backtest_id, c.id AS context_id
        """, idea_id=idea_id)
        pattern = result.single()
        if pattern:
            print(f"Verified pattern: {pattern['idea_id']} -> {pattern['backtest_id']} -> {pattern['context_id']}")
        else:
            print(f"Failed to verify pattern for idea {idea_id}")
    else:
        print("No ideas found")

# Close the driver
driver.close()

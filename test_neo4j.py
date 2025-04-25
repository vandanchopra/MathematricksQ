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

# Test the connection
with driver.session() as session:
    # Check if we can connect
    result = session.run("RETURN 1 as test")
    print(f"Connection test: {result.single()['test']}")
    
    # Check if we have ideas
    result = session.run("MATCH (i:Idea) RETURN count(i) as count")
    print(f"Number of ideas: {result.single()['count']}")
    
    # Check if we have the Idea-Backtest-Context pattern
    result = session.run("""
    MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
    RETURN count(*) as count
    """)
    print(f"Number of Idea-Backtest-Context patterns: {result.single()['count']}")
    
    # Get a sample idea
    result = session.run("""
    MATCH (i:Idea)
    RETURN i.id AS id, i.description AS description
    LIMIT 1
    """)
    idea = result.single()
    if idea:
        print(f"Sample idea: {idea['id']} - {idea['description']}")
        
        # Try to get the Idea-Backtest-Context pattern for this idea
        result = session.run("""
        MATCH (i:Idea {id: $idea_id})-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
        RETURN i.id AS idea_id, b.id AS backtest_id, c.id AS context_id
        LIMIT 1
        """, idea_id=idea['id'])
        pattern = result.single()
        if pattern:
            print(f"Found pattern: {pattern['idea_id']} -> {pattern['backtest_id']} -> {pattern['context_id']}")
        else:
            print(f"No pattern found for idea {idea['id']}")
    else:
        print("No ideas found")

# Close the driver
driver.close()

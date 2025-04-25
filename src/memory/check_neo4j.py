"""
Check the Neo4j database.
"""

from neo4j import GraphDatabase

# Neo4j connection parameters
neo4j_uri = "bolt://localhost:7688"
neo4j_user = "neo4j"
neo4j_password = "trading123"

# Create a driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def check_node_counts():
    """
    Check the number of nodes of each type in the Neo4j database.
    """
    with driver.session() as session:
        result = session.run("""
        MATCH (n)
        RETURN labels(n) as labels, count(n) as count
        """)
        
        print("Node counts:")
        for record in result:
            print(f"  {record['labels']}: {record['count']}")

def check_relationship_counts():
    """
    Check the number of relationships of each type in the Neo4j database.
    """
    with driver.session() as session:
        result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        """)
        
        print("Relationship counts:")
        for record in result:
            print(f"  {record['type']}: {record['count']}")

def check_ideas():
    """
    Check the ideas in the Neo4j database.
    """
    with driver.session() as session:
        result = session.run("""
        MATCH (i:Idea)
        RETURN i.id as id, i.description as description, i.testCount as testCount, i.totalScore as totalScore
        LIMIT 5
        """)
        
        print("Ideas:")
        for record in result:
            print(f"  {record['id']}: {record['description'][:50]}... (testCount: {record['testCount']}, totalScore: {record['totalScore']})")

def check_backtests():
    """
    Check the backtests in the Neo4j database.
    """
    with driver.session() as session:
        result = session.run("""
        MATCH (b:Backtest)
        RETURN b.id as id, b.metric_Sharpe as sharpe, b.metric_CAGR as cagr, b.metric_MaxDrawdown as maxdd
        LIMIT 5
        """)
        
        print("Backtests:")
        for record in result:
            print(f"  {record['id']}: Sharpe={record['sharpe']:.2f}, CAGR={record['cagr']:.2f}, MaxDD={record['maxdd']:.2f}")

def check_contexts():
    """
    Check the contexts in the Neo4j database.
    """
    with driver.session() as session:
        result = session.run("""
        MATCH (c:Context)
        RETURN c.id as id, c.market as market, c.timeframe as timeframe
        LIMIT 5
        """)
        
        print("Contexts:")
        for record in result:
            print(f"  {record['id']}: {record['market']} {record['timeframe']}")

def main():
    """
    Main function.
    """
    try:
        check_node_counts()
        print()
        check_relationship_counts()
        print()
        check_ideas()
        print()
        check_backtests()
        print()
        check_contexts()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()

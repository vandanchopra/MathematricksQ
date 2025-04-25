#!/usr/bin/env python3

from neo4j import GraphDatabase

# Connect to Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Get node labels
with driver.session() as session:
    print("Node labels:")
    result = session.run("MATCH (n) RETURN DISTINCT labels(n) AS labels")
    for record in result:
        print(f"  {record['labels']}")

# Get relationship types
with driver.session() as session:
    print("\nRelationship types:")
    result = session.run("MATCH ()-[r]->() RETURN DISTINCT type(r) AS type")
    for record in result:
        print(f"  {record['type']}")

# Get node properties for each label
with driver.session() as session:
    print("\nNode properties:")
    result = session.run("MATCH (n) RETURN DISTINCT labels(n) AS labels LIMIT 10")
    labels = [record["labels"][0] for record in result]
    
    for label in labels:
        print(f"\n  {label} properties:")
        result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 1")
        for record in result:
            node = record["n"]
            for key in node.keys():
                print(f"    {key}: {type(node[key]).__name__}")

# Close the driver
driver.close()

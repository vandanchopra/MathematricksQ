#!/usr/bin/env python3
"""Script to check Neo4j database contents."""

from neo4j import GraphDatabase

class Neo4jChecker:
    def __init__(self, uri="bolt://localhost:7688", user="neo4j", password="trading123"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
        
    def check_nodes(self):
        """Check all nodes in the database."""
        print("\nChecking Nodes:")
        with self.driver.session() as session:
            # Check node counts by type
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as type, count(*) as count
            """)
            print("\nNode counts by type:")
            for record in result:
                print(f"{record['type']}: {record['count']}")
            
            # Check Strategy nodes with metrics
            result = session.run("""
                MATCH (s:Strategy)
                RETURN s.name as name, s.score as score, 
                       s.description as description
                LIMIT 3
            """)
            print("\nSample Strategy nodes:")
            for record in result:
                print(f"\nStrategy: {record['name']}")
                print(f"Score: {record['score']}")
                print(f"Description: {record['description']}")
            
            # Check Idea nodes
            result = session.run("""
                MATCH (i:Idea)
                RETURN i.name as name, i.description as description
                LIMIT 3
            """)
            print("\nSample Idea nodes:")
            for record in result:
                print(f"\nIdea: {record['name']}")
                print(f"Description: {record['description']}")
    
    def check_relationships(self):
        """Check relationships in the database."""
        print("\nChecking Relationships:")
        with self.driver.session() as session:
            # Count relationships by type
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
            """)
            print("\nRelationship counts by type:")
            for record in result:
                print(f"{record['type']}: {record['count']}")
            
            # Check Strategy-Idea relationships
            result = session.run("""
                MATCH (s:Strategy)-[r]->(i:Idea)
                RETURN s.name as strategy, type(r) as relation, i.name as idea
                LIMIT 5
            """)
            print("\nSample Strategy-Idea relationships:")
            relationships = list(result)
            if relationships:
                for record in relationships:
                    print(f"{record['strategy']} --[{record['relation']}]--> {record['idea']}")
            else:
                print("No Strategy-Idea relationships found!")

            # Check Strategy-Paper relationships
            result = session.run("""
                MATCH (s:Strategy)-[r]->(p:Paper)
                RETURN s.name as strategy, type(r) as relation, p.title as paper
                LIMIT 5
            """)
            print("\nSample Strategy-Paper relationships:")
            relationships = list(result)
            if relationships:
                for record in relationships:
                    print(f"{record['strategy']} --[{record['relation']}]--> {record['paper']}")
            else:
                print("No Strategy-Paper relationships found!")

            # Check Paper-Idea relationships
            result = session.run("""
                MATCH (i:Idea)-[r]->(p:Paper)
                RETURN i.name as idea, type(r) as relation, p.title as paper
                LIMIT 5
            """)
            print("\nSample Idea-Paper relationships:")
            relationships = list(result)
            if relationships:
                for record in relationships:
                    print(f"{record['idea']} --[{record['relation']}]--> {record['paper']}")
            else:
                print("No Idea-Paper relationships found!")

def main():
    checker = Neo4jChecker()
    try:
        checker.check_nodes()
        checker.check_relationships()
    finally:
        checker.close()

if __name__ == "__main__":
    main()
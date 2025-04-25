from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from .interface import MemoryBackend

load_dotenv()

class Neo4jMemoryBackend(MemoryBackend):
    """Neo4j implementation of the graph memory backend."""
    
    def __init__(self):
        """Initialize the Neo4j connection using environment variables."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
    def __del__(self):
        """Close the Neo4j connection when the instance is destroyed."""
        if hasattr(self, 'driver'):
            self.driver.close()
            
    def store_idea(self, 
                   idea_id: str, 
                   content: Dict[str, Any], 
                   metadata: Dict[str, Any],
                   relationships: Optional[List[Dict[str, str]]] = None) -> None:
        """Store a trading idea as a node in Neo4j."""
        with self.driver.session() as session:
            # Create idea node with content and metadata
            query = """
            MERGE (i:Idea {id: $idea_id})
            SET i.content = $content,
                i.metadata = $metadata,
                i.created_at = datetime()
            """
            session.run(query, idea_id=idea_id, content=json.dumps(content),
                       metadata=json.dumps(metadata))
            
            # Create relationships if provided
            if relationships:
                for rel in relationships:
                    query = """
                    MATCH (i:Idea {id: $idea_id})
                    MATCH (other {id: $other_id})
                    MERGE (i)-[r:$rel_type]->(other)
                    """
                    session.run(query, idea_id=idea_id, other_id=rel['target_id'],
                              rel_type=rel['type'])
                              
    def store_backtest(self,
                      backtest_id: str,
                      metrics: Dict[str, Any],
                      strategy_id: str,
                      idea_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store backtest results and create relationships to strategy and idea."""
        with self.driver.session() as session:
            # Create backtest node
            query = """
            MERGE (b:Backtest {id: $backtest_id})
            SET b.metrics = $metrics,
                b.metadata = $metadata,
                b.created_at = datetime()
            """
            session.run(query, backtest_id=backtest_id, metrics=json.dumps(metrics),
                       metadata=json.dumps(metadata or {}))
                       
            # Link to strategy
            query = """
            MATCH (b:Backtest {id: $backtest_id})
            MATCH (s:Strategy {id: $strategy_id})
            MERGE (s)-[r:HAS_BACKTEST]->(b)
            """
            session.run(query, backtest_id=backtest_id, strategy_id=strategy_id)
            
            # Link to idea if provided
            if idea_id:
                query = """
                MATCH (b:Backtest {id: $backtest_id})
                MATCH (i:Idea {id: $idea_id})
                MERGE (b)-[r:IMPLEMENTS_IDEA]->(i)
                """
                session.run(query, backtest_id=backtest_id, idea_id=idea_id)
                
    def store_strategy(self,
                      strategy_id: str,
                      code: str,
                      version: str,
                      idea_id: Optional[str] = None,
                      parent_strategy_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a strategy version and its relationships."""
        with self.driver.session() as session:
            # Create strategy node
            query = """
            MERGE (s:Strategy {id: $strategy_id})
            SET s.code = $code,
                s.version = $version,
                s.metadata = $metadata,
                s.created_at = datetime()
            """
            session.run(query, strategy_id=strategy_id, code=code,
                       version=version, metadata=json.dumps(metadata or {}))
                       
            # Link to parent strategy if provided
            if parent_strategy_id:
                query = """
                MATCH (s:Strategy {id: $strategy_id})
                MATCH (p:Strategy {id: $parent_id})
                MERGE (s)-[r:DERIVED_FROM]->(p)
                """
                session.run(query, strategy_id=strategy_id, parent_id=parent_strategy_id)
                
            # Link to idea if provided
            if idea_id:
                query = """
                MATCH (s:Strategy {id: $strategy_id})
                MATCH (i:Idea {id: $idea_id})
                MERGE (s)-[r:IMPLEMENTS_IDEA]->(i)
                """
                session.run(query, strategy_id=strategy_id, idea_id=idea_id)
                
    def query_similar_ideas(self,
                          text: str,
                          top_k: int = 5,
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find similar ideas using vector similarity (requires vector index in Neo4j)."""
        with self.driver.session() as session:
            query = """
            CALL db.index.vector.queryNodes('idea_embeddings', $top_k, $embedding)
            YIELD node, score
            WHERE node:Idea
            """
            
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(f"node.metadata.{key} = ${key}")
                if filter_conditions:
                    query += " AND " + " AND ".join(filter_conditions)
                    
            query += " RETURN node.id as id, node.content as content, node.metadata as metadata, score"
            
            # Note: In a real implementation, you would compute the embedding of the text here
            # and pass it to the query. This is a simplified version.
            embedding = [0.0] * 768  # Placeholder embedding
            
            result = session.run(query, embedding=embedding, top_k=top_k, **filters or {})
            return [dict(record) for record in result]
            
    def query_strategy_history(self,
                             strategy_id: str,
                             include_backtests: bool = True) -> Dict[str, Any]:
        """Get the full history of a strategy."""
        with self.driver.session() as session:
            query = """
            MATCH (s:Strategy {id: $strategy_id})
            OPTIONAL MATCH path = (s)-[:DERIVED_FROM*]->(ancestor:Strategy)
            """
            
            if include_backtests:
                query += """
                OPTIONAL MATCH (node)-[:HAS_BACKTEST]->(b:Backtest)
                WITH s, path, collect({
                    id: b.id,
                    metrics: b.metrics,
                    created_at: b.created_at
                }) as backtests
                """
            
            query += """
            RETURN {
                strategy: s,
                ancestors: collect(ancestor),
                backtests: backtests
            } as result
            """
            
            result = session.run(query, strategy_id=strategy_id)
            return dict(result.single()['result'])
            
    def find_top_strategies(self,
                          metric: str,
                          timeframe: Optional[str] = None,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Find top performing strategies based on a metric."""
        with self.driver.session() as session:
            query = """
            MATCH (s:Strategy)-[:HAS_BACKTEST]->(b:Backtest)
            WHERE b.metrics.%s IS NOT NULL
            """ % metric
            
            if timeframe:
                query += " AND b.created_at > datetime() - duration($timeframe)"
                
            if filters:
                for key, value in filters.items():
                    query += f" AND s.metadata.{key} = ${key}"
                    
            query += """
            WITH s, avg(b.metrics.%s) as avg_metric
            ORDER BY avg_metric DESC
            LIMIT $limit
            RETURN s.id as id, s.version as version, 
                   s.metadata as metadata, avg_metric
            """ % metric
            
            params = {'limit': limit, 'timeframe': timeframe, **(filters or {})}
            result = session.run(query, **params)
            return [dict(record) for record in result]
            
    def get_related_nodes(self,
                         node_id: str,
                         relationship_types: Optional[List[str]] = None,
                         max_depth: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Get nodes related to a given node."""
        with self.driver.session() as session:
            # Build relationship pattern based on types
            if relationship_types:
                rel_pattern = '|'.join(f':{rel_type}' for rel_type in relationship_types)
                rel_pattern = f"[r:{rel_pattern}]"
            else:
                rel_pattern = "[r]"
                
            query = f"""
            MATCH (n {{id: $node_id}})
            CALL apoc.path.expandConfig(n, {{
                relationshipFilter: $rel_pattern,
                maxLevel: $max_depth,
                uniqueness: 'NODE_GLOBAL'
            }})
            YIELD path
            WITH r, last(nodes(path)) as related
            RETURN type(r) as relationship_type,
                   collect({{
                       id: related.id,
                       labels: labels(related),
                       properties: properties(related)
                   }}) as nodes
            """
            
            result = session.run(query, node_id=node_id, 
                               rel_pattern=rel_pattern,
                               max_depth=max_depth)
                               
            related_nodes = {}
            for record in result:
                related_nodes[record['relationship_type']] = record['nodes']
                
            return related_nodes
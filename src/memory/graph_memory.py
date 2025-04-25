#!/usr/bin/env python3
"""
Graph Memory System

This module provides a hybrid memory system that combines Neo4j for graph relationships
and PatANN for vector embeddings.
"""

import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

from .kg_builder import (
    store_idea, store_scenario, store_context, store_backtest,
    get_description, clear_database
)
from .patann_indexer import (
    index_idea, index_scenario, search_similar, rank_next_ideas
)

# Load environment variables
load_dotenv()

class GraphMemory:
    """
    Hybrid memory system that combines Neo4j for graph relationships
    and PatANN for vector embeddings.
    """
    
    def __init__(self):
        """
        Initialize the graph memory system.
        """
        # Neo4j connection
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def add_idea(self, description, **kwargs):
        """
        Add an idea to the memory system.
        
        Args:
            description (str): Description of the idea
            **kwargs: Additional properties for the idea
        
        Returns:
            str: ID of the created idea
        """
        # Generate a unique ID
        id = str(uuid.uuid4())
        
        # Store in Neo4j
        store_idea(id=id, description=description, **kwargs)
        
        # Index in PatANN
        index_idea(id=id, description=description, **kwargs)
        
        return id
    
    def add_scenario(self, description, parent_idea_id, **kwargs):
        """
        Add a scenario to the memory system.
        
        Args:
            description (str): Description of the scenario
            parent_idea_id (str): ID of the parent idea
            **kwargs: Additional properties for the scenario
        
        Returns:
            str: ID of the created scenario
        """
        # Generate a unique ID
        id = str(uuid.uuid4())
        
        # Store in Neo4j
        store_scenario(id=id, description=description, parent_idea_id=parent_idea_id, **kwargs)
        
        # Index in PatANN
        index_scenario(id=id, description=description, parent_idea_id=parent_idea_id, **kwargs)
        
        return id
    
    def add_context(self, market, timeframe, **kwargs):
        """
        Add a context to the memory system.
        
        Args:
            market (str): Market identifier (e.g., "BTC/USD")
            timeframe (str): Timeframe (e.g., "1d", "4h")
            **kwargs: Additional properties for the context
        
        Returns:
            str: ID of the created context
        """
        # Generate a unique ID
        id = str(uuid.uuid4())
        
        # Store in Neo4j
        store_context(id=id, market=market, timeframe=timeframe, **kwargs)
        
        return id
    
    def add_backtest(self, idea_id, context_id, metrics, scenario_id=None, **kwargs):
        """
        Add a backtest to the memory system.
        
        Args:
            idea_id (str): ID of the idea being tested
            context_id (str): ID of the context in which the backtest was executed
            metrics (dict): Dictionary of metrics (e.g., Sharpe, CAGR, MaxDrawdown)
            scenario_id (str): ID of the scenario to which the backtest applies (optional)
            **kwargs: Additional properties for the backtest
        
        Returns:
            str: ID of the created backtest
        """
        # Generate a unique ID
        id = str(uuid.uuid4())
        
        # Store in Neo4j
        store_backtest(
            id=id,
            idea_id=idea_id,
            context_id=context_id,
            scenario_id=scenario_id,
            metrics=metrics,
            **kwargs
        )
        
        return id
    
    def find_similar_ideas(self, text, k=10):
        """
        Find ideas similar to the given text.
        
        Args:
            text (str): Text to search for
            k (int): Number of results to return
        
        Returns:
            list: List of similar ideas
        """
        return search_similar(text=text, node_type="Idea", k=k)
    
    def find_similar_scenarios(self, text, k=10):
        """
        Find scenarios similar to the given text.
        
        Args:
            text (str): Text to search for
            k (int): Number of results to return
        
        Returns:
            list: List of similar scenarios
        """
        return search_similar(text=text, node_type="Scenario", k=k)
    
    def get_idea_backtests(self, idea_id):
        """
        Get all backtests for a given idea.
        
        Args:
            idea_id (str): ID of the idea
        
        Returns:
            list: List of backtests
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Idea {id: $idea_id})-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
                RETURN b, c
            """, idea_id=idea_id)
            
            backtests = []
            for record in result:
                backtest = dict(record["b"])
                context = dict(record["c"])
                
                # Extract metrics
                metrics = {k.replace("metric_", ""): v for k, v in backtest.items() if k.startswith("metric_")}
                
                backtests.append({
                    "id": backtest["id"],
                    "date": backtest.get("date"),
                    "metrics": metrics,
                    "context": {
                        "id": context["id"],
                        "market": context.get("market"),
                        "timeframe": context.get("timeframe")
                    }
                })
            
            return backtests
    
    def get_context_backtests(self, context_id):
        """
        Get all backtests for a given context.
        
        Args:
            context_id (str): ID of the context
        
        Returns:
            list: List of backtests
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context {id: $context_id})
                RETURN i, b
            """, context_id=context_id)
            
            backtests = []
            for record in result:
                idea = dict(record["i"])
                backtest = dict(record["b"])
                
                # Extract metrics
                metrics = {k.replace("metric_", ""): v for k, v in backtest.items() if k.startswith("metric_")}
                
                backtests.append({
                    "id": backtest["id"],
                    "date": backtest.get("date"),
                    "metrics": metrics,
                    "idea": {
                        "id": idea["id"],
                        "description": idea.get("description")
                    }
                })
            
            return backtests
    
    def get_best_ideas(self, metric="Sharpe", k=10):
        """
        Get the best ideas based on a specific metric.
        
        Args:
            metric (str): Metric to use for ranking (e.g., "Sharpe", "CAGR")
            k (int): Number of results to return
        
        Returns:
            list: List of best ideas
        """
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
                WITH i, max(b.metric_{metric}) AS max_metric
                RETURN i.id AS id, i.description AS description, max_metric
                ORDER BY max_metric DESC
                LIMIT $k
            """, k=k)
            
            return [{
                "id": record["id"],
                "description": record["description"],
                f"max_{metric}": record["max_metric"]
            } for record in result]
    
    def recommend_next_ideas(self, current_idea_ids, k=5):
        """
        Recommend the next ideas to explore based on the current ideas.
        
        Args:
            current_idea_ids (list): List of current idea IDs
            k (int): Number of recommendations to return
        
        Returns:
            list: List of recommended ideas
        """
        ranked_ideas = rank_next_ideas(current_idea_ids, k=k)
        
        # Get full idea details
        ideas = []
        with self.driver.session() as session:
            for idea_id, score in ranked_ideas:
                result = session.run("""
                    MATCH (i:Idea {id: $idea_id})
                    RETURN i
                """, idea_id=idea_id)
                
                record = result.single()
                if record:
                    idea = dict(record["i"])
                    ideas.append({
                        "id": idea["id"],
                        "description": idea.get("description"),
                        "score": score
                    })
        
        return ideas
    
    def get_idea_scenarios(self, idea_id):
        """
        Get all scenarios for a given idea.
        
        Args:
            idea_id (str): ID of the idea
        
        Returns:
            list: List of scenarios
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Scenario)-[:SUBIDEA_OF]->(i:Idea {id: $idea_id})
                RETURN s
            """, idea_id=idea_id)
            
            return [dict(record["s"]) for record in result]
    
    def get_scenario_backtests(self, scenario_id):
        """
        Get all backtests for a given scenario.
        
        Args:
            scenario_id (str): ID of the scenario
        
        Returns:
            list: List of backtests
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (b:Backtest)-[:APPLIES_TO]->(s:Scenario {id: $scenario_id})
                MATCH (i:Idea)-[:TESTED_IN]->(b)
                MATCH (b)-[:EXECUTED_IN]->(c:Context)
                RETURN i, b, c
            """, scenario_id=scenario_id)
            
            backtests = []
            for record in result:
                idea = dict(record["i"])
                backtest = dict(record["b"])
                context = dict(record["c"])
                
                # Extract metrics
                metrics = {k.replace("metric_", ""): v for k, v in backtest.items() if k.startswith("metric_")}
                
                backtests.append({
                    "id": backtest["id"],
                    "date": backtest.get("date"),
                    "metrics": metrics,
                    "idea": {
                        "id": idea["id"],
                        "description": idea.get("description")
                    },
                    "context": {
                        "id": context["id"],
                        "market": context.get("market"),
                        "timeframe": context.get("timeframe")
                    }
                })
            
            return backtests
    
    def get_full_subgraph(self, context_id=None, idea_id=None):
        """
        Get the full subgraph for visualization.
        
        Args:
            context_id (str): ID of the context to filter by (optional)
            idea_id (str): ID of the idea to filter by (optional)
        
        Returns:
            dict: Graph data for visualization
        """
        where_clauses = []
        params = {}
        
        if context_id:
            where_clauses.append("c.id = $context_id")
            params["context_id"] = context_id
        
        if idea_id:
            where_clauses.append("i.id = $idea_id")
            params["idea_id"] = idea_id
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        with self.driver.session() as session:
            # Get Idea-Backtest-Context relationships
            q1 = f"""
            MATCH (i:Idea)-[r1:TESTED_IN]->(b:Backtest)-[r2:EXECUTED_IN]->(c:Context)
            {where_clause}
            RETURN i, r1, b, r2, c
            """
            result1 = list(session.run(q1, **params))
            
            # Get Backtest-Scenario relationships
            q2 = f"""
            MATCH (b:Backtest)-[r:APPLIES_TO]->(s:Scenario)
            {where_clause}
            MATCH (i:Idea)-[:TESTED_IN]->(b)
            MATCH (b)-[:EXECUTED_IN]->(c:Context)
            RETURN b, r, s
            """
            result2 = list(session.run(q2, **params))
            
            # Get Scenario-Idea relationships
            q3 = f"""
            MATCH (s:Scenario)-[r:SUBIDEA_OF]->(i:Idea)
            {where_clause}
            RETURN s, r, i
            """
            result3 = list(session.run(q3, **params))
            
            # Combine results
            nodes = {}
            edges = []
            
            # Process Idea-Backtest-Context relationships
            for record in result1:
                i, r1, b, r2, c = record["i"], record["r1"], record["b"], record["r2"], record["c"]
                
                # Add nodes
                if i["id"] not in nodes:
                    nodes[i["id"]] = {
                        "id": i["id"],
                        "type": "Idea",
                        "label": i.get("description", ""),
                        "properties": dict(i)
                    }
                
                if b["id"] not in nodes:
                    # Extract metrics
                    metrics = {k.replace("metric_", ""): v for k, v in b.items() if k.startswith("metric_")}
                    
                    nodes[b["id"]] = {
                        "id": b["id"],
                        "type": "Backtest",
                        "label": f"BT:{b['id']}",
                        "properties": dict(b),
                        "metrics": metrics
                    }
                
                if c["id"] not in nodes:
                    nodes[c["id"]] = {
                        "id": c["id"],
                        "type": "Context",
                        "label": f"{c.get('market', '')} {c.get('timeframe', '')}",
                        "properties": dict(c)
                    }
                
                # Add edges
                edges.append({
                    "source": i["id"],
                    "target": b["id"],
                    "type": "TESTED_IN",
                    "properties": {k: v for k, v in dict(r1).items() if k != "id"}
                })
                
                edges.append({
                    "source": b["id"],
                    "target": c["id"],
                    "type": "EXECUTED_IN",
                    "properties": {k: v for k, v in dict(r2).items() if k != "id"}
                })
            
            # Process Backtest-Scenario relationships
            for record in result2:
                b, r, s = record["b"], record["r"], record["s"]
                
                # Add nodes
                if s["id"] not in nodes:
                    nodes[s["id"]] = {
                        "id": s["id"],
                        "type": "Scenario",
                        "label": s.get("description", ""),
                        "properties": dict(s)
                    }
                
                # Add edges
                edges.append({
                    "source": b["id"],
                    "target": s["id"],
                    "type": "APPLIES_TO",
                    "properties": {k: v for k, v in dict(r).items() if k != "id"}
                })
            
            # Process Scenario-Idea relationships
            for record in result3:
                s, r, i = record["s"], record["r"], record["i"]
                
                # Add edges
                edges.append({
                    "source": s["id"],
                    "target": i["id"],
                    "type": "SUBIDEA_OF",
                    "properties": {k: v for k, v in dict(r).items() if k != "id"}
                })
            
            return {
                "nodes": list(nodes.values()),
                "edges": edges
            }
    
    def clear(self):
        """
        Clear all data from the memory system.
        WARNING: This will delete all nodes and relationships.
        """
        clear_database()

if __name__ == "__main__":
    # Example usage
    memory = GraphMemory()
    
    # Add some sample data
    idea_id = memory.add_idea(
        description="Using Internal Bar Strength (IBS) for mean reversion trading",
        tags=["mean-reversion", "technical-indicator", "IBS"]
    )
    
    scenario_id = memory.add_scenario(
        description="IBS applied to country ETFs",
        parent_idea_id=idea_id,
        tags=["ETF", "country", "global"]
    )
    
    context_id = memory.add_context(
        market="ETF-Basket",
        timeframe="1d",
        description="Daily timeframe for a basket of country ETFs"
    )
    
    backtest_id = memory.add_backtest(
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
    
    # Find similar ideas
    similar_ideas = memory.find_similar_ideas(
        text="mean reversion trading strategies",
        k=5
    )
    
    print("Similar ideas:")
    for idea in similar_ideas:
        print(f"ID: {idea['id']}, Score: {idea['score']}")
        print(f"Text: {idea['metadata'].get('text', '')}")
        print()
    
    # Get best ideas
    best_ideas = memory.get_best_ideas(metric="Sharpe", k=5)
    
    print("Best ideas by Sharpe ratio:")
    for idea in best_ideas:
        print(f"ID: {idea['id']}, Description: {idea['description']}")
        print(f"Max Sharpe: {idea['max_Sharpe']}")
        print()
    
    # Get full subgraph
    graph = memory.get_full_subgraph()
    
    print(f"Graph contains {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")

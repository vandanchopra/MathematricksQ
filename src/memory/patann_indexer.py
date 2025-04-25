#!/usr/bin/env python3
"""
PatANN Indexer for Memory System

This module provides functions to index and search vectors in PatANN
for the memory system.
"""

import os
import requests
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# PatANN connection
patann_url = os.getenv("PATANN_URL", "http://localhost:9200")

class PatANNClient:
    """
    Client for interacting with the PatANN vector database.
    """
    
    def __init__(self, base_url=None):
        """
        Initialize the PatANN client.
        
        Args:
            base_url (str): Base URL for the PatANN API
        """
        self.base_url = base_url or patann_url
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    def encode(self, text):
        """
        Encode text into a vector embedding.
        
        Args:
            text (str): Text to encode
        
        Returns:
            list: Vector embedding
        """
        return self.embedder.encode(text).tolist()
    
    def upsert(self, id, vector=None, text=None, metadata=None):
        """
        Insert or update a vector in PatANN.
        
        Args:
            id (str): Unique identifier for the vector
            vector (list): Vector embedding (optional if text is provided)
            text (str): Text to encode (optional if vector is provided)
            metadata (dict): Additional metadata for the vector
        
        Returns:
            bool: True if successful, False otherwise
        """
        if vector is None and text is None:
            raise ValueError("Either vector or text must be provided")
        
        if vector is None:
            vector = self.encode(text)
        
        if metadata is None:
            metadata = {}
        
        if text is not None and "text" not in metadata:
            metadata["text"] = text
        
        payload = {
            "id": id,
            "vector": vector,
            "metadata": metadata
        }
        
        try:
            response = requests.post(f"{self.base_url}/upsert", json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error upserting vector: {e}")
            return False
    
    def search(self, vector=None, text=None, k=10, filter=None):
        """
        Search for similar vectors in PatANN.
        
        Args:
            vector (list): Vector embedding to search for (optional if text is provided)
            text (str): Text to encode and search for (optional if vector is provided)
            k (int): Number of results to return
            filter (dict): Filter to apply to the search
        
        Returns:
            list: List of search results
        """
        if vector is None and text is None:
            raise ValueError("Either vector or text must be provided")
        
        if vector is None:
            vector = self.encode(text)
        
        payload = {
            "vector": vector,
            "limit": k
        }
        
        if filter:
            payload["filter"] = filter
        
        try:
            response = requests.post(f"{self.base_url}/search", json=payload)
            if response.status_code == 200:
                return response.json().get("results", [])
            return []
        except Exception as e:
            print(f"Error searching vectors: {e}")
            return []
    
    def delete(self, id):
        """
        Delete a vector from PatANN.
        
        Args:
            id (str): ID of the vector to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.delete(f"{self.base_url}/delete/{id}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleting vector: {e}")
            return False
    
    def batch_upsert(self, items):
        """
        Insert or update multiple vectors in PatANN.
        
        Args:
            items (list): List of dictionaries with id, vector/text, and metadata
        
        Returns:
            bool: True if successful, False otherwise
        """
        processed_items = []
        
        for item in items:
            id = item.get("id")
            vector = item.get("vector")
            text = item.get("text")
            metadata = item.get("metadata", {})
            
            if vector is None and text is None:
                continue
            
            if vector is None:
                vector = self.encode(text)
            
            if text is not None and "text" not in metadata:
                metadata["text"] = text
            
            processed_items.append({
                "id": id,
                "vector": vector,
                "metadata": metadata
            })
        
        if not processed_items:
            return True
        
        try:
            response = requests.post(f"{self.base_url}/batch/upsert", json={"items": processed_items})
            return response.status_code == 200
        except Exception as e:
            print(f"Error batch upserting vectors: {e}")
            return False

def index_idea(id, description, **kwargs):
    """
    Index an idea in PatANN.
    
    Args:
        id (str): ID of the idea
        description (str): Description of the idea
        **kwargs: Additional metadata for the idea
    
    Returns:
        bool: True if successful, False otherwise
    """
    client = PatANNClient()
    metadata = {
        "type": "Idea",
        **kwargs
    }
    return client.upsert(id=id, text=description, metadata=metadata)

def index_scenario(id, description, parent_idea_id=None, **kwargs):
    """
    Index a scenario in PatANN.
    
    Args:
        id (str): ID of the scenario
        description (str): Description of the scenario
        parent_idea_id (str): ID of the parent idea
        **kwargs: Additional metadata for the scenario
    
    Returns:
        bool: True if successful, False otherwise
    """
    client = PatANNClient()
    metadata = {
        "type": "Scenario",
        "parent_idea_id": parent_idea_id,
        **kwargs
    }
    return client.upsert(id=id, text=description, metadata=metadata)

def search_similar(text=None, vector=None, k=10, node_type=None):
    """
    Search for similar nodes in PatANN.
    
    Args:
        text (str): Text to search for (optional if vector is provided)
        vector (list): Vector to search for (optional if text is provided)
        k (int): Number of results to return
        node_type (str): Type of node to search for (e.g., "Idea", "Scenario")
    
    Returns:
        list: List of search results
    """
    client = PatANNClient()
    filter = {"type": node_type} if node_type else None
    return client.search(text=text, vector=vector, k=k, filter=filter)

def rank_next_ideas(current_strategy_idea_ids, k=10):
    """
    Rank the next ideas to explore based on the current strategy.
    
    Args:
        current_strategy_idea_ids (list): List of idea IDs in the current strategy
        k (int): Number of results to return
    
    Returns:
        list: List of (idea_id, score) tuples
    """
    from neo4j import GraphDatabase
    import os
    
    # Neo4j connection
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    # Get descriptions for the current ideas
    descriptions = []
    with driver.session() as session:
        for idea_id in current_strategy_idea_ids:
            result = session.run("""
                MATCH (i:Idea {id: $idea_id})
                RETURN i.description AS description
            """, idea_id=idea_id)
            
            record = result.single()
            if record and record["description"]:
                descriptions.append(record["description"])
    
    if not descriptions:
        return []
    
    # Create composite embedding
    client = PatANNClient()
    sub_vecs = [client.encode(desc) for desc in descriptions]
    comp = np.mean(sub_vecs, axis=0).tolist()
    
    # Search for similar ideas
    hits = client.search(vector=comp, k=k*2, filter={"type": "Idea"})
    cand_ids = [h["id"] for h in hits if h["id"] not in current_strategy_idea_ids][:k]
    
    if not cand_ids:
        return []
    
    # Rank by metrics
    with driver.session() as session:
        result = session.run("""
            MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
            WHERE i.id IN $cand_ids
            WITH i,
                 max(b.metric_Sharpe) AS Sharpe_max,
                 max(b.metric_CAGR) AS CAGR_max,
                 min(b.metric_MaxDrawdown) AS DD_min
            RETURN i.id AS idea,
                   (0.5*Sharpe_max + 0.3*CAGR_max - 0.2*DD_min) AS score
            ORDER BY score DESC
            LIMIT $k
        """, cand_ids=cand_ids, k=k)
        
        return [(record["idea"], record["score"]) for record in result]

if __name__ == "__main__":
    # Example usage
    client = PatANNClient()
    
    # Index some sample data
    index_idea(
        id="idea1",
        description="Using Internal Bar Strength (IBS) for mean reversion trading",
        tags=["mean-reversion", "technical-indicator", "IBS"]
    )
    
    index_scenario(
        id="scenario1",
        description="IBS applied to country ETFs",
        parent_idea_id="idea1",
        tags=["ETF", "country", "global"]
    )
    
    # Search for similar ideas
    results = search_similar(
        text="mean reversion trading strategies",
        node_type="Idea",
        k=5
    )
    
    print("Search results:")
    for result in results:
        print(f"ID: {result['id']}, Score: {result['score']}")
        print(f"Text: {result['metadata'].get('text', '')}")
        print()

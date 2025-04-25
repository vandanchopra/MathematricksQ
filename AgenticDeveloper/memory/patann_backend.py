"""PatAnn client implementation for vector storage and retrieval."""

from typing import Dict, List, Optional, Any
import os
import json
from patann_client import PatAnnClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from .interface import MemoryBackend

load_dotenv()

class PatAnnMemoryBackend(MemoryBackend):
    """PatAnn implementation of the memory backend for vector storage."""
    
    def __init__(self):
        """Initialize the PatAnn client and embedding model."""
        self.api_key = os.getenv("PATANN_API_KEY")
        self.endpoint = os.getenv("PATANN_ENDPOINT", "https://api.patann.com")
        self.collection_name = os.getenv("PATANN_COLLECTION", "trading_ideas")
        
        # Initialize PatAnn client
        self.client = PatAnnClient(
            api_key=self.api_key,
            endpoint=self.endpoint
        )
        
        # Initialize embedding model
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence-transformers."""
        return self.model.encode(text).tolist()
        
    def store_idea(self, 
                  idea_id: str, 
                  content: Dict[str, Any], 
                  metadata: Dict[str, Any],
                  relationships: Optional[List[Dict[str, str]]] = None) -> None:
        """Store a trading idea with vector embeddings."""
        # Convert content to text for embedding
        content_text = json.dumps(content)
        
        # Generate embedding
        embedding = self._get_embedding(content_text)
        
        # Store in PatAnn
        self.client.upsert(
            collection_name=self.collection_name,
            ids=[idea_id],
            embeddings=[embedding],
            metadatas=[{
                "content": content,
                "metadata": metadata,
                "relationships": relationships or []
            }]
        )
        
    def store_backtest(self,
                      backtest_id: str,
                      metrics: Dict[str, Any],
                      strategy_id: str,
                      idea_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store backtest results with vector embeddings."""
        # Convert metrics to text for embedding
        metrics_text = json.dumps(metrics)
        
        # Generate embedding
        embedding = self._get_embedding(metrics_text)
        
        # Store in PatAnn
        self.client.upsert(
            collection_name=self.collection_name,
            ids=[backtest_id],
            embeddings=[embedding],
            metadatas=[{
                "type": "backtest",
                "metrics": metrics,
                "strategy_id": strategy_id,
                "idea_id": idea_id,
                "metadata": metadata or {}
            }]
        )
        
    def store_strategy(self,
                      strategy_id: str,
                      code: str,
                      version: str,
                      idea_id: Optional[str] = None,
                      parent_strategy_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a strategy with vector embeddings."""
        # Generate embedding from code
        embedding = self._get_embedding(code)
        
        # Store in PatAnn
        self.client.upsert(
            collection_name=self.collection_name,
            ids=[strategy_id],
            embeddings=[embedding],
            metadatas=[{
                "type": "strategy",
                "code": code,
                "version": version,
                "idea_id": idea_id,
                "parent_strategy_id": parent_strategy_id,
                "metadata": metadata or {}
            }]
        )
        
    def query_similar_ideas(self,
                          text: str,
                          top_k: int = 5,
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find similar ideas using vector similarity."""
        # Generate embedding for query text
        query_embedding = self._get_embedding(text)
        
        # Build filter condition if needed
        filter_condition = None
        if filters:
            filter_parts = []
            for key, value in filters.items():
                filter_parts.append(f"metadata.{key} == '{value}'")
            if filter_parts:
                filter_condition = " AND ".join(filter_parts)
        
        # Query PatAnn
        results = self.client.query(
            collection_name=self.collection_name,
            query_embeddings=[query_embedding],
            n_results=top_k,
            filter=filter_condition
        )
        
        # Format results
        formatted_results = []
        for match in results.matches[0]:
            metadata = match.metadata
            formatted_results.append({
                "id": match.id,
                "content": metadata.get("content", {}),
                "metadata": metadata.get("metadata", {}),
                "score": match.score
            })
            
        return formatted_results
        
    def query_strategy_history(self,
                             strategy_id: str,
                             include_backtests: bool = True) -> Dict[str, Any]:
        """Get the full history of a strategy."""
        # This would require multiple queries and relationship traversal
        # which is better suited for a graph database like Neo4j
        # For PatAnn, we'll implement a simplified version
        
        # Get the strategy
        strategy_results = self.client.query(
            collection_name=self.collection_name,
            query_embeddings=[[0] * 768],  # Dummy embedding
            n_results=1,
            filter=f"id == '{strategy_id}'"
        )
        
        if not strategy_results.matches[0]:
            return {"error": "Strategy not found"}
            
        strategy = strategy_results.matches[0][0].metadata
        
        # Get parent strategies if any
        ancestors = []
        parent_id = strategy.get("parent_strategy_id")
        while parent_id:
            parent_results = self.client.query(
                collection_name=self.collection_name,
                query_embeddings=[[0] * 768],  # Dummy embedding
                n_results=1,
                filter=f"id == '{parent_id}'"
            )
            
            if not parent_results.matches[0]:
                break
                
            parent = parent_results.matches[0][0].metadata
            ancestors.append(parent)
            parent_id = parent.get("parent_strategy_id")
            
        # Get backtests if requested
        backtests = []
        if include_backtests:
            backtest_results = self.client.query(
                collection_name=self.collection_name,
                query_embeddings=[[0] * 768],  # Dummy embedding
                n_results=100,
                filter=f"type == 'backtest' AND strategy_id == '{strategy_id}'"
            )
            
            for match in backtest_results.matches[0]:
                backtests.append(match.metadata)
                
        return {
            "strategy": strategy,
            "ancestors": ancestors,
            "backtests": backtests
        }
        
    def find_top_strategies(self,
                          metric: str,
                          timeframe: Optional[str] = None,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Find top performing strategies based on a metric."""
        # Build filter condition
        filter_parts = ["type == 'backtest'"]
        
        if filters:
            for key, value in filters.items():
                filter_parts.append(f"metadata.{key} == '{value}'")
                
        filter_condition = " AND ".join(filter_parts)
        
        # Query all backtests matching the filter
        results = self.client.query(
            collection_name=self.collection_name,
            query_embeddings=[[0] * 768],  # Dummy embedding
            n_results=1000,  # Get a large number to sort locally
            filter=filter_condition
        )
        
        # Extract and sort backtests by the specified metric
        backtests = []
        for match in results.matches[0]:
            metadata = match.metadata
            metrics = metadata.get("metrics", {})
            if metric in metrics:
                backtests.append({
                    "id": match.id,
                    "strategy_id": metadata.get("strategy_id"),
                    "metric_value": metrics[metric],
                    "metadata": metadata.get("metadata", {})
                })
                
        # Sort by metric value (descending)
        backtests.sort(key=lambda x: x["metric_value"], reverse=True)
        
        # Get the top strategies
        top_strategies = []
        strategy_ids = set()
        
        for backtest in backtests:
            strategy_id = backtest["strategy_id"]
            if strategy_id not in strategy_ids:
                strategy_ids.add(strategy_id)
                
                # Get strategy details
                strategy_results = self.client.query(
                    collection_name=self.collection_name,
                    query_embeddings=[[0] * 768],  # Dummy embedding
                    n_results=1,
                    filter=f"id == '{strategy_id}'"
                )
                
                if strategy_results.matches[0]:
                    strategy = strategy_results.matches[0][0].metadata
                    top_strategies.append({
                        "id": strategy_id,
                        "version": strategy.get("version"),
                        "metadata": strategy.get("metadata", {}),
                        "avg_metric": backtest["metric_value"]
                    })
                    
                if len(top_strategies) >= limit:
                    break
                    
        return top_strategies
        
    def get_related_nodes(self,
                         node_id: str,
                         relationship_types: Optional[List[str]] = None,
                         max_depth: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Get nodes related to a given node."""
        # This is a graph operation that's not well-suited for vector databases
        # For PatAnn, we'll implement a simplified version that only looks at direct relationships
        
        # Get the node
        node_results = self.client.query(
            collection_name=self.collection_name,
            query_embeddings=[[0] * 768],  # Dummy embedding
            n_results=1,
            filter=f"id == '{node_id}'"
        )
        
        if not node_results.matches[0]:
            return {}
            
        node = node_results.matches[0][0].metadata
        
        # Extract relationships from metadata
        relationships = node.get("relationships", [])
        
        # Filter by relationship types if specified
        if relationship_types:
            relationships = [r for r in relationships if r.get("type") in relationship_types]
            
        # Group by relationship type
        related_nodes = {}
        
        for rel in relationships:
            rel_type = rel.get("type")
            target_id = rel.get("target_id")
            
            if not rel_type or not target_id:
                continue
                
            # Get target node
            target_results = self.client.query(
                collection_name=self.collection_name,
                query_embeddings=[[0] * 768],  # Dummy embedding
                n_results=1,
                filter=f"id == '{target_id}'"
            )
            
            if not target_results.matches[0]:
                continue
                
            target = target_results.matches[0][0].metadata
            
            if rel_type not in related_nodes:
                related_nodes[rel_type] = []
                
            related_nodes[rel_type].append({
                "id": target_id,
                "properties": target
            })
            
        return related_nodes

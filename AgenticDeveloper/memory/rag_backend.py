"""GraphRAG implementation for enhanced retrieval-augmented generation."""

from typing import Dict, List, Optional, Any
import os
import json
from graphrag import GraphRAG
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from .interface import MemoryBackend
from .graph_backend import Neo4jMemoryBackend
from .patann_backend import PatAnnMemoryBackend

load_dotenv()

class GraphRAGMemoryBackend(MemoryBackend):
    """GraphRAG implementation combining graph and vector capabilities."""
    
    def __init__(self):
        """Initialize the GraphRAG backend with Neo4j and PatAnn backends."""
        # Initialize the underlying backends
        self.graph_backend = Neo4jMemoryBackend()
        self.vector_backend = PatAnnMemoryBackend()
        
        # Initialize embedding model
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Initialize GraphRAG
        self.graphrag = GraphRAG(
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            embedding_model=self.model
        )
        
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence-transformers."""
        return self.model.encode(text).tolist()
        
    def store_idea(self, 
                  idea_id: str, 
                  content: Dict[str, Any], 
                  metadata: Dict[str, Any],
                  relationships: Optional[List[Dict[str, str]]] = None) -> None:
        """Store a trading idea in both graph and vector backends."""
        # Store in graph backend
        self.graph_backend.store_idea(idea_id, content, metadata, relationships)
        
        # Store in vector backend
        self.vector_backend.store_idea(idea_id, content, metadata, relationships)
        
        # Add to GraphRAG knowledge graph
        content_text = json.dumps(content)
        self.graphrag.add_node(
            node_id=idea_id,
            node_type="Idea",
            text=content_text,
            properties={
                "content": content,
                "metadata": metadata
            }
        )
        
        # Add relationships to GraphRAG
        if relationships:
            for rel in relationships:
                self.graphrag.add_edge(
                    source_id=idea_id,
                    target_id=rel["target_id"],
                    edge_type=rel["type"]
                )
        
    def store_backtest(self,
                      backtest_id: str,
                      metrics: Dict[str, Any],
                      strategy_id: str,
                      idea_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store backtest results in both graph and vector backends."""
        # Store in graph backend
        self.graph_backend.store_backtest(backtest_id, metrics, strategy_id, idea_id, metadata)
        
        # Store in vector backend
        self.vector_backend.store_backtest(backtest_id, metrics, strategy_id, idea_id, metadata)
        
        # Add to GraphRAG knowledge graph
        metrics_text = json.dumps(metrics)
        self.graphrag.add_node(
            node_id=backtest_id,
            node_type="Backtest",
            text=metrics_text,
            properties={
                "metrics": metrics,
                "metadata": metadata or {}
            }
        )
        
        # Add relationships to GraphRAG
        self.graphrag.add_edge(
            source_id=strategy_id,
            target_id=backtest_id,
            edge_type="HAS_BACKTEST"
        )
        
        if idea_id:
            self.graphrag.add_edge(
                source_id=backtest_id,
                target_id=idea_id,
                edge_type="IMPLEMENTS_IDEA"
            )
        
    def store_strategy(self,
                      strategy_id: str,
                      code: str,
                      version: str,
                      idea_id: Optional[str] = None,
                      parent_strategy_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a strategy in both graph and vector backends."""
        # Store in graph backend
        self.graph_backend.store_strategy(strategy_id, code, version, idea_id, parent_strategy_id, metadata)
        
        # Store in vector backend
        self.vector_backend.store_strategy(strategy_id, code, version, idea_id, parent_strategy_id, metadata)
        
        # Add to GraphRAG knowledge graph
        self.graphrag.add_node(
            node_id=strategy_id,
            node_type="Strategy",
            text=code,
            properties={
                "code": code,
                "version": version,
                "metadata": metadata or {}
            }
        )
        
        # Add relationships to GraphRAG
        if parent_strategy_id:
            self.graphrag.add_edge(
                source_id=strategy_id,
                target_id=parent_strategy_id,
                edge_type="DERIVED_FROM"
            )
            
        if idea_id:
            self.graphrag.add_edge(
                source_id=strategy_id,
                target_id=idea_id,
                edge_type="IMPLEMENTS_IDEA"
            )
        
    def query_similar_ideas(self,
                          text: str,
                          top_k: int = 5,
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find similar ideas using GraphRAG's hybrid search."""
        # Use GraphRAG's hybrid search (combines vector and graph)
        query_embedding = self._get_embedding(text)
        
        # Build filter condition
        filter_condition = "node:Idea"
        if filters:
            for key, value in filters.items():
                filter_condition += f" AND node.metadata.{key} = '{value}'"
        
        # Execute hybrid search
        results = self.graphrag.hybrid_search(
            query=text,
            node_types=["Idea"],
            filter_condition=filter_condition,
            top_k=top_k
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result["node_id"],
                "content": result["properties"].get("content", {}),
                "metadata": result["properties"].get("metadata", {}),
                "score": result["score"]
            })
            
        return formatted_results
        
    def query_strategy_history(self,
                             strategy_id: str,
                             include_backtests: bool = True) -> Dict[str, Any]:
        """Get the full history of a strategy using the graph backend."""
        # This operation is better suited for the graph backend
        return self.graph_backend.query_strategy_history(strategy_id, include_backtests)
        
    def find_top_strategies(self,
                          metric: str,
                          timeframe: Optional[str] = None,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Find top performing strategies using the graph backend."""
        # This operation is better suited for the graph backend
        return self.graph_backend.find_top_strategies(metric, timeframe, filters, limit)
        
    def get_related_nodes(self,
                         node_id: str,
                         relationship_types: Optional[List[str]] = None,
                         max_depth: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Get nodes related to a given node using GraphRAG's graph traversal."""
        # Use GraphRAG's graph traversal capabilities
        
        # Build relationship pattern
        rel_pattern = "*"
        if relationship_types:
            rel_pattern = "|".join(relationship_types)
            
        # Execute graph traversal
        results = self.graphrag.traverse_graph(
            start_node_id=node_id,
            relationship_pattern=rel_pattern,
            max_depth=max_depth
        )
        
        # Group by relationship type
        related_nodes = {}
        
        for result in results:
            rel_type = result["relationship_type"]
            
            if rel_type not in related_nodes:
                related_nodes[rel_type] = []
                
            related_nodes[rel_type].append({
                "id": result["target_id"],
                "labels": result["target_labels"],
                "properties": result["target_properties"]
            })
            
        return related_nodes
        
    def rag_query(self, prompt: str, top_k: int = 5) -> str:
        """
        Perform a RAG query using GraphRAG.
        
        Args:
            prompt: The query prompt
            top_k: Number of relevant nodes to retrieve
            
        Returns:
            Enhanced response with context from the knowledge graph
        """
        # Use GraphRAG's RAG capabilities
        response = self.graphrag.rag_query(
            query=prompt,
            top_k=top_k
        )
        
        return response

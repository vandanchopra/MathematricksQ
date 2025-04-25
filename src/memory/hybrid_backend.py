# src/memory/hybrid_backend.py
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from .interface import MemoryBackend, IdeaDict, ScenarioDict, ContextDict, BacktestDict, MetricsDict
from .graph_backend import Neo4jMemory
from .patann_backend import PatANNMemory

class HybridMemory(MemoryBackend):
    """Hybrid memory implementation combining Neo4j for graph relationships and PatANN for vector embeddings."""
    
    def __init__(self, 
                 neo4j_uri: str = None, 
                 neo4j_user: str = None, 
                 neo4j_password: str = None,
                 patann_url: str = "http://localhost:9200",
                 model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the hybrid memory backend.
        
        Args:
            neo4j_uri: URI for the Neo4j database
            neo4j_user: Username for the Neo4j database
            neo4j_password: Password for the Neo4j database
            patann_url: URL of the PatAnn server
            model_name: Name of the sentence transformer model to use
        """
        # Initialize the underlying backends
        self.graph_backend = Neo4jMemory(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password
        )
        self.vector_backend = PatANNMemory(
            patann_url=patann_url,
            model_name=model_name
        )
    
    def store_idea(self, idea_id: str, description: str, context_ids: List[str]) -> None:
        """Store a trading idea with links to relevant contexts."""
        # Store in both backends
        self.graph_backend.store_idea(idea_id, description, context_ids)
        self.vector_backend.store_idea(idea_id, description, context_ids)
    
    def store_scenario(self, scenario_id: str, description: str, parent_idea_id: str, context_ids: List[str]) -> None:
        """Store a trading scenario with links to parent idea and relevant contexts."""
        # Store in both backends
        self.graph_backend.store_scenario(scenario_id, description, parent_idea_id, context_ids)
        self.vector_backend.store_scenario(scenario_id, description, parent_idea_id, context_ids)
    
    def store_context(self, context_id: str, market: str, timeframe: str) -> None:
        """Store a trading context (market and timeframe)."""
        # Store in both backends
        self.graph_backend.store_context(context_id, market, timeframe)
        self.vector_backend.store_context(context_id, market, timeframe)
    
    def store_backtest(self, backtest_id: str, metrics: MetricsDict, idea_id: str, context_id: str) -> None:
        """Store backtest results with links to the idea and context."""
        # Store in graph backend (vector backend doesn't store backtests)
        self.graph_backend.store_backtest(backtest_id, metrics, idea_id, context_id)
    
    def get_idea(self, idea_id: str) -> Optional[IdeaDict]:
        """Retrieve a specific idea by ID."""
        # Prefer graph backend for retrieving specific entities
        return self.graph_backend.get_idea(idea_id)
    
    def get_scenario(self, scenario_id: str) -> Optional[ScenarioDict]:
        """Retrieve a specific scenario by ID."""
        # Prefer graph backend for retrieving specific entities
        return self.graph_backend.get_scenario(scenario_id)
    
    def get_context(self, context_id: str) -> Optional[ContextDict]:
        """Retrieve a specific context by ID."""
        # Prefer graph backend for retrieving specific entities
        return self.graph_backend.get_context(context_id)
    
    def get_backtest(self, backtest_id: str) -> Optional[BacktestDict]:
        """Retrieve a specific backtest by ID."""
        # Only graph backend stores backtests
        return self.graph_backend.get_backtest(backtest_id)
    
    def query_similar_ideas(self, embedding: List[float], context_id: Optional[str] = None, top_k: int = 10) -> List[IdeaDict]:
        """Find similar ideas using vector similarity."""
        # Use vector backend for similarity search
        return self.vector_backend.query_similar_ideas(embedding, context_id, top_k)
    
    def query_top_ideas_by_metrics(self, context_id: Optional[str] = None, metric: str = "Sharpe", weights: Optional[Dict[str, float]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find top ideas based on backtest metrics, optionally with custom weighting."""
        # Use graph backend for metric-based queries
        return self.graph_backend.query_top_ideas_by_metrics(context_id, metric, weights, limit)
    
    def query_scenarios_for_idea(self, idea_id: str) -> List[ScenarioDict]:
        """Find all scenarios derived from a specific idea."""
        # Use graph backend for relationship queries
        return self.graph_backend.query_scenarios_for_idea(idea_id)
    
    def query_backtests_for_idea(self, idea_id: str, context_id: Optional[str] = None) -> List[BacktestDict]:
        """Find all backtests for a specific idea, optionally filtered by context."""
        # Use graph backend for backtest queries
        return self.graph_backend.query_backtests_for_idea(idea_id, context_id)
    
    def query_ideas_for_context(self, context_id: str) -> List[IdeaDict]:
        """Find all ideas that apply to a specific context."""
        # Use graph backend for relationship queries
        return self.graph_backend.query_ideas_for_context(context_id)
    
    def rag_query(self, prompt: str, context_id: Optional[str] = None, top_k: int = 5) -> str:
        """Perform a RAG query to get insights from the knowledge graph."""
        # This would be implemented with a specialized RAG system
        # For now, we'll return a mock response
        context_str = f" in context {context_id}" if context_id else ""
        return f"RAG response for: {prompt}{context_str}\nTop {top_k} ideas with rationale would be returned here."
    
    def recommend_ideas(self, current_strategy_embedding: List[float], context_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Recommend ideas for a given strategy embedding and context using the hybrid approach."""
        # Step 1: Get similar ideas using vector similarity
        similar_ideas = self.query_similar_ideas(
            embedding=current_strategy_embedding,
            context_id=context_id,
            top_k=top_k * 2  # Get more than we need for re-ranking
        )
        
        if not similar_ideas:
            return []
        
        # Step 2: Re-rank based on backtest metrics
        idea_ids = [idea["id"] for idea in similar_ideas]
        
        # Use the graph backend to re-rank based on metrics
        ranked_ideas = self.graph_backend.query_top_ideas_by_metrics(
            context_id=context_id,
            weights={"Sharpe": 0.5, "CAGR": 0.3, "MaxDrawdown": -0.2},
            limit=top_k
        )
        
        # If we don't have enough ranked ideas, fall back to the vector similarity results
        if len(ranked_ideas) < top_k:
            # Add vector similarity results that aren't already in the ranked ideas
            ranked_idea_ids = {idea["id"] for idea in ranked_ideas}
            for idea in similar_ideas:
                if idea["id"] not in ranked_idea_ids and len(ranked_ideas) < top_k:
                    ranked_ideas.append({
                        "id": idea["id"],
                        "description": idea["description"],
                        "created_at": idea["created_at"],
                        "similarity_score": 0.9,  # Mock similarity score
                        "metrics": {}  # No metrics available
                    })
        
        return ranked_ideas
